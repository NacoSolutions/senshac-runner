from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FLAKE = (ROOT / "flake.nix").read_text()
VERIFY = (ROOT / "scripts/verify-nix-base").read_text()

class FlakeContractTests(unittest.TestCase):
    def test_devenv_and_docker_tools_contract(self):
        self.assertTrue((ROOT / "devenv.nix").is_file())
        self.assertTrue((ROOT / "devenv.lock").is_file())
        self.assertIn("pkgs.dockerTools.buildLayeredImage", FLAKE)
        self.assertIn("devenv", FLAKE)
        self.assertIn("devenv.lock", FLAKE)
        self.assertNotIn("flox", FLAKE.lower())
        self.assertNotIn("apt-get", FLAKE)
        self.assertNotIn("FROM ", FLAKE)

    def test_mounted_project_uses_devenv(self):
        self.assertIn("devenv shell", FLAKE)
        self.assertIn("test -x /usr/bin/env && test -x /usr/bin/bash", VERIFY)
        self.assertIn("run_devenv command -v bun", VERIFY)
        self.assertIn("run_devenv command -v chromium", VERIFY)

if __name__ == "__main__":
    unittest.main()
