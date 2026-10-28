# Alvearium Commons

An open coordination layer for AI research, experimentation and reproducibility. The initial goal is modest: make research runs easier to describe, compare and independently inspect without requiring researchers to adopt a new execution platform.

## Why this exists

AI research workflows often use different tools for model access, interventions, evaluations and artifact storage. Results can be difficult to reproduce when the method, environment, inputs and output artifacts are recorded inconsistently.

Alvearium Commons will start by standardising a small, tool-agnostic research receipt. Later integrations can connect existing tools rather than replace them.

## Current status

**Early prototype. Not yet a complete research platform.**

Commons can create a provenance receipt from a researcher-supplied JSON manifest and can import an existing OBLITERATUS community contribution JSON record. It hashes the source artifact and labels imported measurements as reported, not independently verified. It does not run experiments or load models.

## Design principles

- **Tool-agnostic** — integrate existing research tools instead of rebuilding them.
- **Reproducible by description** — record methods, versions, configuration and artifact hashes.
- **Honest provenance** — distinguish researcher-provided claims from independently verified facts.
- **Local-first** — no hosted service, wallet, token or remote upload is required for the initial milestone.
- **Human-controlled** — never execute experiment code or modify model weights as a side effect of receipt creation.
- **Privacy-aware** — manifests should not contain credentials, private data or sensitive prompts unless there is a deliberate, safe reason to include them.

## Quick start

Requirements: Python 3.10 or newer.

```bash
python -m pip install -e .
python -m alvearium_commons create --manifest examples/experiment.json --output receipt.json
python -m alvearium_commons import-obliteratus --input community_results/example.json --output receipt.json
python -m unittest discover -s tests -v
```

The example manifest points to a small placeholder artifact in `examples/artifacts/`. It is not a real experiment result. Replace `community_results/example.json` with a real local OBLITERATUS contribution file when using the importer. The CLI is an early prototype and should be treated as such.

## OBLITERATUS import

OBLITERATUS can save explicit community contribution records as local JSON files. Commons accepts the contribution envelope (schema version 1) with telemetry schema version 2 and converts selected fields into the Commons receipt format.

```bash
python -m alvearium_commons import-obliteratus \
  --input community_results/your-contribution.json \
  --output receipts/your-contribution.receipt.json
```

The importer does not require OBLITERATUS to be installed. It treats the input as data, hashes the original JSON file, copies an allowlisted set of reported metrics and method settings, and does not copy free-text notes. It does not execute code, load models, or send data to a remote service.

Imported metric values remain **source-reported measurements**. The hash identifies the exact input file bytes; it does not prove that the reported run occurred or that its findings are valid. Keep the source file alongside the receipt if you need to inspect the full contribution.

## Repository layout

- `src/alvearium_commons/` — local CLI and receipt logic
- `schemas/` — machine-readable receipt schema
- `examples/` — illustrative manifest and receipt
- `tests/` — automated tests
- `docs/` — architecture, threat model and integration notes

## Relationship to Alvearium

Alvearium's existing Spawn v0 describes bounded agent jobs, receipts and hash pins. Commons explores whether similar provenance and bounded-work patterns can support research workflows. This repository is a companion experiment, not a claim that Alvearium already provides a complete research coordination platform.

## Scope of the first milestone

1. Read a local JSON manifest or an OBLITERATUS contribution record.
2. Hash explicitly declared artifacts or the original contribution file.
3. Write a deterministic, inspectable receipt.
4. Validate required fields and test failure cases.
5. Document what the receipt can and cannot establish.

Initial scope excludes running experiments, changing model weights, uploading artifacts, blockchain anchoring, identity claims, reward systems and automated trust scores.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Early feedback on the receipt format and missing provenance fields is especially useful.

## License

See [LICENSE](LICENSE) for the repository's license.
