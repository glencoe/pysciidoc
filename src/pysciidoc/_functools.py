from typing import TypeVar, Any
from collections.abc import Callable


_T = TypeVar("_T")
_P = TypeVar("_P")


def curry_or(a: Callable[[_P], bool], b: Callable[[_P], bool]) -> Callable[[_P], bool]:
    def a_or_b(arg: _P) -> bool:
        return a(arg) or b(arg)

    return a_or_b


def curry_and(a: Callable[[_P], bool], b: Callable[[_P], bool]) -> Callable[[_P], bool]:
    def a_and_b(arg: _P) -> bool:
        return a(arg) and b(arg)

    return a_and_b


def dispatching_fn(
    *entries: tuple[Callable[[_P], _T], Callable[[Any], bool]],
) -> Callable[[Any], _T]:
    def call(arg: Any) -> _T:
        for fn, condition in entries:
            if condition(arg):
                return fn(arg)
        raise ValueError(f"could not process {arg}")

    return call
