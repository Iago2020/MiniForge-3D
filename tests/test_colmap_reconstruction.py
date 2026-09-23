from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from miniforge3d.engines.colmap import ColmapSettings, build_colmap_commands
from miniforge3d.reconstruction.processor import (
    ReconstructionError,
    build_reconstruction_plan,
    parse_model_analysis,
    selected_images,
    validate_masks,
)


def create_images(root: Path, count: int) -> Path:
    images = root / "frames_selected"
    images.mkdir()
    for index in range(count):
        (images / f"frame_{index:06d}.jpg").write_bytes(f"image-{index}".encode())
    return images


class ColmapCommandTests(unittest.TestCase):
    def test_sparse_plan_stops_after_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            commands = build_colmap_commands(
                "colmap",
                root / "images",
                root / "output",
                ColmapSettings(mode="sparse", use_gpu=False),
            )
            self.assertEqual(
                [command.stage for command in commands],
                [
                    "feature_extraction",
                    "exhaustive_matching",
                    "sparse_mapping",
                    "sparse_analysis",
                ],
            )
            self.assertIn("0", commands[0].argv)

    def test_full_plan_contains_mesh_and_texture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            commands = build_colmap_commands(
                "colmap",
                root / "images",
                root / "output",
                ColmapSettings(mode="full"),
            )
            stages = [command.stage for command in commands]
            self.assertIn("dense_stereo", stages)
            self.assertIn("poisson_meshing", stages)
            self.assertIn("mesh_texturing", stages)

    def test_cpu_flag_is_applied_to_sparse_gpu_steps(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            commands = build_colmap_commands(
                "colmap",
                root / "images",
                root / "output",
                ColmapSettings(mode="sparse", use_gpu=False),
            )
            self.assertIn("0", commands[0].argv)
            self.assertIn("0", commands[1].argv)

    def test_sequential_matcher_is_optional(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            commands = build_colmap_commands(
                "colmap",
                root / "images",
                root / "output",
                ColmapSettings(mode="sparse", matcher="sequential"),
            )
            self.assertEqual(commands[1].stage, "sequential_matching")
            self.assertIn("--SequentialMatching.overlap", commands[1].argv)


class ReconstructionPlanTests(unittest.TestCase):
    def test_parses_colmap_model_analysis(self) -> None:
        output = """
        Registered images: 91
        Points: 3649
        Observations: 35020
        Mean track length: 9.597150
        Mean observations per image: 384.835165
        Mean reprojection error: 0.776638px
        """
        self.assertEqual(
            parse_model_analysis(output),
            {
                "registered_images": 91,
                "points3d": 3649,
                "observations": 35020,
                "mean_track_length": 9.59715,
                "mean_observations_per_image": 384.835165,
                "mean_reprojection_error_px": 0.776638,
            },
        )

    def test_requires_minimum_image_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            images = create_images(Path(temporary), 11)
            with self.assertRaises(ReconstructionError):
                selected_images(images)

    def test_builds_reproducible_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            images = create_images(root, 20)
            plan = build_reconstruction_plan(
                images,
                root / "output",
                ColmapSettings(mode="sparse", use_gpu=False),
            )
            self.assertEqual(plan["image_count"], 20)
            self.assertEqual(plan["mode"], "sparse")
            self.assertEqual(len(plan["commands"]), 4)
            self.assertTrue(plan["input_fingerprint"])

    def test_validates_colmap_mask_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            images = create_images(root, 12)
            masks = root / "masks"
            masks.mkdir()
            image_paths = selected_images(images)
            for image in image_paths:
                (masks / f"{image.name}.png").write_bytes(b"mask")
            validate_masks(image_paths, masks)


if __name__ == "__main__":
    unittest.main()
