# Bounded Warren Task

Use this skill for focused autonomous changes.

## Contract
- Work only on the named objective and explicitly named files.
- Inspect the smallest relevant surface before editing.
- Follow repository-local instructions and use Seeds/Mulch/Canopy when present.
- Use positive, specific instructions and state the desired outcome.
- Do not perform destructive exploratory tests or remove files outside the objective.
- Run one relevant, bounded quality gate after editing. Avoid repeating a gate unless the previous result is actionable.
- Commit the completed change; do not push directly. Warren delivers the branch and PR.
- After a clean commit and bounded verification, stop and report the commit, checks, and any blocker.
- Respect the task cost/time cap; escalate rather than loop.

## Completion report
State files changed, commit, gate command/result, and remaining follow-up.
