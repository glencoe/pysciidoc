import pkgutil as _pu


def discover_modules(package: str) -> list[_pu.ModuleInfo]:
    root = _pu.resolve_name(package).__path__
    modules = []
    for m in _pu.walk_packages(root, prefix=f"{package}."):
        modules.append(m)

    return modules
