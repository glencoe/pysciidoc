from pytest import fixture

from pysciidoc.generate import generate_ascii_doc
from pysciidoc.objectdoc import ObjectDoc


def short_descr_fn(arg):
    """short description."""
    pass


@fixture
def actual(obj) -> ObjectDoc:
    return extract(obj)


def extract(symbol) -> ObjectDoc:
    return ObjectDoc.from_symbol(symbol)


class Base:
    def build_expected_name(self, rest: str) -> str:
        return f"{self.__module__}.{self.__class__.__name__}.{rest}"

    def test_short_descr(self, actual: ObjectDoc, expected: ObjectDoc):
        assert actual.short_descr == expected.short_descr

    def test_name(self, actual: ObjectDoc, expected: ObjectDoc):
        assert actual.qualified_name == expected.qualified_name

    def test_type(self, actual: ObjectDoc, expected: ObjectDoc):
        assert actual.kind == expected.kind

    def test_long_descr(self, actual: ObjectDoc, expected: ObjectDoc):
        assert actual.long_descr == expected.long_descr

    def test_signature(self, actual: ObjectDoc, expected: ObjectDoc):
        assert actual.signature == expected.signature

    def test_children(self, actual: ObjectDoc, expected: ObjectDoc):
        assert actual.children == expected.children


class TestSimpleFunctionObjectDocExtraction(Base):
    def expected_name(self):
        return self.build_expected_name("obj.<locals>._obj")

    @fixture
    def expected(self) -> ObjectDoc:
        d = ObjectDoc(
            kind="function",
            qualified_name=self.expected_name(),
            signature="(args)",
            short_descr="short description.",
            long_descr="",
            examples="",
            args=dict(),
            returns="",
        )
        return d

    @fixture
    def obj(self) -> object:
        def _obj(args):
            """short description."""
            pass

        return _obj


class TestFunctionWithLongDescription(Base):
    def expected_name(self) -> str:
        return self.build_expected_name("obj.<locals>._obj")

    @fixture
    def expected(self) -> ObjectDoc:
        return ObjectDoc(
            kind="function",
            qualified_name=self.expected_name(),
            long_descr="a longer description\nwith a new line",
            short_descr="other descr.",
            signature="(args)",
            examples="",
            args=dict(),
            returns="",
        )

    @fixture
    def obj(self) -> object:
        def _obj(args):
            """other descr.

            a longer description
            with a new line
            """

        return _obj


class TestClassWithLongDescription(Base):
    def expected_name(self) -> str:
        return self.build_expected_name("obj.<locals>.Obj")

    @fixture
    def expected(self) -> ObjectDoc:
        return ObjectDoc(
            kind="class",
            qualified_name=self.expected_name(),
            signature="(args)",
            long_descr="another long description",
            short_descr="new class.",
            examples="",
            args=dict(),
            returns="",
            children=[
                ObjectDoc(
                    kind="function",
                    qualified_name=f"{self.expected_name()}.__init__",
                    signature="(self, args)",
                    long_descr="",
                    short_descr="",
                    examples="",
                    args=dict(),
                    returns="",
                )
            ],
        )

    @fixture
    def obj(self) -> object:
        class Obj:
            """new class.

            another long description
            """

            def __init__(self, args):
                pass

        return Obj


class TestExtractingMethodFromClass(Base):
    def expected_name(self) -> str:
        return self.build_expected_name("obj.<locals>.Obj")

    @fixture
    def expected(self, obj) -> ObjectDoc:
        return ObjectDoc(
            kind="class",
            qualified_name=self.expected_name(),
            long_descr="",
            short_descr="other descr.",
            signature="()",
            examples="",
            args=dict(),
            returns="",
            children=[
                ObjectDoc(
                    kind="function",
                    long_descr="",
                    qualified_name=f"{self.expected_name()}.a",
                    short_descr="a method.",
                    signature="(self, number: int) -> int",
                    examples="",
                    args=dict(),
                    returns="",
                )
            ],
        )

    @fixture
    def obj(self) -> object:
        class Obj:
            """other descr."""

            def a(self, number: int) -> int:
                """a method."""
                return number

        return Obj
