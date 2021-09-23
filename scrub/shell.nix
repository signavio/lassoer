{ pkgs ?
  import (fetchTarball "http://nixos.org/channels/nixos-20.09/nixexprs.tar.xz")
  { } }:

let
  rEnv = (pkgs.rWrapper.override {
    packages = with pkgs.rPackages;
      let
        sqltypes = buildRPackage {
          name = "sqltypes";
          src = ../sqltypes;
          propagatedBuildInputs = [ stringr readr ];
        };
      in [
        doParallel
        dplyr
        glue
        janitor
        optparse
        readr
        readxl
        sqltypes
        stringr
      ];
  });
  tsvAppend = (pkgs.stdenv.mkDerivation {
    name = "tsv-utils";
    src = ../tsv-utils;
    version = "2.1.2";
    buildInputs = [ pkgs.dmd ];
    buildPhase = ''
      cd tsv-append && make && cd ..
    '';
    installPhase = ''
      mkdir -p $out/bin
      cp bin/tsv-append $out/bin/
    '';
  });
in pkgs.mkShell { buildInputs = [ pkgs.icu rEnv tsvAppend ]; }
