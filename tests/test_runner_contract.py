import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class RunnerContractTests(unittest.TestCase):
    def run_script(self, name, *args, **env):
        return subprocess.run([str(ROOT / "scripts" / name), *args],
            env={**os.environ, **env}, capture_output=True, text=True, timeout=10)

    def test_resolved_lock_passes(self):
        result = self.run_script("check-devenv-lock")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_smoke_propagates_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "runtime"
            runtime.write_text("""#!/usr/bin/env bash
set -eu
if [[ "${!#}" == --probe-failure ]]; then echo SENSHAC_SMOKE_PROBE_EXECUTED; exit 42; fi
echo SENSHAC_RUNNER_SMOKE_OK
""")
            runtime.chmod(0o755)
            result = self.run_script("smoke-ci-runner", "test-image",
                                    CONTAINER_RUNTIME=str(runtime))
            self.assertEqual(result.returncode, 0, result.stderr)

if __name__ == "__main__":
    unittest.main()
