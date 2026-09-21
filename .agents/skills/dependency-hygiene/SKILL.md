# Dependency Hygiene

Use when touching Flox manifests, lock files, container build inputs, or tool versions.

## Commands

```bash
scripts/check-flox-lock
python3 -m unittest discover -s tests -v
rg -n 'manifest|manifest.lock|gnutar|tar|flox|podman' .flox scripts Containerfile.warren-agent .github/workflows
```

Prefer the pinned project dependencies and existing package IDs. Update a manifest and
its generated lock together; do not hand-wave missing outputs or add unrelated tools.

## Acceptance checks

- `scripts/check-flox-lock` exits zero.
- The runner contract tests pass.
- Every added dependency has a declared, resolved lock entry and a repository use.
- No production image, workflow ownership, or web-repository behavior changes occur.
