import time
from .types import TouchPoint
from typing import Optional, List, Literal


class Input:
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Input
    """
    __slots__ = ("_connection",)

    def __init__(self, conn) -> None:

        from ...connection import Connection

        self._connection: Connection = conn

# region [ |>*<|=== Domains ===|>*<| ] Input [ |>*<|=== Domains ===|>*<| ]
    #   https://godoc.org/github.com/unixpickle/muniverse/chrome

    async def dispatchKeyEvent(
        self, type_: str,
        modifiers:             int = 0,
        timestamp:             Optional[int] = None,
        text:                  str = "",
        unmodifiedText:        str = "",
        keyIdentifier:         str = "",
        code:                  str = "",
        key:                   str = "",
        windowsVirtualKeyCode: int = 0,
        nativeVirtualKeyCode:  int = 0,
        autoRepeat:           bool = False,
        isKeypad:             bool = True,
        isSystemKey:          bool = False,
        location:              int = 0,
        commands:             Optional[list] = None
    ) -> None:
        """
        Отправляет событие кнопки на страницу.
        https://chromedevtools.github.io/devtools-protocol/tot/Input#method-dispatchKeyEvent
        :param type_:                   Тип события. Допустимые значения:
                                            keyDown, keyUp, rawKeyDown, char
        :param modifiers:               (optional) Битовое поле, представляющее нажатые клавиши-модификаторы.
                                            Alt = 1, Ctrl = 2, Meta/Command = 4, Shift = 8 (по умолчанию: 0).
        :param timestamp:               (optional) UNIX-time (число секунд с 1 января 1970)
        :param text:                    (optional) Текст генерируется путем обработки кода виртуальной клавиши
                                            с раскладкой клавиатуры. Не требуется для событий keyUp и rawKeyDown
                                            (по умолчанию: "").
        :param unmodifiedText:          (optional) Текст, который был бы сгенерирован клавиатурой, если бы не
                                            были нажаты модификаторы (кроме Shift). Полезно для обработки
                                            сочетаний клавиш (по умолчанию: "").
        :param keyIdentifier:           (optional) Уникальный идентификатор кнопки (например, 'U+0041')
                                            (по умолчанию: "").
        :param code:                    (optional) Уникальное значение строки, определяемое DOM для каждого
                                            физического ключа (например, 'KeyA') (по умолчанию: "").
        :param key:                     (optional) Уникальное строковое значение, определяемое DOM, описывающее
                                            значение клавиши в контексте активных модификаторов, раскладки
                                            клавиатуры и т. д. (Например, 'AltGr') (по умолчанию: "").
        :param windowsVirtualKeyCode:   (optional) Код виртуальной клавиши Windows (по умолчанию: 0).
        :param nativeVirtualKeyCode:    (optional) Собственный код виртуальной клавиши (по умолчанию: 0).
        :param autoRepeat:              (optional) Было ли событие сгенерировано из автоматического повтора
                                            (по умолчанию: false).
        :param isKeypad:                (optional) Было ли событие сгенерировано с клавиатуры (по умолчанию: false).
        :param isSystemKey:             (optional) Было ли событие, событием системной кнопки (по умолчанию: false).
        :param location:                (optional) Было ли событие с левой или правой стороны клавиатуры.
                                            1 = слева, 2 = справа (по умолчанию: 0).
        :param commands:                (optional) Команды редактирования для отправки с ключевым событием (например,
                                            'selectAll') (по умолчанию: []). Они связаны с именами команд,
                                            используемыми в document.execCommand и NSStandardKeyBindingResponding,
                                            но не равны им.(по умолчанию: []).
        :return:        None
        """
        args = {
            "type": type_, "modifiers": modifiers, "text": text, "unmodifiedText": unmodifiedText,
            "keyIdentifier": keyIdentifier, "code": code, "key": key,
            "windowsVirtualKeyCode": windowsVirtualKeyCode, "nativeVirtualKeyCode": nativeVirtualKeyCode,
            "autoRepeat": autoRepeat, "isKeypad": isKeypad, "isSystemKey": isSystemKey, "location": location,
            "commands": (commands if commands else [])
        }
        if timestamp is not None:
            args.update({"timestamp": timestamp})
        else:
            args.update({"timestamp": int(time.time() * 1000)})
        await self._connection.call("Input.dispatchKeyEvent", args)

    async def dispatchMouseEvent(
        self, type_: str, x: float, y: float,
        modifiers:            int = 0,
        timestamp:            Optional[int] = None,
        button:               str = "none",
        buttons:              int = 0,
        clickCount:           int = 1,
        force:              float = 0,
        tangentialPressure: float = 0,
        tiltX:                int = 0,
        tiltY:                int = 0,
        twist:                int = 0,
        deltaX:             float = 0,
        deltaY:             float = 0,
        pointerType:          str = "mouse"
    ) -> None:
        """
        Отправляет событие мышки на страницу.
        https://chromedevtools.github.io/devtools-protocol/tot/Input#method-dispatchMouseEvent
        :param type_:                   Тип события. Допустимые значения:
                                            mousePressed, mouseReleased, mouseMoved, mouseWheel
        :param x:                       Координата X события относительно области просмотра основного
                                            фрейма в пикселях CSS.
        :param y:                       Координата Y события относительно области просмотра основного
                                            фрейма в пикселях CSS.
        :param modifiers:               (optional) Битовое поле, представляющее нажатые клавиши-модификаторы.
                                            Alt = 1, Ctrl = 2, Meta/Command = 4, Shift = 8 (по умолчанию: 0).
        :param timestamp:               (optional) UNIX-time (число секунд с 1 января 1970)
        :param button:                  (optional) Кнопка мыши. Допустимые значения:
                                            none, left, middle, right, back, forward
        :param buttons:                 (optional) Число, указывающее, какие кнопки нажимаются на мыши, когда
                                            вызывается событие мыши.
                                            Left=1, Right=2, Middle=4, Back=8, Forward=16, None=0.
        :param clickCount:              (optional) Количество нажатий кнопки мыши (по умолчанию: 0).

        ========================== опции стилуса ========================
        :param force:                   (optional, EXPERIMENTAL) - Нормализованное давление(на кнопку?) в
                                            интервале от 0 до 1.
        :param tangentialPressure:      (optional, EXPERIMENTAL) - Нормализованное тангенциальное давление
                                            (на кнопку?) в интервале от -1 до 1.
        :param tiltX:                   (optional, EXPERIMENTAL) - Плоский угол между плоскостью YZ и плоскостью,
                                            содержащей ось пера и ось Y, в градусах диапазона [-90,90], положительный
                                            tiltX направлен вправо (по умолчанию: 0).
        :param tiltY:                   (optional, EXPERIMENTAL) - Плоский угол между плоскостью XZ и плоскостью,
                                            содержащей ось пера и ось X, в градусах диапазона [-90,90], положительный
                                            tiltY направлен к пользователю (по умолчанию: 0).
        :param twist:                   (optional, EXPERIMENTAL) - Вращение стилуса пера по часовой стрелке вокруг
                                            своей главной оси в градусах в диапазоне [0,359] (по умолчанию: 0).
        ========================== конец опций стилуса ========================

        :param deltaX:                  (optional) Дельта X в пикселях CSS для события колеса мыши
                                            (по умолчанию: 0).
        :param deltaY:                  (optional) Дельта Y в пикселях CSS для события колеса мыши
                                            (по умолчанию: 0).
        :param pointerType:             (optional) Тип указателя (по умолчанию: "mouse"). Допустимые значения:
                                            mouse, pen
        :return:
        """
        args = {
            "type": type_, "x": x, "y": y, "modifiers": modifiers, "button": button, "buttons": buttons,
            "clickCount": clickCount, "force": force, "tangentialPressure": tangentialPressure, "tiltX": tiltX,
            "tiltY": tiltY, "twist": twist, "deltaX": deltaX, "deltaY": deltaY, "pointerType": pointerType
        }
        if timestamp is not None:
            args.update({"timestamp": timestamp})
        else:
            args.update({"timestamp": int(time.time() * 1000)})
        await self._connection.call("Input.dispatchMouseEvent", args)

    async def dispatchTouchEvent(
        self, type_: str,
        touchPoints: Optional[List[TouchPoint]] = None,
        modifiers:                int = 0,
        timestamp:                Optional[int] = None
    ) -> None:
        """
        Отправляет событие прикосновения на страницу.
        https://chromedevtools.github.io/devtools-protocol/tot/Input#method-dispatchTouchEvent
        :param type_:                   Тип сенсорного события. TouchEnd и TouchCancel не должны содержать
                                            никаких точек касания, в то время как TouchStart и TouchMove
                                            должны содержать хотя бы одну. Допустимые значения:
                                            touchStart, touchEnd, touchMove, touchCancel
        :param touchPoints:             Список точек касания на сенсорном устройстве. Генерируется одно
                                            событие на каждую измененную точку (по сравнению с предыдущим
                                            событием касания в последовательности), эмулируя
                                            нажатия/перемещения/отпускания точек одну за другой.
        :param modifiers:               (optional) Битовое поле, представляющее нажатые клавиши-модификаторы.
                                            Alt = 1, Ctrl = 2, Meta/Command = 4, Shift = 8 (по умолчанию: 0).
        :param timestamp:               (optional) UNIX-time (число секунд с 1 января 1970)
        :return:
        """
        args = { "type": type_, "modifiers": modifiers }
        if type_ == "touchEnd" or type_ == "touchCancel":
            if len(touchPoints) == 0 or touchPoints is None:
                raise ValueError(f"Для действия '{type_}', аргумент 'touchPoints' должен получить хотя-бы одну координату")
            args.update({"touchPoints": [point.to_dict() for point in touchPoints]})

        if timestamp is not None: args.update({"timestamp": timestamp})
        else: args.update({"timestamp": int(time.time() * 1000)})

        await self._connection.call("Input.dispatchTouchEvent", args)

    async def insertText(self, text: str) -> None:
        """
        (EXPERIMENTAL)
        Этот метод эмулирует вставку текста, который не поступает от нажатия клавиши, например,
            клавиатуры Emoji или IME.
        https://chromedevtools.github.io/devtools-protocol/tot/Input/#method-insertText
        :param text:                    Текст для вставки.
        :return:
        """
        await self._connection.call("Input.insertText", {"text": text})

    async def synthesizePinchGesture(
            self, x: float, y: float, scaleFactor: float,
                relativeSpeed: Optional[int] = None,
            gestureSourceType: Optional[Literal["touch", "mouse"]] = None
    ) -> None:
        """
        (EXPERIMENTAL)
        Синтезирует жест щипка за период времени, генерируя соответствующие сенсорные события.
        https://chromedevtools.github.io/devtools-protocol/tot/Input/#method-synthesizePinchGesture
        :param x:                       Координата X начала жеста в пикселях CSS.
        :param y:                       Координата Y начала жеста в пикселях CSS.
        :param scaleFactor:             Относительный масштабный коэффициент после увеличения
                                            (> 1,0 увеличивает, <1,0 уменьшает).
        :param relativeSpeed:           (optional) Относительная скорость указателя в пикселях в секунду (по умолчанию: 800).
        :param gestureSourceType:       (optional) Тип входных событий, который должен быть сгенерирован
                                            (по умолчанию: "default", который запрашивает у платформы
                                            предпочтительный тип ввода). default, touch, mouse
        :return:
        """
        args = {"x": x, "y": y, "scaleFactor": scaleFactor}
        if relativeSpeed is not None:
            args.update({"relativeSpeed": relativeSpeed})
        if gestureSourceType is not None:
            args.update({"gestureSourceType": gestureSourceType})
        await self._connection.call("Input.synthesizePinchGesture", args)

    async def synthesizeScrollGesture(
            self, x: float, y: float,
                      xDistance: Optional[float] = None,
                      yDistance: Optional[float] = None,
                    xOverscroll: Optional[float] = None,
                    yOverscroll: Optional[float] = None,
                    preventFling: Optional[bool] = None,
                            speed: Optional[int] = None,
                gestureSourceType: Optional[Literal["touch", "mouse"]] = None,
                      repeatCount: Optional[int] = None,
                    repeatDelayMs: Optional[int] = None,
            interactionMarkerName: Optional[str] = None
    ) -> None:
        """
        (EXPERIMENTAL)
        Синтезирует жест прокрутки в течение определенного периода времени, генерируя соответствующие сенсорные события.
            Возвращает управление только после выполнения жеста!
        https://chromedevtools.github.io/devtools-protocol/tot/Input/#method-synthesizeScrollGesture
        :param x:                       Координата X начала жеста в пикселях CSS.
        :param y:                       Координата Y начала жеста в пикселях CSS.
        :param xDistance:               (optional) Расстояние для прокрутки вдоль оси X (положительное для прокрутки влево).
        :param yDistance:               (optional) Расстояние для прокрутки вдоль оси Y (положительное для прокрутки вверх).
        :param xOverscroll:             (optional) Количество дополнительных пикселей для прокрутки назад вдоль оси X, в
                                            дополнение к заданному расстоянию.
        :param yOverscroll:             (optional) Количество дополнительных пикселей для прокрутки назад вдоль оси Y, в
                                            дополнение к заданному расстоянию.
        :param preventFling:            (optional) Запретить сброс (по умолчанию: true).
        :param speed:                   (optional) Скорость прокрутки в пикселях в секунду (по умолчанию: 800).
        :param gestureSourceType:       (optional) Тип входных событий, который должен быть сгенерирован
                                            (по умолчанию: "default", который запрашивает у платформы
                                            предпочтительный тип ввода). default, touch, mouse
        :param repeatCount:             (optional) Количество повторений жеста (по умолчанию: 0).
        :param repeatDelayMs:           (optional) Задержка в миллисекундах между повторениями. (по умолчанию: 250).
        :param interactionMarkerName:   (optional) Имя генерируемых маркеров взаимодействия, если оно не пустое (по умолчанию: "").
        :return:
        """
        args = {"x": x, "y": y}
        if xDistance is not None:
            args.update({"xDistance": xDistance})
        if yDistance is not None:
            args.update({"yDistance": yDistance})
        if xOverscroll is not None:
            args.update({"xOverscroll": xOverscroll})
        if yOverscroll is not None:
            args.update({"yOverscroll": yOverscroll})
        if preventFling is not None:
            args.update({"preventFling": preventFling})
        if speed is not None:
            args.update({"speed": speed})
        if gestureSourceType is not None:
            args.update({"gestureSourceType": gestureSourceType})
        if repeatCount is not None:
            args.update({"repeatCount": repeatCount})
        if repeatDelayMs is not None:
            args.update({"repeatDelayMs": repeatDelayMs})
        if interactionMarkerName is not None:
            args.update({"interactionMarkerName": interactionMarkerName})
        await self._connection.call("Input.synthesizeScrollGesture", args)

    async def synthesizeTapGesture(
            self, x: float, y: float,
            duration:          Optional[int] = None,
            tapCount:          Optional[int] = None,
            gestureSourceType: Optional[Literal["touch", "mouse"]] = None
    ) -> None:
        """
        (EXPERIMENTAL)
        Синтезирует жест касания за период времени, генерируя соответствующие сенсорные события.
        https://chromedevtools.github.io/devtools-protocol/tot/Input/#method-synthesizeTapGesture
        :param x:                       Координата X места касания в пикселях CSS.
        :param y:                       Координата Y места касания в пикселях CSS.
        :param duration:                (optional) Продолжительность касания (по умолчанию: 50).
        :param tapCount:                (optional) Количество прикосновений (по умолчанию: 1).
        :param gestureSourceType:       (optional) Тип входных событий, который должен быть сгенерирован
                                            (по умолчанию: "default", который запрашивает у платформы
                                            предпочтительный тип ввода). default, touch, mouse
        :return:
        """
        args = {"x": x, "y": y}
        if duration is not None:
            args.update({"duration": duration})
        if tapCount is not None:
            args.update({"tapCount": tapCount})
        if gestureSourceType is not None:
            args.update({"gestureSourceType": gestureSourceType})
        await self._connection.call("Input.synthesizeTapGesture", args)

    # endregion
