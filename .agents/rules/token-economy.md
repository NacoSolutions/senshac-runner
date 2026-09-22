# Token Economy

Token usage is driven by what the model **re-reads on every turn**, not by how many turns there are. Long threads, pasted files, and incremental follow-ups multiply cost silently because every turn re-processes the entire conversation prefix.

## Rule

Optimize for the smallest correct context per turn. The cheapest token is the one not in the prompt.

## Session hygiene

- **One task, one session.** Start a fresh session when the topic changes. Use `/clear` mid-session when the previous context is no longer load-bearing.
- **Mixing unrelated problems is the most expensive habit** — every later turn reprocesses the earlier unrelated context.
- **Dense handoffs (~400 tokens max).** Resume long-running work from a compact written artifact (plan, summary, diff) rather than replaying prior session context.
- **LITM (Lost-In-The-Middle) awareness.** Keep critical constraints, active blockers, and anchors at prompt boundaries (head/tail), where model attention is sharpest. Avoid burying core invariants mid-document.

## Prompt shape

- **Write one complete prompt** with all requirements, then iterate by editing it. A chain of "also fix this", "also change that" forces full re-reads.
- **Batch related asks** in a single turn: "fix the bug, refactor the helper, add tests" beats three separate turns.
- **Trim pasted context.** Share the relevant snippet, not the entire file. Reference paths the agent can `ctx_read` on demand.
- **Avoid correction loops.** When a thread has gone three rounds without converging, restart with a clean prompt that states the final requirements.

## Model right-sizing

- **Haiku-class** for formatting, simple edits, summaries, lookup.
- **Sonnet-class** for general coding, refactors, multi-file edits.
- **Opus-class** for complex reasoning, architecture, ambiguous bugs.

Using the heaviest model for trivial tasks burns tokens with no quality gain.

## Tool-output discipline

- **Spatial indexing over brute-force reads.** Understand codebase topology and interfaces through structural indexes (symbols, outlines, signatures, targeted search) before reading implementation bodies. Never read thousands of lines of raw code when an index or signature outline suffices.

- Prefer `ctx_read` modes (`map`, `signatures`, `lines:N-M`, `diff`) over full reads. Cached re-reads cost ~13 tokens.
- Run shell through `ctx_shell` so git/npm/cargo output is pattern-compressed.
- For batch transforms, pipe via the `nu` MCP server so large tables stay out of the LLM context.

## Output discipline

- Default to terse output (see <~/.llm/skills/caveman/SKILL.md>). Most tokens in a normal response are glue words ("the", "is", "you can"); strip them when they add no signal.
- Skip preamble and trailing summaries.

## When to spend tokens

- Architecture and planning sessions where breadth matters more than cost.
- Initial context gathering for an unfamiliar codebase (do this once, save the artifact, then implement in a fresh session — see <~/.llm/skills/writing-plans/SKILL.md>).
- Verification gates before shipping (see <~/.llm/skills/verification-before-completion/SKILL.md>).

## Anti-patterns

- "Polite" multi-turn refinement of a clear single-turn ask.
- Pasting whole log files when one error line is the signal.
- Running an Opus-class model for `format with ruff`.
- Letting a stuck session grow past 60–70% context instead of saving state and restarting.
