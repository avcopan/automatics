"""automatics."""

__version__ = "0.0.3"

from . import element, geom, rd
from .calc import Calculation
from .geom import Geometry
from .ident import Identity
from .view import View

__all__ = ["Calculation", "Geometry", "Identity", "View", "element", "geom", "rd"]
