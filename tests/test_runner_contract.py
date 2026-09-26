import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERIFY_NIX_BASE = (ROOT / "scripts/verify-nix-base").read_text()
BUILD_CI_RUNNER = (ROOT / "scripts/build-ci-runner").read_text()


class RunnerContractTests(unittest.TestCase):
    def run_script(self, name, *args, **env):
        return subprocess.run([str(ROOT / "scripts" / name), *args],
            env={**os.environ, **env}, capture_output=True, text=True, timeout=10)

    def test_resolved_lock_passes(self):
        result = self.run_script("check-devenv-lock")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_image_build_is_independent_of_developer_environment(self):
        self.assertNotIn("devenv", BUILD_CI_RUNNER.lower())
        self.assertNotIn("check-devenv-lock", BUILD_CI_RUNNER)
        self.assertIn('"$repo#ociImage"', BUILD_CI_RUNNER)

    def test_verification_checks_rootless_identity_and_writable_mounts(self):
        self.assertIn('verification_workspace="$(mktemp -d', VERIFY_NIX_BASE)
        self.assertIn('git -C "$repo" archive --format=tar HEAD > "$archive"', VERIFY_NIX_BASE)
        self.assertIn('container_args+=(--userns=keep-id:uid=1000,gid=1000 -e EXPECT_RUNNER_USER=1)', VERIFY_NIX_BASE)
        self.assertIn('container_args+=(--user "$runner_uid:$runner_gid")', VERIFY_NIX_BASE)
        self.assertIn('trap cleanup EXIT', VERIFY_NIX_BASE)
        self.assertIn('rm -rf -- "$verification_workspace"', VERIFY_NIX_BASE)
        self.assertIn('test "$uid" -gt 0', VERIFY_NIX_BASE)
        self.assertIn('test "$uid" = 1000', VERIFY_NIX_BASE)
        self.assertIn('test "$(id -un)" = runner', VERIFY_NIX_BASE)
        self.assertIn('test -w "$HOME"', VERIFY_NIX_BASE)
        self.assertIn('test -w /workspace', VERIFY_NIX_BASE)
        self.assertIn('test "$(stat -c %a /tmp)" = 1777', VERIFY_NIX_BASE)
        self.assertIn('command -v "$tool"', VERIFY_NIX_BASE)
        self.assertIn('mktemp "$HOME/.oci-home.XXXXXX"', VERIFY_NIX_BASE)
        self.assertIn('mktemp /tmp/.oci-tmp.XXXXXX', VERIFY_NIX_BASE)
        self.assertIn('mktemp /workspace/.oci-workspace.XXXXXX', VERIFY_NIX_BASE)

    def test_devenv_lock_matches_declared_unstable_input(self):
        lock = json.loads((ROOT / "devenv.lock").read_text())
        checker = (ROOT / "scripts/check-devenv-lock").read_text()
        manifest = (ROOT / "devenv.yaml").read_text()
        root_inputs = lock["nodes"][lock["root"]]["inputs"]
        nixpkgs = lock["nodes"]["nixpkgs"]
        self.assertEqual(lock["version"], 7)
        self.assertEqual(root_inputs, {"devenv": "devenv", "nixpkgs": "nixpkgs"})
        self.assertIn("url: github:NixOS/nixpkgs/nixpkgs-unstable", manifest)
        self.assertIn("devenv", lock["nodes"])
        self.assertNotIn("git-hooks", lock["nodes"])
        self.assertNotIn("gitignore", lock["nodes"])
        self.assertEqual(nixpkgs["original"]["owner"], "NixOS")
        self.assertEqual(nixpkgs["original"]["repo"], "nixpkgs")
        self.assertEqual(nixpkgs["original"]["ref"], "nixpkgs-unstable")
        self.assertEqual(nixpkgs["locked"]["owner"], "NixOS")
        self.assertEqual(nixpkgs["locked"]["repo"], "nixpkgs")
        self.assertTrue(nixpkgs["locked"]["rev"])
        self.assertTrue(nixpkgs["locked"]["narHash"])
        for name, node in lock["nodes"].items():
            if name != lock["root"] and node["locked"]["type"] != "path":
                self.assertTrue(node["locked"].get("rev"), name)
                self.assertTrue(node["locked"].get("narHash"), name)
        self.assertIn('Object.hasOwn(lock.nodes, name)', checker)
        self.assertIn('JSON.stringify(["devenv", "nixpkgs"])', checker)
        self.assertNotIn("16ec914f6fb6f599ce988427d9d94efddf25fe6d", checker)

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
