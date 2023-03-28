
__version__ = '1.0.0'

__all__ = [
    "find_instances",
    "CMDFlags",
    "BrowserEx",
    "PageEx",
    "catch_headers_for_url"
]

__author__ = "PieceOfGood"

from .Browser import CMDFlags
from .Browser import Browser
from .BrowserEx import BrowserEx
from .PageEx import PageEx, catch_headers_for_url

find_instances = Browser.FindInstances
