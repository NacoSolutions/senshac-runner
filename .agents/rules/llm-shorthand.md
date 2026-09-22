# LLM Shorthand — Machine-to-Machine State & Context Compaction

High-density semantic style for LLM ingestion in persistent substrate: **Engram**, **Trellis**, **Seeds**, **Mulch**, inter-agent IPC, compaction handoffs, and session summaries.

## Core Principle
- Natural language prose is acoustically redundant. LLMs ingest semantic density directly.
- Maximize information entropy per token. Zero grammatical fluff or pleasantries.
- **Machine-dense compilation**: Treat persistent state, handoffs, and operational summaries as compiled machine instructions, not human prose.
- **Inviolable anchor**: Never abbreviate, alter, or omit file paths, line numbers, function signatures, variable names, error messages, flags, or commit hashes. High entropy must be exact.

## Syntax & Connectives

| Operator | Semantic Function | Example |
|---|---|---|
| `->` | Synchronous sequence, transition, output | `parse(req) -> Token` |
| `~>` | Asynchronous dispatch, eventual yield | `dispatch(tester) ~> report` |
| `=>` | Implication, cause, requirement | `expired token => 401 AuthError` |
| `:=` | Definition, strict alias | `TDD := token dense dialect` |
| `:` | Key-value assignment | `status: done \| scope: auth` |
| `\|` | Disjunction, alternate | `[cache-hit \| fetch-remote]` |
| `&` | Conjunction (simultaneous) | `atomic & thread-safe` |
| `!` / `≠` | Negation, exclusion, inequality | `!in-memory \| rule ≠ enforcement` |
| `∈` / `∉` | In-scope / out-of-scope | `target ∈ {src/auth} & target ∉ {vendor/*}` |
| `>` | Preference, priority | `specific > general` |
| `~` | Approximate, estimated | `prefill: ~250 tok` |
| `+` / `-` | Added / removed | `+export fn verify / -oldMiddleware` |
| `?` | Hypothesis, unverified | `? race cond on socket close` |
| `@` | Context, location, anchor | `reproduce @ src/jwt.ts#L45` |

## Structural Typology (TDD Notation)

Compact symbolic classifiers for code entities and types:

| Symbol | Kind | Example |
|---|---|---|
| `λ` | Function, handler, method | `λ verify_token(req)` |
| `§` | Struct, class, module | `§ SessionStore` |
| `∂` | Interface, trait, contract | `∂ AuthProvider` |
| `τ` | Type alias | `τ TokenId = string` |
| `ε` | Enum, variant set | `ε Status { Ok, Err }` |

## Standard Abbreviations

| Short | Full | Short | Full | Short | Full |
|---|---|---|---|---|---|
| `cfg` | config | `fn` | function | `req` / `res` | request / response |
| `impl` | implementation | `sig` | signature | `dep` / `deps` | dependency/ies |
| `spec` | specification | `ctx` | context | `err` | error |
| `ret` | return / returns | `auth` | authentication | `sync` | synchronize |

## Substrate Framing (State & Handoffs)

Format observations, records, handoffs, and summaries into dense key-value frames rather than conversational narrative:

### Engram / Mulch / Trellis / Seeds Pattern
```text
Goal: <objective>
State: <in_progress|done|blocked> [!blocker]
Path: <file#lines>
What: <exact-action> (e.g. atomic token rotation via Redis lock)
Why: <driver> (e.g. race cond on concurrent refresh)
Impact: <component> -> <effect>
Next: <action> [-> expected result]
```

### Contrast Example
- **Prose (Avoid in substrate):** "We investigated the authentication failure and found that when a user tries to refresh their token concurrently, both requests enter a race condition. We resolved this by adding a Redis mutex lock inside `src/auth/jwt.ts` around line 45."
- **LLM Shorthand (Preferred):** `Auth refresh race cond: concurrent reqs -> double spend. Fix: Redis mutex lock in src/auth/jwt.ts#L45. Status: resolved & verified.`
