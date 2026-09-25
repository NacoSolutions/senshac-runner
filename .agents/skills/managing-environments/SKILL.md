# Managing Environments

Use the pinned devenv environment for runner commands and preserve the rootless
Podman boundary used by CI.

## Commands

```bash
devenv sd ready
devenv ml prime
devenv scripts/check-devenv-lock
CONTAINER_RUNTIME=podman scripts/verify-ci-runner-local senshac-runner:local
SENSHAC_WEB_REPO=/path/to/clean/web/checkout scripts/act-ci
```

Run `scripts/verify-ci-runner-local` after runner image changes. Use
`scripts/act-ci` with a clean web checkout to validate the producer/consumer
handoff. Keep the runner image reference immutable when a consumer records a
published image.

## Acceptance checks

- devenv manifest and lock validation exits zero.
- The local runner build and smoke test exits zero when image tooling is in scope.
- Act validates the clean web checkout with the selected runner image when CI integration is in scope.
