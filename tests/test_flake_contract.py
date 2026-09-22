from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FLAKE = (ROOT / "flake.nix").read_text()
OCI_CHECK_SCRIPT = (ROOT / "scripts/check-oci-flake").read_text()


class FlakeContractTests(unittest.TestCase):
    def test_exports_minimal_package_and_oci_image(self):
        self.assertIn("ciTools = pkgs.buildEnv", FLAKE)
        self.assertIn("ociImage = pkgs.dockerTools.buildLayeredImage", FLAKE)
        self.assertIn("inherit ciTools ociImage", FLAKE)

    def test_image_has_no_base_image_or_dockerfile_dependency(self):
        self.assertIn("contents = [ ciTools pkgs.cacert ];", FLAKE)
        self.assertIn("base_image=none", FLAKE)
        self.assertNotIn("FROM ", FLAKE)
        self.assertNotIn("docker build", FLAKE)

    def test_oci_validation_enables_nix_command(self):
        flag = "nix --extra-experimental-features nix-command"
        self.assertEqual(OCI_CHECK_SCRIPT.count(flag), 4)
        self.assertIn(f"{flag} flake check", OCI_CHECK_SCRIPT)
        self.assertIn(f"{flag} eval", OCI_CHECK_SCRIPT)
        self.assertIn(f"{flag} build", OCI_CHECK_SCRIPT)

    def test_developer_only_tools_are_not_in_selected_closure(self):
        selected = FLAKE.split("paths = with pkgs; [", 1)[1].split("            ];", 1)[0]
        selected_tools = set(selected.split())
        for tool in ("act", "nixfmt", "ripgrep", "zellij"):
            self.assertNotIn(tool, selected_tools)
        for tool in ("bashInteractive", "bun", "gh", "git", "nodejs_22", "gnutar"):
            self.assertIn(tool, selected_tools)


if __name__ == "__main__":
    unittest.main()
