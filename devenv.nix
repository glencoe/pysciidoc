
{
  pkgs,
  lib,
  config,
  inputs,
  ...
}: {
  packages = [
    pkgs.jujutsu
    pkgs.antora
    pkgs.kramdown-asciidoc
  ];

  languages.python = {
    enable = true;
    uv.enable = true;
    version = "3.10";
    uv.sync.enable = true;
  };

  starship.enable = true;
  tasks = {
    "testing:pytest" = {
      exec = "${pkgs.uv}/bin/uv run pytest";
      before = ["devenv:enterTest"];

    };

    "testing:mypy" = {
      exec = "${pkgs.uv}/bin/uv run mypy";
      before = ["devenv:enterTest"];
    };

    "build:package" = {
      exec = "${pkgs.uv}/bin/uv build";
      before = ["build:all"];
    };

    "build:docs" = let
       out_dir = "docs/modules/api/pages";
       nav_file = "docs/modules/nav.adoc";
       pkg_name = "pysciidoc";
     in {
      exec = ''
        ${pkgs.kramdown-asciidoc}/bin/kramdoc README.md -o docs/modules/ROOT/pages/jjreadme.adoc
        ${pkgs.uv}/bin/uv run pysciidoc --api-output-dir ${out_dir} --nav-file ${nav_file} ${pkg_name}
        ${pkgs.antora}/bin/antora docs/antora-playbook.yml
      '';
      before = ["build:all"];
    };

    "clean:dist" = {
      exec = ''
        if [ -d dist ]; then
          rm -r dist
        fi
      '';
      before = ["clean:all"];
    };

    "clean:docs" = let
      out_dir = "docs/modules/api/pages";
      nav_file = "docs/modules/nav.adoc";
    in
      {

      exec = ''
        if [ -d ${out_dir} ]; then
          rm -r ${out_dir}
        fi
        if [ -e ${nav_file} ]; then
          rm ${nav_file}
        fi
        '';
        before = ["clean:all" "build:docs"];
      };

    "build:all" = {};
    "clean:all" = {};
  };

}
