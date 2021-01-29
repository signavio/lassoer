{ pkgs ?
  import (fetchTarball "http://nixos.org/channels/nixos-20.09/nixexprs.tar.xz")
  { } }:

let
  pythonEnv = pkgs.python38.withPackages (pypkg: [
    pypkg.python-dotenv
    pypkg.joblib
    pypkg.boto3
    pypkg.pyarrow
    pypkg.sqlalchemy
  ]);
in pkgs.mkShell { buildInputs = [ pythonEnv ]; }
