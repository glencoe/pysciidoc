from .objectdoc import ObjectDoc
from .generate import generate_ascii_doc
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


def generate_documentation(docs: Iterable[ObjectDoc], output_dir: Path) -> None:
    """Generate and write AsciiDoc documentation."""
    for doc in docs:
        for filename, txt in generate_ascii_doc(doc):
            filename = f"{filename}.adoc"

            with open(output_dir / filename, "w") as f:
                click.echo(txt, file=f)


@click.command()
@click.argument("package_name")
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default="pysciidocs",
    help="Output directory (default: pysciidocs)",
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed progress")
def main(package_name: str, output: Path, verbose: bool) -> None:
    """Generate AsciiDoc documentation for a Python package.

    PACKAGE_NAME: The name of the package to document
    """
    modules = discover_package_modules(package_name)
    docs = []
    for m in modules:
        docs.append(ObjectDoc.from_symbol(m))
    generate_documentation(docs, output)


if __name__ == "__main__":
    main()
