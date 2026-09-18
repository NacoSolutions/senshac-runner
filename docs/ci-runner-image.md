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

The script defaults to rootless Podman through `flox containerize`. Flox is
the sole image builder and supplies the image entrypoint that activates the
environment before dispatching commands. The publication workflow uses Docker;
the same script and derived-image tar copy are used for both runtimes. The
publication workflow smoke-tests the activated image for the runner's required
tools. Override the runtime when needed:

```bash
CONTAINER_RUNTIME=docker dx scripts/build-ci-runner ghcr.io/nacosolutions/senshac-runner:test
```

## Local no-push verification

For the fast, registry-free build and smoke test, install Flox and rootless
Podman, then run:

```bash
scripts/verify-ci-runner-local
```

The script builds `senshac-runner:local` with `CONTAINER_RUNTIME=podman` and
runs `scripts/verify-ci-runner` against that image. It does not log in to a
registry or push anything. An optional first argument supplies another local
image tag:

```bash
scripts/verify-ci-runner-local senshac-runner:debug
```

For an already-built image, run `scripts/smoke-ci-runner IMAGE` (or set
`CONTAINER_RUNTIME=docker`). The helper mounts the verification script
read-only and runs it by file path through Flox's image entrypoint. It first
requires a deliberate exit-42 probe, then requires the successful check's
completion marker. This verifies both execution and failure propagation.
The standalone activation contract is `FLOX_ENV/bin` on `PATH`; the host
project path and host Flox CLI belong to the build environment.

The script attempts to start the user Podman socket with
`systemctl --user start podman.socket` and exports `DOCKER_HOST` when the
socket is available. The socket is not required by the local build or smoke
test, but it is required by Act. Rootless Podman, Flox, and a Git worktree are
prerequisites; the Flox environment must be able to resolve its packages.

## Local CI

```bash
dx bun run test:workflow:ci
```

`scripts/act-ci` maps `ubuntu-latest` to the same CI runner image and uses the
current user's rootless Podman socket. After local verification, a committed
web checkout can be exercised without GHCR credentials using:

```bash
CI_RUNNER_IMAGE=senshac-runner:local scripts/act-ci /path/to/senshac-web
```

Act must be installed separately. The helper clones the current Git commit
into a temporary checkout so Act runs against committed state, matching
GitHub CI. This Act path still runs the web workflow and may download action
images; it is not part of the no-push image smoke test.

## Update Contract

When `.flox/env/manifest.toml` or `.flox/env/manifest.lock` changes, publish a
new image before expecting GitHub CI to use new tools. The runner contract
requires `tar` to be available on `PATH`; `actions/setup-node` uses it to
extract the Node distribution. The manifest installs Flox's `gnutar` and
`gzip` packages, and the smoke test round-trips a gzip-compressed archive
with `--strip-components=1`.

Use the Flox CLI to reconcile package changes and commit both manifest and
lockfile. `scripts/check-flox-lock` checks manifest equality and resolved
package outputs for each requested system before image construction.
A manifest declaration alone is insufficient: the original missing-tar
failure came from an unresolved `gnutar` entry in the committed lockfile.
Local Flox repaired that entry automatically, making the earlier local/CI
comparison use different inputs. Runtime differences remain a separate
verification question.

The build logs the image PATH and the
actual `/nix/store` tar candidates, then copies the discovered `tar` or
`gtar` executable (following symlinks) into `/usr/bin/tar` in a small derived
image for pre-activation Actions tooling. The build then verifies that the
selected runtime resolves exactly `/usr/bin/tar`
before retagging; invoke it once with `CONTAINER_RUNTIME=podman` and once with
`CONTAINER_RUNTIME=docker` to compare runtimes. The publish workflow runs
on main for those files and can also be started manually from GitHub Actions.
PR verification and publication pin Flox 1.16.0. The read-only PR workflow
builds and smoke-tests a local Docker image, keeping registry publication on
main. Publication verifies the local image, pushes the immutable
`sha-<commit>` tag, pulls and smoke-tests that registry artifact, and only
then advances `latest`.

Fast regression gates (Python 3.11+ and Bash):

```bash
scripts/check-flox-lock
python3 -m unittest discover -s tests -v
for script in scripts/*; do bash -n "$script"; done
```

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
