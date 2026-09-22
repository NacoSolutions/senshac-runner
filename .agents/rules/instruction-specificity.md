# Instruction Specificity

Instructions that **name** a specific tool, file, command, flag, function, or config key are followed roughly 10.9× more often than instructions that describe the same thing at the category level (Cleverhoods, N=1000, p<10⁻³⁰; replicated across the 28,721-repo Reporails corpus, 2026).

## Rule

Every behavioral instruction must reference a **named construct** — exact tool, command, file path, flag, symbol, or config key. Replace category language with the thing itself.

## Apply to

- AGENTS.md / CLAUDE.md and rule files
- SKILL.md bodies
- Plan steps and acceptance criteria
- Sub-agent definitions (worst offenders: 17% specificity in the corpus)

## Transform examples

| Abstract (less effective) | Specific (more effective) |
|---|---|
| "Use consistent code formatting" | "Format with `ruff format` before committing" |
| "Avoid mocks in tests" | "Use the real DB via `test_db` fixture; do not import `unittest.mock`" |
| "Lint the code" | "Run `pnpm lint --fix` and fix every warning" |
| "Use proper error handling" | "Wrap fallible calls in `Result<T, E>`; return errors with `?`, never `unwrap()`" |
| "Follow good naming" | "Functions: `verb_noun`. Booleans: `is_*`/`has_*`. Constants: `SCREAMING_SNAKE`." |
| "Run the tests" | "`cargo test --workspace --all-features`" |

## Self-check

Before shipping a rule or skill, scan each directive line and ask:

1. Does it name an exact tool, file, command, or symbol? If not, add one.
2. Could a reader follow it without guessing? If not, it is still abstract.
3. Is the construct still real in this repo? Memory and templates rot; verify with `ctx_search` before keeping.

## Background

In the median instruction file (50 atoms total), only **12 atoms are actual directives** — the other 73% is structural scaffolding (headings, prose, examples). Of those 12 directives, ~67% stay abstract. So a typical 200-line CLAUDE.md exerts behavioral force through roughly **4 specific instructions**. Specificity is the lever that survives compression.

## Anti-patterns

- Persona prompts ("You are a senior reviewer who cares about quality") with no named tools or commands.
- Sub-agent files that describe a role instead of naming the actions.
- Copy-pasted "best practices" lists ("be DRY", "write clean code") that name nothing.
- Hedged directives ("consider using X when appropriate") — pick a default and name it.
