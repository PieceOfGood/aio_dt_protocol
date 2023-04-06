
__version__ = "0.9.0"
__author__ = "PieceOfGood"
__email__ = "78sanchezz@gmail.com"

__all__ = [
    "find_instances",
    "CMDFlags",
    "BrowserEx",
    "PageEx",
    "catch_headers_for_url"
]

from .Browser import CMDFlags
from .Browser import Browser
from .BrowserEx import BrowserEx
from .PageEx import PageEx, catch_headers_for_url

find_instances = Browser.FindInstances
