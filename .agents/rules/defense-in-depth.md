# Defense in Depth (Rules → Skills → Enforcement)

Written rules **do not enforce**. Agents violate `CLAUDE.md` directives when violation is convenient, then apologize and repeat the violation in the next session. Reliability comes from layered scaffolding where each layer catches what the previous layer missed.

## The three layers

| Layer | Purpose | Bypassable? | Examples |
|-------|---------|-------------|----------|
| **Rules** (training) | Shape default behavior; teach the *why* | Yes — agent can ignore | `AGENTS.md`, `CLAUDE.md`, rule files |
| **Skills / slash commands** (easy path) | Make the right action one keystroke | Yes — agent can avoid | `/pr`, `/release`, project skills, scripts that bundle preflight |
| **Hooks / CI** (enforcement) | Block the wrong action mechanically | No — exits non-zero | Pre-commit hook, pre-push hook, `PreToolUse` hook, branch protection, CI required-check |

## Rule

For any behavior that **must** hold, place enforcement at the lowest reachable layer. Use the higher layers to communicate intent and reduce friction; do not rely on them for guarantees.

## Apply to

Anything destructive, irreversible, or compliance-bearing:

- Pushing to `main` / `production` → pre-push hook + branch protection.
- Running `DROP` / `TRUNCATE` / `DELETE` without `WHERE` → hook on the SQL runner, not just a rule.
- Skipping tests/lint before merge → CI required check, not "always run tests" in the rule file.
- Committing secrets → pre-commit hook (`gitleaks`, `trufflehog`) + server-side push protection.
- Running with the wrong Node/Python/toolchain version → `SessionStart` hook that fails fast.

## Layer-selection heuristic

1. Can a hook detect this in O(ms) before the action runs? → **Hook.**
2. Can a slash command bundle the safe sequence so the safe path is shorter than the unsafe one? → **Skill.**
3. Is this guidance, taste, or convention with no clear failure signal? → **Rule.**

If you find yourself re-explaining the same rule across sessions, you have rule-shaped a skill-shaped or hook-shaped problem.

## Build order

Build layers in the order you need them — the first time something gets past a layer, build the next one inward. Do not pre-build all three for hypothetical risks.

## Anti-patterns

- "We have a rule against it" — rules are training, not walls.
- A skill that wraps the safe path but no hook for when the agent skips the skill.
- A pre-push hook with `--no-verify` allowed — pair it with a `PreToolUse` hook that blocks the bypass flag.
- CI checks that run but are not marked required in branch protection — a non-required check is documentation.

## Cross-references

- Verification gate: <~/.llm/skills/verification-before-completion/SKILL.md>
- Hook configuration in Claude Code: see `update-config` skill.
- Multi-layer review chain: <~/.llm/skills/finishing-a-development-branch/SKILL.md>.
