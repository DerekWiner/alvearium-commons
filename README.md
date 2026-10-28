# Alvearium Commons

An open coordination layer for AI research, experimentation and reproducibility. The initial goal is modest: make research runs easier to describe, compare and independently inspect without requiring researchers to adopt a new execution platform.

## Why this exists

AI research workflows often use different tools for model access, interventions, evaluations and artifact storage. Results can be difficult to reproduce when the method, environment, inputs and output artifacts are recorded inconsistently.

Alvearium Commons will start by standardising a small, tool-agnostic research receipt. Later integrations can connect existing tools rather than replace them.

## Current status

**Early scaffold. Not yet a complete research platform.**

The first milestone is a local, dependency-free Python utility that creates a provenance receipt from a researcher-supplied JSON manifest and computes SHA-256 hashes for declared local artifacts. A receipt records what was supplied; it does not prove that an experiment is valid, safe, or independently reproduced.

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
python -m unittest discover -s tests -v
```

The example manifest points to a small placeholder artifact in `examples/artifacts/`. It is not a real experiment result. The CLI is an early prototype and should be treated as such.

## Repository layout

- `src/alvearium_commons/` — local CLI and receipt logic
- `schemas/` — machine-readable receipt schema
- `examples/` — illustrative manifest and receipt
- `tests/` — automated tests
- `docs/` — architecture, threat model and integration notes

## Relationship to Alvearium

Alvearium's existing Spawn v0 describes bounded agent jobs, receipts and hash pins. Commons explores whether similar provenance and bounded-work patterns can support research workflows. This repository is a companion experiment, not a claim that Alvearium already provides a complete research coordination platform.

## Scope of the first milestone

1. Read a local JSON manifest.
2. Hash explicitly declared local artifact files.
3. Write a deterministic, inspectable receipt.
4. Validate required fields and test failure cases.
5. Document what the receipt can and cannot establish.

Initial scope excludes running experiments, changing model weights, uploading artifacts, blockchain anchoring, identity claims, reward systems and automated trust scores.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Early feedback on the receipt format and missing provenance fields is especially useful.

## License

See [LICENSE](LICENSE) for the repository's license.
