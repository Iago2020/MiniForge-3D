from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from miniforge3d.photo_to_model.models import PhotoToModelError, PhotoToModelSettings


HUNYUAN_SPACE = "tencent/Hunyuan3D-2.1"
TRELLIS_SPACE = "trellis-community/TRELLIS"


class GenerationEngine(Protocol):
    name: str
    source: str

    def generate(self, image: Path, has_alpha: bool, output_dir: Path) -> Path:
        """Gera a malha bruta a partir da imagem e devolve o caminho dela em output_dir."""


def _client(space: str) -> Any:
    try:
        from gradio_client import Client
    except ImportError as exc:
        raise PhotoToModelError(
            "Geração por foto não instalada. Execute: python -m pip install -e '.[photo]'"
        ) from exc
    token = os.environ.get("HF_TOKEN") or None
    try:
        return Client(space, token=token, verbose=False)
    except Exception as exc:
        raise PhotoToModelError(f"Não foi possível conectar ao Space '{space}': {exc}") from exc


def _remote_error(space: str, exc: Exception) -> PhotoToModelError:
    message = str(exc)
    hint = ""
    lowered = message.lower()
    if "quota" in lowered or "gpu" in lowered:
        hint = (
            " A cota gratuita de GPU acabou por agora. Defina HF_TOKEN com um token "
            "gratuito do Hugging Face para ganhar mais cota, espere a cota renovar ou "
            "tente --engine com o outro serviço."
        )
    return PhotoToModelError(f"O Space '{space}' falhou: {message}.{hint}")


def _copy_result(result: Any, output_dir: Path, stem: str) -> Path:
    path = result
    # Gradio pode devolver o arquivo direto, como {"path": ...} ou como gr.update {"value": ...}.
    while isinstance(path, dict):
        path = path.get("path") or path.get("value")
    if not path or not Path(path).is_file():
        raise PhotoToModelError(f"O serviço não devolveu um arquivo de malha: {result!r}")
    source = Path(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{stem}{source.suffix.lower() or '.glb'}"
    shutil.copyfile(source, target)
    return target


@dataclass
class HunyuanSpaceEngine:
    settings: PhotoToModelSettings
    space: str = HUNYUAN_SPACE
    name: str = "hunyuan3d"

    @property
    def source(self) -> str:
        return f"huggingface.co/spaces/{self.space}"

    def generate(self, image: Path, has_alpha: bool, output_dir: Path) -> Path:
        from gradio_client import handle_file

        client = _client(self.space)
        try:
            result = client.predict(
                image=handle_file(str(image)),
                mv_image_front=None,
                mv_image_back=None,
                mv_image_left=None,
                mv_image_right=None,
                steps=self.settings.steps,
                guidance_scale=5.0,
                seed=self.settings.seed,
                octree_resolution=self.settings.octree_resolution,
                check_box_rembg=not has_alpha,
                num_chunks=8000,
                randomize_seed=False,
                api_name="/shape_generation",
            )
        except Exception as exc:
            raise _remote_error(self.space, exc) from exc
        return _copy_result(result[0], output_dir, "raw_mesh")


@dataclass
class TrellisSpaceEngine:
    settings: PhotoToModelSettings
    space: str = TRELLIS_SPACE
    name: str = "trellis"

    @property
    def source(self) -> str:
        return f"huggingface.co/spaces/{self.space}"

    def generate(self, image: Path, has_alpha: bool, output_dir: Path) -> Path:
        from gradio_client import handle_file

        client = _client(self.space)
        try:
            client.predict(api_name="/start_session")
            result = client.predict(
                image=handle_file(str(image)),
                multiimages=[],
                seed=self.settings.seed,
                ss_guidance_strength=7.5,
                ss_sampling_steps=max(12, self.settings.steps // 2),
                slat_guidance_strength=3.0,
                slat_sampling_steps=max(12, self.settings.steps // 2),
                multiimage_algo="stochastic",
                mesh_simplify=0.9,
                texture_size=1024,
                api_name="/generate_and_extract_glb",
            )
        except Exception as exc:
            raise _remote_error(self.space, exc) from exc
        return _copy_result(result[1], output_dir, "raw_mesh")


def build_engine(settings: PhotoToModelSettings) -> GenerationEngine:
    if settings.engine == "hunyuan3d":
        return HunyuanSpaceEngine(settings)
    if settings.engine == "trellis":
        return TrellisSpaceEngine(settings)
    raise PhotoToModelError(f"Engine desconhecida: {settings.engine}")
