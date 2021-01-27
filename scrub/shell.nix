{ pkgs ?
  import (fetchTarball "http://nixos.org/channels/nixos-20.09/nixexprs.tar.xz")
  { } }:

let
  sqltypes = (pkgs.rWrapper.override {
    packages = with pkgs.rPackages;
      let
        sqltypes = buildRPackage {
          name = "sqltypes";
          src = ../sqltypes;
          propagatedBuildInputs = [ stringr readr ];
        };
      in [ sqltypes readxl optparse ];
  });
  rEnv = with pkgs.rPackages; [ optparse readxl janitor glue readr stringr ];
in pkgs.mkShell { buildInputs = [ pkgs.icu sqltypes ] ++ rEnv; }
