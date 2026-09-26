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
        self.assertNotIn('git-hooks.enable', (ROOT / "devenv.nix").read_text())
        self.assertIn('verification_home="$verification_workspace/.home"', VERIFY_NIX_BASE)
        self.assertIn('verification_tmp="$verification_workspace/.tmp"', VERIFY_NIX_BASE)
        self.assertIn('mkdir -m 700 -- "$verification_home" "$verification_tmp"', VERIFY_NIX_BASE)
        self.assertIn('runner_uid="$(id -u)"', VERIFY_NIX_BASE)
        self.assertIn('runner_gid="$(id -g)"', VERIFY_NIX_BASE)
        self.assertIn("prepare_verification_workspace()", VERIFY_NIX_BASE)
        self.assertIn('git -C "$repo" archive --format=tar HEAD > "$archive"', VERIFY_NIX_BASE)
        self.assertIn("tar -xOf \"$archive\" devenv.nix | grep -Fq 'git-hooks.enable'", VERIFY_NIX_BASE)
        self.assertIn('rm -rf -- "$verification_workspace/.devenv"', VERIFY_NIX_BASE)
        self.assertIn("grep -Fq 'git-hooks.enable = false' \"$verification_workspace/.devenv.flake.nix\"", VERIFY_NIX_BASE)
        self.assertNotIn("--exclude='./.devenv'", VERIFY_NIX_BASE)
        self.assertNotIn("--exclude='./.devenv.flake.nix'", VERIFY_NIX_BASE)
        self.assertIn('trap cleanup EXIT', VERIFY_NIX_BASE)
        self.assertIn('"$runtime" run --rm --pull=never --user 0:0', VERIFY_NIX_BASE)
        self.assertIn("rm -rf -- /workspace/.??* /workspace/*", VERIFY_NIX_BASE)
        self.assertIn('rm -rf -- "$verification_workspace"', VERIFY_NIX_BASE)
        self.assertLess(VERIFY_NIX_BASE.index("prepare_verification_workspace\n"),
                        VERIFY_NIX_BASE.index("run_image()"))
        self.assertEqual(VERIFY_NIX_BASE.count('--user "$runner_uid:$runner_gid"'), 2)
        # Two host-user verification containers share the workspace; cleanup
        # uses a third, root-owned container to remove Nix-owned paths safely.
        self.assertEqual(VERIFY_NIX_BASE.count('--volume "$verification_workspace:/workspace:rw"'), 3)
        cleanup_start = VERIFY_NIX_BASE.index("cleanup() {")
        cleanup_end = VERIFY_NIX_BASE.index("\n}\ntrap cleanup EXIT", cleanup_start)
        cleanup = VERIFY_NIX_BASE[cleanup_start:cleanup_end]
        self.assertEqual(cleanup.count('--volume "$verification_workspace:/workspace:rw"'), 1)
        self.assertIn('--user 0:0', cleanup)
        self.assertIn('/workspace/.??* /workspace/*', cleanup)
        verification_commands = VERIFY_NIX_BASE[VERIFY_NIX_BASE.index("run_image()"):]
        self.assertEqual(verification_commands.count('--volume "$verification_workspace:/workspace:rw"'), 2)
        self.assertEqual(VERIFY_NIX_BASE.count('-e HOME=/workspace/.home'), 2)
        self.assertEqual(VERIFY_NIX_BASE.count('-e TMPDIR=/workspace/.tmp'), 2)
        self.assertNotIn('--volume "$repo:/workspace:', VERIFY_NIX_BASE)
        self.assertNotIn("--tmpfs /workspace/.devenv", VERIFY_NIX_BASE)

    def test_devenv_lock_matches_pinned_devenv_release(self):
        self.assertIn('devenv v1.8.1', (ROOT / "scripts/check-devenv-lock").read_text())
        self.assertIn('fa466640195d38ec97cf0493d6d6882bc4d14969',
                      (ROOT / "devenv.lock").read_text())

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
