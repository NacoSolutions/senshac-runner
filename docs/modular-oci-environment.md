# Modular OCI environment

Seed: `senshac-workspace-oci-ci`

The repo-local `flake.nix` is the published runner producer. The committed
`.flox/env/manifest.toml` and lock remain the package contract and are checked
before the Nix build. It is the only Flox source contract for non-base tools.

## Responsibilities

- **Flox** owns the developer environment, package manifest, lockfile, custom
  Senshac tools, and activation contract. Changes to
  `.flox/env/manifest.toml` continue to require the matching lockfile.
- **Nix** owns the reproducible published closure in `flake.nix`, including
  Bun, Chromium and its runtime libraries, and the `dockerTools` OCI artifact.
  It has no Dockerfile, `FROM` image, apt-get step, or base distribution layer.

The selected closure is intentionally limited to the current CI boundary:
Bash, core utilities, curl, findutils, GNU grep/tar/gzip, unzip, jq, git, gh,
Bun, Node.js, and CA certificates. The image also contains the tiny
`flox-bootstrap` and `senshac-runtime` profile scripts, but not the Flox
binary or the legacy environment. Developer-only tools (Act, formatters,
linters, Seeds/Mulch/Trellis, Cloudflare tooling, and interactive utilities)
stay in Flox and are not copied into this image.

## Evaluate and inspect

With Nix flakes enabled, run the commands with the `nix-command` feature
explicitly enabled (this also works when it is not enabled in global Nix
configuration):

```bash
nix --extra-experimental-features 'nix-command flakes' flake check --no-write-lock-file
nix --extra-experimental-features 'nix-command flakes' build --no-write-lock-file .#ciTools
nix --extra-experimental-features 'nix-command flakes' build --no-write-lock-file .#ociImage
```

The public `ociImage` output is a Docker-compatible archive suitable for
`podman load` or `docker load`; it is assembled directly by
`pkgs.dockerTools.buildLayeredImage`. Its evaluated derivation name is
`senshac-runner-oci.tar.gz`, the Docker-compatible archive produced by that
builder. The public output attribute remains `ociImage` for compatibility (it
is not `dockerArchive` or `oci-img`). Validate the selected closure, build both
outputs, and check their deterministic metadata with:

```bash
scripts/check-oci-flake
```

This check evaluates both exported packages and builds the
`oci-closure-metadata` check. It requires Nix, but does not require a daemon,
registry credentials, or a container runtime.

## Runtime profiles

The image defaults to `SENSHAC_RUNTIME_PROFILE=minimal`. This profile forwards
the command without invoking Flox, a resolver, or a package manager, so
minimal CI has no silent network dependency. The verification contract is
`scripts/verify-nix-base IMAGE`.

Use the optional runtime overlay when a project needs its Flox environment:
mount the checkout (including `.flox/env/manifest.lock`), provide a pinned Flox
binary on `PATH`, and set `SENSHAC_RUNTIME_PROFILE=flox` plus `FLOX_PROJECT`.
The entrypoint validates the lockfile and runs `flox activate`; it does not
install Flox or mutate the lock. Prefer a pre-warmed Flox/Nix cache in CI and
fail cache misses explicitly in the job that prepares the environment. This
keeps the base image immutable and avoids rebuilding it for each repository.

Example:

```sh
docker run --rm -e SENSHAC_RUNTIME_PROFILE=flox -e FLOX_PROJECT=/workspace \\
  -v "$PWD:/workspace" -v "$HOME/.local/bin/flox:/usr/local/bin/flox:ro" \\
  senshac-runner-oci:modular bash -lc 'command -v bun'
```

## Caches and migration boundary

Nix may use the configured binary cache for `nixpkgs` and substitutes. A cache
miss realizes the selected closure locally; the image remains deterministic
for the pinned flake input and system. No registry cache or Docker base image
is assumed. The existing Flox lockfile and cache behavior are independent.

## Canary status and limitations

The `verify-ci-runner` pull-request workflow has one producer job that builds
all three image variants once and uploads their Docker-compatible archives.
Its dependent verification job downloads and loads those exact archives,
including `ociImage` as `senshac-runner-oci:modular`, then runs the existing
Flox and Nix smoke contracts. The Nix image uses a small argument-forwarding
shell entrypoint so the smoke script exercises the image itself and failures
propagate. A failing smoke check fails verification without relying on a
container daemon shared between jobs.

The Nix OCI archive is now the publication producer. The selected closure
intentionally does not include Flox-only Seeds, Mulch, Terrarium, Trellis, or
other interactive developer tooling; those remain available through the
explicit mounted Flox activation contract.

## CI size measurements

The `verify-ci-runner` workflow builds one archive and appends its archive and
loaded-runtime measurements to the GitHub Actions step summary. Both values
come from the same `pkgs.dockerTools` derivation; they are different
representations and are not interchangeable.

Cache and network assumptions are part of the report. Nix may substitute from
its configured binary cache or build on a cache miss. The minimal profile has
no package-manager or network bootstrap, while smoke-test TLS probes need
network access. Measurement failures fail the producer job.
