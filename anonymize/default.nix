{ pkgs ?
  import (fetchTarball "http://nixos.org/channels/nixos-20.09/nixexprs.tar.xz")
  { } }:

let
  nodeDependencies =
    (pkgs.callPackage ./node-composition.nix { }).shell.nodeDependencies;

in pkgs.stdenv.mkDerivation {
  name = "anonymize";
  version = "0.2.0";
  src = ./.;
  buildInputs = [ pkgs.nodejs ];
  installPhase = ''
    mkdir -p $out/bin
    ln -s ${nodeDependencies}/lib/node_modules $out/bin/node_modules
    export PATH="${nodeDependencies}/bin:$PATH"

    cp anonymize $out/bin/
  '';
  doInstallCheck = true;
  installCheckPhase = ''
    export PATH=$out/bin:$PATH
    ${pkgs.bash}/bin/bash tests/test_anonymize
  '';
}
