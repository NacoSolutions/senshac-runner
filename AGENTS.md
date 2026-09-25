# Senshac Runner

This is the focused CI and local-runner repository. It owns devenv
containerization, rootless Podman/Act execution, and runner image publishing.
It does not own the Astro application, Tina content, or media processing.

The live web repository remains the checkout supplied to the runner. Validate
runner changes against a clean web checkout before changing image tags or
workflow ownership. This repository also owns Bun-based tooling used by the
container images and CI runner builds.

## Agent guidance

Apply [Senshac Agent Principles](.agents/skills/senshac-agent-principles/SKILL.md)
to every focused change. The principles are direct execution, instruction
specificity, positive phrasing, defense in depth, gentle coding, and token
economy.

Use [Bounded Warren Task](.agents/skills/bounded-warren-task/SKILL.md) for
focused autonomous changes. Apply positive phrasing, specific instructions,
defense in depth, gentle coding, direct execution, and token economy. Inspect
the smallest relevant surface, preserve adjacent behavior, and keep edits
limited to the named objective and files. Use repository tools and local
conventions, run a focused quality gate, and commit the completed change;
Warren delivers the branch and pull request.

Use these focused role skills for their corresponding work:

- [Git Workflow](.agents/skills/git-workflow/SKILL.md) for scoped diffs, commits,
  and delivery checks.
- [Managing Environments](.agents/skills/managing-environments/SKILL.md) for
  devenv, rootless Podman, Act, and producer/consumer validation.
- [Dependency Hygiene](.agents/skills/dependency-hygiene/SKILL.md) for devenv
  manifest, lock, and runner dependency checks.
- [Verification Before Completion](.agents/skills/verification-before-completion/SKILL.md)
  for bounded documentation/configuration validation and final acceptance.

## Seeds and Mulch

This repository uses the pinned devenv tools `sd` (Seeds) and `ml` (Mulch).

- Run `sd prime` at session start or after context compaction; use `sd ready`
  to find unblocked work. Track work with Seeds rather than ad hoc task files.
- Run `ml prime` at session start to load relevant project expertise. Before
  finishing a task, use `ml record` for durable conventions, decisions, or
  failures that future agents should know.
- Keep `.seeds/`, `.mulch/`, and their merge-union entries in `.gitattributes`
  under version control. Run the commands through the project devenv environment
  (`devenv sd ...` / `devenv ml ...`) when the host does not provide them directly.
- On a fresh checkout, bootstrap with `sd init` and `ml init`, then create or
  claim work with `sd create`/`sd update`; validate both stores with `sd doctor`
  and `ml validate` before committing tracker changes.
- Runner-image work must preserve the producer/consumer boundary: this repo
  produces the image, while the web checkout consumes an immutable image digest.

## Portable rules and CLI skills

Load `.agents/rules/` for Caveman ultra, direct execution, positive phrasing,
defense in depth, gentle coding, token economy, and llm-shorthand. Load
`instruction-specificity.md` when authoring agent guidance. Use the local
`seeds-cli`, `mulch-cli`, `warren-operations`, and
`verification-before-completion` skills for tracker, expertise, Warren, and
completion work. Load role-specific skills for the implementation surface.
