# Dependency Hygiene

Keep Flox package declarations, resolved lock entries, and runner checks in
agreement.

## Commands

```bash
scripts/check-flox-lock
python3 -m unittest discover -s tests -v
for script in scripts/*; do bash -n "$script"; done
```

Update `.flox/env/manifest.toml` through the pinned Flox workflow, commit the
matching `.flox/env/manifest.lock`, and run the checks above. Keep package
exposure covered by `scripts/verify-ci-runner` when the runner image changes.

## Acceptance checks

- Every declared package has a resolved lock entry and outputs.
- Runner contract tests pass.
- Every repository script passes Bash syntax validation.
- The dependency diff stays limited to the intended package update and its lock resolution.
