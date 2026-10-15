from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import cv2
import numpy as np

from miniforge3d.photo_to_model.models import PhotoToModelError
from miniforge3d.segmentation.processor import (
    PersonSegmentationError,
    PersonSegmentationSettings,
    _load_rembg,
    _normalize_mask,
)


MAX_SIDE = 1024
MaskProvider = Callable[[np.ndarray], Any]


@dataclass(frozen=True)
class PreparedPhoto:
    path: Path
    has_alpha: bool
    foreground_ratio: float | None
    warnings: list[str]


def _square_rgba(image: np.ndarray, mask: np.ndarray | None, margin_ratio: float) -> np.ndarray:
    height, width = image.shape[:2]
    if mask is None:
        alpha = np.full((height, width), 255, dtype=np.uint8)
        x0, y0, x1, y1 = 0, 0, width, height
    else:
        alpha = mask
        ys, xs = np.nonzero(mask)
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1

    rgba = np.dstack((image, alpha))[y0:y1, x0:x1]
    crop_h, crop_w = rgba.shape[:2]
    side = int(round(max(crop_h, crop_w) * (1 + 2 * margin_ratio)))
    canvas = np.zeros((side, side, 4), dtype=np.uint8)
    if mask is None:
        canvas[:, :, :3] = 255
        canvas[:, :, 3] = 255
    top = (side - crop_h) // 2
    left = (side - crop_w) // 2
    canvas[top : top + crop_h, left : left + crop_w] = rgba
    if side > MAX_SIDE:
        canvas = cv2.resize(canvas, (MAX_SIDE, MAX_SIDE), interpolation=cv2.INTER_AREA)
    return canvas


def prepare_photo(
    image_path: Path,
    output_path: Path,
    margin_ratio: float,
    use_segmentation: bool,
    mask_provider: MaskProvider | None = None,
) -> PreparedPhoto:
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise PhotoToModelError(f"Não foi possível ler a foto: {image_path}")

    warnings: list[str] = []
    mask: np.ndarray | None = None
    if use_segmentation:
        try:
            provider = mask_provider or _load_rembg(PersonSegmentationSettings())
            mask = _normalize_mask(provider(image), image.shape[:2], 127)
        except PersonSegmentationError as exc:
            warnings.append(
                f"Recorte local indisponível ({exc}). A foto será enviada inteira e o "
                "serviço remoto fará a remoção de fundo."
            )

    foreground_ratio = None
    if mask is not None:
        foreground_ratio = float(np.count_nonzero(mask)) / float(mask.size)
        if foreground_ratio < 0.03:
            warnings.append(
                "A pessoa ocupa pouco da foto. Use uma foto mais próxima para melhor fidelidade."
            )

    rgba = _square_rgba(image, mask, margin_ratio)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), rgba):
        raise PhotoToModelError(f"Falha ao gravar: {output_path}")
    return PreparedPhoto(
        path=output_path,
        has_alpha=mask is not None,
        foreground_ratio=None if foreground_ratio is None else round(foreground_ratio, 6),
        warnings=warnings,
    )
