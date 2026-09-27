import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RESOLVER = ROOT / "scripts/resolve-ci-runner-rollback-digest"
WORKFLOW = (ROOT / ".github/workflows/publish-ci-runner.yml").read_text()


class RollbackDigestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bin = Path(self.temp.name)
        self.docker_log = self.bin / "docker.log"
        self.curl_log = self.bin / "curl.log"
        self._command("docker", '''#!/usr/bin/env bash
printf '%s\\n' "$*" > "$DOCKER_LOG"
printf '%s' "$MOCK_DIGEST"
exit "$MOCK_INSPECT_STATUS"
''')
        self._command("curl", '''#!/usr/bin/env bash
output=''
headers=''
printf '%s\\n' '--- call ---' >> "$CURL_LOG"
while (($#)); do
  case "$1" in
    --output) output="$2"; shift 2 ;;
    --dump-header) headers="$2"; shift 2 ;;
    --user) printf 'user=%s\\n' "$2" >> "$CURL_LOG"; shift 2 ;;
    --header) printf 'header=%s\\n' "$2" >> "$CURL_LOG"; shift 2 ;;
    --data-urlencode) printf 'data=%s\\n' "$2" >> "$CURL_LOG"; shift 2 ;;
    --write-out) shift 2 ;;
    --get) shift ;;
    *) url="$1"; shift ;;
  esac
done
printf 'url=%s\\n' "$url" >> "$CURL_LOG"
if [[ "$url" == */token ]]; then
  printf '%s' "$MOCK_TOKEN_BODY" > "$output"
  printf '%s' "$MOCK_TOKEN_HTTP_STATUS"
  exit "$MOCK_TOKEN_CURL_STATUS"
fi
printf '%s' "$MOCK_HEADERS" > "$headers"
printf '%s' "$MOCK_BODY" > "$output"
printf '%s' "$MOCK_HTTP_STATUS"
exit "$MOCK_CURL_STATUS"
''')

    def _command(self, name, body):
        command = self.bin / name
        command.write_text(body)
        command.chmod(0o755)

    def resolve(self, **overrides):
        env = {
            **os.environ,
            "PATH": f"{self.bin}:{os.environ['PATH']}",
            "DOCKER_LOG": str(self.docker_log),
            "CURL_LOG": str(self.curl_log),
            "MOCK_DIGEST": "sha256:" + "a" * 64,
            "MOCK_INSPECT_STATUS": "0",
            "MOCK_TOKEN_HTTP_STATUS": "200",
            "MOCK_TOKEN_CURL_STATUS": "0",
            "MOCK_TOKEN_BODY": '{"token":"registry-token"}',
            "MOCK_HTTP_STATUS": "200",
            "MOCK_CURL_STATUS": "0",
            "MOCK_BODY": '{"schemaVersion":2}',
            "MOCK_HEADERS": 'HTTP/1.1 200 OK\r\nDocker-Content-Digest: sha256:' + 'b' * 64 + '\r\n\r\n',
            "GITHUB_ACTOR": "ci-bot",
            "GH_TOKEN": "test-token",
            "REGISTRY": "ghcr.io",
            "IMAGE_NAME": "nacosolutions/senshac-runner",
        }
        env.update(overrides)
        return subprocess.run(
            [str(RESOLVER), "ghcr.io/nacosolutions/senshac-runner:latest"],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_extracts_and_validates_manifest_digest(self):
        digest = "sha256:" + "a" * 64
        result = self.resolve()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), f"ghcr.io/nacosolutions/senshac-runner@{digest}")
        self.assertEqual(
            self.docker_log.read_text().strip(),
            "buildx imagetools inspect --format {{.Manifest.digest}} ghcr.io/nacosolutions/senshac-runner:latest",
        )
        self.assertFalse(self.curl_log.exists())

    def test_rejects_invalid_inspect_digest_without_api_fallback(self):
        result = self.resolve(MOCK_DIGEST="sha256:bad")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid manifest digest", result.stderr)
        self.assertFalse(self.curl_log.exists())

    def test_captures_authenticated_manifest_digest_header(self):
        digest = "sha256:" + "b" * 64
        result = self.resolve(MOCK_INSPECT_STATUS="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), f"ghcr.io/nacosolutions/senshac-runner@{digest}")

    def test_rejects_invalid_or_missing_manifest_digest_header(self):
        for headers in (
            "HTTP/1.1 200 OK\r\nDocker-Content-Digest: sha256:bad\r\n",
            "HTTP/1.1 200 OK\r\n",
        ):
            with self.subTest(headers=headers):
                result = self.resolve(MOCK_INSPECT_STATUS="1", MOCK_HEADERS=headers)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("invalid or missing", result.stderr)

    def test_only_authenticated_manifest_unknown_404_means_first_publication(self):
        result = self.resolve(
            MOCK_INSPECT_STATUS="1",
            MOCK_HTTP_STATUS="404",
            MOCK_BODY='{"errors":[{"code":"MANIFEST_UNKNOWN","message":"manifest unknown"}]}',
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "none (first publication)")
        curl_log = self.curl_log.read_text()
        token_call, manifest_call = curl_log.split("--- call ---")[1:]
        self.assertIn("user=ci-bot:test-token", token_call)
        self.assertIn("https://ghcr.io/token", token_call)
        self.assertIn("data=service=ghcr.io", token_call)
        self.assertIn("data=scope=repository:nacosolutions/senshac-runner:pull", token_call)
        self.assertNotIn("user=", manifest_call)
        self.assertIn("header=Authorization: Bearer registry-token", manifest_call)
        self.assertIn("https://ghcr.io/v2/nacosolutions/senshac-runner/manifests/latest", manifest_call)

    def test_missing_registry_credentials_fail_closed(self):
        result = self.resolve(MOCK_INSPECT_STATUS="1", GH_TOKEN="")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("authenticated GHCR credentials", result.stderr)
        self.assertFalse(self.curl_log.exists())

    def test_inspect_and_api_failures_are_not_first_publication(self):
        cases = (
            ("404", '{"errors":[{"code":"DENIED"}]}', "0"),
            ("401", '{"errors":[{"code":"UNAUTHORIZED"}]}', "0"),
            ("500", "internal error", "0"),
            ("000", "", "7"),
        )
        for status, body, curl_status in cases:
            with self.subTest(status=status, body=body, curl_status=curl_status):
                result = self.resolve(
                    MOCK_INSPECT_STATUS="1",
                    MOCK_HTTP_STATUS=status,
                    MOCK_BODY=body,
                    MOCK_CURL_STATUS=curl_status,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("none (first publication)", result.stdout)

    def test_token_exchange_failures_stop_before_manifest_request(self):
        cases = (
            ("401", '{"errors":[{"code":"UNAUTHORIZED"}]}', "0"),
            ("500", "internal error", "0"),
            ("200", "not-json", "0"),
            ("200", '{"token":""}', "0"),
            ("000", "", "7"),
        )
        for status, body, curl_status in cases:
            with self.subTest(status=status, body=body, curl_status=curl_status):
                self.curl_log.unlink(missing_ok=True)
                result = self.resolve(
                    MOCK_INSPECT_STATUS="1",
                    MOCK_TOKEN_HTTP_STATUS=status,
                    MOCK_TOKEN_BODY=body,
                    MOCK_TOKEN_CURL_STATUS=curl_status,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("bearer token", result.stderr)
                self.assertEqual(self.curl_log.read_text().count("--- call ---"), 1)

    def test_workflow_removes_only_rollback_pull(self):
        rollback = WORKFLOW.split("      - name: Record current rollback digest\n", 1)[1].split(
            "      - name: Push immutable image\n", 1
        )[0]
        self.assertNotIn("docker pull", rollback)
        self.assertIn("scripts/resolve-ci-runner-rollback-digest", rollback)
        self.assertIn('"scripts/resolve-ci-runner-rollback-digest"', WORKFLOW)
        self.assertEqual(WORKFLOW.count("docker pull "), 2)
        self.assertIn('docker pull "${immutable}"', WORKFLOW)
        self.assertIn('docker pull "${image}:latest"', WORKFLOW)
        self.assertIn("runner-image-digest.txt", WORKFLOW)
        self.assertIn("published-runner-image.tar", WORKFLOW)
        self.assertIn("senshac-runner-published-${{ github.sha }}", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
