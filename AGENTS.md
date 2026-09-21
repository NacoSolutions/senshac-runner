# Senshac Runner

This repository's role is Bun tooling, container images, and CI runner builds. It is the focused CI and local-runner repository. It owns Flox
containerization, rootless Podman/Act execution, and runner image publishing.
It does not own the Astro application, Tina content, or media processing.

The live web repository remains the checkout supplied to the runner. Validate
runner changes against a clean web checkout before changing image tags or
workflow ownership.

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

## Bounded Warren work

Use [the Bounded Warren Task skill](.agents/skills/bounded-warren-task/SKILL.md) for focused changes. State the desired outcome with positive, specific instructions; use defense in depth through repository guidance and a bounded quality gate; make gentle, direct edits that preserve adjacent behavior; and spend tokens economically by inspecting only the smallest relevant surface. Keep work within the named objective and files, then commit and report the files, checks, commit, and follow-up.
