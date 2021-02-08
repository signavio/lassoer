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
      in [ sqltypes dplyr readxl optparse janitor glue readr stringr ];
  };
in pkgs.stdenv.mkDerivation {
  name = "scrub";
  version = "0.3.0";
  src = ./.;
  buildInputs = [ pkgs.icu.dev pkgs.file pkgs.perl rEnv ];
  installPhase = ''
    mkdir -p $out/bin
    cp scrub $out/bin
    cp ${pkgs.icu.dev}/bin/uconv $out/bin
  '';
  installCheckPhase = ''
    PATH=$PATH:$out/bin
    ${pkgs.bash}/bin/bash tests/test_scrub
  '';
  doInstallCheck = true;
}
