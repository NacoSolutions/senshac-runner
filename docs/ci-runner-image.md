# CI Runner Image

Seed: `senshac-50a2`

The CI runner image is the shared execution surface for GitHub Actions and
local Act runs. It is built from the project Flox environment with
`flox containerize`, including GNU `tar` for actions such as
`actions/setup-node`, then published to:

```text
ghcr.io/nacosolutions/senshac-runner:latest
ghcr.io/nacosolutions/senshac-runner:sha-<commit>
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
CONTAINER_RUNTIME=docker dx scripts/build-ci-runner ghcr.io/nacosolutions/senshac-runner:test
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
new image before expecting GitHub CI to use new tools. The runner contract
requires `tar` to be available on `PATH`; `actions/setup-node` uses it to
extract the Node distribution. The publish workflow runs
on main for those files and can also be started manually from GitHub Actions.
It pushes the immutable `sha-<commit>` tag first, pulls and smoke-tests that
registry artifact, and only then advances `latest`.

## Producer/consumer handoff

This repository is the **producer**. A successful publication verifies the
registry digest and exposes the full immutable image reference in two places:

- the workflow job output `image_digest`;
- the `senshac-runner-image-digest` workflow artifact, whose
  `runner-image-digest.txt` contains one `ghcr.io/...@sha256:...` reference.

The workflow summary also prints that reference and the previous `latest`
digest for rollback. The web repository is the **consumer**: its workflow
should pin `runs-on`'s runner image to the artifact's digest (not `latest` or
the `sha-<commit>` tag). Updating that consumer is intentionally a separate
change in `senshac-web`; this repository does not edit or own the web checkout.

The local Act helper defaults to the published `senshac-runner:latest` image;
set `CI_RUNNER_IMAGE` to the exported `@sha256:` reference when reproducing a
consumer run exactly.
