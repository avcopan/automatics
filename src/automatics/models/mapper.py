"""Mapper registry."""

from collections.abc import Callable
from typing import Any, overload

type TargetType = type | str

_MAPPERS: dict[tuple[str, str], Callable[[Any], Any]] = {}


class MapperNotFoundError(Exception):
    """Raise an error when object mapper is not registered."""

    def __init__(self, inp: str, out: str) -> None:
        message = f"No registered mapper found for converting {inp} to {out}."
        super().__init__(message)


def _get_type_fullname[T](datatype: T) -> str:
    """Get a fully qualified type string, e.g. `qcdata.Structure`."""
    if isinstance(datatype, str):
        return datatype

    module = getattr(datatype, "__module__", "")
    name = getattr(datatype, "__qualname__", getattr(datatype, "__name__", ""))
    return f"{module}.{name}" if module and module != "builtins" else name


def register_mapper(
    inp_type: TargetType, out_type: TargetType
) -> Callable[[Callable[[Any], Any]], Callable[[Any], Any]]:
    """Register a conversion function mapping an input type to an output type."""
    inp_str = _get_type_fullname(inp_type)
    out_str = _get_type_fullname(out_type)

    def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
        _MAPPERS[(inp_str, out_str)] = func
        return func

    return decorator


@overload
def convert_from[InternalT, ExternalT](
    obj: InternalT, target_type: type[ExternalT]
) -> ExternalT: ...


@overload
def convert_from[InternalT](obj: InternalT, target_type: str) -> str: ...


def convert_from(obj: Any, *, target_type: TargetType) -> Any:
    """Convert an object dynamically to a target type or formatted string."""
    inp_str = _get_type_fullname(type(obj))
    out_str = _get_type_fullname(target_type)

    if (inp_str, out_str) in _MAPPERS:
        return _MAPPERS[(inp_str, out_str)](obj)

    if (out_str, inp_str) in _MAPPERS:
        return _MAPPERS[(out_str, inp_str)](obj)

    raise MapperNotFoundError(inp=inp_str, out=out_str)
