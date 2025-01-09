"""Use inspection to create high-level object representations of docstrings."""

import inspect as _insp
from dataclasses import dataclass, field
from typing import Literal, Any
from types import ModuleType, MethodType, FunctionType
from ._functools import dispatching_fn as _dispatching_fn
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
    module: str
    short_descr: str
    long_descr: str
    signature: str
    examples: str
    args: dict[str, str]
    returns: str
    inherited_from: list[tuple[str, str]] = field(default_factory=list)
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

        process_children = _dispatching_fn(
            (self._process_routine_children, self._is_valid_routine),
            (self._process_module_children, _insp.ismodule),
            (self._process_class_children, _insp.isclass),
            (lambda x: None, lambda x: True),
        )
        process_children(symbol)
        process = _dispatching_fn(
            (self._process_class, _insp.isclass),
            (self._process_module, _insp.ismodule),
            (self._process_routine, self._is_valid_routine),
            (lambda x: None, lambda x: True),
        )
        return process(symbol)

    @staticmethod
    def _find_first_base_class_that_defines_method(_cls: type, method_name: str) ->  type | None:
        for base in _insp.getmro(_cls):
            if hasattr(base, method_name):
                return base
        return None
    
    @staticmethod
    def _docstring_is_inherited(symbol: Any, docstring: str) -> bool:
        if symbol.__doc__ is None and docstring is not None:
            return True
        return False

    def _handle_inherited_docstring(self, symbol: Any, docstring: str) -> str:
        if self._docstring_is_inherited(symbol, docstring):
            return ""
        return docstring

    def _set_txt(self, symbol):
        text = _insp.getdoc(symbol)
        text = self._handle_inherited_docstring(symbol, text)
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
                self._is_valid_routine,
            ),
            (lambda x: "", lambda x: True),
        )(symbol)

    def _get_routine_signature(self, routine) -> str:
        return SignatureFormatter().format(_insp.signature(routine))

    def _get_defined_names(self, cls_: type) -> set[str]:
        names = set()
        for name, obj in vars(cls_).items():
            if self._is_valid_routine(obj):
                names.add(name)
        return names

    @staticmethod
    def _is_magic(name: str) -> bool:
        return name.startswith("__") and name.endswith("__")

    @staticmethod
    def _is_private(name: str) -> bool:
        return name.startswith("_") and not _ObjectDocBuilder._is_magic(name)

    @staticmethod
    def _symbol_is_defined_in_module(module: ModuleType| str, symbol: Any) -> bool:
        if isinstance(module, str):
            module_name = module
        else:
            module_name = module.__name__
        if hasattr(symbol, "__module__"):
            return module_name == symbol.__module__  # type: ignore
        else:
            return False

    @classmethod
    def _is_valid_routine(cls, obj: Any) -> bool:
        return (
            _insp.isfunction(obj) and hasattr(obj, "__module__") and hasattr(obj, "__name__")
            and not cls._is_private(obj.__name__) 
            and cls._symbol_is_defined_in_module(obj.__module__, obj)
        )

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
            if self._is_valid_routine(obj):
                self._children.append(self.build(obj))

    def _process_routine_children(self, routine) -> None:
        self._children.clear()

    def _process_routine(self, symbol: MethodType | FunctionType) -> ObjectDoc:
        inherited_from = []
        base = _ObjectDocBuilder._find_first_base_class_that_defines_method(symbol.__class__, symbol.__name__)
        if base is not None and base is not object:
            inherited_from.append((base.__module__, base.__name__))

        return ObjectDoc(
            kind="function",
            qualified_name=f"{symbol.__module__}.{symbol.__qualname__}",
            module=symbol.__module__,
            signature=self._get_signature(symbol),
            short_descr=self._get_short_descr(),
            long_descr=self._get_long_descr(),
            examples="",
            args=dict(),
            returns="",
            children=self._children,
            inherited_from=inherited_from,
        )

    def _process_module(self, symbol: ModuleType) -> ObjectDoc:
        return ObjectDoc(
            kind="module",
            qualified_name=symbol.__name__,
            short_descr=self._get_short_descr(),
            long_descr=self._get_long_descr(),
            module=symbol.__name__,
            signature="",
            examples="",
            args=dict(),
            returns="",
            children=self._children,
            inherited_from=[],
        )

    def _process_class(self, symbol: type) -> ObjectDoc:
        inherited_from = []
        for base in symbol.__bases__:
            if base is not object:
                inherited_from.append((base.__module__, base.__name__))
        return ObjectDoc(
            kind="class",
            qualified_name=f"{symbol.__module__}.{symbol.__qualname__}",
            short_descr=self._get_short_descr(),
            long_descr=self._get_long_descr(),
            signature=self._get_signature(symbol),
            module=symbol.__module__,
            examples="",
            args=dict(),
            returns="",
            children=self._children,
            inherited_from=inherited_from,
        )

    def __call__(self, symbol: Any) -> ObjectDoc:
        self._set_txt(symbol)
        return self._process_symbol(symbol)

    @staticmethod
    def build(symbol: Any) -> ObjectDoc:
        return _ObjectDocBuilder()(symbol)
