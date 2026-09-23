from __future__ import annotations

import json
import platform
import re
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from miniforge3d.engines.colmap import (
    ColmapCommand,
    ColmapSettings,
    build_colmap_commands,
    detect_colmap,
)
from miniforge3d.fingerprints import config_fingerprint, input_fingerprint
from miniforge3d.logging_utils import append_event
from miniforge3d.manifests import write_json_atomic


class ReconstructionError(RuntimeError):
    """Raised when reconstruction cannot be planned or executed safely."""


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def parse_model_analysis(output: str) -> dict[str, int | float]:
    fields: dict[str, tuple[str, type[int] | type[float]]] = {
        "Registered images": ("registered_images", int),
        "Points": ("points3d", int),
        "Observations": ("observations", int),
        "Mean track length": ("mean_track_length", float),
        "Mean observations per image": ("mean_observations_per_image", float),
        "Mean reprojection error": ("mean_reprojection_error_px", float),
    }
    statistics: dict[str, int | float] = {}
    for label, (key, converter) in fields.items():
        match = re.search(rf"{re.escape(label)}:\s+([0-9.]+)", output)
        if match:
            statistics[key] = converter(match.group(1))
    return statistics


def selected_images(images_dir: Path) -> list[Path]:
    images_dir = images_dir.resolve()
    if not images_dir.is_dir():
        raise ReconstructionError(f"Pasta de frames não encontrada: {images_dir}")
    images = sorted(
        path for path in images_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )
    if len(images) < 12:
        raise ReconstructionError(
            f"Foram encontrados apenas {len(images)} frames; são necessários pelo menos 12."
        )
    return images


def validate_masks(images: list[Path], masks_dir: Path | None) -> None:
    if masks_dir is None:
        return
    masks_dir = masks_dir.resolve()
    if not masks_dir.is_dir():
        raise ReconstructionError(f"Pasta de máscaras não encontrada: {masks_dir}")
    missing = [image.name for image in images if not (masks_dir / f"{image.name}.png").is_file()]
    if missing:
        preview = ", ".join(missing[:5])
        suffix = "..." if len(missing) > 5 else ""
        raise ReconstructionError(
            f"Faltam {len(missing)} máscaras no formato <imagem>.png: {preview}{suffix}"
        )


def _cuda_available() -> bool:
    executable = shutil.which("nvidia-smi")
    if not executable:
        return False
    try:
        result = subprocess.run(
            [executable, "--query-gpu=name", "--format=csv,noheader"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def build_reconstruction_plan(
    images_dir: Path,
    output_dir: Path,
    settings: ColmapSettings,
    executable: str = "colmap",
) -> dict[str, Any]:
    images = selected_images(images_dir)
    validate_masks(images, settings.masks_dir)
    commands = build_colmap_commands(executable, images_dir, output_dir, settings)
    warnings: list[str] = []
    if len(images) < 50:
        warnings.append(
            "Dataset pequeno para corpo inteiro; a cobertura pode ser insuficiente."
        )
    if settings.mode == "full" and not _cuda_available():
        warnings.append(
            "CUDA/NVIDIA não detectada: o plano completo não poderá ser executado nesta máquina."
        )
    return {
        "schema_version": "1.0",
        "engine": "colmap",
        "mode": settings.mode,
        "matcher": settings.matcher,
        "platform": platform.platform(),
        "images_dir": str(images_dir.resolve()),
        "image_count": len(images),
        "input_fingerprint": input_fingerprint(images),
        "config_fingerprint": config_fingerprint(
            {
                "mode": settings.mode,
                "matcher": settings.matcher,
                "camera_model": settings.camera_model,
                "sequential_overlap": settings.sequential_overlap,
                "max_image_size": settings.max_image_size,
                "use_gpu": settings.use_gpu,
                "masks_dir": str(settings.masks_dir.resolve()) if settings.masks_dir else None,
            }
        ),
        "cuda_available": _cuda_available(),
        "warnings": warnings,
        "commands": [command.to_dict() for command in commands],
    }


def _ensure_empty_output(output_dir: Path) -> None:
    if output_dir.exists():
        if not output_dir.is_dir():
            raise ReconstructionError(f"A saída não é um diretório: {output_dir}")
        if any(output_dir.iterdir()):
            raise ReconstructionError(
                f"A saída já contém arquivos e não será sobrescrita: {output_dir}"
            )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "logs").mkdir()
    (output_dir / "sparse").mkdir()


def _run_command(command: ColmapCommand, logs_dir: Path) -> dict[str, Any]:
    started = time.monotonic()
    result = subprocess.run(command.argv, check=False, capture_output=True, text=True)
    record = {
        "stage": command.stage,
        "command": list(command.argv),
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "duration_seconds": round(time.monotonic() - started, 4),
    }
    (logs_dir / f"{command.stage}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise ReconstructionError(
            f"COLMAP falhou em '{command.stage}' com código {result.returncode}."
        )
    return record


def reconstruct_colmap(
    images_dir: Path,
    output_dir: Path,
    settings: ColmapSettings,
    run_id: str,
) -> dict[str, Any]:
    availability = detect_colmap()
    if not availability.available or not availability.executable:
        raise ReconstructionError(availability.error or "COLMAP indisponível.")
    if settings.mode == "full" and not _cuda_available():
        raise ReconstructionError(
            "A reconstrução densa do COLMAP requer NVIDIA/CUDA. "
            "Neste Mac use --mode sparse ou execute --mode full no Nitro."
        )

    images = selected_images(images_dir)
    validate_masks(images, settings.masks_dir)
    output_dir = output_dir.resolve()
    _ensure_empty_output(output_dir)
    logs_dir = output_dir / "logs"
    pipeline_log = logs_dir / "reconstruction.log"
    commands = build_colmap_commands(
        availability.executable,
        images_dir,
        output_dir,
        settings,
    )
    started_at = datetime.now(UTC)
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": run_id,
        "step": "reconstruction",
        "status": "running",
        "tool_versions": {"colmap": availability.version_output},
        "effective_config": {
            "engine": "colmap",
            "mode": settings.mode,
            "matcher": settings.matcher,
            "camera_model": settings.camera_model,
            "sequential_overlap": settings.sequential_overlap,
            "max_image_size": settings.max_image_size,
            "use_gpu": settings.use_gpu,
            "masks_dir": str(settings.masks_dir.resolve()) if settings.masks_dir else None,
        },
        "inputs": [str(path) for path in images],
        "outputs": [],
        "input_fingerprint": input_fingerprint(images),
        "config_fingerprint": config_fingerprint(
            {
                "engine": "colmap",
                "mode": settings.mode,
                "matcher": settings.matcher,
                "camera_model": settings.camera_model,
                "sequential_overlap": settings.sequential_overlap,
                "max_image_size": settings.max_image_size,
                "use_gpu": settings.use_gpu,
                "masks_dir": str(settings.masks_dir.resolve()) if settings.masks_dir else None,
            }
        ),
        "statistics": {"input_images": len(images), "completed_stages": 0},
        "warnings": [],
        "error": None,
        "started_at": started_at.isoformat(),
        "finished_at": None,
        "duration_seconds": None,
    }
    manifest_path = output_dir / "manifest.json"
    write_json_atomic(manifest_path, manifest)
    write_json_atomic(
        output_dir / "reconstruction-plan.json",
        build_reconstruction_plan(images_dir, output_dir, settings, availability.executable),
    )
    append_event(pipeline_log, "reconstruction_started", {"mode": settings.mode})

    try:
        for command in commands:
            record = _run_command(command, logs_dir)
            manifest["statistics"]["completed_stages"] += 1
            if command.stage == "sparse_analysis":
                analysis = parse_model_analysis(
                    f"{record['stdout']}\n{record['stderr']}"
                )
                manifest["statistics"].update(analysis)
                registered = int(analysis.get("registered_images", 0))
                manifest["statistics"]["registration_ratio"] = round(
                    registered / len(images), 6
                )
                if registered < len(images):
                    manifest["warnings"].append(
                        f"COLMAP registrou {registered} de {len(images)} imagens."
                    )
            write_json_atomic(manifest_path, manifest)

        outputs = [str(output_dir / "database.db"), str(output_dir / "sparse" / "0")]
        if settings.mode == "full":
            outputs.extend(
                [
                    str(output_dir / "dense" / "fused.ply"),
                    str(output_dir / "dense" / "meshed-poisson.ply"),
                    str(output_dir / "dense" / "meshed-delaunay.ply"),
                    str(output_dir / "dense" / "textured"),
                ]
            )
        missing_outputs = [path for path in outputs if not Path(path).exists()]
        if missing_outputs:
            raise ReconstructionError(
                "COLMAP terminou sem produzir saídas obrigatórias: "
                + ", ".join(missing_outputs)
            )
        finished_at = datetime.now(UTC)
        manifest.update(
            {
                "status": "completed",
                "outputs": outputs,
                "finished_at": finished_at.isoformat(),
                "duration_seconds": round((finished_at - started_at).total_seconds(), 4),
            }
        )
        write_json_atomic(manifest_path, manifest)
        append_event(pipeline_log, "reconstruction_completed", manifest["statistics"])
        return manifest
    except Exception as exc:
        finished_at = datetime.now(UTC)
        manifest.update(
            {
                "status": "failed",
                "error": {"type": type(exc).__name__, "message": str(exc)},
                "finished_at": finished_at.isoformat(),
                "duration_seconds": round((finished_at - started_at).total_seconds(), 4),
            }
        )
        write_json_atomic(manifest_path, manifest)
        append_event(pipeline_log, "reconstruction_failed", {"error": manifest["error"]})
        raise
