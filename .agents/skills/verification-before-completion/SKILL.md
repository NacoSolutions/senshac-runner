# Verification Before Completion

Run the smallest complete validation for documentation and configuration
changes, then inspect the final commit.

## Commands

```bash
python3 - <<'PY'
from pathlib import Path
import yaml

root = Path('.')
config = yaml.safe_load((root / '.warren/config.yaml').read_text())
assert config['defaultProvider'] == 'openrouter'
assert config['defaultModel'] == 'openai/gpt-5.6-luna'
for name in ('git-workflow', 'managing-environments', 'dependency-hygiene',
             'verification-before-completion'):
    assert (root / '.agents/skills' / name / 'SKILL.md').is_file()
print('runner role skills and Warren configuration validated')
PY
git diff --check
git status --short
git log -1 --oneline
```

Run the repository's documented bounded check after editing. Review the diff
for scope, verify every requested link, and confirm the committed files match
the objective before reporting completion.

## Acceptance checks

- The bounded documentation/configuration check prints its success message and exits zero.
- `git diff --check` exits zero.
- The final commit contains the four role skills, their `AGENTS.md` links, and the required Warren defaults.
