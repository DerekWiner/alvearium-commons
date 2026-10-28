"""Create provenance receipts without executing research code."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"cannot read manifest {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("manifest root must be a JSON object")
    return value


def _sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def build_receipt(manifest_path: Path) -> dict[str, Any]:
    """Build a receipt from a manifest and hash its declared local artifacts.

    Artifact paths are resolved relative to the manifest's directory. Paths
    that escape that directory, missing files, and non-regular files are
    rejected. This function never executes commands or opens network URLs.
    """
    manifest_path = manifest_path.expanduser().resolve()
    manifest = _read_json(manifest_path)

    for key in ("title", "tool", "method"):
        if not isinstance(manifest.get(key), str) or not manifest[key].strip():
            raise ValueError(f"manifest field {key!r} must be a non-empty string")

    declared_artifacts = manifest.get("artifacts", [])
    if not isinstance(declared_artifacts, list):
        raise ValueError("manifest field 'artifacts' must be a list")

    base_dir = manifest_path.parent.resolve()
    artifacts: list[dict[str, Any]] = []
    for index, item in enumerate(declared_artifacts):
        if not isinstance(item, dict):
            raise ValueError(f"artifact {index} must be a JSON object")
        raw_path = item.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError(f"artifact {index} must have a non-empty 'path'")
        relative_path = Path(raw_path)
        if relative_path.is_absolute():
            raise ValueError(f"artifact path must be relative: {raw_path}")
        candidate = (base_dir / relative_path).resolve()
        try:
            candidate.relative_to(base_dir)
        except ValueError as exc:
            raise ValueError(f"artifact path escapes manifest directory: {raw_path}") from exc
        if not candidate.is_file():
            raise ValueError(f"artifact is missing or is not a regular file: {raw_path}")

        digest, size = _sha256_file(candidate)
        artifacts.append({
            "path": relative_path.as_posix(),
            "sha256": digest,
            "size_bytes": size,
            "media_type": item.get("media_type"),
            "description": item.get("description"),
        })

    experiment_keys = (
        "title", "tool", "tool_version", "model", "model_revision",
        "dataset", "dataset_revision", "method", "configuration",
        "started_at", "completed_at",
    )
    experiment = {key: manifest[key] for key in experiment_keys if key in manifest}
    claims = manifest.get("claims", [])
    if not isinstance(claims, list) or not all(isinstance(x, str) for x in claims):
        raise ValueError("manifest field 'claims' must be a list of strings")

    # Hash the described run and artifact digests to produce a stable content ID.
    identity_payload = {
        "experiment": experiment,
        "artifacts": artifacts,
        "claims": claims,
    }
    canonical = json.dumps(identity_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    receipt_id = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    environment = manifest.get("environment", {})
    if not isinstance(environment, dict):
        raise ValueError("manifest field 'environment' must be a JSON object")

    return {
        "schema_version": "1.0",
        "receipt_id": receipt_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "experiment": experiment,
        "environment": environment,
        "artifacts": artifacts,
        "claims": claims,
        "limitations": [
            "Receipt generation records supplied metadata and file hashes; it does not prove that the experiment ran as described.",
            "Receipt generation does not establish scientific validity, safety, causality or independent replication.",
        ],
        "verification": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="alvearium-commons",
        description="Create a local provenance receipt from a JSON research manifest.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    create_parser = subparsers.add_parser("create", help="create a receipt and hash declared local artifacts")
    create_parser.add_argument("--manifest", required=True, type=Path, help="path to the JSON manifest")
    create_parser.add_argument("--output", required=True, type=Path, help="path for the output receipt JSON")
    args = parser.parse_args(argv)

    try:
        receipt = build_receipt(args.manifest)
        output = args.output.expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Receipt written to {output}")
    print(f"Receipt ID: {receipt['receipt_id']}")
    print(f"Artifacts hashed: {len(receipt['artifacts'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
