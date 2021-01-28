{ pkgs ?
  import (fetchTarball "http://nixos.org/channels/nixos-20.09/nixexprs.tar.xz")
  { } }:

let
  pythonEnv =
    pkgs.python38.withPackages (pypkg: [ pypkg.python-dotenv pypkg.joblib ]);
in pkgs.mkShell { buildInputs = [ pythonEnv ]; }
