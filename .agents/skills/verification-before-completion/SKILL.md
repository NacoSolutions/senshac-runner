# Verification Before Completion

Use before committing any runner-repository change.

## Commands

```bash
git diff --check
scripts/check-flox-lock
python3 -m unittest discover -s tests -v
for script in scripts/*; do bash -n "$script"; done
```

For a full CI-equivalent run, use the configured gate only with a clean web checkout:
`SENSHAC_WEB_REPO=/path/to/web ./scripts/act-ci`. For documentation/config-only work,
use the bounded checks above and verify the exact requested keys and links.

## Acceptance checks

- Every command exits zero with no warnings treated as failures.
- Tests cover the changed contract or the documentation/config assertions are explicit.
- `git diff --check` is clean and the final diff is limited to the objective.
- Run the selected gate once before commit and once after the final edit.
