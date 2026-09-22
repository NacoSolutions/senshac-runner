# Positive Phrasing (Pink-Elephant Rule)

LLMs (and humans) attend to the noun in a negation. "Don't think of a pink elephant" plants the elephant. Negative instructions raise the probability of the forbidden behavior because the model conditions on the named token.

## Rule

Phrase instructions, prompts, and skill bodies as **what to do**, not what to avoid. When an anti-pattern must be named, pair it immediately with the positive replacement.

## Apply to

- System prompts and skill bodies
- Plan steps and acceptance criteria
- Code review feedback
- Commit messages and PR descriptions
- User-facing error messages

## Transform examples

| Avoid (negative-leading) | Prefer (positive-leading) |
|---|---|
| "Don't use `var`" | "Use `let` or `const`" |
| "Never commit secrets" | "Load secrets from `.env` / secret store" |
| "Don't break the API" | "Preserve the existing public signature" |
| "Avoid N+1 queries" | "Batch queries with `IN (...)` or a join" |
| "Don't be vague" | "Cite file:line for each claim" |

## When negation is unavoidable

If the rule must forbid something (security, irreversible action), the positive replacement must appear **in the same sentence**, after the negation. The model conditions most strongly on the trailing tokens, so end with the action you want, not the action you forbid.

> ✗ "Never force-push to `main`."
> ✓ "Do not force-push to `main`; open a PR with `gh pr create` and request review."

> ✗ "Avoid using mocks in tests."
> ✓ "Do not import `unittest.mock`; use the real DB via the `test_db` fixture."

A bare prohibition without an in-sentence replacement amplifies the forbidden behavior — see <~/.llm/rules/instruction-specificity.md> for the related finding that named constructs win 10.9× more often.

## Self-check

Before shipping a prompt or instruction, scan for "don't / never / avoid / no" at sentence start. For each, ask: *what should be done instead?* If you cannot answer, the rule is incomplete.
