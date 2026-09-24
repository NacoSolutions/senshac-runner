# Modular OCI environment

Seed: `senshac-workspace-oci-ci`

The repo-local `flake.nix` is the published runner producer. The committed
`.flox/env/manifest.toml` and lock remain the package contract and are checked
before the Nix build. It is the only Flox source contract for non-base tools.

## Responsibilities

- **Flox** owns the developer environment, package manifest, lockfile, custom
  Senshac tools, and activation contract. Changes to
  `.flox/env/manifest.toml` continue to require the matching lockfile.
- **Nix** owns the reproducible published base closure in `flake.nix`, including
  the pinned Flox CLI/runtime package and the `dockerTools` OCI artifact. Bun,
  Chromium, and every other project tool remain owned by the mounted Flox
  manifest/lock. It has no Dockerfile, `FROM` image, apt-get step, or base
  distribution layer.

The image closure contains only the base shell/runtime, the pinned Flox
CLI/runtime, CA certificates, and the activation wrapper. Bun, Chromium,
Node.js, GNU tar, and every other project tool are resolved by the mounted
project's committed `.flox/env/manifest.lock`; no hand-maintained tool list is
duplicated in the flake. The image build never evaluates the developer-only
custom Flox inputs (Canopy, Cloudflare CLI, Knip, Mulch, Seeds, Terrarium, or
Trellis), so their Cargo/Rust closures do not become OCI build inputs. Runtime
activation still uses the complete project lock and preserves the existing CI
tool checks.

## Evaluate and inspect

With Nix flakes enabled, run the commands with the `nix-command` feature
explicitly enabled (this also works when it is not enabled in global Nix
configuration):

```bash
nix --accept-flake-config --extra-experimental-features 'nix-command flakes' flake check --no-write-lock-file
nix --accept-flake-config --extra-experimental-features 'nix-command flakes' build --no-write-lock-file .#ociImage
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
packages or mutates the lock. Because `dockerTools` supplies no distribution
base, the image explicitly provides `/usr/bin/env` and `/usr/bin/bash`, which
are required by Flox's activation interpreter contract. The
`scripts/verify-nix-base IMAGE` check validates both paths before mounting this
repository and verifying `flox activate --
command -v bun`, `flox activate -- command -v chromium`, and a headless
Chromium launch. Prefer a pre-warmed Flox/Nix cache in CI; the image itself
remains minimal and immutable.

Example:

```sh
docker run --rm -e FLOX_PROJECT=/workspace \\
  -v "$PWD:/workspace:ro" senshac-runner-oci:modular \\
  flox activate -- command -v bun
```

## Official Flox cache and Cargo measurement

The flake pins the released Flox flake and declares Flox's official
`cache.flox.dev` substituter and public key through `nixConfig`. The validation
scripts pass `--accept-flake-config`, which is required on generic Nix hosts;
this prevents the Flox CLI and patched Nix Rust closure from being built from
source when the flake configuration would otherwise be ignored.

To inspect the exact producer closure and identify an unexpected Rust input, run
these commands after `nix flake check`:

```bash
nix --accept-flake-config --extra-experimental-features 'nix-command flakes' \
  path-info --recursive --closure-size .#ociImage
nix --accept-flake-config --extra-experimental-features 'nix-command flakes' \
  why-depends .#ociImage '<rust-or-cargo-store-path>'
```

The expected closure contains the pinned Flox runtime but no project package
paths. Custom Flox inputs remain in the committed project lock for developer
activation; they are not dependencies of `ociImage`, so dev-only Cargo work is
not resolved while producing the CI image. A cache miss realizes only the
selected immutable closure locally; no registry cache or Docker base image is
assumed.

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
