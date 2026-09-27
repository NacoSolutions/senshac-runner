# Rootless OCI runner image

Seed: `senshac-runner-300e`

The repo-local `flake.nix` produces the published runner image. Nix packages
the complete CI runtime directly into a `dockerTools.buildLayeredImage` OCI
archive. The final image uses no distribution base, environment manager,
project activation, or mounted developer lockfile. The separate `devenv.nix`
and `devenv.lock` remain available for developer shells and are validated by
the repository CI independently of image production.

## Runtime contract

The OCI closure packages Bash, Bun, CA certificates, Chromium, coreutils, curl,
GCC, Git, GitHub CLI, GNU tar, gzip, jq, Node.js 22, and unzip. These tools are
available directly on `PATH`. The image defines a real `runner` account with
UID/GID 1000, configures it as the default image user, and uses `/workspace`
as its working directory. `/home/runner` and `/workspace` belong to that user;
`/tmp` has mode `1777`. The image supplies `/usr/bin/env` and `/usr/bin/bash`
for mounted CI scripts without adding a distribution layer.
It also provides `/lib64/ld-linux-x86-64.so.2` and the matching glibc library
path for dynamically linked Linux executables installed by consumer
dependencies. The runtime verifier compiles and executes a probe using that
system interpreter, covering dependencies such as Cloudflare's `workerd`.

`pkgs.dockerTools` assembles the Nix closure into `senshac-runner-oci:modular`.
Nix flake evaluation/build and metadata checks run with:

```sh
scripts/check-oci-flake
```

This checks the flake, evaluates stable public package names, builds the OCI
archive and validates the direct-tool, user, and writable-path metadata. It
requires Nix but does not require a container runtime.

## Runtime verification

Load the archive, then run the runtime contract check with rootless Podman:

```sh
OCI_ARCHIVE_OUTPUT=/tmp/senshac-runner-oci.tar.gz scripts/check-oci-flake
podman load --input /tmp/senshac-runner-oci.tar.gz
CONTAINER_RUNTIME=podman scripts/verify-nix-base senshac-runner-oci:modular
CONTAINER_RUNTIME=podman scripts/smoke-ci-runner senshac-runner-oci:modular
```

`verify-nix-base` creates an isolated copy of the committed checkout, binds it
writable at `/workspace`, and uses Podman's `keep-id` mapping to run the image's
UID-1000 `runner` account as the invoking host user. It confirms each required
tool is executable and verifies that the home directory, `/tmp`, and mounted
workspace support writes. The smoke test executes mounted scripts directly
with the packaged Bash, tests failure propagation, exercises GNU tar, Git, and
GitHub CLI, validates Node and Bun TLS access, and launches headless Chromium.

The pull-request verification workflow builds the OCI archive once, verifies
that exact artifact with Docker, then loads and exercises it again under
rootless Podman. Published images are also smoke-tested after pulling the
immutable image reference. Consumer workflows continue to use the published
image digest as the immutable handoff.

## Developer environment boundary

The project `devenv.nix` remains a separate developer shell contract and is
checked by `scripts/check-devenv-lock` and the standard CI workflow. Image
build, verification, and publication do not read or activate that environment.
Changes to developer-only tools therefore do not add packages or activation
behavior to the runner image.
