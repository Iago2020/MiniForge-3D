from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from miniforge3d.config import ConfigError, load_config
from miniforge3d.engines.colmap import ColmapSettings, detect_colmap
from miniforge3d.hardware import detect_hardware
from miniforge3d.frame_preparation.models import FramePreparationSettings
from miniforge3d.frame_preparation.processor import FramePreparationError, prepare_frames
from miniforge3d.photo_to_model.models import (
    BASES,
    ENGINES,
    PhotoToModelError,
    PhotoToModelSettings,
)
from miniforge3d.photo_to_model.processor import generate_from_photo
from miniforge3d.pipeline import PipelineError, STEPS, plan_new_run, plan_resume_run
from miniforge3d.reconstruction.processor import (
    ReconstructionError,
    build_reconstruction_plan,
    reconstruct_colmap,
)
from miniforge3d.segmentation.processor import (
    PersonSegmentationError,
    PersonSegmentationSettings,
    segment_person_frames,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="miniforge3d")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser("preflight", help="Detecta ambiente e ferramentas.")
    preflight.add_argument("--base-dir", type=Path, default=Path.cwd())

    run = subparsers.add_parser("run", help="Planeja ou executa o pipeline.")
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--workspaces-root", type=Path, default=Path("workspaces"))
    run.add_argument("--workspace", type=Path)
    run.add_argument("--resume", action="store_true")
    run.add_argument("--base-dir", type=Path, default=Path.cwd())
    run.add_argument("--start-from", choices=STEPS)
    run.add_argument("--only", choices=STEPS)
    run.add_argument("--dry-run", action="store_true")

    frames = subparsers.add_parser(
        "prepare-frames",
        help="Extrai e seleciona frames de um vídeo.",
    )
    frames.add_argument("--video", type=Path, required=True)
    frames.add_argument("--output", type=Path, required=True)
    frames.add_argument("--candidate-fps", type=float, default=8.0)
    frames.add_argument("--selection-window-seconds", type=float, default=0.35)
    frames.add_argument("--max-selected-frames", type=int, default=350)
    frames.add_argument("--blur-percentile", type=float, default=20.0)
    frames.add_argument("--min-blur-score", type=float, default=40.0)
    frames.add_argument("--min-brightness", type=float, default=25.0)
    frames.add_argument("--max-brightness", type=float, default=235.0)
    frames.add_argument("--min-contrast", type=float, default=18.0)
    frames.add_argument("--duplicate-hash-distance", type=int, default=6)
    frames.add_argument("--max-duplicate-gap-seconds", type=float, default=0.75)

    segmentation = subparsers.add_parser(
        "segment-person",
        help="Cria máscaras da pessoa e frames com fundo uniforme.",
    )
    segmentation.add_argument("--frames", type=Path, required=True)
    segmentation.add_argument("--output", type=Path, required=True)
    segmentation.add_argument("--model", default="u2net_human_seg")
    segmentation.add_argument("--threshold", type=int, default=127)
    segmentation.add_argument("--background", choices=("white", "black"), default="white")

    reconstruction = subparsers.add_parser(
        "reconstruct",
        help="Executa ou planeja uma reconstrução com COLMAP.",
    )
    reconstruction.add_argument("--frames", type=Path, required=True)
    reconstruction.add_argument("--output", type=Path, required=True)
    reconstruction.add_argument("--mode", choices=("sparse", "full"), default="full")
    reconstruction.add_argument(
        "--matcher",
        choices=("exhaustive", "sequential"),
        default="exhaustive",
    )
    reconstruction.add_argument("--camera-model", default="SIMPLE_RADIAL")
    reconstruction.add_argument("--sequential-overlap", type=int, default=10)
    reconstruction.add_argument("--max-image-size", type=int, default=2000)
    reconstruction.add_argument(
        "--masks",
        type=Path,
        help="Pasta com máscaras COLMAP no formato <nome-da-imagem>.png.",
    )
    reconstruction.add_argument(
        "--cpu",
        action="store_true",
        help="Usa CPU nas etapas esparsas. A etapa densa continua exigindo CUDA.",
    )
    reconstruction.add_argument("--dry-run", action="store_true")

    photo = subparsers.add_parser(
        "from-photo",
        help="Gera uma miniatura imprimível (STL) a partir de uma única foto.",
    )
    photo.add_argument("--image", type=Path, required=True)
    photo.add_argument("--output", type=Path, required=True)
    photo.add_argument("--engine", choices=ENGINES, default="hunyuan3d")
    photo.add_argument("--height-mm", type=float, default=150.0)
    photo.add_argument("--base", choices=BASES, default="round")
    photo.add_argument("--base-height-mm", type=float, default=3.0)
    photo.add_argument("--base-margin-mm", type=float, default=4.0)
    photo.add_argument("--flatten-mm", type=float, default=0.5)
    photo.add_argument("--seed", type=int, default=1234)
    photo.add_argument("--octree-resolution", type=int, default=384)
    photo.add_argument("--steps", type=int, default=30)
    photo.add_argument(
        "--allow-cropped",
        action="store_true",
        help="Gera mesmo se a pessoa estiver cortada pela borda ou perto demais.",
    )
    photo.add_argument(
        "--no-local-segmentation",
        action="store_true",
        help="Envia a foto inteira e deixa o serviço remoto remover o fundo.",
    )
    return parser


def _preflight(base_dir: Path) -> int:
    report = detect_hardware(base_dir)
    report["adapters"] = {"colmap": detect_colmap().__dict__}
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _run(args: argparse.Namespace) -> int:
    if not args.dry_run:
        raise PipelineError(
            "Execução externa ainda não está habilitada. Use --dry-run nesta versão."
        )
    config = load_config(args.config)
    if args.resume and not args.workspace:
        raise PipelineError("--resume requer --workspace.")
    if args.workspace and not args.resume:
        raise PipelineError("--workspace só pode ser usado junto com --resume.")
    if args.resume:
        workspace, plan = plan_resume_run(
            config=config,
            base_dir=args.base_dir,
            workspace_root=args.workspace,
            start_from=args.start_from,
            only=args.only,
        )
    else:
        workspace, plan = plan_new_run(
            config=config,
            base_dir=args.base_dir,
            workspaces_root=args.workspaces_root,
            start_from=args.start_from,
            only=args.only,
        )
    print(
        json.dumps(
            {
                "run_id": workspace.run_id,
                "workspace": str(workspace.root),
                "selected_steps": plan["selected_steps"],
                "reusable_steps": plan["reusable_steps"],
                "missing_inputs": plan["missing_inputs"],
                "status": plan["status"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 2 if plan["missing_inputs"] else 0


def _prepare_frames(args: argparse.Namespace) -> int:
    settings = FramePreparationSettings(
        candidate_fps=args.candidate_fps,
        selection_window_seconds=args.selection_window_seconds,
        max_selected_frames=args.max_selected_frames,
        blur_percentile=args.blur_percentile,
        min_blur_score=args.min_blur_score,
        min_brightness=args.min_brightness,
        max_brightness=args.max_brightness,
        min_contrast=args.min_contrast,
        duplicate_hash_distance=args.duplicate_hash_distance,
        max_duplicate_gap_seconds=args.max_duplicate_gap_seconds,
    )
    run_id = f"frameprep-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    manifest = prepare_frames(args.video, args.output, settings, run_id)
    print(
        json.dumps(
            {
                "run_id": run_id,
                "status": manifest["status"],
                "output": str(args.output.resolve()),
                "statistics": manifest["statistics"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _reconstruct(args: argparse.Namespace) -> int:
    if args.mode == "full" and args.cpu and not args.dry_run:
        raise ReconstructionError(
            "--cpu não torna o dense stereo compatível sem CUDA. "
            "Use --mode sparse no Mac ou remova --cpu no Nitro."
        )
    settings = ColmapSettings(
        mode=args.mode,
        matcher=args.matcher,
        camera_model=args.camera_model,
        sequential_overlap=args.sequential_overlap,
        max_image_size=args.max_image_size,
        use_gpu=not args.cpu,
        masks_dir=args.masks,
    )
    run_id = f"reconstruction-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    if args.dry_run:
        availability = detect_colmap()
        executable = availability.executable or "colmap"
        plan = build_reconstruction_plan(args.frames, args.output, settings, executable)
        plan["colmap_available"] = availability.available
        plan["colmap_error"] = availability.error
        print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    manifest = reconstruct_colmap(
        images_dir=args.frames,
        output_dir=args.output,
        settings=settings,
        run_id=run_id,
    )
    print(
        json.dumps(
            {
                "run_id": run_id,
                "status": manifest["status"],
                "output": str(args.output.resolve()),
                "statistics": manifest["statistics"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _segment_person(args: argparse.Namespace) -> int:
    settings = PersonSegmentationSettings(
        model=args.model,
        threshold=args.threshold,
        background=args.background,
    )
    run_id = f"segmentation-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    manifest = segment_person_frames(args.frames, args.output, settings, run_id)
    print(
        json.dumps(
            {
                "run_id": run_id,
                "status": manifest["status"],
                "output": str(args.output.resolve()),
                "statistics": manifest["statistics"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _from_photo(args: argparse.Namespace) -> int:
    settings = PhotoToModelSettings(
        engine=args.engine,
        height_mm=args.height_mm,
        base=args.base,
        base_height_mm=args.base_height_mm,
        base_margin_mm=args.base_margin_mm,
        flatten_mm=args.flatten_mm,
        seed=args.seed,
        octree_resolution=args.octree_resolution,
        steps=args.steps,
        local_segmentation=not args.no_local_segmentation,
        allow_cropped=args.allow_cropped,
    )
    run_id = f"photo-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    manifest = generate_from_photo(args.image, args.output, settings, run_id)
    print(
        json.dumps(
            {
                "run_id": run_id,
                "status": manifest["status"],
                "stl": manifest["outputs"][-1],
                "statistics": manifest["statistics"],
                "warnings": manifest["warnings"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "preflight":
            return _preflight(args.base_dir)
        if args.command == "run":
            return _run(args)
        if args.command == "prepare-frames":
            return _prepare_frames(args)
        if args.command == "segment-person":
            return _segment_person(args)
        if args.command == "reconstruct":
            return _reconstruct(args)
        if args.command == "from-photo":
            return _from_photo(args)
        parser.error(f"Comando desconhecido: {args.command}")
    except (
        ConfigError,
        FramePreparationError,
        PipelineError,
        ReconstructionError,
        PersonSegmentationError,
        PhotoToModelError,
        ValueError,
    ) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    return 0
