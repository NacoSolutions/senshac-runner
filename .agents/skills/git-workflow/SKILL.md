# Git Workflow

Use this workflow for every focused runner change.

## Commands

```bash
git status --short --branch
git diff --check
git diff -- AGENTS.md .agents/skills .warren/config.yaml
git add AGENTS.md .agents/skills .warren/config.yaml
git commit -m "docs: add runner role skills"
git status --short
git log -1 --oneline
```

Stage only the named guidance and configuration files. Review the staged diff,
create one focused commit, and confirm the worktree and commit are ready for
Warren's delivery.

## Acceptance checks

- `git diff --check` exits zero.
- The commit contains only the requested skills, `AGENTS.md`, and Warren config.
- `git status --short` shows a clean worktree for tracked work.
- `git log -1 --oneline` identifies the completed commit.
