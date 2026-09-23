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
Bun, Node.js, and CA certificates. Developer-only tools (Act, formatters,
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

## Caches and migration boundary

Nix may use the configured binary cache for `nixpkgs` and substitutes. A cache
miss realizes the selected closure locally; the image remains deterministic
for the pinned flake input and system. No registry cache or Docker base image
is assumed. The existing Flox lockfile and cache behavior are independent.

The current CI workflows continue to build and smoke-test the Flox image.
Adopting `ociImage` as the published runner requires a later compatibility
migration because the current smoke contract also exercises Flox-provided
Seeds, Mulch, Terrarium, and Trellis commands.

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
- **Nix archive size:** the byte count of the `ociImage` archive on disk,
  measured with `wc -c`.
- **Loaded Nix runtime image size (optional):** the runtime's `image inspect`
  `Size` after loading the archive, when the selected runtime supports load.

The archive and runtime values describe different representations and are not
expected to have a fixed ratio. Measurement availability does not turn a CI
failure into a pass: build and smoke failures still fail the job, while an
unsupported optional inspect/load operation is reported as `unavailable`.
