from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FLAKE = (ROOT / "flake.nix").read_text()
OCI_CHECK_SCRIPT = (ROOT / "scripts/check-oci-flake").read_text()
VERIFY_SCRIPT = (ROOT / "scripts/verify-nix-base").read_text()
VERIFY_WORKFLOW = (ROOT / ".github/workflows/verify-ci-runner.yml").read_text()


class FlakeContractTests(unittest.TestCase):
    def test_exports_one_docker_tools_image_and_minimal_base(self):
        self.assertIn("baseRuntime = pkgs.buildEnv", FLAKE)
        self.assertIn("paths = with pkgs; [ bashInteractive cacert coreutils flox ];", FLAKE)
        self.assertIn("ociImage = pkgs.dockerTools.buildLayeredImage", FLAKE)
        self.assertIn("inherit baseRuntime ociImage", FLAKE)
        self.assertNotIn("ciTools", FLAKE)
        for tool in ("bun", "chromium", "git", "gh", "nodejs", "gnutar"):
            self.assertNotIn(f"{tool} ]", FLAKE)

    def test_activation_requires_mounted_lock_and_runs_flox(self):
        self.assertIn('lock="$project/.flox/env/manifest.lock"', FLAKE)
        self.assertIn('exec flox activate -d "$project" -- "$@"', FLAKE)
        self.assertIn("if [ \"''${1:-}\" = flox ] && [ \"''${2:-}\" = activate ]; then", FLAKE)
        self.assertIn("FLOX_PROJECT=/workspace", FLAKE)
        self.assertIn("'activation=mounted-project-manifest-lock'", FLAKE)

    def test_image_has_no_other_builder_or_base_image(self):
        self.assertIn("contents = [ baseRuntime activationWrapper pkgs.cacert ];", FLAKE)
        self.assertIn("'image_builder=dockerTools.buildLayeredImage'", FLAKE)
        self.assertIn("'base_image=none'", FLAKE)
        self.assertNotIn("FROM ", FLAKE)
        self.assertNotIn("docker build", FLAKE)
        self.assertNotIn("flox containerize", FLAKE)
        self.assertNotIn("apt-get", FLAKE)

    def test_oci_validation_builds_only_image(self):
        flag = "nix --extra-experimental-features 'nix-command flakes'"
        self.assertIn("nix_cmd=(" + flag + ")", OCI_CHECK_SCRIPT)
        self.assertIn('"${nix_cmd[@]}" flake check', OCI_CHECK_SCRIPT)
        self.assertIn('"${nix_cmd[@]}" build --no-write-lock-file --out-link "$oci_link" .#ociImage', OCI_CHECK_SCRIPT)
        self.assertIn("assert_output senshac-runner-base eval --raw .#packages.x86_64-linux.baseRuntime.name", OCI_CHECK_SCRIPT)
        self.assertNotIn(".#ciTools", OCI_CHECK_SCRIPT)

    def test_mounted_project_verification_is_realistic(self):
        self.assertIn('run_flox command -v bun', VERIFY_SCRIPT)
        self.assertIn('run_flox command -v chromium', VERIFY_SCRIPT)
        self.assertIn('run_flox chromium --headless --no-sandbox', VERIFY_SCRIPT)
        self.assertIn('--volume "$repo:/workspace:ro"', VERIFY_SCRIPT)
        self.assertIn('"$image" flox activate -- "$@"', VERIFY_SCRIPT)

    def test_runner_has_one_canonical_producer_path(self):
        self.assertIn("scripts/check-oci-flake", VERIFY_WORKFLOW)
        self.assertIn("needs: build-image", VERIFY_WORKFLOW)
        for stale_path in ("build-minimal-flox", "verify-minimal-flox", ".flox/ci", "flox containerize"):
            self.assertNotIn(stale_path, VERIFY_WORKFLOW)
        self.assertNotIn("flox/install-flox-action", VERIFY_WORKFLOW)
        self.assertNotIn("docker build", VERIFY_WORKFLOW)


if __name__ == "__main__":
    unittest.main()
