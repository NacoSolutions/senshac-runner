# Managing Environments

Use when changing or validating Flox, Podman, Act, runner images, or Warren settings.

## Commands

```bash
sd prime
ml prime
scripts/check-flox-lock
bash -n scripts/*
python3 - <<'PY'
from pathlib import Path
import yaml
config = yaml.safe_load(Path('.warren/config.yaml').read_text())
assert config['defaultProvider'] == 'openrouter'
assert config['defaultModel'] == 'openai/gpt-5.6-luna'
PY
```

Use the project Flox environment (`fx ...`) when host tools are unavailable. Keep
`.warren/config.yaml`, `.flox/env/manifest.toml`, and `manifest.lock` consistent;
do not retag or change image ownership without validating the producer/consumer boundary.

## Acceptance checks

- The Flox lock check reports complete resolved package entries.
- All changed shell scripts pass `bash -n`.
- Warren config retains the required provider and model.
- `.seeds/` and `.mulch/` remain unchanged.
