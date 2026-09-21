# Bounded Warren Task

Use this skill for focused autonomous changes and apply the shared
[Senshac Agent Principles](../senshac-agent-principles/SKILL.md).

## Contract
- Work on the named objective and explicitly named files.
- Inspect the smallest relevant surface before editing.
- Follow repository-local instructions and use Seeds, Mulch, Canopy, and project tools when present.
- Use positive, specific instructions and state the desired outcome.
- Keep edits within the stated objective and preserve adjacent behavior.
- Run one relevant, bounded quality gate after editing and repair any reported failure.
- Commit the completed change; Warren delivers the branch and pull request.
- After a clean commit and bounded verification, stop and report the commit, checks, and follow-up.
- Complete the task within its cost/time cap and report a blocker when the acceptance check cannot pass.

## Acceptance checks
- Confirm the changed files match the named objective with `git diff --check` and `git status --short`.
- Run the repository command documented for the objective and confirm it exits zero.
- Confirm the completed change is committed with `git status --short` and `git log -1 --oneline`.

## Completion report
State files changed, commit, gate command/result, and remaining follow-up.
