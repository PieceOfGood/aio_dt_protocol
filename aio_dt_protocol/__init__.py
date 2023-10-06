
__version__ = "1.3.0"
__author__ = "PieceOfGood"
__email__ = "78sanchezz@gmail.com"

__all__ = [
    "find_instances",
    "CMDFlags",
    "FlagBuilder",
    "Browser",
    "Connection",
    "BrowserName",
    "Serializer",
]

from .browser import CMDFlags
from .browser import FlagBuilder
from .browser import Browser
from .connection import Connection
from .utils import find_instances
from .data import Serializer


class BrowserName:
    CHROME = "chrome"
    CHROMIUM = "chromium"
    BRAVE = "brave"
    EDGE = "edge"
