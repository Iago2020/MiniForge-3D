from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np
import trimesh

from miniforge3d.photo_to_model.models import PhotoToModelError, PhotoToModelSettings
from miniforge3d.photo_to_model.processor import generate_from_photo


class FakeEngine:
    name = "fake"
    source = "test"

    def __init__(self) -> None:
        self.received: tuple[Path, bool] | None = None

    def generate(self, image: Path, has_alpha: bool, output_dir: Path) -> Path:
        self.received = (image, has_alpha)
        output_dir.mkdir(parents=True, exist_ok=True)
        # Figura simples em Y para cima (convenção glTF) e um fragmento solto minúsculo.
        body = trimesh.creation.capsule(height=1.6, radius=0.25)
        body.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, (1, 0, 0)))
        speck = trimesh.creation.icosphere(subdivisions=0, radius=0.01)
        speck.apply_translation((2, 2, 2))
        path = output_dir / "raw_mesh.glb"
        trimesh.util.concatenate([body, speck]).export(str(path))
        return path


def _photo(root: Path) -> Path:
    image = np.full((200, 120, 3), 30, dtype=np.uint8)
    image[20:180, 40:80] = (10, 80, 180)
    path = root / "person.jpg"
    cv2.imwrite(str(path), image)
    return path


def _mask(_: np.ndarray) -> np.ndarray:
    mask = np.zeros((200, 120), dtype=np.uint8)
    mask[20:180, 40:80] = 255
    return mask


class PhotoToModelTests(unittest.TestCase):
    def test_generates_watertight_stl_scaled_with_base(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            engine = FakeEngine()
            output = root / "out"
            settings = PhotoToModelSettings(height_mm=120, base_height_mm=3)
            manifest = generate_from_photo(
                _photo(root), output, settings, "test-run", engine=engine, mask_provider=_mask
            )

            self.assertEqual(manifest["status"], "completed")
            self.assertTrue(engine.received[1])
            prepared = cv2.imread(str(output / "01-input" / "prepared.png"), cv2.IMREAD_UNCHANGED)
            self.assertEqual(prepared.shape[0], prepared.shape[1])
            self.assertEqual(prepared.shape[2], 4)

            stl = trimesh.load(str(output / "03-print" / "model.stl"))
            self.assertTrue(stl.is_watertight)
            self.assertAlmostEqual(stl.bounds[0][2], 0.0, places=3)
            self.assertAlmostEqual(stl.extents[2], 123.0, delta=0.5)
            self.assertAlmostEqual(manifest["statistics"]["figure_size_mm"]["z"], 120.0, delta=0.1)
            self.assertTrue(any("fragmento" in w for w in manifest["warnings"]))
            self.assertTrue((output / "manifest.json").is_file())

    def test_without_base_keeps_requested_height(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "out"
            settings = PhotoToModelSettings(height_mm=80, base="none")
            generate_from_photo(
                _photo(root), output, settings, "test-run", engine=FakeEngine(), mask_provider=_mask
            )
            stl = trimesh.load(str(output / "03-print" / "model.stl"))
            self.assertAlmostEqual(stl.extents[2], 80.0, delta=0.1)
            self.assertTrue(stl.is_watertight)

    def test_refuses_to_overwrite_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "out"
            output.mkdir()
            (output / "existing.txt").write_text("x")
            with self.assertRaises(PhotoToModelError):
                generate_from_photo(
                    _photo(root), output, PhotoToModelSettings(), "r", engine=FakeEngine()
                )

    def test_validates_settings(self) -> None:
        with self.assertRaises(ValueError):
            PhotoToModelSettings(height_mm=5).validate()
        with self.assertRaises(ValueError):
            PhotoToModelSettings(engine="other").validate()


if __name__ == "__main__":
    unittest.main()
