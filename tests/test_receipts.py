import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from alvearium_commons.cli import build_obliteratus_receipt, build_receipt


class BuildReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "artifacts").mkdir()
        (self.root / "artifacts" / "result.txt").write_text("hello research\n", encoding="utf-8")
        self.manifest_path = self.root / "experiment.json"
        self.manifest_path.write_text(json.dumps({
            "title": "Test run",
            "tool": "unit-test",
            "method": "Test hashing only",
            "environment": {"runtime": "Python"},
            "artifacts": [{"path": "artifacts/result.txt", "description": "test output"}],
            "claims": ["Example claim, not independently verified."],
        }), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_hashes_artifact_and_records_size(self):
        receipt = build_receipt(self.manifest_path)
        artifact = receipt["artifacts"][0]
        expected = hashlib.sha256(b"hello research\n").hexdigest()
        self.assertEqual(artifact["sha256"], expected)
        self.assertEqual(artifact["size_bytes"], len(b"hello research\n"))
        self.assertEqual(artifact["path"], "artifacts/result.txt")

    def test_receipt_id_is_stable_for_same_content(self):
        first = build_receipt(self.manifest_path)
        second = build_receipt(self.manifest_path)
        self.assertEqual(first["receipt_id"], second["receipt_id"])
        self.assertNotEqual(first["created_at"], "")  # Timestamp is metadata, not part of the ID.

    def test_missing_artifact_is_rejected(self):
        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        data["artifacts"][0]["path"] = "artifacts/missing.txt"
        self.manifest_path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "missing"):
            build_receipt(self.manifest_path)

    def test_path_traversal_is_rejected(self):
        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        data["artifacts"][0]["path"] = "../outside.txt"
        self.manifest_path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "escapes"):
            build_receipt(self.manifest_path)

    def test_required_fields_are_checked(self):
        self.manifest_path.write_text(json.dumps({"title": "Missing method"}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "tool"):
            build_receipt(self.manifest_path)


class ObliteratusImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source_path = self.root / "contribution.json"
        self.source = {
            "contribution_schema_version": 1,
            "timestamp": "20261028T010203Z",
            "model_name": "example/model-7b",
            "config_fingerprint": "abc12345",
            "notes": "Not copied into the receipt",
            "telemetry": {
                "schema_version": 2,
                "method": "example-method",
                "model": {
                    "architecture": "LlamaForCausalLM",
                    "num_layers": 32,
                    "num_heads": 32,
                },
                "environment": {"python_version": "3.12"},
                "method_config": {"n_directions": 2},
                "quality_metrics": {
                    "refusal_rate": 0.25,
                    "coherence": 0.91,
                    "unrecognised_metric": "must not be copied",
                },
                "quality_metric_status": {
                    "refusal_rate": "measured",
                    "coherence": "measured",
                },
            },
        }
        self.source_path.write_text(json.dumps(self.source), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_import_preserves_source_hash_and_reported_metrics(self):
        receipt = build_obliteratus_receipt(self.source_path)
        artifact = receipt["artifacts"][0]
        self.assertEqual(
            artifact["sha256"],
            hashlib.sha256(self.source_path.read_bytes()).hexdigest(),
        )
        self.assertEqual(receipt["experiment"]["tool"], "OBLITERATUS")
        self.assertEqual(receipt["experiment"]["model"], "example/model-7b")
        config = receipt["experiment"]["configuration"]
        self.assertEqual(config["reported_metrics"]["refusal_rate"], 0.25)
        self.assertNotIn("unrecognised_metric", config["reported_metrics"])
        self.assertEqual(receipt["verification"], [])
        self.assertTrue(any("not been independently verified" in x for x in receipt["limitations"]))

    def test_import_rejects_wrong_schema(self):
        self.source["contribution_schema_version"] = 99
        self.source_path.write_text(json.dumps(self.source), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "schema version"):
            build_obliteratus_receipt(self.source_path)

    def test_import_does_not_copy_free_text_notes(self):
        receipt = build_obliteratus_receipt(self.source_path)
        encoded = json.dumps(receipt)
        self.assertNotIn("Not copied into the receipt", encoded)



if __name__ == "__main__":
    unittest.main()
