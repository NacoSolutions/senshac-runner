# CI Runner Image

Seed: `senshac-50a2`

The CI runner image is the shared execution surface for GitHub Actions and
local Act runs. It is built from the project Flox environment with
`flox containerize`, then published to:

```text
ghcr.io/nacosolutions/senshac-ci-runner:latest
ghcr.io/nacosolutions/senshac-ci-runner:sha-<commit>
```

## Why

Direct `flox activate` in GitHub CI rebuilds the environment from a clean Nix
cache on every run. A single bad fixed-output hash in a custom package can fail
CI before the project gate starts, while local machines pass from cache. The
runner image moves that realization step to one image-publishing workflow and
makes CI consume the same prebuilt toolchain every time.

## Local Build

```bash
dx scripts/build-ci-runner senshac-ci-runner:latest
```

The script defaults to rootless Podman through `flox containerize`. Flox builds
the local `senshac:ci-runner` image first, then the script adds a small POSIX
compatibility layer so Node package shebangs using `/usr/bin/env` work inside
GitHub CI, Act, and direct `podman run` smoke checks. It also exposes the Flox
glibc runtime at `/lib64` so Cloudflare's prebuilt `workerd` executable can
load inside the otherwise non-FHS image. Override the runtime when needed:

```bash
CONTAINER_RUNTIME=docker dx scripts/build-ci-runner ghcr.io/nacosolutions/senshac-ci-runner:test
```

## Local CI

```bash
dx bun run test:workflow:ci
```

`scripts/act-ci` maps `ubuntu-latest` to the same CI runner image and uses the
current user's rootless Podman socket. It clones the current Git commit into a
temporary checkout so Act runs against committed state, matching GitHub CI.

## Update Contract

When `.flox/env/manifest.toml` or `.flox/env/manifest.lock` changes, publish a
new image before expecting GitHub CI to use new tools. The publish workflow runs
on main for those files and can also be started manually from GitHub Actions.
