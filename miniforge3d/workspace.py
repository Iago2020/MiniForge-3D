from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from secrets import token_hex
from typing import Any

from miniforge3d.manifests import write_json_atomic


WORKSPACE_DIRECTORIES = {
    "input": "input",
    "frame_preparation": "01-frames",
    "reconstruction": "02-reconstruction",
    "mesh_processing": "03-mesh",
    "print_preparation": "04-print",
    "logs": "logs",
}


@dataclass(frozen=True)
class Workspace:
    run_id: str
    root: Path

    def directory(self, key: str) -> Path:
        return self.root / WORKSPACE_DIRECTORIES[key]


def create_workspace(workspaces_root: Path, project_id: str) -> Workspace:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{project_id}-{timestamp}-{token_hex(2)}"
    root = workspaces_root.resolve() / run_id
    root.mkdir(parents=True, exist_ok=False)
    for relative in WORKSPACE_DIRECTORIES.values():
        (root / relative).mkdir()
    return Workspace(run_id=run_id, root=root)


def open_workspace(root: Path) -> Workspace:
    root = root.resolve()
    pipeline_path = root / "pipeline.json"
    if not pipeline_path.is_file():
        raise ValueError(f"Workspace inválido; pipeline.json ausente: {root}")
    from miniforge3d.manifests import read_json

    pipeline = read_json(pipeline_path)
    run_id = pipeline.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError(f"run_id inválido em {pipeline_path}")
    return Workspace(run_id=run_id, root=root)


def initialize_workspace_files(
    workspace: Workspace,
    config: dict[str, Any],
    pipeline: dict[str, Any],
) -> None:
    write_json_atomic(workspace.root / "resolved-config.json", config)
    write_json_atomic(workspace.root / "pipeline.json", pipeline)

