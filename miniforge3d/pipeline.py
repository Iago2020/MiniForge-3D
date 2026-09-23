from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from miniforge3d.config import resolve_video_paths
from miniforge3d.fingerprints import config_fingerprint, input_fingerprint
from miniforge3d.hardware import detect_hardware
from miniforge3d.logging_utils import append_event
from miniforge3d.manifests import read_json
from miniforge3d.workspace import (
    Workspace,
    create_workspace,
    initialize_workspace_files,
    open_workspace,
)


STEPS = (
    "frame_preparation",
    "reconstruction",
    "mesh_processing",
    "print_preparation",
)


class PipelineError(RuntimeError):
    """Raised when a requested pipeline operation is invalid or unavailable."""


def select_steps(start_from: str | None = None, only: str | None = None) -> list[str]:
    if start_from and only:
        raise PipelineError("Use apenas um entre --start-from e --only.")
    if only:
        if only not in STEPS:
            raise PipelineError(f"Etapa desconhecida: {only}")
        return [only]
    if start_from:
        if start_from not in STEPS:
            raise PipelineError(f"Etapa desconhecida: {start_from}")
        return list(STEPS[STEPS.index(start_from) :])
    return list(STEPS)


def build_pipeline_plan(
    config: dict[str, Any],
    base_dir: Path,
    workspace: Workspace,
    steps: list[str],
) -> dict[str, Any]:
    video_paths = resolve_video_paths(config, base_dir)
    missing = [str(path) for path in video_paths if not path.is_file()]
    now = datetime.now(UTC).isoformat()
    return {
        "schema_version": "1.0",
        "run_id": workspace.run_id,
        "status": "planned",
        "created_at": now,
        "updated_at": now,
        "base_dir": str(base_dir.resolve()),
        "config_fingerprint": config_fingerprint(config),
        "input_fingerprint": input_fingerprint(video_paths),
        "inputs": [str(path) for path in video_paths],
        "missing_inputs": missing,
        "selected_steps": steps,
        "hardware": detect_hardware(base_dir),
    }


def plan_new_run(
    config: dict[str, Any],
    base_dir: Path,
    workspaces_root: Path,
    start_from: str | None,
    only: str | None,
) -> tuple[Workspace, dict[str, Any]]:
    steps = select_steps(start_from=start_from, only=only)
    workspace = create_workspace(workspaces_root, config["project"]["id"])
    plan = build_pipeline_plan(config, base_dir, workspace, steps)
    plan["reusable_steps"] = []
    initialize_workspace_files(workspace, config, plan)
    append_event(
        workspace.directory("logs") / "pipeline.log",
        "pipeline_planned",
        {"run_id": workspace.run_id, "selected_steps": steps},
    )
    return workspace, plan


def _completed_reusable_steps(
    workspace: Workspace,
    config_hash: str,
    input_hash: str,
) -> list[str]:
    reusable: list[str] = []
    for step in STEPS:
        manifest_path = workspace.directory(step) / "manifest.json"
        if not manifest_path.is_file():
            continue
        manifest = read_json(manifest_path)
        if (
            manifest.get("status") == "completed"
            and manifest.get("config_fingerprint") == config_hash
            and manifest.get("input_fingerprint") == input_hash
        ):
            reusable.append(step)
    return reusable


def plan_resume_run(
    config: dict[str, Any],
    base_dir: Path,
    workspace_root: Path,
    start_from: str | None,
    only: str | None,
) -> tuple[Workspace, dict[str, Any]]:
    requested_steps = select_steps(start_from=start_from, only=only)
    workspace = open_workspace(workspace_root)
    previous = read_json(workspace.root / "pipeline.json")
    plan = build_pipeline_plan(config, base_dir, workspace, requested_steps)
    reusable = _completed_reusable_steps(
        workspace,
        plan["config_fingerprint"],
        plan["input_fingerprint"],
    )
    plan["resumed_from_status"] = previous.get("status")
    plan["reusable_steps"] = reusable
    plan["selected_steps"] = [step for step in requested_steps if step not in reusable]
    initialize_workspace_files(workspace, config, plan)
    append_event(
        workspace.directory("logs") / "pipeline.log",
        "pipeline_resume_planned",
        {
            "run_id": workspace.run_id,
            "selected_steps": plan["selected_steps"],
            "reusable_steps": reusable,
        },
    )
    return workspace, plan
