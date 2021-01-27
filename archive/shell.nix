{ pkgs ? import
  (fetchTarball "http://nixos.org/channels/nixos-unstable/nixexprs.tar.xz") { }
}:

let
  archive = (pkgs.writeShellScriptBin "archive"
    (builtins.readFile "/home/sd/projects/lassoer/archive/archive"));

in pkgs.mkShell { buildInputs = [ archive pkgs.age pkgs.pigz ]; }
