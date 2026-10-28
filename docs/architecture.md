# Initial architecture

## Goal

Provide a small, inspectable provenance layer that can sit beside existing AI research tools. It should help researchers record what they ran and which artifacts resulted without pretending to verify scientific claims.

## Data flow

1. A researcher prepares a JSON manifest describing a completed run.
2. The local CLI checks the manifest's required fields.
3. The CLI hashes declared local artifact files with SHA-256.
4. The CLI writes a receipt containing the manifest details, artifact hashes and receipt-generation metadata.
5. The researcher can share the receipt and artifacts according to their own privacy and licensing decisions.

The CLI must not execute commands from a manifest or imported record, download remote content, upload files or modify model artifacts. The OBLITERATUS importer treats the contribution as untrusted data, does not import the OBLITERATUS package, and does not copy arbitrary free-text notes into the receipt.

## Trust boundaries

A receipt can show that a particular file's bytes match a recorded hash. By itself, it cannot show that:
- the described experiment actually ran as stated
- the model or dataset is authentic
- the method is scientifically sound
- the output is safe or unbiased
- another researcher reproduced the result
- the author has permission to redistribute the referenced artifacts

Values entered by a researcher remain claims unless separately verified. Independent verification should be represented as a separate event with its own actor, method, evidence and timestamp, not inferred from receipt creation.

## Planned components

- **Manifest** — researcher-authored description of a run.
- **Receipt schema** — versioned JSON structure for provenance.
- **Local CLI** — validates inputs, hashes local artifacts and writes a receipt.
- **OBLITERATUS importer** — accepts the existing community contribution envelope, hashes the source JSON and maps a small allowlist of reported metrics into a Commons receipt.
- **Adapters** — future optional connectors to existing evaluation and model-intervention tools.
- **Verification records** — a future format for independent checks, kept distinct from the original receipt.

## Initial non-goals

No orchestration service, agent marketplace, token, blockchain dependency, automatic model intervention, experiment execution, remote artifact upload or trust score is required for the first milestone.

## Evolution path

1. Establish a stable receipt schema and tested local CLI.
2. Import an existing OBLITERATUS contribution record and preserve a hash of the original file.
3. Test the mapping against real exported records and gather researcher feedback.
4. Add a narrow adapter for another tool only when it removes real integration friction.
5. Explore optional signing or external anchoring after the local workflow is useful on its own.
