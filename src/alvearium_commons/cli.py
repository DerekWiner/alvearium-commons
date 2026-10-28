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



def build_obliteratus_receipt(input_path: Path) -> dict[str, Any]:
    """Import an OBLITERATUS community contribution as a Commons receipt.

    The source JSON is treated as data only. This function does not import
    OBLITERATUS, run model code, contact a network service, or verify claims.
    The original contribution is hashed as a source artifact; selected
    measurements are copied as reported values, not independently validated.
    """
    input_path = input_path.expanduser().resolve()
    contribution = _read_json(input_path)

    if contribution.get("contribution_schema_version") != 1:
        raise ValueError("unsupported OBLITERATUS contribution schema version")
    telemetry = contribution.get("telemetry")
    if not isinstance(telemetry, dict) or telemetry.get("schema_version") != 2:
        raise ValueError("expected an OBLITERATUS telemetry schema v2 record")

    model_name = contribution.get("model_name")
    timestamp = contribution.get("timestamp")
    method = telemetry.get("method")
    if not isinstance(model_name, str) or not model_name.strip():
        raise ValueError("contribution field 'model_name' must be a non-empty string")
    if not isinstance(timestamp, str) or not timestamp.strip():
        raise ValueError("contribution field 'timestamp' must be a non-empty string")
    if not isinstance(method, str) or not method.strip():
        raise ValueError("contribution telemetry field 'method' must be a non-empty string")

    raw_metrics = telemetry.get("quality_metrics", {})
    if not isinstance(raw_metrics, dict):
        raise ValueError("contribution telemetry 'quality_metrics' must be an object")
    # Allowlist simple reported metrics. Do not copy arbitrary external JSON
    # into the receipt's configuration.
    metric_names = (
        "refusal_rate", "invalid_count", "invalid_rate", "perplexity",
        "coherence", "kl_divergence", "kl_budget", "perplexity_increase",
        "capability_score", "capability_total_count", "capability_completed_count",
        "degenerate_count", "time_seconds",
    )
    reported_metrics = {
        key: raw_metrics[key]
        for key in metric_names
        if key in raw_metrics and (
            raw_metrics[key] is None
            or isinstance(raw_metrics[key], (str, int, float, bool))
        )
    }
    raw_status = telemetry.get("quality_metric_status", {})
    metric_status = {}
    if isinstance(raw_status, dict):
        metric_status = {
            key: raw_status[key]
            for key in metric_names
            if key in raw_status and isinstance(raw_status[key], str)
        }

    raw_method_config = telemetry.get("method_config", {})
    if not isinstance(raw_method_config, dict):
        raw_method_config = {}
    allowed_config_keys = {
        "n_directions", "norm_preserve", "regularization", "refinement_passes",
        "project_biases", "use_chat_template", "use_whitened_svd",
        "true_iterative_refinement", "use_jailbreak_contrast",
        "layer_adaptive_strength", "attention_head_surgery",
        "safety_neuron_masking", "per_expert_directions", "use_sae_features",
        "invert_refusal", "project_embeddings", "embed_regularization",
        "activation_steering", "steering_strength", "expert_transplant",
        "transplant_blend", "reflection_strength",
    }
    method_config = {
        key: value
        for key, value in raw_method_config.items()
        if key in allowed_config_keys
        and isinstance(value, (str, int, float, bool, type(None)))
    }
    model_info = telemetry.get("model", {})
    if not isinstance(model_info, dict):
        model_info = {}
    environment = telemetry.get("environment", {})
    if not isinstance(environment, dict):
        environment = {}

    digest, size = _sha256_file(input_path)
    experiment = {
        "title": f"Imported OBLITERATUS contribution for {model_name[:160]}",
        "tool": "OBLITERATUS",
        "method": method[:120],
        "model": model_name[:240],
        "configuration": {
            "source_format": "OBLITERATUS community contribution",
            "contribution_schema_version": 1,
            "telemetry_schema_version": 2,
            "source_timestamp": timestamp[:80],
            "config_fingerprint": (
                contribution.get("config_fingerprint")[:80]
                if isinstance(contribution.get("config_fingerprint"), str) else None
            ),
            "reported_metrics": reported_metrics,
            "reported_metric_status": metric_status,
            "method_config": method_config,
            "model_summary": {
                key: model_info[key]
                for key in ("architecture", "num_layers", "num_heads", "hidden_size", "total_params")
                if key in model_info and isinstance(model_info[key], (str, int, float, bool, type(None)))
            },
        },
    }
    artifacts = [{
        "path": input_path.name,
        "sha256": digest,
        "size_bytes": size,
        "media_type": "application/json",
        "description": "Original OBLITERATUS community contribution record",
    }]
    claims: list[str] = []
    identity_payload = {
        "experiment": experiment,
        "artifacts": artifacts,
        "claims": claims,
    }
    canonical = json.dumps(
        identity_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )
    receipt_id = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    # Retain only a small set of environment fields to avoid copying arbitrary
    # values from an external contribution into the receipt.
    environment_summary = {
        key: environment[key]
        for key in ("python_version", "platform", "device", "gpu_name", "cuda_version")
        if key in environment and isinstance(environment[key], (str, int, float, bool, type(None)))
    }
    return {
        "schema_version": "1.0",
        "receipt_id": receipt_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "experiment": experiment,
        "environment": environment_summary,
        "artifacts": artifacts,
        "claims": claims,
        "limitations": [
            "Imported metrics are reported by the source contribution and have not been independently verified by Commons.",
            "The source record hash identifies these exact JSON bytes; it does not prove the experiment ran as described.",
            "This adapter does not load models, execute experiment code, or contact OBLITERATUS services.",
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
    import_parser = subparsers.add_parser(
        "import-obliteratus",
        help="convert an OBLITERATUS community contribution JSON file to a Commons receipt",
    )
    import_parser.add_argument("--input", required=True, type=Path, help="path to the source contribution JSON")
    import_parser.add_argument("--output", required=True, type=Path, help="path for the output receipt JSON")
    args = parser.parse_args(argv)

    try:
        if args.command == "create":
            receipt = build_receipt(args.manifest)
        else:
            receipt = build_obliteratus_receipt(args.input)
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
