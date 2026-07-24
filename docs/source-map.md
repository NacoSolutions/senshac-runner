# Runner Extraction Source Map

Initial extraction from `NacoSolutions/senshac`:

| Runner file | Source purpose |
| --- | --- |
| `scripts/build-ci-runner` | Flox container image build |
| `scripts/act-ci` | Rootless Podman local CI |
| `.github/workflows/build-runner.yml` | Runner image validation |
| `.github/workflows/publish-ci-runner.yml` | GHCR image publishing |
| `.github/workflows/ci.yml` | Reference CI contract |
| `.flox/` | Reproducible runner toolchain |
| `docs/ci-runner-image.md` | Image operations and verification |

The source web repository remains authoritative until clean-container
verification and workflow parity pass from this repository.

## Local Act consumer

Run the runner against an explicit web checkout. The runner does not guess its
consumer repository:

```bash
SENSHAC_WEB_REPO=/path/to/senshac \
  scripts/act-ci
```
