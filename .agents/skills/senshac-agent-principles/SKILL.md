# Senshac Agent Principles

Use these principles for every focused change in this repository:

- **Direct execution:** inspect the smallest relevant surface, make the requested edit, and run the relevant check rather than narrating an unperformed plan.
- **Instruction specificity:** name the files, commands, expected result, and stopping point; follow repository guidance before general preferences.
- **Positive phrasing:** state the desired behavior as an affirmative instruction (for example, “keep the lock complete”) and pair it with a concrete acceptance check.
- **Defense in depth:** validate at the source, script, and integration boundaries; fail clearly instead of allowing a swallowed or partial success.
- **Gentle coding:** preserve adjacent behavior, tracker state, configs, and production paths; make the smallest reversible change that satisfies the objective.
- **Token economy:** read only relevant files, reuse existing commands, avoid speculative refactors, and stop after the bounded gate is green.

## Acceptance check

Confirm the requested files are the only intended changes with `git diff --check` and
`git status --short`, then run the repository quality gate from `.warren/config.yaml`
or the focused check documented by the task.
