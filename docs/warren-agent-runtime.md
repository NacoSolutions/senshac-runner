# Warren agent runtime plan

## Production evaluation

devenv/Nix is valuable for repository quality gates and the published CI runner,
but it is not required in the Warren agent image. Production needs reproducible
builds, Cloudflare tooling, Bun dependencies, and media tooling; these belong
to CI and the media runner. The agent image uses Node 24 because Pi currently
exercises Node/Web API compatibility that Bun 1.3.13 does not fully provide.
Warren primarily needs to inspect repositories, edit files, run lightweight checks,
update Seeds, and prepare pull requests.

## Post-rotation smoke-test finding

After credential rotation, read-only Git remote access worked, while GitHub CLI authentication was unavailable in the agent sandbox. This observation alone does not establish that GitHub App authentication is broken.

## Runtime split

```text
Warren agent image
  Pi + Node 24 + Git + GitHub CLI + lightweight project CLIs
          |
          v
senshac-runner / GitHub CI
  devenv/Nix + full quality gates + Cloudflare build compatibility
```

The Warren image should not install devenv, Nix, Plot, or Claude. Warren may
invoke a sibling runner or defer heavyweight validation to GitHub Actions.

## Required Warren image tools

- Pi
- Git and GitHub CLI
- Node 24 runtime for Pi; Bun remains the Senshac repository/tooling runtime
- `jq`, `yq`, and POSIX shell utilities
- Seeds (`sd`), Mulch (`ml`), Terrarium (`tr`/`terrarium`), and Jayminwest Trellis

The image pins Seeds 0.5.15, Mulch 0.10.7, Trellis CLI 1.0.1, and Bun
1.3.13 for these Bun-based CLIs. Terrarium is installed from the
`RogerNavelsaker/terrarium` source tarball at commit
`afeec9cc0b7e6e7f4315647e4556afe42e140897`, with its SHA-256 verified during
the image build; it is not fetched from npm because `@os-eco/terrarium-cli` is
not published there. The source and production dependencies are retained under
`/opt/terrarium`, and explicit Bun wrappers at `/usr/local/bin/tr` and
`/usr/local/bin/terrarium` ensure the Terrarium `tr` takes precedence over
coreutils. Keep the real Node 24 runtime for Pi unchanged.
- Warren repository/run helper scripts

## Gate policy

- Lightweight formatting, metadata, Seeds integrity, and static checks may run
  directly in Warren. The image build smoke-tests `tr --help`,
  `terrarium --help`, `sd --version`, `ml --version`, and `trellis --help`.
- devenv/Nix-dependent build, Cloudflare, browser, and production smoke gates
  run in `senshac-runner` or GitHub Actions.
- Warren may open a PR only after authoritative runner/CI gates pass.
- `senshac-web` remains blocked from production cutover until it has protected
  branches, CI, Pages preview, and smoke-test contracts.

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
