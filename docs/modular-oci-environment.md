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

The image closure contains only the base shell/runtime, Flox CLI, CA
certificates, and the activation wrapper. Bun, Chromium, Node.js, GNU tar,
and every other project tool are resolved by the mounted project's committed
`.flox/env/manifest.lock`; no hand-maintained tool list is duplicated in the
flake.

## Evaluate and inspect

With Nix flakes enabled, run the commands with the `nix-command` feature
explicitly enabled (this also works when it is not enabled in global Nix
configuration):

```bash
nix --extra-experimental-features 'nix-command flakes' flake check --no-write-lock-file
nix --extra-experimental-features 'nix-command flakes' build --no-write-lock-file .#ociImage
```

The public `ociImage` output is a Docker-compatible archive suitable for
`podman load` or `docker load`; it is assembled directly by
`pkgs.dockerTools.buildLayeredImage`. Its evaluated derivation name is
`senshac-runner-oci.tar.gz`, the Docker-compatible archive produced by that
builder. The public output attribute remains `ociImage` for compatibility (it
is not `dockerArchive` or `oci-img`). Validate the base runtime and image output, and check their deterministic
metadata with:

```bash
scripts/check-oci-flake
```

This check evaluates the base runtime and image outputs and builds the
`oci-closure-metadata` check. It requires Nix, but does not require a daemon,
registry credentials, or a container runtime.

## Mounted-project activation

The entrypoint contains the Flox CLI and always activates the mounted project.
It requires `.flox/env/manifest.lock`, runs `flox activate`, and never installs
packages or mutates the lock. `scripts/verify-nix-base IMAGE` mounts this
repository and verifies `flox activate -- command -v bun`, `flox activate --
command -v chromium`, and a headless Chromium launch. Prefer a pre-warmed
Flox/Nix cache in CI; the image itself remains minimal and immutable.

Example:

```sh
docker run --rm -e FLOX_PROJECT=/workspace \\
  -v "$PWD:/workspace:ro" senshac-runner-oci:modular \\
  flox activate -- command -v bun
```

## Caches and migration boundary

Nix may use the configured binary cache for `nixpkgs` and substitutes. A cache
miss realizes the selected closure locally; the image remains deterministic
for the pinned flake input and system. No registry cache or Docker base image
is assumed. The existing Flox lockfile and cache behavior are independent.

## Canary status and limitations

The `verify-ci-runner` pull-request workflow has one producer job that builds
the single Docker-compatible image archive once and uploads it.
Its dependent verification job downloads and loads those exact archives,
including `ociImage` as `senshac-runner-oci:modular`, then runs the existing
Flox and Nix smoke contracts. The image uses an activation wrapper so the smoke script exercises the
mounted project's lock and failures propagate. A failing smoke check fails verification without relying on a
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
its configured binary cache or build on a cache miss. Flox activation uses the
mounted project's lock, while smoke-test TLS probes need
network access. Measurement failures fail the producer job.
