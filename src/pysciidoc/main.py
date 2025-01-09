from .objectdoc import ObjectDoc
from .generate import generate_ascii_doc, generate_module_crossrefs
import click
from collections.abc import Iterable, Iterator
from types import ModuleType
from importlib import import_module
from pathlib import Path

import pkgutil as _pu


def discover_modules(package: str) -> list[_pu.ModuleInfo]:
    root = _pu.resolve_name(package).__path__
    modules = []
    for m in _pu.walk_packages(root, prefix=f"{package}."):
        modules.append(m)

    return modules


def discover_package_modules(package_name: str) -> Iterator[ModuleType]:
    """Discover all modules in a package with progress bar."""
    modules = discover_modules(package_name)

    def is_private(name: str):
        return name.split(".")[-1].startswith("_")

    names = []
    for _, name, _ in modules:
        if not is_private(name):
            names.append(name)
    click.echo(f"Found {len(names)} modules")
    return map(import_module, names)


def generate_documentation(docs: Iterable[ObjectDoc], output_dir: Path, package_name: str) -> None:
    """Generate and write AsciiDoc documentation."""
    output_dir.mkdir(exist_ok=True, parents=True)
    for doc in docs:
        for filename, txt in generate_ascii_doc(doc, package_name):
            filename = f"{filename}.adoc"

            with open(output_dir / filename, "w") as f:
                click.echo(txt, file=f)


def generate_navigation(docs: Iterable[ObjectDoc], out_file: Path, package_name) -> None:
    out_file.parent.mkdir(exist_ok=True, parents=True)
    with open(out_file, "w") as f:

        def write(txt: str) -> None:
            click.echo(txt, file=f)

        for line, level in generate_module_crossrefs(docs, package_name):
            write(f"*{'*'*level} {line}")


@click.command()
@click.argument("package_name")
@click.option(
    "--api-output-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default="docs/modules/api/pages",
    help="Output directory of generated api adoc files (default: docs/modules/api/pages)",
)
@click.option(
    "--nav-file",
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    default="docs/modules/api/nav.adoc",
    help="output file for navigation file (default: docs/module/api/nav.adoc)",
)
def main(package_name: str, api_output_dir: Path, nav_file: Path) -> None:
    """Generate AsciiDoc API documentation for a Python package.

    PACKAGE_NAME: The name of the package to document
    """
    modules = discover_package_modules(package_name)
    docs = []
    for m in modules:
        docs.append(ObjectDoc.from_symbol(m))
    generate_documentation(docs, api_output_dir, package_name)
    generate_navigation(docs, nav_file, package_name)


if __name__ == "__main__":
    main()
