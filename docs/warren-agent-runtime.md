# Warren agent runtime plan

## Production evaluation

Flox/Nix is valuable for repository quality gates and the published CI runner,
but it is not required in the Warren agent image. Production needs reproducible
builds, Cloudflare tooling, Bun dependencies, and media tooling; these belong
to CI and the media runner. Warren primarily needs to inspect repositories,
edit files, run lightweight checks, update Seeds, and prepare pull requests.

## Runtime split

```text
Warren agent image
  Pi + Git + GitHub CLI + Bun + lightweight project CLIs
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
- Bun/Node runtime
- `jq`, `yq`, and POSIX shell utilities
- Seeds, Mulch, Canopy, Terrarium, and Jayminwest Trellis
- Warren repository/run helper scripts

## Gate policy

- Lightweight formatting, metadata, Seeds integrity, and static checks may run
  directly in Warren.
- Flox/Nix-dependent build, Cloudflare, browser, and production smoke gates
  run in `senshac-runner` or GitHub Actions.
- Warren may open a PR only after authoritative runner/CI gates pass.
- `senshac-web` remains blocked from production cutover until it has protected
  branches, CI, Pages preview, and smoke-test contracts.

Maintain one minimal Warren agent image and the existing full CI runner image.
Do not merge them unless measured evidence shows the boundary harms reliability.
