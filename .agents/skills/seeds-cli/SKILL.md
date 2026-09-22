---
name: seeds-cli
description: Use the repository-local Seeds issue tracker as the source of task ownership.
---

# Seeds CLI

Use the installed `seeds` executable; it displays its historical command name
as `sd` in help output. Run from the owning repository root.

1. Load context with `seeds prime` and inspect work with `seeds ready`.
2. Read the selected item with `seeds show <id>` before editing.
3. Create or update work with `seeds create`, `seeds update`, `seeds block`,
   `seeds unblock`, and `seeds close`; keep acceptance criteria and links
   truthful.
4. Validate with `seeds doctor` before delivery. Keep `.seeds/*.jsonl`
   changes in the same focused commit as the work they describe.

Acceptance: one owned, unblocked issue; visible acceptance criteria; linked
commit or PR evidence; `seeds doctor` passes.
