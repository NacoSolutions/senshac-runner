# Senshac Agent Principles

Apply these six principles to every focused change in this repository.

## Direct execution
- Run the repository command that verifies each stated outcome.
- Record the command and its result in the completion report.
- Acceptance check: the relevant command exits zero and demonstrates the requested outcome.

## Instruction specificity
- Name the objective, files, commands, and acceptance checks before editing.
- Keep each instruction concrete enough for another agent to execute without interpretation.
- Acceptance check: the diff contains only the named objective and the documented checks pass.

## Positive phrasing
- State the desired action and outcome directly in every instruction.
- Prefer “run the validation and confirm it passes” over indirect or prohibitive wording.
- Acceptance check: each new instruction identifies an action and its successful result.

## Defense in depth
- Validate configuration at the file level and behavior at the repository level.
- Use independent checks for critical paths, such as syntax validation and a focused test.
- Acceptance check: every critical setting has a direct check and a broader repository check.

## Gentle coding
- Inspect the smallest relevant surface, preserve adjacent behavior, and make the smallest complete edit.
- Keep production behavior unchanged when the objective concerns guidance or configuration.
- Acceptance check: the diff is limited to guidance/configuration files and the focused checks pass.

## Token economy
- Read only the files needed for the objective and use bounded commands with clear output.
- Stop after the acceptance checks pass and report the commit and remaining follow-up.
- Acceptance check: one bounded validation covers the objective without unrelated work.

## Repository validation

Run this bounded documentation/configuration check from the repository root:

```bash
python3 - <<'PY'
from pathlib import Path
import yaml

root = Path('.')
principles = (root / '.agents/skills/senshac-agent-principles/SKILL.md').read_text()
for name in ('direct execution', 'instruction specificity', 'positive phrasing',
             'defense in depth', 'gentle coding', 'token economy'):
    assert f'## {name.title()}' in principles
config = yaml.safe_load((root / '.warren/config.yaml').read_text())
assert config['defaultProvider'] == 'openrouter'
assert config['defaultModel'] == 'openai/gpt-5.6-luna'
assert (root / '.agents/skills/bounded-warren-task/SKILL.md').is_file()
print('guidance and Warren configuration validated')
PY
```

Acceptance check: the command prints `guidance and Warren configuration validated` and exits zero.
