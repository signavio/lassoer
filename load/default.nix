{ pkgs ?
  import (fetchTarball "http://nixos.org/channels/nixos-20.09/nixexprs.tar.xz")
  { } }:

pkgs.python38Packages.buildPythonApplication {
  pname = "load";
  src = ./.;
  version = "0.3.0";
  buildInputs = [ pkgs.sqlite ];
  propagatedBuildInputs = with pkgs.python38Packages; [
    boto3
    psycopg2
    pyarrow
    python-dotenv
    sqlalchemy
  ];
  postInstall = ''
    ln -sf "${pkgs.sqlite}/bin/sqlite3" "$out/bin/"
  '';
  doInstallCheck = true;
  installCheckPhase = ''
    PATH=$PATH:$out/bin
    ${pkgs.bash}/bin/bash tests/test_load
  '';
}
