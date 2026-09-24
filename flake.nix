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
              # Chromium and its transitive graphics/font/X11 runtime closure
              # are realized by Nix as one immutable input.
              chromium
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

          # The base image owns the profile and bootstrap only. A project
          # supplies its Flox environment at runtime; it is never copied into
          # this closure.
          floxBootstrap = pkgs.writeShellScriptBin "flox-bootstrap" ''
            set -eu
            if ! command -v flox >/dev/null 2>&1; then
              echo "Flox runtime is not present; mount or install Flox for the flox profile" >&2
              exit 127
            fi
            project="''${1:-$PWD}"
            test -f "$project/.flox/env/manifest.lock" || {
              echo "Flox profile requires a pinned .flox/env/manifest.lock" >&2
              exit 2
            }
            printf '%s\n' "$project"
          '';
          runtimeProfile = pkgs.writeShellScriptBin "senshac-runtime" ''
            set -eu
            mode="''${SENSHAC_RUNTIME_PROFILE:-minimal}"
            case "$mode" in
              minimal)
                # Minimal CI is hermetic: this branch never invokes a package
                # manager, resolver, or network-dependent bootstrapper.
                exec "$@"
                ;;
              flox)
                project="''${FLOX_PROJECT:-$PWD}"
                ${floxBootstrap}/bin/flox-bootstrap "$project" >/dev/null
                exec flox activate -d "$project" -- "$@"
                ;;
              *) echo "Unknown SENSHAC_RUNTIME_PROFILE: $mode" >&2; exit 64 ;;
            esac
          '';

          # Keep this public output name stable. dockerTools produces a
          # Docker-compatible archive (loadable by Docker or Podman).
          ociImage = pkgs.dockerTools.buildLayeredImage {
            name = "senshac-runner-oci";
            tag = "modular";
            # dockerTools assembles only the selected Nix closure and its
            # runtime metadata; no distribution layer is added.
            contents = [ ciTools floxBootstrap runtimeProfile pkgs.cacert ];
            config = {
              # The profile is the only entrypoint. Minimal mode forwards
              # commands; Flox mode activates a mounted project on demand.
              Entrypoint = [ "${runtimeProfile}/bin/senshac-runtime" ];
              Cmd = [ "${pkgs.bashInteractive}/bin/bash" ];
              Env = [
                "PATH=/usr/local/bin:${runtimeProfile}/bin:${floxBootstrap}/bin:${ciTools}/bin"
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
              'selected_tools=bash bun chromium cacert coreutils curl findutils gh git gnugrep gnutar gzip jq nodejs_22 unzip' \
              'runtime_profiles=minimal,flox' \
              'flox_environment=runtime-mounted,pinned-lock-required' \
              'minimal_network=disabled' \
              'base_image=none' \
              > "$out/metadata"
          '';
        });
    };
}
