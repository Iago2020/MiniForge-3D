from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


ENGINES = ("hunyuan3d", "trellis")
BASES = ("round", "none")


class PhotoToModelError(RuntimeError):
    """Raised when a printable model cannot be produced from a photo."""


@dataclass(frozen=True)
class PhotoToModelSettings:
    engine: str = "hunyuan3d"
    height_mm: float = 150.0
    base: str = "round"
    base_height_mm: float = 3.0
    base_margin_mm: float = 4.0
    flatten_mm: float = 0.5
    seed: int = 1234
    octree_resolution: int = 384
    steps: int = 30
    min_component_ratio: float = 0.02
    crop_margin_ratio: float = 0.08
    local_segmentation: bool = True
    allow_cropped: bool = False

    def validate(self) -> None:
        if self.engine not in ENGINES:
            raise ValueError(f"engine deve ser um de: {', '.join(ENGINES)}.")
        if not 20 <= self.height_mm <= 400:
            raise ValueError("height_mm deve estar entre 20 e 400.")
        if self.base not in BASES:
            raise ValueError(f"base deve ser um de: {', '.join(BASES)}.")
        if not 0.5 <= self.base_height_mm <= 20:
            raise ValueError("base_height_mm deve estar entre 0.5 e 20.")
        if not 0 <= self.base_margin_mm <= 50:
            raise ValueError("base_margin_mm deve estar entre 0 e 50.")
        if not 0 <= self.flatten_mm <= 5:
            raise ValueError("flatten_mm deve estar entre 0 e 5.")
        if not 0 <= self.seed <= 10_000_000:
            raise ValueError("seed deve estar entre 0 e 10000000.")
        if not 64 <= self.octree_resolution <= 512:
            raise ValueError("octree_resolution deve estar entre 64 e 512.")
        if not 5 <= self.steps <= 100:
            raise ValueError("steps deve estar entre 5 e 100.")
        if not 0 <= self.min_component_ratio < 1:
            raise ValueError("min_component_ratio deve estar entre 0 e 1.")
        if not 0 <= self.crop_margin_ratio <= 0.5:
            raise ValueError("crop_margin_ratio deve estar entre 0 e 0.5.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
