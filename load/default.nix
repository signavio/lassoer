{ pkgs ?
  import (fetchTarball "http://nixos.org/channels/nixos-20.09/nixexprs.tar.xz")
  { } }:

pkgs.python3Packages.buildPythonApplication {
  pname = "load";
  src = ./.;
  version = "0.3.0";
  propagatedBuildInputs = with pkgs.python38Packages; [
    python-dotenv
    joblib
    multiprocess
  ];
}
