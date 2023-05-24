
__version__ = "1.0.0"
__author__ = "PieceOfGood"
__email__ = "78sanchezz@gmail.com"

__all__ = [
    "find_instances",
    "CMDFlags",
    "FlagBuilder",
    "Browser",
    "Connection"
]

from .browser import CMDFlags
from .browser import FlagBuilder
from .browser import Browser
from .connection import Connection
from .utils import find_instances
