# CI Runner Image

Seed: `senshac-50a2`

The CI runner image is the shared execution surface for GitHub Actions and
local Act runs. The pinned Nix flake packages the complete runtime directly
into a `dockerTools.buildLayeredImage` OCI archive. The image has no
distribution base or environment-manager activation: it runs as UID/GID 1000
and provides its tools directly on `PATH`. The developer `devenv.nix` and
`devenv.lock` remain a separate shell contract.

```text
ghcr.io/nacosolutions/senshac-runner:latest
ghcr.io/nacosolutions/senshac-runner:sha-<commit>
```

## Runtime contract

The flake packages Bash, Bun, CA certificates, Chromium, coreutils, curl,
fontconfig (including its default configuration and fallback fonts), GCC, Git,
GitHub CLI, GNU tar, grep, gzip, jq, Node.js 22, and unzip. The image
provides a non-root `runner` account (UID/GID 1000), `/workspace` as its working
directory, and writable `/home/runner`, `/workspace`, and `/tmp` (mode `1777`).
It also supplies `/usr/bin/env` and `/usr/bin/bash` for mounted CI scripts.
The image exposes the Nix glibc loader at `/lib64/ld-linux-x86-64.so.2` and
sets `LD_LIBRARY_PATH` to that glibc closure so native Linux executables
installed by consumer dependencies (for example Cloudflare's `workerd`) can
run in this distroless filesystem. The base verifier compiles and runs a
system-interpreter probe to guard this ABI contract.

## Local build and smoke verification

Install Nix and rootless Podman, then run the no-push build and verification:

```bash
scripts/verify-ci-runner-local
```

This builds `senshac-runner:local` and runs `scripts/smoke-ci-runner`. The
smoke test checks failure propagation, GNU tar and gzip, Git and GitHub CLI,
Node and Bun TLS access, and headless Chromium. Run `scripts/verify-nix-base`
separately to check the directly packaged tools, non-root identity, and
writable paths.

The Podman checks require a rootless runtime; Docker can be selected with
`CONTAINER_RUNTIME=docker` for the smoke helper or build script. For an existing
image, run:

```bash
CONTAINER_RUNTIME=podman scripts/verify-nix-base IMAGE
CONTAINER_RUNTIME=podman scripts/smoke-ci-runner IMAGE
```

The verifier copies the committed checkout into a temporary writable
workspace. Smoke scripts are mounted read-only and executed by the packaged
Bash. Neither path activates devenv, mounts a developer lockfile, installs
packages, or mutates the checkout.

The build script defaults to rootless Podman and loads the flake's
Docker-compatible archive. Docker is also supported:

```bash
CONTAINER_RUNTIME=docker dx scripts/build-ci-runner ghcr.io/nacosolutions/senshac-runner:test
```

## Developer environment and updates

`devenv.nix` and `devenv.lock` remain for developer shells and are validated by
`scripts/check-devenv-lock` in standard CI. They do not supply or activate
runtime image tools. To change image tools, update `runtimePackages` and
`runtime_tools` metadata in `flake.nix`, then verify the image with the commands
above. Keep the smoke and base-verification tool requirements aligned with the
flake package closure.

The OCI archive and metadata contract can also be checked without a container
runtime:

```bash
scripts/check-oci-flake
```

Run the focused repository checks with Python 3.11+ and Bash:

```bash
python3 -m unittest discover -s tests -v
for script in scripts/*; do bash -n "$script"; done
git diff --check
```

## Local CI and image handoff

`scripts/act-ci` maps `ubuntu-latest` to the same runner image and uses the
current user's rootless Podman socket. Act is included in `devenv.nix`; run it
from the project shell. The default image is the immutable digest currently
validated by `senshac-web`:

```bash
devenv shell -- scripts/act-ci /path/to/senshac-web
```

For a local candidate, set `CI_RUNNER_IMAGE` explicitly:

```bash
CI_RUNNER_IMAGE=senshac-runner:local \
  devenv shell -- scripts/act-ci /path/to/senshac-web
```

The helper rewrites only the temporary cloned workflow's pinned runner image;
the checked-in web workflow remains unchanged. It defaults to `workflow_dispatch`
so Act does not need a synthetic pull-request number; set `ACT_EVENT` to use a
different event supported by the workflow.

Act clones the current Git commit into a temporary checkout, matching GitHub
CI; it may download action images and is separate from the no-push smoke test.

This repository produces the image; the web repository consumes it. PR
verification builds the OCI archive once and tests that artifact. Publication
resolves the previous `latest` rollback digest from remote Buildx manifest
metadata, without downloading its image layers. If that inspection fails, the
workflow reports a first publication only when an authenticated GHCR manifest
API request confirms HTTP 404 with `MANIFEST_UNKNOWN`; other failures stop the
publication. It then smoke-tests the immutable `sha-<commit>` image, records
its registry digest, and advances `latest`. Consumer workflows should pin the
verified `@sha256:` digest rather than a mutable tag. Updating the web consumer
remains a separate change in `senshac-web`.
