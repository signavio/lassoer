{ pkgs ?
  import (fetchTarball "http://nixos.org/channels/nixos-20.09/nixexprs.tar.xz")
  { } }:

pkgs.python38Packages.buildPythonApplication {
  pname = "synthesize";
  src = ./.;
  version = "0.5.0";
  propagatedBuildInputs = with pkgs.python38Packages; [ numpy pandas ];
}
