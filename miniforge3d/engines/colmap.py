from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class ColmapAvailability:
    available: bool
    executable: str | None
    version_output: str | None
    error: str | None


@dataclass(frozen=True)
class ColmapSettings:
    mode: Literal["sparse", "full"] = "full"
    matcher: Literal["exhaustive", "sequential"] = "exhaustive"
    camera_model: str = "SIMPLE_RADIAL"
    sequential_overlap: int = 10
    max_image_size: int = 2000
    use_gpu: bool = True
    masks_dir: Path | None = None

    def validate(self) -> None:
        if self.mode not in {"sparse", "full"}:
            raise ValueError("mode deve ser 'sparse' ou 'full'.")
        if self.matcher not in {"exhaustive", "sequential"}:
            raise ValueError("matcher deve ser 'exhaustive' ou 'sequential'.")
        if not self.camera_model or not self.camera_model.replace("_", "").isalnum():
            raise ValueError("camera_model inválido.")
        if not 1 <= self.sequential_overlap <= 100:
            raise ValueError("sequential_overlap deve estar entre 1 e 100.")
        if not 320 <= self.max_image_size <= 16000:
            raise ValueError("max_image_size deve estar entre 320 e 16000.")


@dataclass(frozen=True)
class ColmapCommand:
    stage: str
    argv: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {"stage": self.stage, "argv": list(self.argv)}


def detect_colmap() -> ColmapAvailability:
    executable = shutil.which("COLMAP.bat") or shutil.which("colmap")
    if not executable:
        return ColmapAvailability(False, None, None, "COLMAP não encontrado no PATH.")
    try:
        result = subprocess.run(
            [executable, "-h"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return ColmapAvailability(True, executable, None, str(exc))
    output = (result.stdout or result.stderr).strip()
    return ColmapAvailability(True, executable, output.splitlines()[0] if output else None, None)


def build_colmap_commands(
    executable: str,
    images_dir: Path,
    output_dir: Path,
    settings: ColmapSettings,
) -> list[ColmapCommand]:
    settings.validate()
    images_dir = images_dir.resolve()
    output_dir = output_dir.resolve()
    database = output_dir / "database.db"
    sparse = output_dir / "sparse"
    sparse_model = sparse / "0"
    dense = output_dir / "dense"
    gpu_flag = "1" if settings.use_gpu else "0"

    commands = [
        ColmapCommand(
            "feature_extraction",
            (
                executable,
                "feature_extractor",
                "--database_path",
                str(database),
                "--image_path",
                str(images_dir),
                "--ImageReader.camera_model",
                settings.camera_model,
                "--ImageReader.single_camera",
                "1",
                "--FeatureExtraction.use_gpu",
                gpu_flag,
                "--FeatureExtraction.max_image_size",
                str(settings.max_image_size),
            ),
        ),
        ColmapCommand(
            "sparse_mapping",
            (
                executable,
                "mapper",
                "--database_path",
                str(database),
                "--image_path",
                str(images_dir),
                "--output_path",
                str(sparse),
            ),
        ),
        ColmapCommand(
            "sparse_analysis",
            (
                executable,
                "model_analyzer",
                "--path",
                str(sparse_model),
            ),
        ),
    ]
    if settings.masks_dir is not None:
        feature_argv = list(commands[0].argv)
        feature_argv.extend(
            ["--ImageReader.mask_path", str(settings.masks_dir.resolve())]
        )
        commands[0] = ColmapCommand("feature_extraction", tuple(feature_argv))
    if settings.matcher == "exhaustive":
        matching_command = ColmapCommand(
            "exhaustive_matching",
            (
                executable,
                "exhaustive_matcher",
                "--database_path",
                str(database),
                "--FeatureMatching.use_gpu",
                gpu_flag,
            ),
        )
    else:
        matching_command = ColmapCommand(
            "sequential_matching",
            (
                executable,
                "sequential_matcher",
                "--database_path",
                str(database),
                "--FeatureMatching.use_gpu",
                gpu_flag,
                "--SequentialMatching.overlap",
                str(settings.sequential_overlap),
                "--SequentialMatching.loop_detection",
                "1",
            ),
        )
    commands.insert(1, matching_command)
    if settings.mode == "sparse":
        return commands

    commands.extend(
        [
            ColmapCommand(
                "image_undistortion",
                (
                    executable,
                    "image_undistorter",
                    "--image_path",
                    str(images_dir),
                    "--input_path",
                    str(sparse_model),
                    "--output_path",
                    str(dense),
                    "--output_type",
                    "COLMAP",
                    "--max_image_size",
                    str(settings.max_image_size),
                ),
            ),
            ColmapCommand(
                "dense_stereo",
                (
                    executable,
                    "patch_match_stereo",
                    "--workspace_path",
                    str(dense),
                    "--workspace_format",
                    "COLMAP",
                    "--PatchMatchStereo.geom_consistency",
                    "1",
                    "--PatchMatchStereo.max_image_size",
                    str(settings.max_image_size),
                ),
            ),
            ColmapCommand(
                "stereo_fusion",
                (
                    executable,
                    "stereo_fusion",
                    "--workspace_path",
                    str(dense),
                    "--workspace_format",
                    "COLMAP",
                    "--input_type",
                    "geometric",
                    "--output_path",
                    str(dense / "fused.ply"),
                ),
            ),
            ColmapCommand(
                "poisson_meshing",
                (
                    executable,
                    "poisson_mesher",
                    "--input_path",
                    str(dense / "fused.ply"),
                    "--output_path",
                    str(dense / "meshed-poisson.ply"),
                ),
            ),
            ColmapCommand(
                "delaunay_meshing",
                (
                    executable,
                    "delaunay_mesher",
                    "--input_path",
                    str(dense),
                    "--output_path",
                    str(dense / "meshed-delaunay.ply"),
                ),
            ),
            ColmapCommand(
                "mesh_texturing",
                (
                    executable,
                    "mesh_texturer",
                    "--workspace_path",
                    str(dense),
                    "--input_path",
                    str(dense / "meshed-poisson.ply"),
                    "--output_path",
                    str(dense / "textured"),
                ),
            ),
        ]
    )
    return commands
