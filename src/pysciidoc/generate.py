from .objectdoc import ObjectDoc
from typing import Iterator, Iterable
from string import Template
import logging


class AsciiDocGenerator:
    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)
        self.toc_position = "left"
        self.current_doc = ObjectDoc(
            kind="function",
            qualified_name="",
            short_descr="",
            long_descr="",
            signature="",
            examples="",
            args=dict(),
            returns="",
            module="",
        )

    def _toc(self) -> str:
        return Template(""":toc: $toc_position
:toclevels: $toc_levels
""").substitute(toc_position=self.toc_position, toc_levels=3)

    @staticmethod
    def _escape_dollars(s: str) -> str:
        return s.replace("$", "$$")

    def _short_descr(self) -> str:
        if self.current_doc.short_descr not in (None, ""):
            return f"[.lead]\n{self._escape_dollars(self.current_doc.short_descr)}"
        return ""

    def _build_basic_template(self) -> Template:
        return Template("""$define_id

[id={$id_name}]
= $title
$short_descr

$signature

$inheritance

$long_descr

:leveloffset: +1
$children
:leveloffset: -1

:!$id_name:
""")

    def _determine_children(self) -> Template:
        children: list[str] = []
        for child in self.current_doc.children:
            if child is not None:
                child_generator = AsciiDocGenerator()
                children.append(child_generator.generate(child, self.package_name))
        return Template("\n".join(children))

    def _define_id(self) -> str:
        definitions = {
            "module": ":module: {qualified_name}",
            "class": """ifndef::module[]
:class: {qualified_name}
endif::[]
ifdef::module[]
:class: {{module}}.{name}
endif::[]
""",
            "function": """ifndef::class[]
ifdef::module[]
:function: {{module}}.{name}
endif::[]
ifndef::module[]
:function: {qualified_name}
endif::[]
endif::[]
ifdef::class[]
:function: {{class}}.{name}
endif::[]
""",
        }
        doc = self.current_doc
        return definitions[doc.kind].format(
            qualified_name=doc.qualified_name, name=doc.name
        )

    def _get_title(self) -> str:
        name = self.current_doc.name
        kind = self.current_doc.kind
        return f"*_{kind}_* +{name}+"

    def _get_signature(self) -> str:
        if self.current_doc.signature == "":
            return ""
        else:
            return """[source, python]
----
{name}{signature}
----
""".format(signature=self.current_doc.signature, name=self.current_doc.name)

    def _get_long_descr(self) -> str:
        return self._escape_dollars(self.current_doc.long_descr)

    def _get_inheritance(self) -> str:
        if len(self.current_doc.inherited_from) == 0:
            return ""

        def contains_private_namespace(s: str) -> bool:
            for part in s.split("."):
                if part.startswith("_"):
                    return True
            return False

        def get_xref_if_possible(base_module: str, base_name: str) -> str:
            if base_module.startswith(
                self.package_name
            ) and not contains_private_namespace(f"{base_module}.{base_name}"):
                return (
                    f"xref::{base_module}.adoc#{base_module}.{base_name}[{base_name}]"
                )
            return f"{base_module}.{base_name}"

        if self.current_doc.kind == "class":
            bases = [".Base classes"]
            for module, name in self.current_doc.inherited_from:
                base = get_xref_if_possible(module, name)
                bases.append(f"* {base}")
            return "\n".join(bases)
        if self.current_doc.kind == "function":
            module, name = self.current_doc.inherited_from[0]
            base = get_xref_if_possible(module, name)
            if not base.startswith("builtins"):
                return f"Inherited from {base}"
        return ""

    def generate(self, d: ObjectDoc, package_name) -> str:
        logging.debug(f"Generating doc for {d.qualified_name}")
        self.current_doc = d
        self.package_name = package_name
        children = self._determine_children().substitute(id_name=d.kind)
        template = self._build_basic_template()
        return template.substitute(
            define_id=self._define_id(),
            id_name=d.kind,
            title=self._get_title(),
            toc=self._toc(),
            short_descr=self._short_descr(),
            signature=self._get_signature(),
            long_descr=self._get_long_descr(),
            inheritance=self._get_inheritance(),
            children=children,
        )


def generate_ascii_doc(d: ObjectDoc, package_name: str) -> Iterator[tuple[str, str]]:
    """Generate formatted asciidoc content from a given `ObjectDoc` item."""

    generator = AsciiDocGenerator()

    yield d.qualified_name, generator.generate(d, package_name=package_name)


def generate_module_crossrefs(
    docs: Iterable[ObjectDoc], package_name: str, prefix: str = ""
) -> list[tuple[str, int]]:
    logger = logging.getLogger(__name__)

    def collect_all_modules(doc: ObjectDoc) -> Iterator[ObjectDoc]:
        if doc.kind == "module":
            yield doc
        for child in doc.children:
            yield from collect_all_modules(child)

    def collect_all_modules_from_docs(docs: Iterable[ObjectDoc]) -> Iterator[ObjectDoc]:
        for d in docs:
            yield from collect_all_modules(d)

    tree: dict = {}

    def add_module_path(module_path: list[str], tree: dict) -> None:
        if len(module_path) == 0:
            tree["."] = None
            return
        tree[module_path[0]] = tree.get(module_path[0], {})
        add_module_path(module_path[1:], tree[module_path[0]])

    for qualname in (m.qualified_name for m in docs):
        qualname = qualname.removeprefix(f"{package_name}.")
        logger.debug(f"Adding module path {qualname}")

        module_path = qualname.split(".")
        add_module_path(module_path, tree)

    def produce_crossrefs(
        tree: dict, path: list[str], level: int
    ) -> Iterator[tuple[str, int]]:
        for key in tree:
            if key == ".":
                yield ".".join(path), level
            else:
                yield from produce_crossrefs(tree[key], path + [key], level + 1)

    crossrefs = []
    for name, level in produce_crossrefs(tree, [], 0):
        crossrefs.append((f"xref:{prefix}:{package_name}.{name}.adoc[{name}]", level))
    return crossrefs
