from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from miniforge3d.config import ConfigError, load_config, validate_config
from miniforge3d.fingerprints import config_fingerprint, input_fingerprint
from miniforge3d.manifests import read_json, write_json_atomic
from miniforge3d.pipeline import PipelineError, plan_resume_run, select_steps
from miniforge3d.workspace import create_workspace, initialize_workspace_files, open_workspace


def valid_config() -> dict:
    return {
        "project": {"id": "person-001"},
        "input": {"videos": ["input/person.mp4"]},
        "reconstruction": {"engine": "colmap"},
        "model": {"height_mm": 150},
    }


class ConfigTests(unittest.TestCase):
    def test_loads_json_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            path.write_text(json.dumps(valid_config()), encoding="utf-8")
            self.assertEqual(load_config(path)["project"]["id"], "person-001")

    def test_rejects_invalid_project_id(self) -> None:
        config = valid_config()
        config["project"]["id"] = "inválido com espaços"
        with self.assertRaises(ConfigError):
            validate_config(config)


class FingerprintTests(unittest.TestCase):
    def test_config_fingerprint_is_order_independent(self) -> None:
        first = {"a": 1, "b": 2}
        second = {"b": 2, "a": 1}
        self.assertEqual(config_fingerprint(first), config_fingerprint(second))

    def test_input_fingerprint_changes_with_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.bin"
            path.write_bytes(b"first")
            before = input_fingerprint([path])
            path.write_bytes(b"second")
            self.assertNotEqual(before, input_fingerprint([path]))


class PipelineTests(unittest.TestCase):
    def test_selects_partial_steps(self) -> None:
        self.assertEqual(
            select_steps(start_from="mesh_processing"),
            ["mesh_processing", "print_preparation"],
        )
        self.assertEqual(select_steps(only="reconstruction"), ["reconstruction"])

    def test_rejects_conflicting_selection(self) -> None:
        with self.assertRaises(PipelineError):
            select_steps(start_from="reconstruction", only="reconstruction")


class WorkspaceTests(unittest.TestCase):
    def test_workspace_is_unique_and_reopenable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = create_workspace(root, "person-001")
            second = create_workspace(root, "person-001")
            self.assertNotEqual(first.run_id, second.run_id)
            pipeline = {"run_id": first.run_id, "status": "planned"}
            initialize_workspace_files(first, valid_config(), pipeline)
            self.assertEqual(open_workspace(first.root).run_id, first.run_id)

    def test_atomic_json_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            write_json_atomic(path, {"status": "completed"})
            self.assertEqual(read_json(path)["status"], "completed")

    def test_resume_reuses_only_matching_completed_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            video = root / "person.mp4"
            video.write_bytes(b"video")
            config = valid_config()
            config["input"]["videos"] = [str(video)]
            workspace = create_workspace(root / "workspaces", "person-001")
            pipeline = {"run_id": workspace.run_id, "status": "failed"}
            initialize_workspace_files(workspace, config, pipeline)
            from miniforge3d.fingerprints import config_fingerprint, input_fingerprint

            write_json_atomic(
                workspace.directory("frame_preparation") / "manifest.json",
                {
                    "status": "completed",
                    "config_fingerprint": config_fingerprint(config),
                    "input_fingerprint": input_fingerprint([video]),
                },
            )
            _, resumed = plan_resume_run(config, root, workspace.root, None, None)
            self.assertEqual(resumed["reusable_steps"], ["frame_preparation"])
            self.assertNotIn("frame_preparation", resumed["selected_steps"])


if __name__ == "__main__":
    unittest.main()
