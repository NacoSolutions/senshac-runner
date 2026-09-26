# CI Runner Image

Seed: `senshac-50a2`

The CI runner image is the shared execution surface for GitHub Actions and
local Act runs. It is assembled by the pinned Nix flake with
`pkgs.dockerTools.buildLayeredImage`, then published to. devenv remains the
committed manifest/lock source and is checked before the Nix build; the image
contains no apt-get step or separate CI browser install.

```text
ghcr.io/nacosolutions/senshac-runner:latest
ghcr.io/nacosolutions/senshac-runner:sha-<commit>
```

## Why

Direct `devenv shell` in GitHub CI rebuilds the environment from a clean Nix
cache on every run. A single bad fixed-output hash in a custom package can fail
CI before the project gate starts, while local machines pass from cache. The
runner image moves that realization step to one image-publishing workflow and
makes CI consume the same prebuilt toolchain every time.

## Local Build

```bash
dx scripts/build-ci-runner senshac-ci-runner:latest
```

The script defaults to rootless Podman, builds the flake's `ociImage` with
Nix, and loads its Docker-compatible archive. `dockerTools` is the sole image
builder; the publication workflow uses Docker and the same script works with
either runtime. The image contains only the devenv CLI/runtime, shell, and
certificates. The mounted project's lock supplies Bun, Chromium, and all other
tools. Override the runtime when needed:

```bash
CONTAINER_RUNTIME=docker dx scripts/build-ci-runner ghcr.io/nacosolutions/senshac-runner:test
```

## Local no-push verification

For the fast, registry-free build and smoke test, install Nix and rootless
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
read-only and runs it by file path through devenv's image entrypoint. It first
requires a deliberate exit-42 probe, then requires the successful check's
completion marker. This verifies both execution and failure propagation.
The Nix image's default entrypoint is a devenv shell activation wrapper. It requires
the mounted project's `devenv.lock`; activation exposes Bun,
Chromium, and every declared tool without installing packages or mutating the
lock. The smoke check explicitly runs `devenv shell -- command -v bun`,
`devenv shell -- command -v chromium`, and a headless Chromium launch.

The script attempts to start the user Podman socket with
`systemctl --user start podman.socket` and exports `DOCKER_HOST` when the
socket is available. The socket is not required by the local build or smoke
test, but it is required by Act. Rootless Podman, Nix, and a Git worktree are
prerequisites; the committed devenv lock must pass validation.

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

When `devenv.nix` or `devenv.lock` changes, publish a
new image before expecting GitHub CI to use new tools. The runner contract
requires `tar` to be available on `PATH`; `actions/setup-node` uses it to
extract the Node distribution. The manifest installs devenv's `gnutar` and
`gzip` packages, and the smoke test round-trips a gzip-compressed archive
with `--strip-components=1`. The manifest records `chromium` as the browser dependency and its committed
lock resolves the matching runtime. No browser download, apt-get step, or
second CI installation is allowed.

Use the devenv CLI to reconcile package changes and commit both manifest and
lockfile. `scripts/check-devenv-lock` checks manifest equality and resolved
package outputs for each requested system before image construction.
A manifest declaration alone is insufficient: the original missing-tar
failure came from an unresolved `gnutar` entry in the committed lockfile.
Keep Chromium's manifest and committed lock entry together; runtime checks use
the activated PATH rather than installing browsers or libraries.
Local devenv repaired that entry automatically, making the earlier local/CI
comparison use different inputs. Runtime differences remain a separate
verification question.

The Nix closure includes only the activation bootstrap. `scripts/verify-nix-base`
checks the mounted-project contract, including `command -v bun`,
`command -v chromium`, and a headless Chromium launch after devenv shell activation. The publish workflow runs
on main for those files and can also be started manually from GitHub Actions.
PR verification builds the comparison environments and Nix OCI archive. The
read-only PR workflow builds and smoke-tests a local Docker image, keeping
registry publication on main. Publication verifies the local image, pushes the immutable
`sha-<commit>` tag, pulls and smoke-tests that registry artifact, and only
then advances `latest`.

Fast regression gates (Python 3.11+ and Bash):

```bash
scripts/check-devenv-lock
python3 -m unittest discover -s tests -v
for script in scripts/*; do bash -n "$script"; done
```

## Workflow event matrix

The workflows use one validation owner per pull request and one publication
owner per merged commit. A merge is represented by the resulting `push` to
`main`; it does not replay pull-request verification as a main-branch check.
All three workflow classes use path filters so unrelated documentation or
metadata changes do not allocate runner/image jobs.

| Event | Workflow | Work | Concurrency and handoff |
| --- | --- | --- | --- |
| `pull_request` (changed runner paths) | `CI` | Bash, manifest, and Python contract validation | `ci-pr-<number>` cancels superseded commits; this is the required source-validation check |
| `pull_request` (changed image/OCI paths) | `Verify CI Runner Container` | Builds each producer image once, then verifies the immutable uploaded archives | `verify-runner-pr-<number>` cancels superseded commits; it relies on CI for the general validation pass |
| `push` to `main` after merge (publication paths) | `Publish CI Runner Container` | Builds the runner needed by the merge, smoke-tests it, publishes its immutable `sha-<commit>` tag, verifies the registry digest, and promotes `latest` | `publish-ci-runner-main` cancels an obsolete in-flight publication; the digest artifact is the consumer handoff |
| `workflow_dispatch` | `Publish CI Runner Container` or `Verify CI Runner Container` | Explicit operator rerun of the selected build or verification | Uses the same concurrency group and immutable archive/digest rules |

The PR image workflow and the post-merge publication workflow intentionally do
not trigger each other. The PR workflow does not publish, and the main
workflow does not run the full PR validation suite again. Both workflows use
`flake.nix` and `pkgs.dockerTools`; the publication workflow retains its
registry pull-and-smoke step because it proves the exact immutable digest that
consumers pin.

## Producer/consumer handoff

This repository is the **producer**. A successful publication verifies the
registry digest and exposes the full immutable image reference in two places:

### Build once, verify by artifact

The pull-request workflow has one `build-image` producer job. It builds the
public Nix `ociImage` exactly once, then uploads its Docker-compatible archive.
The dependent `verify-image` job only downloads and loads that archive; it
never rebuilds the image. This keeps the handoff independent of a Docker
daemon shared between jobs while ensuring smoke tests use the producer's exact
bytes.

For reuse across workflows, publish the archive or image to a content-addressed
registry reference and pass its `@sha256:` digest as an explicit job input.
Consumers should pull/load that digest and verify it before measurement; never
substitute a mutable tag such as `latest`. The publication workflow already
records the verified GHCR digest and retains a digest handoff artifact for
this cross-workflow producer/consumer boundary.

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
