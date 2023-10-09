from dataclasses import dataclass
from typing import Optional


@dataclass
class WindowInfo:
    windowId: int
    bounds: "Bounds"


@dataclass
class Bounds:
    """ Описывает положение, размер и состояние окна браузера """
    left: Optional[int] = None              # Смещение от левого края экрана до окна в пикселях.
    top: Optional[int] = None               # Смещение от верхнего края экрана к окну в пикселях.
    width: Optional[int] = None             # Ширина окна в пикселях.
    height: Optional[int] = None            # Высота окна в пикселях.
    windowState: Optional[str] = "normal"   # normal, minimized, maximized, fullscreen
                                        #   minimized, maximized и fullscreen нельзя сочетать с  left, top,
                                        #   width или height. Неопределенные поля останутся без изменений.

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class Version:
    protocolVersion: str
    product: str
    revision: str
    userAgent: str
    jsVersion: str
