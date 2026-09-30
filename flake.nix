{
  description = "Senshac rootless OCI runner image";


  nixConfig = {
    extra-substituters = [
      "https://cache.nixos.org"
      "https://nix-community.cachix.org"
      "https://rogernavelsaker.cachix.org"
      "https://nacosolutions.cachix.org"
    ];
    extra-trusted-public-keys = [
      "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
      "rogernavelsaker.cachix.org-1:n1DtzMNhA9Rz4Kg3xlXOi/KceULu8VrMbs9WXyMFQNQ="
      "nacosolutions.cachix.org-1:JzCiW2CLcuLXtwOVAg3SlSK/kpqWbfSFEVenyKVUlug="
    ];
  };

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  outputs = { self, nixpkgs, ... }:
    let
      systems = [ "x86_64-linux" ];
      forEachSystem = f: nixpkgs.lib.genAttrs systems (system: f (import nixpkgs { inherit system; }));
    in {
      packages = forEachSystem (pkgs:
        let
          runtimePackages = with pkgs; [
            bashInteractive cacert coreutils curl findutils gnutar gnugrep gzip git gh jq
            bun chromium fontconfig gcc nodejs_22 unzip
          ];
          runtime = pkgs.buildEnv {
            name = "senshac-runner-runtime";
            paths = runtimePackages;
            pathsToLink = [ "/bin" "/lib" "/share" ];
          };
          ociImage = pkgs.dockerTools.buildLayeredImage {
            name = "senshac-runner-oci";
            tag = "modular";
            contents = [ runtime pkgs.cacert ];
            extraCommands = ''
              mkdir -p ./usr/bin ./lib64 ./etc ./home/runner ./tmp ./workspace
              ln -s ${runtime}/bin ./bin
              ln -s ${pkgs.coreutils}/bin/env ./usr/bin/env
              ln -s ${runtime}/bin/bash ./usr/bin/bash
              ln -s ${pkgs.glibc}/lib/ld-linux-x86-64.so.2 ./lib64/ld-linux-x86-64.so.2
              printf '%s\n' \
                'root:x:0:0:root:/root:/bin/bash' \
                'runner:x:1000:1000:Senshac Runner:/home/runner:/bin/bash' \
                > ./etc/passwd
              printf '%s\n' \
                'root:x:0:' \
                'runner:x:1000:' \
                > ./etc/group
              printf '%s\n' 'passwd: files' 'group: files' 'hosts: files dns' > ./etc/nsswitch.conf
              chmod 0755 ./home ./home/runner ./workspace
              chmod 1777 ./tmp
              ln -s ${pkgs.fontconfig}/etc/fonts ./etc/fonts
            '';
            fakeRootCommands = ''
              chown 1000:1000 ./home/runner ./workspace
              chown 0:0 ./tmp
            '';
            config = {
              User = "1000:1000";
              Cmd = [ "/bin/bash" ];
              Env = [
                "PATH=/bin:/usr/bin:${runtime}/bin"
                "HOME=/home/runner"
                "TMPDIR=/tmp"
                "LD_LIBRARY_PATH=${pkgs.glibc}/lib"
                "FONTCONFIG_FILE=${pkgs.fontconfig}/etc/fonts/fonts.conf"
                "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
                "NIX_SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
              ];
              WorkingDir = "/workspace";
            };
          };
        in {
          inherit runtime ociImage;
          default = ociImage;
        });
      checks = forEachSystem (pkgs:
        let runtime = self.packages.${pkgs.system}.runtime;
            ociImage = self.packages.${pkgs.system}.ociImage;
        in {
          oci-closure-metadata = pkgs.runCommand "senshac-oci-closure-metadata" {} ''
            mkdir -p "$out"
            printf '%s\n' \
              'image=senshac-runner-oci:modular' \
              'runtime=${runtime}' \
              'image_tarball=${ociImage}' \
              'runtime_tools=bash bun cacert chromium coreutils curl fc-match findutils fontconfig gcc git gh gnutar gnugrep gzip jq nodejs unzip' \
              'runtime_user=runner:1000:1000' \
              'writable_paths=/home/runner /tmp /workspace' \
              'runtime_contract=direct-packaged-runtime' \
              'glibc_abi_loader=/lib64/ld-linux-x86-64.so.2' \
              'image_builder=dockerTools.buildLayeredImage' \
              'base_image=none' > "$out/metadata"
          '';
        });
    };
}
