
__version__ = "1.2.1"
__author__ = "PieceOfGood"
__email__ = "78sanchezz@gmail.com"

__all__ = [
    "find_instances",
    "CMDFlags",
    "FlagBuilder",
    "Browser",
    "Connection",
    "BrowserName"
]

from .browser import CMDFlags
from .browser import FlagBuilder
from .browser import Browser
from .connection import Connection
from .utils import find_instances


class BrowserName:
    CHROME = "chrome"
    CHROMIUM = "chromium"
    BRAVE = "brave"
    EDGE = "edge"
