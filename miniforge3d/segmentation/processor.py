from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import cv2
import numpy as np

from miniforge3d.fingerprints import config_fingerprint, input_fingerprint
from miniforge3d.manifests import write_json_atomic
from miniforge3d.reconstruction.processor import IMAGE_SUFFIXES


class PersonSegmentationError(RuntimeError):
    """Raised when person masks cannot be generated safely."""


@dataclass(frozen=True)
class PersonSegmentationSettings:
    model: str = "u2net_human_seg"
    threshold: int = 127
    background: str = "white"

    def validate(self) -> None:
        if not self.model.strip():
            raise ValueError("model não pode ser vazio.")
        if not 0 <= self.threshold <= 255:
            raise ValueError("threshold deve estar entre 0 e 255.")
        if self.background not in {"white", "black"}:
            raise ValueError("background deve ser 'white' ou 'black'.")


def _load_rembg(settings: PersonSegmentationSettings) -> Callable[[np.ndarray], Any]:
    try:
        from rembg import new_session, remove
    except ImportError as exc:
        raise PersonSegmentationError(
            "Segmentação não instalada. Execute: python -m pip install -e '.[segmentation]'"
        ) from exc
    try:
        session = new_session(settings.model)
    except Exception as exc:
        raise PersonSegmentationError(
            f"Não foi possível carregar o modelo de segmentação '{settings.model}': {exc}"
        ) from exc

    def provider(image: np.ndarray) -> Any:
        return remove(image, session=session, only_mask=True)

    return provider


def _normalize_mask(raw_mask: Any, shape: tuple[int, int], threshold: int) -> np.ndarray:
    if isinstance(raw_mask, bytes):
        raw_mask = cv2.imdecode(np.frombuffer(raw_mask, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    mask = np.asarray(raw_mask)
    if mask.ndim == 3:
        mask = mask[:, :, 3] if mask.shape[2] == 4 else cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    if mask.shape[:2] != shape:
        mask = cv2.resize(mask, (shape[1], shape[0]), interpolation=cv2.INTER_LINEAR)
    mask = np.where(mask >= threshold, 255, 0).astype(np.uint8)

    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if count <= 1:
        raise PersonSegmentationError("A máscara não encontrou uma pessoa.")
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    mask = np.where(labels == largest, 255, 0).astype(np.uint8)
    kernel = np.ones((5, 5), dtype=np.uint8)
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)


def segment_person_frames(
    frames_dir: Path,
    output_dir: Path,
    settings: PersonSegmentationSettings,
    run_id: str,
    mask_provider: Callable[[np.ndarray], Any] | None = None,
) -> dict[str, Any]:
    settings.validate()
    frames_dir = frames_dir.resolve()
    if not frames_dir.is_dir():
        raise PersonSegmentationError(f"Pasta de frames não encontrada: {frames_dir}")
    frames = sorted(
        path for path in frames_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )
    if not frames:
        raise PersonSegmentationError("Nenhum frame compatível foi encontrado.")

    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise PersonSegmentationError(
            f"A saída já contém arquivos e não será sobrescrita: {output_dir}"
        )
    provider = mask_provider or _load_rembg(settings)
    masked_dir = output_dir / "frames_masked"
    masks_dir = output_dir / "masks"
    masked_dir.mkdir(parents=True, exist_ok=True)
    masks_dir.mkdir()

    started_at = datetime.now(UTC)
    foreground_ratios: list[float] = []
    outputs: list[str] = []
    background_value = 255 if settings.background == "white" else 0

    try:
        for frame in frames:
            image = cv2.imread(str(frame), cv2.IMREAD_COLOR)
            if image is None:
                raise PersonSegmentationError(f"Não foi possível ler o frame: {frame}")
            mask = _normalize_mask(provider(image), image.shape[:2], settings.threshold)
            foreground_ratios.append(float(np.count_nonzero(mask)) / float(mask.size))

            output_name = f"{frame.stem}.png"
            masked_path = masked_dir / output_name
            mask_path = masks_dir / f"{output_name}.png"
            composed = np.full_like(image, background_value)
            composed[mask > 0] = image[mask > 0]
            if not cv2.imwrite(str(masked_path), composed):
                raise PersonSegmentationError(f"Falha ao gravar: {masked_path}")
            if not cv2.imwrite(str(mask_path), mask):
                raise PersonSegmentationError(f"Falha ao gravar: {mask_path}")
            outputs.extend((str(masked_path), str(mask_path)))

        finished_at = datetime.now(UTC)
        manifest = {
            "schema_version": "1.0",
            "run_id": run_id,
            "step": "person_segmentation",
            "status": "completed",
            "effective_config": {
                "model": settings.model,
                "threshold": settings.threshold,
                "background": settings.background,
            },
            "inputs": [str(path) for path in frames],
            "outputs": outputs,
            "input_fingerprint": input_fingerprint(frames),
            "config_fingerprint": config_fingerprint(
                {
                    "model": settings.model,
                    "threshold": settings.threshold,
                    "background": settings.background,
                }
            ),
            "statistics": {
                "input_images": len(frames),
                "generated_masks": len(frames),
                "mean_foreground_ratio": round(sum(foreground_ratios) / len(foreground_ratios), 6),
                "min_foreground_ratio": round(min(foreground_ratios), 6),
                "max_foreground_ratio": round(max(foreground_ratios), 6),
            },
            "warnings": [],
            "error": None,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_seconds": round((finished_at - started_at).total_seconds(), 4),
        }
        write_json_atomic(output_dir / "manifest.json", manifest)
        return manifest
    except Exception:
        raise
