"""automatics."""

__version__ = "0.0.4"

from . import element, geom, rd
from .calc import Model
from .geom import Geometry
from .ident import Identity
from .view import View

__all__ = [
    "Geometry",
    "Identity",
    "Model",
    "View",
    "element",
    "geom",
    "rd",
]
