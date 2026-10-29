# Alvearium Commons

**Adapters and reproducibility receipts for research workflows.**

Alvearium Commons is intended to connect existing research tools through narrow adapters and portable receipts. It is distinct from REA Core and REA Orchestrator.

## Responsibility boundary

- REA defines the evidence-first research methodology.
- REA Core defines the shared investigation record and validation contract.
- REA Orchestrator is intended to route bounded tasks.
- Alvearium Commons is intended to adapt existing tools and produce reproducibility and evaluation receipts.
- Alvearium provides a broader coordination architecture for agents, identity, permissions and governance.

Commons should not introduce a competing investigation schema or a second general-purpose orchestration runtime.

## First proposed deliverable

Build one adapter that accepts a valid REA Core investigation record, invokes no external service by default, and emits a reproducibility receipt describing the input record identifier and hash, adapter name and version, declared parameters, execution mode, network-access status, output artifact references and hashes where available, warnings, failures and limitations.

A receipt records what the adapter reports. It is not independent proof that an experiment was correct or reproducible.

## Current status

This repository establishes the intended purpose. A complete adapter framework, evaluation runtime and verifiable research workflow should not be assumed to exist until implemented and tested.

## Design constraints

- Prefer small adapters around existing tools.
- Keep secrets out of receipts.
- Make network access explicit.
- Preserve provenance and tool versions.
- Do not execute untrusted artifacts without an approved execution environment.
- Keep integration with REA Core versioned and tested.

## Next milestone

Define the receipt format and create one mock adapter with tests. Add a second adapter only after the first end-to-end example is reproducible.
