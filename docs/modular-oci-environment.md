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

The workflow reports two separate tables: archive bytes and loaded runtime
bytes. Each table includes the four requested variants: Nix base/minimal,
Nix base with the runtime-mounted Flox overlay, a minimal Flox environment
when a separately built manifest exists, and the legacy/full Flox image. Each
row includes a ratio to the Nix base in that table. The current repository has
no separate minimal Flox manifest, so that row is explicitly `unavailable`
rather than being inferred from the full environment.

The Nix archive is measured with `wc -c`; the Flox archive is a gzip-compressed
`runtime save` stream. Loaded runtime size is the container runtime's
`image inspect` `Size` after loading/creating the image. These are different
representations and are not interchangeable. The runtime-mounted overlay rows
intentionally report the Nix image bytes: the overlay is outside the image and
its checkout, Flox store, and cache footprint are not included. A separately
built overlay archive can be passed as the optional third argument to the
report script.

Cache and network assumptions are part of the report. Nix may substitute from
its configured binary cache or build on a cache miss; Flox containerize may
use its configured package cache. The minimal profile has no package-manager
or network bootstrap, while the Flox overlay needs a pinned lock and supplied
Flox binary. The smoke test's GitHub/TLS probes need network access. No
registry pull is needed for the Nix archive measurement, and the full Flox
baseline is the locally built locked image. Measurement availability does not
turn a CI failure into a pass: build and smoke failures still fail the job,
while unsupported optional inspect/load operations remain `unavailable`.
