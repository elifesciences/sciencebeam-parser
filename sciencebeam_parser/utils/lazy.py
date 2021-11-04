from abc import abstractmethod
from typing import Callable, Generic, Optional, TypeVar


T = TypeVar('T')


class Preloadable:
    @abstractmethod
    def preload(self):
        raise NotImplementedError()


class LazyLoaded(Generic[T]):
    def __init__(self, factory: Callable[[], T]):
        super().__init__()
        self.factory = factory
        self._value: Optional[T] = None

    def __repr__(self) -> str:
        return '%s(_value=%r)' % (
            type(self).__name__, self._value
        )

    @property
    def is_loaded(self) -> bool:
        return self._value is not None

    def get(self) -> T:
        if self._value is None:
            self._value = self.factory()
            assert self._value is not None
        return self._value
