{
  description = "Senshac Runner's Flox activation OCI image";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" ];
      forEachSystem = f: nixpkgs.lib.genAttrs systems (system: f (import nixpkgs { inherit system; }));
    in {
      packages = forEachSystem (pkgs:
        let
          # The committed Flox manifest/lock owns every project tool. This is
          # only the immutable bootstrap needed to run activation.
          baseRuntime = pkgs.buildEnv {
            name = "senshac-runner-base";
            paths = with pkgs; [ bashInteractive cacert coreutils flox ];
            pathsToLink = [ "/bin" "/lib" "/share" ];
          };

          activationWrapper = pkgs.writeShellScriptBin "senshac-activate" ''
            set -eu
            project="''${FLOX_PROJECT:-$PWD}"
            lock="$project/.flox/env/manifest.lock"
            if [ ! -f "$lock" ]; then
              echo "Flox activation requires a mounted project lock: $lock" >&2
              exit 2
            fi
            export FLOX_PROJECT="$project"
            # Keep an explicit command form available for mounted-project
            # verification while making the image entrypoint an activation
            # wrapper for ordinary commands.
            if [ "''${1:-}" = flox ] && [ "''${2:-}" = activate ]; then
              exec "$@"
            fi
            exec flox activate -d "$project" -- "$@"
          '';

          ociImage = pkgs.dockerTools.buildLayeredImage {
            name = "senshac-runner-oci";
            tag = "modular";
            contents = [ baseRuntime activationWrapper pkgs.cacert ];
            config = {
              Entrypoint = [ "${activationWrapper}/bin/senshac-activate" ];
              Cmd = [ "${pkgs.bashInteractive}/bin/bash" ];
              Env = [
                "PATH=/usr/local/bin:${activationWrapper}/bin:${baseRuntime}/bin"
                "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
                "NIX_SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
                "HOME=/tmp"
                "FLOX_PROJECT=/workspace"
              ];
              WorkingDir = "/workspace";
            };
          };
        in {
          inherit baseRuntime ociImage;
          default = ociImage;
        });

      checks = forEachSystem (pkgs:
        let
          baseRuntime = self.packages.${pkgs.system}.baseRuntime;
          ociImage = self.packages.${pkgs.system}.ociImage;
        in {
          oci-closure-metadata = pkgs.runCommand "senshac-oci-closure-metadata" {
            nativeBuildInputs = [ pkgs.coreutils ];
          } ''
            mkdir -p "$out"
            printf '%s\n' \
              'image=senshac-runner-oci:modular' \
              'base_runtime=${baseRuntime}' \
              'image_tarball=${ociImage}' \
              'base_tools=bash cacert coreutils flox' \
              'activation=mounted-project-manifest-lock' \
              'project_tools=committed-flox-manifest-lock' \
              'image_builder=dockerTools.buildLayeredImage' \
              'base_image=none' \
              > "$out/metadata"
          '';
        });
    };
}
