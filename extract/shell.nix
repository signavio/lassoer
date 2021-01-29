{ pkgs ?
  import (fetchTarball "http://nixos.org/channels/nixos-20.09/nixexprs.tar.xz")
  { } }:

pkgs.mkShell { buildInputs = [ pkgs.jdk11 ]; }
