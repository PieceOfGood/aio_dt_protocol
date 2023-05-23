
__version__ = "0.10.0"
__author__ = "PieceOfGood"
__email__ = "78sanchezz@gmail.com"

__all__ = [
    "find_instances",
    "CMDFlags",
    "FlagBuilder",
    # "BrowserEx",
    # "PageEx"
]

from .browser import CMDFlags
from .browser import FlagBuilder
# from .BrowserEx import BrowserEx
# from .PageEx import PageEx
from .utils import find_instances
