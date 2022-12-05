{
  inputs = {
    utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };
  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = (import nixpkgs) {
          inherit system;
        };

        python-with-packages = pkgs.python3.withPackages (p: with p; [
          beautifulsoup4
        ]);
      in
      {
        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/scrape";
        };

        packages.default = pkgs.writeShellScriptBin "scrape" ''
          set -euo pipefail

          set -x

          URL="https://www.uhcw.nhs.uk/patients-and-visitors/live-waiting-times/"

          # curl the HTML of the page
          ${pkgs.curl}/bin/curl -Lo page.html "$URL"
        '';
      });
}
