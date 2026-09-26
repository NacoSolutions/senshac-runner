import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERIFY_NIX_BASE = (ROOT / "scripts/verify-nix-base").read_text()

class RunnerContractTests(unittest.TestCase):
    def run_script(self, name, *args, **env):
        return subprocess.run([str(ROOT / "scripts" / name), *args],
            env={**os.environ, **env}, capture_output=True, text=True, timeout=10)

    def test_resolved_lock_passes(self):
        result = self.run_script("check-devenv-lock")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_nix_verification_uses_an_isolated_writable_workspace(self):
        self.assertIn('verification_workspace="$(mktemp -d', VERIFY_NIX_BASE)
        self.assertIn('verification_home="$verification_workspace/.home"', VERIFY_NIX_BASE)
        self.assertIn('verification_tmp="$verification_workspace/.tmp"', VERIFY_NIX_BASE)
        self.assertIn('mkdir -m 700 -- "$verification_home" "$verification_tmp"', VERIFY_NIX_BASE)
        self.assertIn('runner_uid="$(id -u)"', VERIFY_NIX_BASE)
        self.assertIn('runner_gid="$(id -g)"', VERIFY_NIX_BASE)
        self.assertIn("prepare_verification_workspace()", VERIFY_NIX_BASE)
        self.assertIn("--exclude='./.devenv'", VERIFY_NIX_BASE)
        self.assertIn("--exclude='./.devenv.flake.nix'", VERIFY_NIX_BASE)
        self.assertIn('trap cleanup EXIT', VERIFY_NIX_BASE)
        self.assertIn('rm -rf -- "$verification_workspace"', VERIFY_NIX_BASE)
        self.assertLess(VERIFY_NIX_BASE.index("prepare_verification_workspace\n"),
                        VERIFY_NIX_BASE.index("run_image()"))
        self.assertEqual(VERIFY_NIX_BASE.count('--user "$runner_uid:$runner_gid"'), 2)
        self.assertEqual(VERIFY_NIX_BASE.count('--volume "$verification_workspace:/workspace:rw"'), 2)
        self.assertEqual(VERIFY_NIX_BASE.count('-e HOME=/workspace/.home'), 2)
        self.assertEqual(VERIFY_NIX_BASE.count('-e TMPDIR=/workspace/.tmp'), 2)
        self.assertNotIn('--volume "$repo:/workspace:', VERIFY_NIX_BASE)
        self.assertNotIn("--tmpfs /workspace/.devenv", VERIFY_NIX_BASE)

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
