import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RunnerContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "scripts", self.root / "scripts")
        (self.root / ".flox/env").mkdir(parents=True)
        for name in ("manifest.toml", "manifest.lock"):
            shutil.copy(ROOT / ".flox/env" / name, self.root / ".flox/env" / name)

    def run_script(self, name, *args, **env):
        return subprocess.run(
            [str(self.root / "scripts" / name), *args],
            env={**os.environ, **env}, capture_output=True, text=True, timeout=10,
        )

    def mutate_lock(self, mutate):
        path = self.root / ".flox/env/manifest.lock"
        lock = json.loads(path.read_text())
        mutate(lock)
        path.write_text(json.dumps(lock))

    def test_resolved_lock_passes(self):
        result = self.run_script("check-flox-lock")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_tar_resolution_fails(self):
        self.mutate_lock(lambda lock: lock.update(
            packages=[p for p in lock["packages"] if p["install_id"] != "gnutar"]
        ))
        result = self.run_script("check-flox-lock")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("gnutar/x86_64-linux: missing resolved", result.stderr)

    def test_empty_package_outputs_fail(self):
        self.mutate_lock(lambda lock: next(
            p for p in lock["packages"] if p["install_id"] == "gnutar"
        ).update(outputs={}))
        self.assertNotEqual(self.run_script("check-flox-lock").returncode, 0)

    def test_stale_manifest_fails(self):
        self.mutate_lock(lambda lock: lock["manifest"]["install"].pop("gnutar"))
        result = self.run_script("check-flox-lock")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("differs from manifest.toml", result.stderr)

    def smoke(self, mode):
        runtime = self.root / "runtime"
        runtime.write_text("""#!/usr/bin/env bash
set -eu
# Assert mounted file invocation through the default image entrypoint.
[[ "$*" == *'/scripts:/runner-check:ro'* ]]
[[ "$*" == *'sh /runner-check/verify-ci-runner'* ]]
[[ "$*" != *'--entrypoint'* ]]
case "$SMOKE_TEST_MODE" in
  empty) exit 0 ;;
esac
if [[ "${!#}" == --probe-failure ]]; then
  echo SENSHAC_SMOKE_PROBE_EXECUTED
  [[ "$SMOKE_TEST_MODE" == swallowed_failure ]] && exit 0
  exit 42
fi
case "$SMOKE_TEST_MODE" in
  missing_completion) exit 0 ;;
  marker_then_failure) echo SENSHAC_RUNNER_SMOKE_OK; exit 17 ;;
  success) echo SENSHAC_RUNNER_SMOKE_OK ;;
esac
""")
        runtime.chmod(0o755)
        return self.run_script("smoke-ci-runner", "test-image",
                               CONTAINER_RUNTIME=str(runtime), SMOKE_TEST_MODE=mode)

    def test_empty_execution_fails(self):
        self.assertNotEqual(self.smoke("empty").returncode, 0)

    def test_swallowed_exit_fails(self):
        self.assertNotEqual(self.smoke("swallowed_failure").returncode, 0)

    def test_missing_completion_fails(self):
        self.assertNotEqual(self.smoke("missing_completion").returncode, 0)

    def test_success_marker_with_failure_fails(self):
        self.assertNotEqual(self.smoke("marker_then_failure").returncode, 0)

    def test_nix_canary_has_separate_minimal_contract(self):
        contract = (ROOT / "scripts/verify-nix-ci-runner").read_text()
        smoke = (ROOT / "scripts/smoke-nix-ci-runner").read_text()
        for tool in ("tar", "gzip", "git", "gh", "bun", "node", "curl", "jq", "unzip"):
            self.assertIn(f'command -v "{tool}"', contract)
        self.assertIn("https://github.com", contract)
        self.assertIn("tar -czf", contract)
        self.assertIn("exit 42", contract)
        self.assertIn("verify-nix-ci-runner", smoke)
        self.assertIn("SENSHAC_NIX_RUNNER_SMOKE_OK", smoke)

    def test_executed_success_passes(self):
        result = self.smoke("success")
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
