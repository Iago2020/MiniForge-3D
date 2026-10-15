from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from miniforge3d.fingerprints import config_fingerprint, input_fingerprint
from miniforge3d.manifests import write_json_atomic
from miniforge3d.photo_to_model.engines import GenerationEngine, build_engine
from miniforge3d.photo_to_model.image_prep import MaskProvider, prepare_photo
from miniforge3d.photo_to_model.mesh import make_printable
from miniforge3d.photo_to_model.models import PhotoToModelError, PhotoToModelSettings
from miniforge3d.reconstruction.processor import IMAGE_SUFFIXES


def generate_from_photo(
    image_path: Path,
    output_dir: Path,
    settings: PhotoToModelSettings,
    run_id: str,
    engine: GenerationEngine | None = None,
    mask_provider: MaskProvider | None = None,
) -> dict[str, Any]:
    settings.validate()
    image_path = image_path.resolve()
    if not image_path.is_file():
        raise PhotoToModelError(f"Foto não encontrada: {image_path}")
    if image_path.suffix.lower() not in IMAGE_SUFFIXES | {".webp"}:
        raise PhotoToModelError(f"Formato de foto não suportado: {image_path.suffix}")

    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise PhotoToModelError(
            f"A saída já contém arquivos e não será sobrescrita: {output_dir}"
        )
    engine = engine or build_engine(settings)
    started_at = datetime.now(UTC)

    prepared = prepare_photo(
        image_path,
        output_dir / "01-input" / "prepared.png",
        margin_ratio=settings.crop_margin_ratio,
        use_segmentation=settings.local_segmentation,
        mask_provider=mask_provider,
    )
    if prepared.framing_problems and not settings.allow_cropped:
        raise PhotoToModelError(
            "Foto inadequada: " + "; ".join(prepared.framing_problems) + ". A IA tende a gerar "
            "uma placa achatada nesses casos. Use uma foto com a pessoa inteira dentro do "
            "quadro e espaço em volta da cabeça, ou rode com --allow-cropped para tentar assim mesmo. "
            f"Recorte salvo em {prepared.path}."
        )
    raw_mesh = engine.generate(prepared.path, prepared.has_alpha, output_dir / "02-generation")
    printable = make_printable(raw_mesh, settings)

    print_dir = output_dir / "03-print"
    print_dir.mkdir(parents=True, exist_ok=True)
    stl_path = print_dir / "model.stl"
    printable.mesh.export(str(stl_path))

    finished_at = datetime.now(UTC)
    manifest = {
        "schema_version": "1.0",
        "run_id": run_id,
        "step": "photo_to_model",
        "status": "completed",
        "effective_config": settings.to_dict(),
        "engine": {"name": engine.name, "source": engine.source},
        "inputs": [str(image_path)],
        "outputs": [str(prepared.path), str(raw_mesh), str(stl_path)],
        "input_fingerprint": input_fingerprint([image_path]),
        "config_fingerprint": config_fingerprint(settings.to_dict()),
        "statistics": {
            "foreground_ratio": prepared.foreground_ratio,
            **printable.statistics,
        },
        "warnings": prepared.warnings
        + [f"Enquadramento: {problem}." for problem in prepared.framing_problems]
        + printable.warnings,
        "error": None,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 4),
    }
    write_json_atomic(output_dir / "manifest.json", manifest)
    return manifest
