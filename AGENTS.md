# Senshac Runner

This is the focused CI and local-runner repository. It owns Flox
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

## Seeds and Mulch

This repository uses the pinned Flox tools `sd` (Seeds) and `ml` (Mulch).

- Run `sd prime` at session start or after context compaction; use `sd ready`
  to find unblocked work. Track work with Seeds rather than ad hoc task files.
- Run `ml prime` at session start to load relevant project expertise. Before
  finishing a task, use `ml record` for durable conventions, decisions, or
  failures that future agents should know.
- Keep `.seeds/`, `.mulch/`, and their merge-union entries in `.gitattributes`
  under version control. Run the commands through the project Flox environment
  (`fx sd ...` / `fx ml ...`) when the host does not provide them directly.
- On a fresh checkout, bootstrap with `sd init` and `ml init`, then create or
  claim work with `sd create`/`sd update`; validate both stores with `sd doctor`
  and `ml validate` before committing tracker changes.
- Runner-image work must preserve the producer/consumer boundary: this repo
  produces the image, while the web checkout consumes an immutable image digest.
