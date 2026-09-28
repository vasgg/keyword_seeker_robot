from typing import Any, Generic, TypeAlias, TypeVar

T = TypeVar("T", covariant=True)  # Success type
E = TypeVar("E", covariant=True)  # Error type


class Err(Generic[E]):
    """
    A value that signifies failure and which stores arbitrary data for the error.
    """

    __match_args__ = ("value",)
    __slots__ = ("value",)

    def __init__(self, value: E) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"Err({repr(self.value)})"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Err) and self.value == other.value


class Ok(Generic[T]):
    """
    A value that indicates success and which stores arbitrary data for the return value.
    """

    __match_args__ = ("value",)
    __slots__ = ("value",)

    def __init__(self, value: T) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"Ok({repr(self.value)})"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Ok) and self.value == other.value


Result: TypeAlias = Ok[T] | Err[E]
