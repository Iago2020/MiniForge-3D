from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from miniforge3d.segmentation.processor import (
    PersonSegmentationSettings,
    segment_person_frames,
)


class PersonSegmentationTests(unittest.TestCase):
    def test_creates_masked_frames_and_colmap_masks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            frames = root / "frames"
            frames.mkdir()
            image = np.zeros((40, 30, 3), dtype=np.uint8)
            image[5:35, 10:20] = (10, 80, 180)
            cv2.imwrite(str(frames / "frame_000001.jpg"), image)

            def provider(_: np.ndarray) -> np.ndarray:
                mask = np.zeros((40, 30), dtype=np.uint8)
                mask[5:35, 10:20] = 255
                return mask

            output = root / "segmentation"
            manifest = segment_person_frames(
                frames,
                output,
                PersonSegmentationSettings(background="white"),
                "test-run",
                mask_provider=provider,
            )

            self.assertEqual(manifest["statistics"]["generated_masks"], 1)
            self.assertTrue((output / "frames_masked" / "frame_000001.png").is_file())
            self.assertTrue((output / "masks" / "frame_000001.png.png").is_file())


if __name__ == "__main__":
    unittest.main()
