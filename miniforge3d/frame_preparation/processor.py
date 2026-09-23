from __future__ import annotations

import json
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from miniforge3d.fingerprints import config_fingerprint, input_fingerprint
from miniforge3d.frame_preparation.models import FramePreparationSettings
from miniforge3d.frame_preparation.quality import analyze_frame, select_frames
from miniforge3d.logging_utils import append_event
from miniforge3d.manifests import write_json_atomic


class FramePreparationError(RuntimeError):
    """Raised when frame extraction or analysis fails."""


def _require_tool(name: str) -> str:
    executable = shutil.which(name)
    if not executable:
        raise FramePreparationError(f"Ferramenta obrigatória não encontrada: {name}")
    return executable


def _first_version_line(executable: str) -> str | None:
    try:
        result = subprocess.run(
            [executable, "-version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    output = (result.stdout or result.stderr).strip()
    return output.splitlines()[0] if output else None


def _tool_versions() -> dict[str, str | None]:
    ffmpeg = _require_tool("ffmpeg")
    ffprobe = _require_tool("ffprobe")
    try:
        import cv2

        opencv_version: str | None = cv2.__version__
    except ImportError:
        opencv_version = None
    return {
        "ffmpeg": _first_version_line(ffmpeg),
        "ffprobe": _first_version_line(ffprobe),
        "opencv": opencv_version,
    }


def probe_video(video_path: Path) -> dict[str, Any]:
    ffprobe = _require_tool("ffprobe")
    command = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration,size,bit_rate:stream=index,codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,pix_fmt",
        "-of",
        "json",
        str(video_path),
    ]
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        stderr = getattr(exc, "stderr", None)
        raise FramePreparationError(f"FFprobe falhou: {stderr or exc}") from exc
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise FramePreparationError("FFprobe retornou JSON inválido.") from exc


def _extract_candidates(
    video_path: Path,
    frames_dir: Path,
    settings: FramePreparationSettings,
    external_log: Path,
) -> list[Path]:
    ffmpeg = _require_tool("ffmpeg")
    output_pattern = frames_dir / "frame_%06d.jpg"
    command = [
        ffmpeg,
        "-hide_banner",
        "-nostdin",
        "-i",
        str(video_path),
        "-vf",
        f"fps={settings.candidate_fps:g}",
        "-q:v",
        str(settings.jpeg_quality),
        "-start_number",
        "1",
        str(output_pattern),
    ]
    started = time.monotonic()
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    external_log.write_text(
        json.dumps(
            {
                "command": command,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration_seconds": round(time.monotonic() - started, 4),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise FramePreparationError(
            f"FFmpeg falhou com exit code {result.returncode}. Consulte {external_log}."
        )
    frames = sorted(frames_dir.glob("frame_*.jpg"))
    if not frames:
        raise FramePreparationError("FFmpeg não produziu frames candidatos.")
    return frames


def _ensure_new_output(output_dir: Path) -> None:
    if output_dir.exists():
        if not output_dir.is_dir():
            raise FramePreparationError(f"A saída não é um diretório: {output_dir}")
        if any(output_dir.iterdir()):
            raise FramePreparationError(
                f"O diretório de saída já contém arquivos e não será sobrescrito: {output_dir}"
            )
    output_dir.mkdir(parents=True, exist_ok=True)


def prepare_frames(
    video_path: Path,
    output_dir: Path,
    settings: FramePreparationSettings,
    run_id: str,
) -> dict[str, Any]:
    settings.validate()
    video_path = video_path.resolve()
    output_dir = output_dir.resolve()
    if not video_path.is_file():
        raise FramePreparationError(f"Vídeo não encontrado: {video_path}")
    _ensure_new_output(output_dir)

    frames_all = output_dir / "frames_all"
    frames_selected = output_dir / "frames_selected"
    logs_dir = output_dir / "logs"
    frames_all.mkdir()
    frames_selected.mkdir()
    logs_dir.mkdir()
    pipeline_log = logs_dir / "frame-preparation.log"
    manifest_path = output_dir / "manifest.json"
    started_at = datetime.now(UTC)
    config_hash = config_fingerprint(settings.to_dict())
    input_hash = input_fingerprint([video_path])
    base_manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": run_id,
        "step": "frame_preparation",
        "status": "running",
        "tool_versions": _tool_versions(),
        "effective_config": settings.to_dict(),
        "inputs": [str(video_path)],
        "outputs": [],
        "input_fingerprint": input_hash,
        "config_fingerprint": config_hash,
        "statistics": {},
        "warnings": [],
        "error": None,
        "started_at": started_at.isoformat(),
        "finished_at": None,
        "duration_seconds": None,
    }
    write_json_atomic(manifest_path, base_manifest)
    append_event(pipeline_log, "frame_preparation_started", {"video": str(video_path)})

    try:
        video_metadata = probe_video(video_path)
        candidates = _extract_candidates(
            video_path,
            frames_all,
            settings,
            logs_dir / "ffmpeg-extraction.json",
        )
        metrics = [
            analyze_frame(path, index, settings.candidate_fps)
            for index, path in enumerate(candidates, start=1)
        ]
        selected, statistics = select_frames(metrics, settings)
        for frame in selected:
            shutil.copy2(frame.path, frames_selected / frame.path.name)

        metadata = {
            "schema_version": "1.0",
            "run_id": run_id,
            "source": str(video_path),
            "video": video_metadata,
            "settings": settings.to_dict(),
            "statistics": statistics,
            "frames": [frame.to_dict(output_dir) for frame in metrics],
        }
        write_json_atomic(output_dir / "metadata.json", metadata)
        finished_at = datetime.now(UTC)
        base_manifest.update(
            {
                "status": "completed",
                "outputs": [
                    str(frames_all),
                    str(frames_selected),
                    str(output_dir / "metadata.json"),
                ],
                "statistics": statistics,
                "finished_at": finished_at.isoformat(),
                "duration_seconds": round((finished_at - started_at).total_seconds(), 4),
            }
        )
        write_json_atomic(manifest_path, base_manifest)
        append_event(
            pipeline_log,
            "frame_preparation_completed",
            {"statistics": statistics},
        )
        return base_manifest
    except Exception as exc:
        finished_at = datetime.now(UTC)
        base_manifest.update(
            {
                "status": "failed",
                "error": {"type": type(exc).__name__, "message": str(exc)},
                "finished_at": finished_at.isoformat(),
                "duration_seconds": round((finished_at - started_at).total_seconds(), 4),
            }
        )
        write_json_atomic(manifest_path, base_manifest)
        append_event(
            pipeline_log,
            "frame_preparation_failed",
            {"error": base_manifest["error"]},
        )
        raise
