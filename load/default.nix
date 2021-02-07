{ pkgs ?
  import (fetchTarball "http://nixos.org/channels/nixos-20.09/nixexprs.tar.xz")
  { } }:

pkgs.python38Packages.buildPythonApplication {
  pname = "load";
  src = ./.;
  version = "0.3.0";
  propagatedBuildInputs = with pkgs.python38Packages; [
    boto3
    joblib
    multiprocess
    pyarrow
    python-dotenv
    sqlalchemy
  ];
}
