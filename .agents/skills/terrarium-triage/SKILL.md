---
name: terrarium-triage
description: Triage the canonical Terrarium graph and select one actionable seed.
---

# Terrarium triage

1. Establish the canonical graph before acting. In the modular Senshac layout,
   use the active `senshac-web` repository unless an explicit tracker
   migration says otherwise; read its local instructions and registry entry.
2. Run the repository's supported triage command (normally `dx tr triage`) and
   inspect ready work, stale work, blocked dependencies, and ownership. Use
   `sd` for issue details and mutations.
3. Select one bounded, unblocked seed whose acceptance criteria can be tested
   in the current repository. Explain why it is next; do not pull work merely
   because it is old or convenient.
4. If the graph is inconsistent, preserve the evidence, fix the smallest
   tracker error with the native tool, and report the remaining ambiguity.
   Do not create duplicate seeds to work around a bad link.
5. Start the selected workflow with its issue identifier, target repository,
   gate, and expected delivery link visible. Return to the graph after delivery
   to update status and dependencies.

Triage is a routing decision. Implementation and tracker mutation remain
separate, reviewable steps.

## Commands and acceptance

Run `dx tr triage` in the active repository and use `sd show` for the selected
seed. Acceptance is one owned, unblocked seed with a visible repository, gate,
and delivery link plan.
