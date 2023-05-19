
__version__ = "0.9.5"
__author__ = "PieceOfGood"
__email__ = "78sanchezz@gmail.com"

__all__ = [
    "find_instances",
    "CMDFlags",
    "FlagBuilder",
    "BrowserEx",
    "PageEx"
]

from .Browser import CMDFlags
from .Browser import FlagBuilder
from .BrowserEx import BrowserEx
from .PageEx import PageEx
from .utils import find_instances
