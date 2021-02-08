{ pkgs ? import
  (fetchTarball "http://nixos.org/channels/nixos-unstable/nixexprs.tar.xz") { }
}:

let
  archive = (pkgs.writeShellScriptBin "archive"
    (builtins.readFile "/home/sd/projects/lassoer/archive/archive"));

in pkgs.stdenv.mkDerivation {
  name = "archive";
  src = ./.;
  version = "0.2.0";
  buildInputs = [ pkgs.age pkgs.pigz ];
  installPhase = ''
    mkdir -p $out/bin
    export PATH="${pkgs.age}/bin:${pkgs.pigz}/bin:$PATH"
    echo $PATH
    ln -sf ${pkgs.age}/bin/age $out/bin/
    ln -sf ${pkgs.age}/bin/age-keygen $out/bin/
    ln -sf ${pkgs.pigz}/bin/pigz $out/bin/
    ln -sf ${archive}/bin/archive $out/bin/
  '';
  doInstallCheck = false;
  installCheckPhase = ''
    export PATH=$out/bin:$PATH
    ${pkgs.bash}/bin/bash tests/test_archive
  '';
}
