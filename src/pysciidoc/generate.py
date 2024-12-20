from .objectdoc import ObjectDoc
from typing import Iterator, Iterable
from string import Template


class AsciiDocGenerator:
    def __init__(self) -> None:
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
        )

    def _toc(self) -> str:
        return Template(""":toc: $toc_position
:toclevels: $toc_levels
""").substitute(toc_position=self.toc_position, toc_levels=3)

    def _short_descr(self) -> str:
        if self.current_doc.short_descr not in (None, ""):
            return f"[.lead]\n{self.current_doc.short_descr}"
        return ""

    def _build_basic_template(self) -> Template:
        return Template("""$define_id

[id={$id_name}]
== $title
$short_descr

$signature

$long_descr

:leveloffset: +1
$children
:leveloffset: -1

:!$id_name:
""")

    def _determine_children(self) -> Template:
        children: list[str] = []
        for child in self.current_doc.children:
            children.append(f"include::{{$id_name}}.{child.name}.adoc[]")
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

    def generate(self, d: ObjectDoc) -> str:
        self.current_doc = d
        children = self._determine_children().substitute(id_name=d.kind)
        template = self._build_basic_template()
        return template.substitute(
            define_id=self._define_id(),
            id_name=d.kind,
            title=self._get_title(),
            toc=self._toc(),
            short_descr=self._short_descr(),
            signature=self._get_signature(),
            long_descr=d.long_descr,
            children=children,
        )


def generate_ascii_doc(d: ObjectDoc) -> Iterator[tuple[str, str]]:
    """Generate formatted asciidoc content from a given `ObjectDoc` item."""

    generator = AsciiDocGenerator()

    def generate(d: ObjectDoc):
        for child in d.children:
            yield from generate(child)
        yield d.qualified_name, generator.generate(d)

    yield from generate(d)


def generate_module_crossrefs(
    docs: Iterable[ObjectDoc], prefix: str = "api"
) -> list[str]:
    def collect_all_modules(doc: ObjectDoc) -> Iterator[ObjectDoc]:
        if doc.kind == "module":
            yield doc
        for child in doc.children:
            yield from collect_all_modules(child)

    def collect_all_modules_from_docs(docs: Iterable[ObjectDoc]) -> Iterator[ObjectDoc]:
        for d in docs:
            yield from collect_all_modules(d)

    def name_qual_name_pairs(docs: Iterable[ObjectDoc]) -> Iterator[tuple[str, str]]:
        for d in docs:
            yield d.name, d.qualified_name

    modules = name_qual_name_pairs(collect_all_modules_from_docs(docs))
    crossrefs = []
    for name, qualified_name in modules:
        crossrefs.append(f"xref:api:{qualified_name}.adoc[{name}]")
    return crossrefs
