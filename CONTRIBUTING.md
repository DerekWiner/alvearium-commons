# Contributing

Thanks for considering a contribution to Alvearium Commons.

## Current priorities

1. Improve the research receipt format.
2. Identify provenance fields needed to reproduce or audit a run.
3. Add tests for malformed manifests, missing artifacts and deterministic output.
4. Propose small adapters to existing tools, with a clear user need and an upstream reference.

## Contribution principles

- Keep the initial tool local-first and dependency-light.
- Do not claim a receipt proves correctness, safety, causality or independent replication.
- Label researcher-entered claims separately from values measured by the tool.
- Do not add automatic execution of experiment code as part of receipt creation.
- Never commit API keys, access tokens, private datasets, model weights or other secrets.
- Preserve the licenses and attribution of third-party projects. Prefer documented interfaces over copied implementation code.

## Before opening a pull request

- Explain the problem and the proposed change.
- Add or update tests for behaviour changes.
- Document schema changes and their compatibility implications.
- Run the test suite with `python -m unittest discover -s tests -v`.
- Keep pull requests focused and small.

For major changes, open an issue first so the design can be discussed before implementation.
