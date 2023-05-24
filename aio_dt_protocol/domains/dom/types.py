from dataclasses import dataclass
from typing import Optional


@dataclass
class StyleProp:
    """ Описывает имя и значение стиля """
    name: str
    value: str


@dataclass
class NodeCenter:
    x: int
    y: int



@dataclass
class NodeRect:
    """ Пространственное положение и размеры узла """
    x: int
    y: int
    width: int
    height: int
    left: int
    right: int
    top: int
    bottom: int



@dataclass
class ShapeOutsideInfo:
    bounds: list
    shape: list
    marginShape: list


@dataclass
class BoxModel:
    content: list
    padding: list
    border: list
    margin: list
    width: int
    height: int
    shapeOutside: Optional[ShapeOutsideInfo] = None
