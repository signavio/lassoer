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
      in [ sqltypes dplyr optparse glue readr stringr ];
  };
in pkgs.stdenv.mkDerivation {
  name = "inspect";
  version = "0.3.0";
  src = ./.;
  buildInputs = [ pkgs.file pkgs.glibcLocales rEnv ];
  installPhase = ''
    mkdir -p $out/bin
    cp inspect $out/bin
  '';
  doInstallCheck = true;
  installCheckPhase = ''
    PATH=$PATH:$out/bin
    ${pkgs.bash}/bin/bash tests/test_inspect
  '';
}
