# Git Workflow

Use when changing runner scripts, workflows, documentation, or configuration.

## Commands

```bash
git status --short
git diff --check
git diff -- AGENTS.md .agents/skills .warren/config.yaml
git add AGENTS.md .agents/skills .warren/config.yaml
git commit -m "docs: curate runner agent skills"
git status --short
git log -1 --oneline
```

Keep the change scoped to the named objective. Do not push from the runner workspace;
Warren publishes the committed branch and opens the pull request.

## Acceptance checks

- `git diff --check` exits zero.
- The commit contains only documentation/skills/config changes.
- `git status --short` is clean apart from pre-existing Warren runtime files.
- The final commit is present in `git log`.
