{ pkgs, ... }:
{
  name = "senshac-runner";

  packages = with pkgs; [
    act age betterleaks biome bun chromium curl nixfmt-rfc-style fd findutils
    ripgrep procps gnugrep gcc glibc gnutar gh git jq perl sops
    typescript-language-server unzip gzip yq zellij nodejs_24 cacert
  ];

  env.NODE_ENV = "development";

  enterShell = ''
    export PATH="$DEVENV_ROOT/scripts:$PATH"
    GCC_RUNTIME_LIB="$(dirname "$(gcc -print-file-name=libstdc++.so.6)")"
    export LD_LIBRARY_PATH="$GCC_RUNTIME_LIB''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    if [ -f package.json ] && [ ! -d node_modules ]; then
      echo "Installing dependencies..."
      bun install
    fi
  '';
}
