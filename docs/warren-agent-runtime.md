# Warren agent runtime plan

## Production evaluation

Flox/Nix is valuable for repository quality gates and the published CI runner,
but it is not required in the Warren agent image. Production needs reproducible
builds, Cloudflare tooling, Bun dependencies, and media tooling; these belong
to CI and the media runner. The agent image uses Node 24 because Pi currently
exercises Node/Web API compatibility that Bun 1.3.13 does not fully provide.
Warren primarily needs to inspect repositories, edit files, run lightweight checks,
update Seeds, and prepare pull requests.

## Runtime split

```text
Warren agent image
  Pi + Node 24 + Git + GitHub CLI + lightweight project CLIs
          |
          v
senshac-runner / GitHub CI
  Flox/Nix + full quality gates + Cloudflare build compatibility
```

The Warren image should not install Flox, Nix, Plot, or Claude. Warren may
invoke a sibling runner or defer heavyweight validation to GitHub Actions.

## Required Warren image tools

- Pi
- Git and GitHub CLI
- Node 24 runtime for Pi; Bun remains the Senshac repository/tooling runtime
- `jq`, `yq`, and POSIX shell utilities
- Seeds CLI `sd` 0.5.12
- Mulch CLI `ml` 0.10.7
- Jayminwest Trellis at commit `fd3bbadf1fa92c3b15e72836689b30094f4f534a`
- Bun 1.3.13 (the pinned runtime for Trellis; Node 24 remains the Pi runtime)
- Warren repository/run helper scripts

## Gate policy

- Lightweight formatting, metadata, Seeds integrity, and static checks may run
  directly in Warren.
- Flox/Nix-dependent build, Cloudflare, browser, and production smoke gates
  run in `senshac-runner` or GitHub Actions.
- Warren may open a PR only after authoritative runner/CI gates pass.
- `senshac-web` remains blocked from production cutover until it has protected
  branches, CI, Pages preview, and smoke-test contracts.

The image build runs `sd --version`, `ml --version`, and `trellis --help` as
smoke checks. The publish workflow repeats those checks on the built image,
alongside Node, Pi, GitHub CLI, Git, and jq checks. Trellis is cloned from the
same pinned commit used by `.github/workflows/trellis-readiness.yml` and its
frozen Bun lockfile is installed during the image build.

Maintain one minimal Warren agent image and the existing full CI runner image.
Do not merge them unless measured evidence shows the boundary harms reliability.

## Bun compatibility boundary

Bun remains preferred for Senshac repository tooling and application builds. Do
not replace Node with a `node -> bun` symlink in the Warren image: Pi 0.85.1
failed under Bun 1.3.13 with `webidl.util.markAsUncloneable is not a function`.
Application-owned Bun services may use a narrowly scoped preload shim when a
dependency requires it, but the Warren agent runtime must use a real Node 24
binary until Pi passes the same production smoke tests under Bun.

When evaluating Bun for an application, test the bundled production path rather
than only development startup:

```sh
bun install --frozen-lockfile
bun run build
bun run start
```
