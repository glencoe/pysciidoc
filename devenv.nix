
{
  pkgs,
  lib,
  config,
  inputs,
  ...
}: {
  packages = [
    pkgs.jujutsu
    pkgs.asciidoctor-with-extensions
    pkgs.antora
  ];

  languages.python = {
    enable = true;
    uv.enable = true;
    version = "3.10";
    uv.sync.enable = true;
  };

  starship.enable = true;
  tasks = {
    "bash:pytest" = {
      exec = "${pkgs.uv}/bin/uv run pytest";
      after = ["devenv:enterTest"];
    };

    "bash:mypy" = {
      exec = "${pkgs.uv}/bin/uv run mypy";
      after = ["devenv:enterTest"];
    };
  };
}
