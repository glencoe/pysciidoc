"""Use inspection to create high-level object representations of docstrings."""

import inspect as _insp
from dataclasses import dataclass, field
from typing import Literal, Any
from types import ModuleType, MethodType, FunctionType
from ._functools import curry_or as _curry_or, dispatching_fn as _dispatching_fn
from .python_type_formatters import SignatureFormatter


@dataclass
class ObjectDoc:
    """High-level representation of a doc string.

    Objects of this type are formatted to asciidoc in a later step.
    Depending on `kind` signature will be either the signature of
    a callable (class, function) or an empty string (module).

    Though not implemented right now, examples, args, returns fields
    should contain the corresponding lines of text from a docstring
    in google style format.

    As such

    ```python
    def fn():
    '''
        Examples:
          my example
          with a second line


        Args:
          arg0: explanation
          arg1: explanation

        Returns:
          my value
    '''
      pass
    ```

    should be parsed into

    ```
        ObjectDoc(
            kind="function",
            short_descr="",
            long_descr="",
            signature="()",
            examples="my example\nwith a second line",
            args={'arg0': "explanation", 'arg1': "explanation"},
            returns="my value",
            children=[]
        )
    ```
    """

    kind: Literal["function", "class", "module"]
    qualified_name: str
    short_descr: str
    long_descr: str
    signature: str
    examples: str
    args: dict[str, str]
    returns: str
    children: list["ObjectDoc"] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.qualified_name.split(".")[-1]

    @staticmethod
    def from_symbol(symbol: Any) -> "ObjectDoc":
        return _ObjectDocBuilder.build(symbol)


class _ObjectDocBuilder:
    def __init__(self) -> None:
        self._txt: list[str] = []
        self._children: list[ObjectDoc] = []

    def _process_symbol(self, symbol: Any) -> ObjectDoc:
        def is_user_routine(s: Any) -> bool:
            return _insp.isroutine(s) and not (
                _insp.isbuiltin(s) or _insp.ismethodwrapper(s)
            )

        process_children = _dispatching_fn(
            (self._process_routine_children, is_user_routine),
            (self._process_module_children, _insp.ismodule),
            (self._process_class_children, _insp.isclass),
        )
        process_children(symbol)
        process = _dispatching_fn(
            (self._process_class, _insp.isclass),
            (self._process_module, _insp.ismodule),
            (self._process_routine, is_user_routine),
        )
        return process(symbol)

    def _set_txt(self, symbol):
        text = _insp.getdoc(symbol)
        if text is None:
            text = ""
        self._txt = text.splitlines()

    def _get_long_descr(self) -> str:
        long_descr = ""
        text = self._txt
        if len(text) > 2:
            long_descr = "\n".join([line.strip() for line in text[2:]])
        return long_descr

    def _get_short_descr(self) -> str:
        return self._txt[0] if len(self._txt) > 0 else ""

    def _get_signature(self, symbol) -> str:
        return _dispatching_fn(
            (
                self._get_routine_signature,
                _curry_or(_insp.isroutine, _insp.isclass),
            ),
            (self._get_module_signature, _insp.ismodule),
        )(symbol)

    def _get_routine_signature(self, routine) -> str:
        return SignatureFormatter().format(_insp.signature(routine))

    def _get_module_signature(self, module) -> str:
        return ""

    @staticmethod
    def _get_defined_names(cls_: type) -> set[str]:
        names = set()
        for name, obj in vars(cls_).items():
            if _insp.isroutine(obj):
                names.add(name)
        return names

    @staticmethod
    def _is_magic(name: str) -> bool:
        return name.startswith("__") and name.endswith("__")

    @staticmethod
    def _is_private(name: str) -> bool:
        return name.startswith("_") and not _ObjectDocBuilder._is_magic(name)

    @staticmethod
    def _has_docs(symbol) -> bool:
        docs = _insp.getdoc(symbol)
        return docs is not None and docs != ""

    def _filter_relevant_children(
        self,
        pairs: tuple[
            tuple[str, Any],
            ...,
        ],
    ):
        for name, obj in pairs:
            if not self._is_private(name):
                yield name, obj

    @staticmethod
    def _symbol_is_defined_in_module(module: ModuleType, symbol: Any) -> bool:
        if hasattr(symbol, "__module__"):
            return module.__name__ == symbol.__module__  # type: ignore
        else:
            return False

    def _process_module_children(self, symbol: ModuleType) -> None:
        for name, obj in vars(symbol).items():
            if (
                (_insp.isroutine(obj) or _insp.isclass(obj))
                and self._symbol_is_defined_in_module(symbol, obj)
                and not self._is_private(name)
            ):
                self._children.append(self.build(obj))

    def _process_class_children(self, symbol: type) -> None:
        for name, obj in vars(symbol).items():
            if _insp.isroutine(obj) and not self._is_private(name):
                self._children.append(self.build(obj))

    def _process_routine_children(self, routine) -> None:
        self._children.clear()

    def _process_routine(self, symbol: MethodType | FunctionType) -> ObjectDoc:
        return ObjectDoc(
            kind="function",
            qualified_name=f"{symbol.__module__}.{symbol.__qualname__}",
            signature=self._get_signature(symbol),
            short_descr=self._get_short_descr(),
            long_descr=self._get_long_descr(),
            examples="",
            args=dict(),
            returns="",
            children=self._children,
        )

    def _process_module(self, symbol: ModuleType) -> ObjectDoc:
        return ObjectDoc(
            kind="module",
            qualified_name=symbol.__name__,
            short_descr=self._get_short_descr(),
            long_descr=self._get_long_descr(),
            signature="",
            examples="",
            args=dict(),
            returns="",
            children=self._children,
        )

    def _process_class(self, symbol: type) -> ObjectDoc:
        return ObjectDoc(
            kind="class",
            qualified_name=f"{symbol.__module__}.{symbol.__qualname__}",
            short_descr=self._get_short_descr(),
            long_descr=self._get_long_descr(),
            signature=self._get_signature(symbol),
            examples="",
            args=dict(),
            returns="",
            children=self._children,
        )

    def __call__(self, symbol: Any) -> ObjectDoc:
        self._set_txt(symbol)
        return self._process_symbol(symbol)

    @staticmethod
    def build(symbol: Any) -> ObjectDoc:
        return _ObjectDocBuilder()(symbol)
