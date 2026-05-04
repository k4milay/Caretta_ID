"""Lightweight DI container.

Agents and services are registered as factories and resolved lazily so tests
can swap implementations (e.g. fake feature extractor) without monkey-patching.
"""
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class Container:
    def __init__(self) -> None:
        self._factories: dict[type, Callable[[], Any]] = {}
        self._singletons: dict[type, Any] = {}

    def register(self, key: type[T], factory: Callable[[], T], *, singleton: bool = True) -> None:
        self._factories[key] = factory
        if not singleton and key in self._singletons:
            del self._singletons[key]

    def resolve(self, key: type[T]) -> T:
        if key in self._singletons:
            return self._singletons[key]
        if key not in self._factories:
            raise KeyError(f"No factory registered for {key.__name__}")
        instance = self._factories[key]()
        self._singletons[key] = instance
        return instance


container = Container()
