from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

from miniforge3d.frame_preparation.models import FrameMetrics, FramePreparationSettings


class FrameAnalysisError(RuntimeError):
    """Raised when a candidate image cannot be analyzed."""


def percentile(values: Iterable[float], percent: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("Não é possível calcular percentil de lista vazia.")
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percent / 100.0
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def hamming_distance(first: int, second: int) -> int:
    return (first ^ second).bit_count()


def analyze_frame(path: Path, index: int, candidate_fps: float) -> FrameMetrics:
    try:
        import cv2
    except ImportError as exc:
        raise FrameAnalysisError(
            "OpenCV não está instalado. Execute 'python -m pip install -e .'."
        ) from exc

    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise FrameAnalysisError(f"Não foi possível abrir o frame: {path}")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    contrast = float(gray.std())

    resized = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
    comparisons = resized[:, 1:] > resized[:, :-1]
    difference_hash = 0
    for bit in comparisons.flatten():
        difference_hash = (difference_hash << 1) | int(bit)

    height, width = gray.shape
    return FrameMetrics(
        index=index,
        path=path,
        timestamp_seconds=(index - 1) / candidate_fps,
        blur_score=blur_score,
        brightness=brightness,
        contrast=contrast,
        difference_hash=difference_hash,
        width=int(width),
        height=int(height),
    )


def adaptive_blur_threshold(
    frames: list[FrameMetrics],
    settings: FramePreparationSettings,
) -> float:
    return max(
        settings.min_blur_score,
        percentile((frame.blur_score for frame in frames), settings.blur_percentile),
    )


def _initial_rejection_reason(
    frame: FrameMetrics,
    blur_threshold: float,
    settings: FramePreparationSettings,
) -> str | None:
    if frame.blur_score < blur_threshold:
        return "blur"
    if frame.brightness < settings.min_brightness:
        return "underexposed"
    if frame.brightness > settings.max_brightness:
        return "overexposed"
    if frame.contrast < settings.min_contrast:
        return "low_contrast"
    return None


def _uniform_cap(frames: list[FrameMetrics], maximum: int) -> list[FrameMetrics]:
    if len(frames) <= maximum:
        return frames
    if maximum == 1:
        return [max(frames, key=lambda frame: frame.quality_score)]
    indices = {
        round(position * (len(frames) - 1) / (maximum - 1))
        for position in range(maximum)
    }
    return [frames[index] for index in sorted(indices)]


def select_frames(
    frames: list[FrameMetrics],
    settings: FramePreparationSettings,
) -> tuple[list[FrameMetrics], dict[str, float | int]]:
    if not frames:
        raise ValueError("Nenhum frame candidato foi recebido.")
    settings.validate()
    blur_threshold = adaptive_blur_threshold(frames, settings)

    eligible: list[FrameMetrics] = []
    for frame in frames:
        frame.selected = False
        frame.rejection_reason = _initial_rejection_reason(frame, blur_threshold, settings)
        if frame.rejection_reason is None:
            eligible.append(frame)

    window_winners: list[FrameMetrics] = []
    windows: dict[int, list[FrameMetrics]] = {}
    for frame in eligible:
        window = int(frame.timestamp_seconds / settings.selection_window_seconds)
        windows.setdefault(window, []).append(frame)
    for candidates in windows.values():
        winner = max(candidates, key=lambda frame: frame.quality_score)
        window_winners.append(winner)
        for candidate in candidates:
            if candidate is not winner:
                candidate.rejection_reason = "lower_quality_in_time_window"

    diverse: list[FrameMetrics] = []
    for frame in sorted(window_winners, key=lambda item: item.timestamp_seconds):
        if not diverse:
            diverse.append(frame)
            continue
        previous = diverse[-1]
        distance = hamming_distance(previous.difference_hash, frame.difference_hash)
        time_gap = frame.timestamp_seconds - previous.timestamp_seconds
        if (
            distance >= settings.duplicate_hash_distance
            or time_gap >= settings.max_duplicate_gap_seconds
        ):
            diverse.append(frame)
        elif frame.quality_score > previous.quality_score:
            previous.rejection_reason = "near_duplicate"
            diverse[-1] = frame
        else:
            frame.rejection_reason = "near_duplicate"

    selected = _uniform_cap(diverse, settings.max_selected_frames)
    selected_ids = {id(frame) for frame in selected}
    for frame in diverse:
        if id(frame) not in selected_ids:
            frame.rejection_reason = "maximum_frame_limit"
    for frame in selected:
        frame.selected = True
        frame.rejection_reason = None

    reason_counts: dict[str, int] = {}
    for frame in frames:
        if frame.rejection_reason:
            reason_counts[frame.rejection_reason] = reason_counts.get(frame.rejection_reason, 0) + 1
    statistics: dict[str, float | int] = {
        "candidates": len(frames),
        "eligible_after_quality": len(eligible),
        "selected": len(selected),
        "blur_threshold": round(blur_threshold, 4),
    }
    for reason, count in sorted(reason_counts.items()):
        statistics[f"rejected_{reason}"] = count
    return selected, statistics
