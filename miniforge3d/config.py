from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


PROJECT_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$")


class ConfigError(ValueError):
    """Raised when a project configuration is missing or invalid."""


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise ConfigError(
            "Configuração YAML requer PyYAML. Instale o projeto com "
            "'python -m pip install -e .'."
        ) from exc

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML inválido em {path}: {exc}") from exc
    return data


def load_config(path: Path) -> dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise ConfigError(f"Configuração não encontrada: {path}")

    try:
        if path.suffix.lower() == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix.lower() in {".yaml", ".yml"}:
            data = _load_yaml(path)
        else:
            raise ConfigError("Use um arquivo .yaml, .yml ou .json.")
    except json.JSONDecodeError as exc:
        raise ConfigError(f"JSON inválido em {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError("A raiz da configuração deve ser um objeto/mapeamento.")

    validate_config(data)
    return data


def validate_config(config: dict[str, Any]) -> None:
    project = config.get("project")
    if not isinstance(project, dict):
        raise ConfigError("A seção 'project' é obrigatória.")

    project_id = project.get("id")
    if not isinstance(project_id, str) or not PROJECT_ID_PATTERN.fullmatch(project_id):
        raise ConfigError(
            "project.id deve ter 2 a 64 caracteres e usar apenas letras, "
            "números, ponto, hífen ou underscore."
        )

    input_config = config.get("input")
    videos = input_config.get("videos") if isinstance(input_config, dict) else None
    if not isinstance(videos, list) or not videos:
        raise ConfigError("input.videos deve conter ao menos um vídeo.")
    if any(not isinstance(video, str) or not video.strip() for video in videos):
        raise ConfigError("Cada item de input.videos deve ser um caminho não vazio.")

    reconstruction = config.get("reconstruction", {})
    if not isinstance(reconstruction, dict):
        raise ConfigError("reconstruction deve ser um mapeamento.")
    engine = reconstruction.get("engine", "colmap")
    if not isinstance(engine, str) or not engine.strip():
        raise ConfigError("reconstruction.engine deve ser um texto não vazio.")

    model = config.get("model", {})
    if not isinstance(model, dict):
        raise ConfigError("model deve ser um mapeamento.")
    height = model.get("height_mm")
    if height is not None and (not isinstance(height, (int, float)) or height <= 0):
        raise ConfigError("model.height_mm deve ser maior que zero.")


def resolve_video_paths(config: dict[str, Any], base_dir: Path) -> list[Path]:
    return [
        (base_dir / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
        for value in config["input"]["videos"]
    ]

