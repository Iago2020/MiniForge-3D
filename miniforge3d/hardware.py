from __future__ import annotations

import ctypes
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _total_memory_bytes() -> int | None:
    if os.name == "nt":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_ulong),
                ("memory_load", ctypes.c_ulong),
                ("total_physical", ctypes.c_ulonglong),
                ("available_physical", ctypes.c_ulonglong),
                ("total_page_file", ctypes.c_ulonglong),
                ("available_page_file", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong),
                ("available_virtual", ctypes.c_ulonglong),
                ("available_extended_virtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.length = ctypes.sizeof(MemoryStatus)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.total_physical)
        return None

    try:
        return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
    except (AttributeError, OSError, ValueError):
        return None


def _nvidia_gpu() -> dict[str, Any] | None:
    executable = shutil.which("nvidia-smi")
    if not executable:
        return None
    command = [
        executable,
        "--query-gpu=name,memory.total,driver_version",
        "--format=csv,noheader,nounits",
    ]
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return {"vendor": "NVIDIA", "detected": True, "query_failed": True}

    first_line = result.stdout.strip().splitlines()[0]
    parts = [part.strip() for part in first_line.split(",")]
    if len(parts) != 3:
        return {"vendor": "NVIDIA", "detected": True, "raw": first_line}
    return {
        "vendor": "NVIDIA",
        "detected": True,
        "name": parts[0],
        "memory_total_mib": int(parts[1]),
        "driver_version": parts[2],
        "cuda_runtime_available": True,
    }


def detect_hardware(base_dir: Path) -> dict[str, Any]:
    disk = shutil.disk_usage(base_dir.resolve())
    memory = _total_memory_bytes()
    return {
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
        },
        "cpu": {
            "model": platform.processor() or "unknown",
            "logical_cores": os.cpu_count(),
        },
        "ram_total_bytes": memory,
        "gpu": _nvidia_gpu(),
        "disk": {
            "path": str(base_dir.resolve()),
            "total_bytes": disk.total,
            "free_bytes": disk.free,
        },
        "tools": {
            "ffmpeg": shutil.which("ffmpeg"),
            "ffprobe": shutil.which("ffprobe"),
            "colmap": shutil.which("COLMAP.bat") or shutil.which("colmap"),
            "blender": shutil.which("blender"),
        },
    }

