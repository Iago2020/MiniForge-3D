from __future__ import annotations

import unittest
from pathlib import Path

from miniforge3d.frame_preparation.models import FrameMetrics, FramePreparationSettings
from miniforge3d.frame_preparation.quality import (
    hamming_distance,
    percentile,
    select_frames,
)


def frame(
    index: int,
    timestamp: float,
    blur: float = 100.0,
    brightness: float = 120.0,
    contrast: float = 40.0,
    difference_hash: int | None = None,
) -> FrameMetrics:
    return FrameMetrics(
        index=index,
        path=Path(f"frame_{index:06d}.jpg"),
        timestamp_seconds=timestamp,
        blur_score=blur,
        brightness=brightness,
        contrast=contrast,
        difference_hash=index if difference_hash is None else difference_hash,
        width=1920,
        height=1080,
    )


class MetricTests(unittest.TestCase):
    def test_percentile_interpolates(self) -> None:
        self.assertEqual(percentile([0, 10, 20, 30, 40], 25), 10)
        self.assertEqual(percentile([0, 100], 25), 25)

    def test_hamming_distance(self) -> None:
        self.assertEqual(hamming_distance(0b0000, 0b1111), 4)
        self.assertEqual(hamming_distance(0b1010, 0b1010), 0)


class SelectionTests(unittest.TestCase):
    def settings(self, **overrides) -> FramePreparationSettings:
        values = {
            "candidate_fps": 8.0,
            "selection_window_seconds": 0.25,
            "max_selected_frames": 100,
            "blur_percentile": 0.0,
            "min_blur_score": 40.0,
            "min_brightness": 25.0,
            "max_brightness": 235.0,
            "min_contrast": 18.0,
            "duplicate_hash_distance": 1,
            "max_duplicate_gap_seconds": 10.0,
        }
        values.update(overrides)
        return FramePreparationSettings(**values)

    def test_rejects_quality_failures(self) -> None:
        frames = [
            frame(1, 0.0, blur=10),
            frame(2, 0.5, brightness=5),
            frame(3, 1.0, brightness=250),
            frame(4, 1.5, contrast=2),
            frame(5, 2.0, difference_hash=0xFFFF),
        ]
        selected, statistics = select_frames(frames, self.settings())
        self.assertEqual([item.index for item in selected], [5])
        self.assertEqual(statistics["rejected_blur"], 1)
        self.assertEqual(statistics["rejected_underexposed"], 1)
        self.assertEqual(statistics["rejected_overexposed"], 1)
        self.assertEqual(statistics["rejected_low_contrast"], 1)

    def test_keeps_best_frame_in_time_window(self) -> None:
        frames = [
            frame(1, 0.00, blur=80, difference_hash=1),
            frame(2, 0.10, blur=160, difference_hash=2),
            frame(3, 0.40, blur=120, difference_hash=4),
        ]
        selected, _ = select_frames(frames, self.settings())
        self.assertEqual([item.index for item in selected], [2, 3])
        self.assertEqual(frames[0].rejection_reason, "lower_quality_in_time_window")

    def test_replaces_near_duplicate_with_sharper_frame(self) -> None:
        frames = [
            frame(1, 0.0, blur=80, difference_hash=0),
            frame(2, 0.5, blur=180, difference_hash=0),
        ]
        selected, _ = select_frames(
            frames,
            self.settings(duplicate_hash_distance=2),
        )
        self.assertEqual([item.index for item in selected], [2])
        self.assertEqual(frames[0].rejection_reason, "near_duplicate")

    def test_preserves_temporal_coverage_for_similar_frames(self) -> None:
        frames = [
            frame(1, 0.0, difference_hash=0),
            frame(2, 0.5, difference_hash=0),
            frame(3, 1.0, difference_hash=0),
            frame(4, 1.5, difference_hash=0),
        ]
        selected, _ = select_frames(
            frames,
            self.settings(
                duplicate_hash_distance=6,
                max_duplicate_gap_seconds=0.75,
            ),
        )
        self.assertEqual([item.index for item in selected], [1, 3])

    def test_caps_frames_while_preserving_timeline(self) -> None:
        frames = [
            frame(index, float(index), difference_hash=1 << index)
            for index in range(1, 11)
        ]
        selected, statistics = select_frames(
            frames,
            self.settings(max_selected_frames=3, duplicate_hash_distance=1),
        )
        self.assertEqual([item.index for item in selected], [1, 5, 10])
        self.assertEqual(statistics["selected"], 3)


if __name__ == "__main__":
    unittest.main()
