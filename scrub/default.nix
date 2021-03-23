{ pkgs ?
  import (fetchTarball "http://nixos.org/channels/nixos-20.09/nixexprs.tar.xz")
  { } }:

let
  rEnv = pkgs.rWrapper.override {
    packages = with pkgs.rPackages;
      let
        sqltypes = buildRPackage {
          name = "sqltypes";
          src = ../sqltypes;
          propagatedBuildInputs = [ stringr readr ];
        };
      in [
        sqltypes
        dplyr
        readxl
        doParallel
        optparse
        janitor
        glue
        readr
        stringr
      ];
  };
  tsvAppend = pkgs.stdenv.mkDerivation {
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
  };
in pkgs.stdenv.mkDerivation {
  name = "scrub";
  version = "0.3.0";
  src = ./.;
  buildInputs = [ pkgs.icu.dev pkgs.file pkgs.perl rEnv tsvAppend ];
  installPhase = ''
    mkdir -p $out/bin
    cp scrub $out/bin
    cp ${pkgs.icu.dev}/bin/uconv $out/bin
    cp ${tsvAppend}/bin/tsv-append $out/bin
  '';
  doInstallCheck = true;
  installCheckPhase = ''
    PATH=$PATH:$out/bin
    ${pkgs.bash}/bin/bash tests/test_scrub
  '';
}
