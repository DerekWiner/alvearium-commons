import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from alvearium_commons.cli import build_receipt


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


if __name__ == "__main__":
    unittest.main()
