---
name: warren-operations
description: Dispatch bounded Warren runs with tracker, cost, and delivery evidence.
---

# Warren operations

1. Start from one open Seeds item with an owner, acceptance criteria, target
   repository, gate, and cost cap.
2. Use the registered Warren project for that repository. Give the agent one
   positive, narrow objective and name the files or surface it owns.
3. Instruct the agent to use `seeds`, `mulch`, and the repository's native gate;
   include the Seeds ID in its branch, commit, PR body, and final report.
4. Prefer commit-and-report delivery when the run is implementation-only. Use
   Warren PR delivery when host-side push and PR creation are explicitly part
   of the run contract.
5. Review run output, branch, checks, and PR before merge. Update the Seed only
   with verified evidence.

Acceptance: bounded run, green repository gate, committed result, tracker link,
and reviewed delivery state.
