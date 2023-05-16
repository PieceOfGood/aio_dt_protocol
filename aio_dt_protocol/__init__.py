
__version__ = "0.9.4"
__author__ = "PieceOfGood"
__email__ = "78sanchezz@gmail.com"

__all__ = [
    "find_instances",
    "CMDFlags",
    "FlagBuilder",
    "BrowserEx",
    "PageEx",
    "catch_headers_for_url"
]

from .Browser import CMDFlags
from .Browser import FlagBuilder
from .Browser import Browser
from .BrowserEx import BrowserEx
from .PageEx import PageEx, catch_headers_for_url

find_instances = Browser.FindInstances
