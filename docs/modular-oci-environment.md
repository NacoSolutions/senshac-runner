# Modular OCI environment

Seed: `senshac-workspace-oci-ci`

This is the first, additive step toward a modular runner environment. The
existing `.flox/env/manifest.toml` remains the published runner contract. The
repo-local `flake.nix` provides a separately testable Nix closure and does not
replace Flox containerization yet.

## Responsibilities

- **Flox** owns the developer environment, its lockfile, custom Senshac tools,
  activation hook, and the existing `flox containerize` CI image. Changes to
  `.flox/env/manifest.toml` continue to require the matching lockfile and the
  existing runner smoke test.
- **Nix** owns the small, reproducible migration surface in `flake.nix`:
  `packages.x86_64-linux.ciTools` and the `dockerTools` OCI artifact. It has no
  Dockerfile, `FROM` image, or base distribution layer.

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

The `verify-ci-runner` pull-request workflow now loads the built
`ociImage` archive as `senshac-runner-oci:modular` and runs the existing
`scripts/smoke-ci-runner` contract against it. The Nix image uses a small
argument-forwarding shell entrypoint so the smoke script exercises the image
itself and failures propagate. A failing Nix smoke check fails verification;
the existing Flox build and smoke steps remain unchanged.

This is a canary only. The publish workflow still produces the Flox image, and
no consumer workflow is switched to Nix. The selected Nix closure intentionally
does not include Flox-only Seeds, Mulch, Terrarium, Trellis, or other
interactive developer tooling, so this canary does not establish replacement
parity for those tools. A later migration must decide whether to expand the
closure or narrow the consumer contract before changing publication ownership.

## CI size measurements

The `verify-ci-runner` workflow builds both artifacts and appends a measurement
table to the GitHub Actions step summary. The first workflow run containing this
change is the first measured result; the summary records its actual byte values
rather than a value copied from a local or unrelated build.

The table reports:

- **Flox compressed image:** the byte count of `runtime save` piped through
  `gzip`, representing a transport-like compressed image stream.
- **Flox runtime image size:** the `Size` value returned by the container
  runtime's `image inspect`, representing the engine's unpacked/virtual image
  size.
- **Nix base:** the byte count of the `ociImage` archive on disk, measured
  with `wc -c`.
- **Nix base + Flox environment:** the runtime-mounted overlay contribution.
  It is measured separately and does not copy the legacy environment into the
  Nix image.
- **Current full Flox baseline:** the compressed `runtime save` stream of the
  existing published-style image.
- **Loaded Nix runtime image size (optional):** the runtime's `image inspect`
  `Size` after loading the archive, when the selected runtime supports load.

The archive and runtime values describe different representations and are not
expected to have a fixed ratio. Measurement availability does not turn a CI
failure into a pass: build and smoke failures still fail the job, while an
unsupported optional inspect/load operation is reported as `unavailable`.
