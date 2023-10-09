"""
    Набор вспомогательных методов, фокусированных на действиях в браузере.
"""

import asyncio
import random
from typing import Tuple, Optional, Literal
from .data import WINDOWS_KEY_SET, KeyModifiers, KeyEvents
from .domains.browser.types import Bounds


class Actions:
    __slots__ = ("_connection",)

    def __init__(self, conn) -> None:
        from .connection import Connection

        self._connection: Connection = conn

    async def swipeTo(
        self,
        direction: Literal["up", "down", "left", "right"],
        x:             Optional[float] = None,
        y:             Optional[float] = None,
        distance:      Optional[float] = None,
        speed:         Optional[float] = None,
        overscroll:    Optional[float] = None,
        repeatCount:     Optional[int] = None,
        repeatDelayMs: Optional[float] = None,
        gestureSourceType: Literal["touch", "mouse"] = "mouse"
    ) -> None:
        """ Скроллит вьюпорт жестом на всю его длину/высоту.
        Возвращает управление только после выполнения жеста!
        :param direction:           (optional) Направление. Может быть следующим:
                                        up — пальцем вверх(прокрутка вниз)
                                        down — пальцем вниз(прокрутка вверх)
                                        left — пальцем влево(прокрутка вправо)
                                        right — пальцем вправо(прокрутка влево)
        :param x:                   (optional) X-координата начальной точки.
        :param y:                   (optional) Y-координата начальной точки.
        :param distance:            (optional) Дистанция движения.
        :param speed:               (optional) Скорость движения(по умолчанию = 800).
        :param overscroll:          (optional) Дополнительная дистанция в пикселях. Отрицательное
                                        значение инвертирует направление этой дистанции.
        :param repeatCount:         (optional) Кол-во повторений сделанного жеста.
        :param repeatDelayMs:       (optional) Задержка между повторениями.
        :param gestureSourceType:   (optional) Тип используемого жеста.
        :return:
        """
        if direction not in ("up", "down", "left", "right"):
            raise ValueError("'direction' must be one from — up; down; left; right")
        sign = -1 if direction in ("up", "left") else 1
        rect = await self._connection.extend.getViewportRect()
        if x is None:
            x = 10 if direction == "right" else rect.width - 10 if direction == "left" else rect.height / 2

        if y is None:
            y = 10 if direction == "down" else rect.height - 10 if direction == "up" else rect.width / 2

        if distance is None:
            distance = (rect.height if direction in ["up", "down"] else rect.width) - 10

        overscroll = overscroll if overscroll is not None else 0

        args = dict(x=x, y=y)
        if speed is not None:
            args["speed"] = speed
        if repeatCount is not None:
            args["repeatCount"] = repeatCount
        if repeatDelayMs is not None:
            args["repeatDelayMs"] = repeatDelayMs
        if gestureSourceType is not None:
            args["gestureSourceType"] = gestureSourceType
        if direction in ["left", "right"]:
            args["xDistance"] = distance * sign
            if overscroll is not None:
                args["xOverscroll"] = overscroll * -sign

        if direction in ["up", "down"]:
            args["yDistance"] = distance * sign
            if overscroll is not None:
                args["yOverscroll"] = overscroll * -sign

        await self._connection.Input.synthesizeScrollGesture(**args)

    async def clickTo(self, x: int, y: int, delay: float = None) -> None:
        """ Эмулирует клик мыши по координатам.
        :param x:               x - координата
        :param y:               y - координата
        :param delay:           задержка перед отпусканием
        :return:
        """
        await self._connection.Input.dispatchMouseEvent("mousePressed", x, y, button="left")
        if delay:
            await asyncio.sleep(delay)
        await self._connection.Input.dispatchMouseEvent("mouseReleased", x, y, button="left")

    async def mouseMoveTo(self, x: int, y: int) -> None:
        await self._connection.Input.dispatchMouseEvent("mouseMoved", x, y)

    async def mouseWheel(self, x: float, y: float, deltaX: float = 0, deltaY: float = 0) -> None:
        """ Крутит колесо мышки.
        :param x:               Положение
        :param y:               указателя мыши.
        :param deltaX:          Скроллит по-горизонтали.
        :param deltaY:          Скроллит по-вертикали, положительное значение == вниз.
        :return:
        """
        await self._connection.Input.dispatchMouseEvent(
            "mouseWheel", x, y, button="middle", deltaX=deltaX, deltaY=deltaY)

    async def wheelTo(self, direction: Literal["down", "up", "left", "right"] = "down") -> None:
        """ Эмулирует вращение колеса мышки, для скролла окна браузера
        в указанном направлении, предварительно вычисляя размер вьюпорта
        и располагая курсор в 10 пикселях от стороны, в которой указано
        направление скролла.
        """
        sign = -1 if direction in ["up", "left"] else 1
        rect = await self._connection.extend.getViewportRect()
        x = 10 if direction == "right" else rect.width - 10 if direction == "left" else rect.height / 2
        y = 10 if direction == "down" else rect.height - 10 if direction == "up" else rect.width / 2
        distance = ((rect.height if direction in ["up", "down"] else rect.width) - 10) * sign
        delta = {"deltaX": distance} if direction in ["left", "rigth"] else {"deltaY": distance}
        await self.mouseWheel(x, y, **delta)

    async def mouseMoveToCoordinatesAndClick(self, x: int, y: int) -> None:
        """ Перемещает курсор на указанные координаты и кликает. """
        await self.mouseMoveTo(x, y)
        await self.clickTo(x, y)

    async def sendChar(self, char: str) -> None:
        """ Эмулирует ввод символа нажатием соответствующей кнопки клавиатуры.
        !Внимание! Курсор должен быть установлен в эдит-боксе!
        :param char:             Символ для ввода.
        :return:
        """
        upper_key = char.upper()
        args = {
            "text": char, "key": char, "keyIdentifier": f"U+{WINDOWS_KEY_SET[upper_key]:X}",
            "windowsVirtualKeyCode": WINDOWS_KEY_SET[upper_key],
            "nativeVirtualKeyCode": WINDOWS_KEY_SET[upper_key]
        }
        if len(char) > 1: raise ValueError(f"Передаваемая строка: '{char}' — должна быть из одного символа!")
        await self._connection.Input.dispatchKeyEvent("char", **args)

    async def sendText(
            self, text: str, interval: Optional[Tuple[float, float]] = None
    ) -> None:
        """ Эмулирует последовательный набор текста.
        !Внимание! Курсор должен быть установлен в эдит-боксе!
        :param text:             Последовательность символов для ввода.
        :param interval:         Задержка после нажатия кнопки. None - отключает задержку.
                                     Кортеж из двух чисел описывает интервал, вычисляемый рандомно.
                                     Кортеж (10, None) — устанавливает фиксированное ожидание в 10 секунд
        :return:
        """
        for letter in text:
            await self.sendChar(letter)
            if interval is not None: await asyncio.sleep(random.uniform(interval[0], interval[1]))

    async def sendKeyEvent(self, event: dict, *modifiers: KeyModifiers) -> None:
        """ Генерирует событие нажатия и отпускания клавиши
        с учётом клавиш-модификаторов.
        """
        args = {}
        if modifiers:
            args.update(modifiers=sum(m.value for m in modifiers))

        args.update(event)
        await self._connection.Input.dispatchKeyEvent("keyDown", **args)
        await self._connection.Input.dispatchKeyEvent("keyUp", **args)

    async def controlA(self) -> None:
        """ Выделить весь текст(Ctrl+A). """
        await self.sendKeyEvent(KeyEvents.keyA, KeyModifiers.ctrl)

    async def backspaceText(
            self, count: int = 1, modifier: KeyModifiers = KeyModifiers.none) -> None:
        """ Удаляет текст в текстовом поле с позиции курсора по направлению в лево.
        !Внимание! Курсор должен быть установлен в эдит-боксе!
        :param count:       (optional) Количество нажатий.
        :param modifier:    (optional) none - удалить один символ, ctrl - слово, включая стоящие перед
                                ним пробелы.
        :return:
        """
        for i in range(count):
            await self.sendKeyEvent(KeyEvents.backspace, modifier)

    async def setWindowBounds(self, bounds: Bounds, windowId: Optional[int] = None) -> None:
        """ Устанавливает позицию и/или размер окна.
        !(EXPERIMENTAL)
        https://chromedevtools.github.io/devtools-protocol/tot/Browser#method-setWindowBounds
        :param bounds:          Новые границы окна, а так же состояние.
        :param windowId:        Идентификатор окна.
        """
        if windowId is None:
            windowId = (await self._connection.Target.getWindowForTarget()).windowId
        await self._connection.call(
            "Browser.setWindowBounds",
            {"windowId": windowId, "bounds": bounds.to_dict()}
        )
