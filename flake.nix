{
  inputs = {
    utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    mach-nix.url = "github:DavHau/mach-nix";
    mach-nix.inputs.nixpkgs.follows = "nixpkgs";
    mach-nix.inputs.flake-utils.follows = "utils";
  };
  outputs = { self, nixpkgs, flake-utils, mach-nix, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = (import nixpkgs) {
          inherit system;
        };

        git-history = mach-nix.lib."${system}".mkPython {
          requirements = ''
            git-history
          '';
          ignoreDataOutdated = true;
        };

        python-shell = mach-nix.lib."${system}".mkPython {
          requirements = ''
            numpy
            matplotlib
            beautifulsoup4
          '';
          ignoreDataOutdated = true;
        };

      in
      {
        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/scrape";
        };
        apps.extract = {
          type = "app";
          program = "${self.packages.${system}.extract}/bin/extract";
        };
        apps.analyse = {
          type = "app";
          program = "${self.packages.${system}.analyse}/bin/analyse";
        };

        packages.analyse = pkgs.stdenv.mkDerivation {
          name = "analyse";
          buildInputs = [
            python-shell
          ];

          unpackPhase = ":";
          installPhase = "install -m 755 -D ${./analyse.py} $out/bin/analyse";
        };

        packages.extract = pkgs.writeShellScriptBin "extract" ''
          set -euo pipefail

          rm -f res.db
          ${git-history}/bin/git-history file res.db ./times.json --id location
        '';

        packages.parser = pkgs.writeScriptBin "parser" ''
          #!${python-shell}/bin/python

          import argparse
          import json

          from bs4 import BeautifulSoup

          parser = argparse.ArgumentParser()
          parser.add_argument("html")
          parser.add_argument("-o", "--output", required=True)
          args = parser.parse_args()

          with open(args.html) as infile:
              html = infile.read()

          soup = BeautifulSoup(html, "html.parser")

          items = soup.select(".live_waiting_time_item_content")
          results = []
          for item in items:
              key = item.select_one(".live_waiting_time_item_hospital_name").text
              for child in item.select("div"):
                  if "WAIT TIME" in child.text:
                      results.append({
                        "location": key,
                        "wait_time": child.text,
                      })

          with open(args.output, "w") as outfile:
              json.dump(results, outfile)
        '';
        packages.scrape = pkgs.writeShellScriptBin "scrape" ''
          set -euo pipefail

          set -x

          URL="https://www.uhcw.nhs.uk/patients-and-visitors/live-waiting-times/"

          # curl the HTML of the page
          ${pkgs.curl}/bin/curl -Lso page.html "$URL"

          ${self.packages.${system}.parser}/bin/parser page.html -o times.json
        '';
        packages.default = self.packages.${system}.scrape;

        devShells.default = pkgs.mkShell {
          buildInputs = [
            python-shell
            pkgs.sqlite
            git-history
          ];
        };
      });
}
