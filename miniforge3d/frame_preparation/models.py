from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FramePreparationSettings:
    candidate_fps: float = 8.0
    selection_window_seconds: float = 0.35
    max_selected_frames: int = 350
    blur_percentile: float = 20.0
    min_blur_score: float = 40.0
    min_brightness: float = 25.0
    max_brightness: float = 235.0
    min_contrast: float = 18.0
    duplicate_hash_distance: int = 6
    max_duplicate_gap_seconds: float = 0.75
    jpeg_quality: int = 2

    def validate(self) -> None:
        if self.candidate_fps <= 0 or self.candidate_fps > 60:
            raise ValueError("candidate_fps deve estar entre 0 e 60.")
        if self.selection_window_seconds <= 0:
            raise ValueError("selection_window_seconds deve ser maior que zero.")
        if self.max_selected_frames <= 0:
            raise ValueError("max_selected_frames deve ser maior que zero.")
        if not 0 <= self.blur_percentile <= 100:
            raise ValueError("blur_percentile deve estar entre 0 e 100.")
        if not 0 <= self.min_brightness < self.max_brightness <= 255:
            raise ValueError("Faixa de brilho inválida.")
        if self.min_contrast < 0:
            raise ValueError("min_contrast não pode ser negativo.")
        if not 0 <= self.duplicate_hash_distance <= 64:
            raise ValueError("duplicate_hash_distance deve estar entre 0 e 64.")
        if self.max_duplicate_gap_seconds <= 0:
            raise ValueError("max_duplicate_gap_seconds deve ser maior que zero.")
        if not 1 <= self.jpeg_quality <= 31:
            raise ValueError("jpeg_quality deve estar entre 1 e 31.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FrameMetrics:
    index: int
    path: Path
    timestamp_seconds: float
    blur_score: float
    brightness: float
    contrast: float
    difference_hash: int
    width: int
    height: int
    selected: bool = False
    rejection_reason: str | None = None

    @property
    def quality_score(self) -> float:
        return self.blur_score * (1.0 + min(self.contrast, 128.0) / 128.0)

    def to_dict(self, root: Path) -> dict[str, Any]:
        try:
            path_value = str(self.path.relative_to(root))
        except ValueError:
            path_value = str(self.path)
        return {
            "index": self.index,
            "path": path_value,
            "timestamp_seconds": round(self.timestamp_seconds, 6),
            "blur_score": round(self.blur_score, 4),
            "brightness": round(self.brightness, 4),
            "contrast": round(self.contrast, 4),
            "difference_hash": f"{self.difference_hash:016x}",
            "width": self.width,
            "height": self.height,
            "quality_score": round(self.quality_score, 4),
            "selected": self.selected,
            "rejection_reason": self.rejection_reason,
        }
