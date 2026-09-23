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

    def test_oci_validation_enables_nix_command_and_flakes(self):
        flag = "nix --extra-experimental-features 'nix-command flakes'"
        self.assertIn("nix_cmd=(" + flag + ")", OCI_CHECK_SCRIPT)
        self.assertIn('"${nix_cmd[@]}" flake check', OCI_CHECK_SCRIPT)
        self.assertIn('"${nix_cmd[@]}" "$@" --no-write-lock-file', OCI_CHECK_SCRIPT)
        self.assertIn('"${nix_cmd[@]}" build --no-write-lock-file .#ciTools .#ociImage', OCI_CHECK_SCRIPT)
        self.assertIn(
            "assert_output senshac-runner-oci.tar.gz eval --raw "
            ".#packages.x86_64-linux.ociImage.name",
            OCI_CHECK_SCRIPT,
        )
        self.assertNotIn(
            "assert_output senshac-runner-oci eval --raw "
            ".#packages.x86_64-linux.ociImage.name",
            OCI_CHECK_SCRIPT,
        )

    def test_oci_validation_does_not_write_flake_lock(self):
        self.assertIn('flake check --no-write-lock-file', OCI_CHECK_SCRIPT)
        self.assertIn('build --no-write-lock-file', OCI_CHECK_SCRIPT)
        self.assertNotIn('grep -F', OCI_CHECK_SCRIPT)
        self.assertNotIn('<<<', OCI_CHECK_SCRIPT)

    def test_metadata_writer_preserves_exact_contract_lines(self):
        self.assertIn("printf '%s\\n' \\", FLAKE)
        self.assertNotIn('<<EOF', FLAKE)
        for line in (
            'image=senshac-runner-oci:modular',
            'ci_tools=${ciTools}',
            'image_tarball=${ociImage}',
            'selected_tools=bash bun cacert coreutils curl findutils gh git gnugrep gnutar gzip jq nodejs_22 unzip',
            'base_image=none',
        ):
            with self.subTest(line=line):
                self.assertIn(f"'{line}'", FLAKE)

    def test_developer_only_tools_are_not_in_selected_closure(self):
        selected = FLAKE.split("paths = with pkgs; [", 1)[1].split("            ];", 1)[0]
        selected_tools = set(selected.split())
        for tool in ("act", "nixfmt", "ripgrep", "zellij"):
            self.assertNotIn(tool, selected_tools)
        for tool in ("bashInteractive", "bun", "gh", "git", "nodejs_22", "gnutar"):
            self.assertIn(tool, selected_tools)


if __name__ == "__main__":
    unittest.main()
