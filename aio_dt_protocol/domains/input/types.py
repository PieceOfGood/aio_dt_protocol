from dataclasses import dataclass
from typing import Optional


@dataclass
class TouchPoint:
    """ Описывает точку прикосновения стилуса для метода DispatchTouchEvent() """
    x: float
    y: float                                # Координаты точки касания
    radiusX: Optional[float] = None         # X-радиус прикосновения(по умолчанию 1.0)
    radiusY: Optional[float] = None         # Y-радиус прикосновения(по умолчанию 1.0)
    rotationAngle: Optional[float] = None   # Угол вращения(по умолчанию 0.0)
    force: Optional[float] = None           # Сила(по умолчанию 1.0)
    tangentialPressure: Optional[float] = None  # Нормализованное тангенциальное давление в
                                                #   диапазоне [-1,1](по умолчанию 0.0)
    tiltX: Optional[int] = None             # Угол между плоскостью Y-Z и плоскостью,
                                                #   содержащей ось стилуса и ось Y, в градусах
                                                #   диапазона [-90,90], положительный tiltX
                                                #   - наклон вправо (по умолчанию: 0).
    tiltY: Optional[int] = None             # Угол между плоскостью X-Z и плоскостью,
                                                #   содержащей ось стилуса и ось X, в градусах
                                                #   диапазона [-90,90], положительный tiltY
                                                #   - наклон вниз (по умолчанию: 0).
    twist: Optional[int] = None             # Поворот стилуса пера по часовой стрелке вокруг
                                                #   своей главной оси в градусах в диапазоне
                                                #   [0,359] (по умолчанию: 0).
    id: Optional[float] = None              # Идентификатор, используемый для отслеживания
                                                #   источников касания между событиями, должен
                                                #   быть уникальным в пределах события.
    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}
