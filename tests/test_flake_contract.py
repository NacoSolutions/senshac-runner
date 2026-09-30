from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FLAKE = (ROOT / "flake.nix").read_text()
CHECK = (ROOT / "scripts/check-oci-flake").read_text()
VERIFY = (ROOT / "scripts/verify-nix-base").read_text()
SMOKE = (ROOT / "scripts/smoke-ci-runner").read_text()


class FlakeContractTests(unittest.TestCase):
    def test_direct_nix_runtime_has_required_tools_and_no_environment_activation(self):
        self.assertIn("pkgs.dockerTools.buildLayeredImage", FLAKE)
        self.assertIn("pkgs.glibc}/lib/ld-linux-x86-64.so.2", FLAKE)
        self.assertIn("LD_LIBRARY_PATH=${pkgs.glibc}/lib", FLAKE)
        self.assertIn("glibc_abi_loader=/lib64/ld-linux-x86-64.so.2", FLAKE)
        self.assertIn("assert_metadata glibc_abi_loader '/lib64/ld-linux-x86-64.so.2'", CHECK)
        self.assertIn('inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable"', FLAKE)
        for package in ("bashInteractive", "cacert", "coreutils", "curl", "findutils", "gnutar",
                        "gnugrep", "gzip", "git", "gh", "jq", "bun", "chromium", "gcc",
                        "nodejs_22", "unzip", "fontconfig"):
            self.assertIn(package, FLAKE)
        self.assertNotIn("devenv", FLAKE.lower())
        self.assertNotIn("flox", FLAKE.lower())
        self.assertNotIn("activationWrapper", FLAKE)
        self.assertNotIn("apt-get", FLAKE)
        self.assertNotIn("FROM ", FLAKE)

    def test_image_has_non_root_identity_and_writable_runtime_paths(self):
        self.assertIn('User = "1000:1000"', FLAKE)
        self.assertIn("runner:x:1000:1000:Senshac Runner:/home/runner:/bin/bash", FLAKE)
        self.assertIn("chown 1000:1000 ./home/runner ./workspace", FLAKE)
        self.assertIn("chmod 1777 ./tmp", FLAKE)
        for path in ("HOME=/home/runner", "TMPDIR=/tmp", "./workspace"):
            self.assertIn(path, FLAKE)
        for marker in ("runtime_tools", "runtime_user", "writable_paths", "direct-packaged-runtime"):
            self.assertIn(marker, FLAKE)
        self.assertIn("FONTCONFIG_FILE=${pkgs.fontconfig.out}/etc/fonts/fonts.conf", FLAKE)
        self.assertIn("ln -s ${pkgs.fontconfig.out}/etc/fonts ./etc/fonts", FLAKE)
        self.assertIn("runtime_tools=bash bun cacert chromium coreutils curl fc-match findutils fontconfig gcc git gh gnutar gnugrep gzip jq nodejs unzip", FLAKE)
        self.assertIn("assert_metadata runtime_tools 'bash bun cacert chromium coreutils curl fc-match findutils fontconfig gcc git gh gnutar gnugrep gzip jq nodejs unzip'", CHECK)
        self.assertIn("assert_metadata runtime_user 'runner:1000:1000'", CHECK)
        self.assertIn("for output in runtime ociImage", CHECK)
        self.assertIn('path-info --recursive ".#$output"', CHECK)
        self.assertIn("test -x /lib64/ld-linux-x86-64.so.2", VERIFY)
        self.assertIn("-Wl,--dynamic-linker=/lib64/ld-linux-x86-64.so.2", VERIFY)

    def test_verification_exercises_rootless_runtime_and_write_permissions(self):
        self.assertIn("--userns=keep-id:uid=1000,gid=1000", VERIFY)
        self.assertIn("info --format '{{.Host.Security.Rootless}}'", VERIFY)
        self.assertIn("-e EXPECT_RUNNER_USER=1", VERIFY)
        self.assertIn('test "$(id -un)" = runner', VERIFY)
        self.assertIn('test "$(stat -c %a /tmp)" = 1777', VERIFY)
        self.assertIn('mktemp "$HOME/.oci-home.XXXXXX"', VERIFY)
        self.assertIn('mktemp /tmp/.oci-tmp.XXXXXX', VERIFY)
        self.assertIn('mktemp /workspace/.oci-workspace.XXXXXX', VERIFY)
        self.assertIn('command -v "$tool"', VERIFY)
        self.assertIn("for tool in bash tar gzip grep find git gh bun node gcc unzip chromium fc-match jq curl; do", VERIFY)
        self.assertIn("fc-match sans-serif >/dev/null", VERIFY)
        self.assertIn("for tool in tar gzip grep find git gh bun node gcc unzip chromium fc-match jq curl; do", (ROOT / "scripts/verify-ci-runner").read_text())
        self.assertIn("fc-match sans-serif >/dev/null", (ROOT / "scripts/verify-ci-runner").read_text())
        self.assertIn("--userns=keep-id:uid=1000,gid=1000", SMOKE)
        self.assertIn('"$image" bash /runner-check/verify-ci-runner', SMOKE)


if __name__ == "__main__":
    unittest.main()
