{
  description = "Senshac Runner devenv OCI image";

  # Use devenv's release closure instead of the nixpkgs package. The latter
  # currently applies a nix-2.24 patch that no longer matches its source.
  nixConfig = {
    extra-substituters = [ "https://devenv.cachix.org" ];
    extra-trusted-public-keys = [
      "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw="
    ];
  };

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  inputs.devenv.url = "github:cachix/devenv/v1.8.1";
  outputs = { self, nixpkgs, devenv, ... }:
    let
      systems = [ "x86_64-linux" ];
      forEachSystem = f: nixpkgs.lib.genAttrs systems (system: f (import nixpkgs { inherit system; }));
    in {
      packages = forEachSystem (pkgs:
        let
          runnerPackages = with pkgs; [
            bashInteractive cacert coreutils curl gnutar gzip git gh jq
            bun chromium gcc nodejs_22 unzip
          ];
          devenvPackage = devenv.packages.${pkgs.system}.devenv;
          runnerPackagesWithDevenv = runnerPackages ++ [ devenvPackage ];
          baseRuntime = pkgs.buildEnv {
            name = "senshac-runner-base";
            paths = runnerPackagesWithDevenv;
            pathsToLink = [ "/bin" "/lib" "/share" ];
          };
          activationWrapper = pkgs.writeShellScriptBin "senshac-activate" ''
            set -eu
            project="''${DEVENV_ROOT:-$PWD}"
            lock="$project/devenv.lock"
            if [ ! -f "$lock" ]; then
              echo "devenv shell requires a mounted project lock: $lock" >&2
              exit 2
            fi
            export DEVENV_ROOT="$project"
            exec devenv shell -- "$@"
          '';
          ociImage = pkgs.dockerTools.buildLayeredImage {
            name = "senshac-runner-oci";
            tag = "modular";
            contents = [ baseRuntime activationWrapper pkgs.cacert ];
            extraCommands = ''
              mkdir -p ./usr/bin
              ln -s ${pkgs.coreutils}/bin/env ./usr/bin/env
              ln -s ${pkgs.bashInteractive}/bin/bash ./usr/bin/bash
            '';
            config = {
              Entrypoint = [ "${activationWrapper}/bin/senshac-activate" ];
              Cmd = [ "${pkgs.bashInteractive}/bin/bash" ];
              Env = [
                "PATH=/usr/local/bin:/usr/bin:/bin:${activationWrapper}/bin:${baseRuntime}/bin"
                "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
                "NIX_SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
                "HOME=/tmp"
                "DEVENV_ROOT=/workspace"
              ];
              WorkingDir = "/workspace";
            };
          };
        in { inherit baseRuntime ociImage; default = ociImage; });
      checks = forEachSystem (pkgs:
        let baseRuntime = self.packages.${pkgs.system}.baseRuntime;
            ociImage = self.packages.${pkgs.system}.ociImage;
        in {
          oci-closure-metadata = pkgs.runCommand "senshac-oci-closure-metadata" {} ''
            mkdir -p "$out"
            printf '%s\n' \
              'image=senshac-runner-oci:modular' \
              'base_runtime=${baseRuntime}' \
              'image_tarball=${ociImage}' \
              'base_tools=bash cacert coreutils devenv' \
              'activation=mounted-project-devenv-lock' \
              'project_tools=committed-devenv-manifest-lock' \
              'image_builder=dockerTools.buildLayeredImage' \
              'base_image=none' > "$out/metadata"
          '';
        });
    };
}
