import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERIFY_NIX_BASE = (ROOT / "scripts/verify-nix-base").read_text()
BUILD_CI_RUNNER = (ROOT / "scripts/build-ci-runner").read_text()
PUBLISH_WORKFLOW = (ROOT / ".github/workflows/publish-ci-runner.yml").read_text()


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

    def run_rollback_helper(self, directory, *, inspect_status=0, manifest='{"digest":"sha256:' + "a" * 64 + '"}',
                             http_status="404", http_body='{"errors":[{"code":"MANIFEST_UNKNOWN"}]}',
                             curl_failure=""):
        mock_bin = Path(directory) / "bin"
        mock_bin.mkdir()
        docker = mock_bin / "docker"
        docker.write_text("""#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$DOCKER_LOG"
printf '%s' "$MANIFEST_JSON"
exit "$DOCKER_STATUS"
""")
        docker.chmod(0o755)
        curl = mock_bin / "curl"
        curl.write_text("""#!/usr/bin/env bash
set -eu
printf '%s\\n' "$*" >> "$CURL_LOG"
case "$*" in
  *https://ghcr.io/token*)
    [[ "$*" == *'--user test-user:test-token'* ]]
    if [[ "$CURL_FAILURE" == token ]]; then exit 22; fi
    printf '{"token":"registry-token"}'
    ;;
  *)
    [[ "$*" == *'--header Authorization: Bearer registry-token'* ]]
    if [[ "$CURL_FAILURE" == manifest ]]; then exit 7; fi
    output=''
    while (($#)); do
      if [[ "$1" == --output ]]; then output="$2"; shift 2; else shift; fi
    done
    printf '%s' "$HTTP_BODY" > "$output"
    printf '%s' "$HTTP_STATUS"
    ;;
esac
""")
        curl.chmod(0o755)
        log_path = Path(directory) / "docker.log"
        curl_log_path = Path(directory) / "curl.log"
        result = subprocess.run(
            [str(ROOT / "scripts/resolve-runner-rollback-digest"),
             "ghcr.io/nacosolutions/senshac-runner"],
            env={**os.environ, "PATH": f"{mock_bin}:{os.environ['PATH']}",
                 "DOCKER_LOG": str(log_path), "CURL_LOG": str(curl_log_path),
                 "DOCKER_STATUS": str(inspect_status), "MANIFEST_JSON": manifest,
                 "GHCR_USERNAME": "test-user",
                 "GHCR_TOKEN": "test-token", "HTTP_STATUS": http_status,
                 "HTTP_BODY": http_body, "CURL_FAILURE": curl_failure},
            capture_output=True, text=True, timeout=10)
        docker_log = log_path.read_text() if log_path.exists() else ""
        curl_log = curl_log_path.read_text() if curl_log_path.exists() else ""
        return result, docker_log, curl_log

    def test_rollback_digest_extracts_and_validates_manifest_digest(self):
        expected = "sha256:" + "a" * 64
        with tempfile.TemporaryDirectory() as directory:
            result, docker_log, _ = self.run_rollback_helper(directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), expected)
            self.assertIn("buildx imagetools inspect", docker_log)
            self.assertIn("--format {{json .Manifest}}", docker_log)

        invalid_manifests = (
            "{}", '{"digest":"sha256:' + "a" * 63 + '"}',
            '{"digest":"sha256:' + "A" * 64 + '"}', "not-json")
        for manifest in invalid_manifests:
            with self.subTest(manifest=manifest), tempfile.TemporaryDirectory() as directory:
                result, _, _ = self.run_rollback_helper(directory, manifest=manifest)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("no valid sha256 digest", result.stderr)

    def test_inspect_failure_requires_authenticated_manifest_unknown_404(self):
        first_publish = '{"errors":[{"code":"MANIFEST_UNKNOWN"}]}'
        with tempfile.TemporaryDirectory() as directory:
            result, _, curl_log = self.run_rollback_helper(
                directory, inspect_status=1, http_status="404", http_body=first_publish)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "none (first publication)")
            self.assertIn("--user test-user:test-token", curl_log)
            self.assertIn("Authorization: Bearer registry-token", curl_log)

        for status, body in (("404", '{"errors":[{"code":"DENIED"}]}'),
                             ("401", first_publish), ("500", first_publish)):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                result, _, _ = self.run_rollback_helper(
                    directory, inspect_status=1, http_status=status, http_body=body)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"HTTP {status}", result.stderr)

        for curl_failure in ("token", "manifest"):
            with self.subTest(curl_failure=curl_failure), tempfile.TemporaryDirectory() as directory:
                result, _, _ = self.run_rollback_helper(
                    directory, inspect_status=1, curl_failure=curl_failure)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("first publication", result.stdout)

    def test_rollback_lookup_skips_pull_and_preserves_publication_verification(self):
        start = PUBLISH_WORKFLOW.index("      - name: Record current rollback digest")
        end = PUBLISH_WORKFLOW.index("      - name:", start + 1)
        rollback_step = PUBLISH_WORKFLOW[start:end]
        self.assertIn("scripts/resolve-runner-rollback-digest", rollback_step)
        self.assertNotIn("docker pull", rollback_step)
        self.assertIn('docker pull "${immutable}"', PUBLISH_WORKFLOW)
        self.assertIn('docker pull "${image}:latest"', PUBLISH_WORKFLOW)
        self.assertIn('docker push "${image}:sha-${GITHUB_SHA}"', PUBLISH_WORKFLOW)
        self.assertIn("scripts/smoke-ci-runner", PUBLISH_WORKFLOW)
        self.assertIn("senshac-runner-published-${{ github.sha }}", PUBLISH_WORKFLOW)
        self.assertIn("senshac-runner-image-digest", PUBLISH_WORKFLOW)

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
