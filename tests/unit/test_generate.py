from pysciidoc.generate import generate_ascii_doc
from pysciidoc.objectdoc import ObjectDoc


class TestGeneratingAsciiDocForFunction:
    def test_function(self):
        doc = ObjectDoc(
            kind="function",
            signature="()",
            qualified_name="my_module.my_class.my_func",
            short_descr="short descr.",
            long_descr="long desc\nover\nmany lines\n",
            examples="",
            args={},
            returns="",
        )

        actual = generate_ascii_doc(doc)
        assert (
            actual
            == """[[my_module.my_class.my_func]]<<#my_module.my_class.my_func, `**my_func**()`>>::
short descr.
+
long desc
over
many lines
"""
        )

    def test_method_and_class(self):
        doc = ObjectDoc(
            kind="class",
            signature="()",
            qualified_name="m.A",
            short_descr="my class A.",
            long_descr="a longer\ntext\n",
            examples="",
            args=dict(),
            returns="",
            children=[
                ObjectDoc(
                    qualified_name="m.A.f",
                    kind="function",
                    short_descr="i'm a method.",
                    long_descr="i live inside\nclass A.",
                    signature="(txt: str) -> int",
                    examples="",
                    args={},
                    returns="",
                )
            ],
        )
        asciidoc = generate_ascii_doc(doc)
        assert asciidoc == (
            "[[m.A]]<<#m.A, `**A**()`>>::\n"
            "my class A.\n+\n"
            "a longer\ntext\n\n"
            "[[m.A.f]]<<#m.A.f, `**f**(txt: str) -> int`>>:::\n"
            "i'm a method.\n+\n"
            "i live inside\nclass A."
        )
