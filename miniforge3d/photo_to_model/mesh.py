from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from miniforge3d.photo_to_model.models import PhotoToModelError, PhotoToModelSettings


FEET_BAND_MM = 3.0
BASE_OVERLAP_MM = 0.6
MIN_BASE_RADIUS_RATIO = 0.15


@dataclass
class PrintableMesh:
    mesh: Any
    statistics: dict[str, Any]
    warnings: list[str] = field(default_factory=list)


def _trimesh() -> Any:
    try:
        import trimesh
    except ImportError as exc:
        raise PhotoToModelError(
            "Processamento de malha não instalado. Execute: python -m pip install -e '.[photo]'"
        ) from exc
    return trimesh


def load_mesh(path: Path) -> Any:
    trimesh = _trimesh()
    try:
        loaded = trimesh.load(str(path), force="mesh")
    except Exception as exc:
        raise PhotoToModelError(f"Não foi possível ler a malha gerada: {exc}") from exc
    if loaded.is_empty or len(loaded.faces) == 0:
        raise PhotoToModelError("A malha gerada está vazia.")
    # Somente a geometria interessa para impressão monocromática.
    return trimesh.Trimesh(vertices=loaded.vertices, faces=loaded.faces, process=True)


def _keep_main_components(mesh: Any, min_ratio: float, warnings: list[str]) -> Any:
    trimesh = _trimesh()
    parts = mesh.split(only_watertight=False)
    if len(parts) <= 1:
        return mesh
    total = sum(len(part.faces) for part in parts)
    kept = [part for part in parts if len(part.faces) >= total * min_ratio]
    if not kept:
        kept = [max(parts, key=lambda part: len(part.faces))]
    removed = len(parts) - len(kept)
    if removed:
        warnings.append(f"{removed} fragmento(s) solto(s) removido(s) da malha.")
    return trimesh.util.concatenate(kept)


def _orient_y_up_to_z_up(mesh: Any) -> None:
    trimesh = _trimesh()
    # glTF usa Y para cima e frente em +Z; o Bambu Studio usa Z para cima e frente em -Y.
    mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0)))


def _scale_to_height(mesh: Any, height_mm: float) -> None:
    extent = float(mesh.extents[2])
    if extent <= 0:
        raise PhotoToModelError("A malha gerada não tem altura.")
    mesh.apply_scale(height_mm / extent)
    _place_on_plate(mesh)


def _place_on_plate(mesh: Any) -> None:
    bounds = mesh.bounds
    center_xy = (bounds[0][:2] + bounds[1][:2]) / 2.0
    mesh.apply_translation((-center_xy[0], -center_xy[1], -bounds[0][2]))


def _flatten_bottom(mesh: Any, flatten_mm: float, warnings: list[str]) -> Any:
    if flatten_mm <= 0:
        return mesh
    if not mesh.is_watertight:
        warnings.append("Malha não fechada: os pés não foram aplainados.")
        return mesh
    try:
        cut = mesh.slice_plane(plane_origin=(0, 0, flatten_mm), plane_normal=(0, 0, 1), cap=True)
    except Exception as exc:
        warnings.append(f"Não foi possível aplainar os pés: {exc}")
        return mesh
    if cut is None or cut.is_empty or not cut.is_watertight:
        warnings.append("O corte dos pés não ficou fechado; mantida a malha original.")
        return mesh
    cut.apply_translation((0, 0, -flatten_mm))
    return cut


def _round_base(mesh: Any, settings: PhotoToModelSettings) -> Any:
    trimesh = _trimesh()
    vertices = mesh.vertices
    feet = vertices[vertices[:, 2] <= FEET_BAND_MM][:, :2]
    if len(feet) == 0:
        feet = vertices[:, :2]
    center = (feet.min(axis=0) + feet.max(axis=0)) / 2.0
    radius = float(np.linalg.norm(feet - center, axis=1).max()) + settings.base_margin_mm
    radius = max(radius, settings.height_mm * MIN_BASE_RADIUS_RATIO)
    height = settings.base_height_mm + BASE_OVERLAP_MM
    base = trimesh.creation.cylinder(radius=radius, height=height, sections=128)
    base.apply_translation((center[0], center[1], BASE_OVERLAP_MM - height / 2.0))
    return base


def _merge_base(mesh: Any, base: Any, warnings: list[str]) -> Any:
    trimesh = _trimesh()
    if mesh.is_watertight:
        try:
            merged = trimesh.boolean.union([mesh, base], engine="manifold")
            if merged is not None and not merged.is_empty:
                return merged
        except Exception as exc:
            warnings.append(f"União figura+base falhou ({exc}); peças apenas sobrepostas.")
    else:
        warnings.append("Figura não fechada: base apenas sobreposta (o Bambu Studio une ao fatiar).")
    return trimesh.util.concatenate([mesh, base])


def _try_close(mesh: Any, warnings: list[str]) -> Any:
    if mesh.is_watertight:
        return mesh
    mesh.fill_holes()
    mesh.fix_normals()
    if not mesh.is_watertight:
        warnings.append(
            "A malha não ficou totalmente fechada. Use 'Reparar modelo' no Bambu Studio "
            "antes de fatiar."
        )
    return mesh


def make_printable(raw_mesh_path: Path, settings: PhotoToModelSettings) -> PrintableMesh:
    warnings: list[str] = []
    mesh = load_mesh(raw_mesh_path)
    raw_faces = int(len(mesh.faces))

    mesh = _keep_main_components(mesh, settings.min_component_ratio, warnings)
    mesh = _try_close(mesh, warnings)
    _orient_y_up_to_z_up(mesh)
    _scale_to_height(mesh, settings.height_mm)
    mesh = _flatten_bottom(mesh, settings.flatten_mm, warnings)
    _scale_to_height(mesh, settings.height_mm)

    figure_extents = [round(float(value), 2) for value in mesh.extents]
    if settings.base == "round":
        base = _round_base(mesh, settings)
        mesh = _merge_base(mesh, base, warnings)
        _place_on_plate(mesh)

    statistics = {
        "raw_faces": raw_faces,
        "faces": int(len(mesh.faces)),
        "vertices": int(len(mesh.vertices)),
        "watertight": bool(mesh.is_watertight),
        "figure_size_mm": dict(zip(("x", "y", "z"), figure_extents)),
        "total_size_mm": dict(zip(("x", "y", "z"), (round(float(v), 2) for v in mesh.extents))),
        "volume_cm3": round(float(mesh.volume) / 1000.0, 2) if mesh.is_watertight else None,
    }
    return PrintableMesh(mesh=mesh, statistics=statistics, warnings=warnings)
