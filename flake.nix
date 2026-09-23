{
  description = "Senshac Runner's minimal CI tool closure and OCI image";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" ];
      forEachSystem = f: nixpkgs.lib.genAttrs systems (system: f (import nixpkgs { inherit system; }));
    in {
      packages = forEachSystem (pkgs:
        let
          # This is deliberately limited to tools exercised by the runner's
          # current Actions contract. Developer tooling remains in Flox.
          ciTools = pkgs.buildEnv {
            name = "senshac-ci-tools";
            paths = with pkgs; [
              bashInteractive
              bun
              cacert
              coreutils
              curl
              findutils
              git
              gh
              gnugrep
              gnutar
              gzip
              jq
              nodejs_22
              unzip
            ];
            pathsToLink = [ "/bin" "/sbin" "/share" ];
          };

          ociImage = pkgs.dockerTools.buildLayeredImage {
            name = "senshac-runner-oci";
            tag = "modular";
            # dockerTools assembles only the selected Nix closure and its
            # runtime metadata; no distribution layer is added.
            contents = [ ciTools pkgs.cacert ];
            config = {
              Entrypoint = [ "${pkgs.bashInteractive}/bin/bash" ];
              Cmd = [ "-lc" ];
              Env = [
                "PATH=${ciTools}/bin"
                "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
                "NIX_SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
                "HOME=/tmp"
              ];
              WorkingDir = "/workspace";
            };
          };
        in {
          inherit ciTools ociImage;
          default = ciTools;
        });

      checks = forEachSystem (pkgs:
        let
          ciTools = self.packages.${pkgs.system}.ciTools;
          ociImage = self.packages.${pkgs.system}.ociImage;
        in {
          oci-closure-metadata = pkgs.runCommand "senshac-oci-closure-metadata" {
            nativeBuildInputs = [ pkgs.coreutils ];
          } ''
            mkdir -p "$out"
            printf '%s\n' \
              'image=senshac-runner-oci:modular' \
              'ci_tools=${ciTools}' \
              'image_tarball=${ociImage}' \
              'selected_tools=bash bun cacert coreutils curl findutils gh git gnugrep gnutar gzip jq nodejs_22 unzip' \
              'base_image=none' \
              > "$out/metadata"
          '';
        });
    };
}
