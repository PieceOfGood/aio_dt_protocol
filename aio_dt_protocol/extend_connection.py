from .actions import Actions
from .data import ViewportRect, WindowRect, GeoInfo, Serializer

import base64
import re
from typing import Optional, Any, TYPE_CHECKING

from .exceptions import (
    PromiseEvaluateError,
    EvaluateError,
    JavaScriptError,
    JAVASCRIPT_EXCEPTIONS
)

if TYPE_CHECKING:
    from .connection import Connection


class Extend:
    """ Расширение для 'Connection' некоторыми полезными методами.
    """
    __slots__ = ("_connection", "action", "_py_call_script_id")

    def __init__(self, conn) -> None:
        self._connection: Connection = conn
        self._py_call_script_id: str = ""
        self.action = Actions(conn)             # Совершает действия на странице. Клики;
                                                # движения мыши; события клавиш

    @property
    def py_call_enabled(self) -> bool:
        """ Был ли обработчик `py_call()` зарегистрирован на страницу.
        """
        return bool(self._py_call_script_id)

    async def pyCallAddOnload(self) -> None:
        """ Включает автоматически добавляющийся JavaScript, вызывающий слушателей
        клиента, добавленных на страницу с помощью await <Connection>.bindFunction(...)
        и await <Connection>.bindFunctions(...).

        Например, `test_func()` объявленная следующим образом:
        async def test_func(number: int, text: str, bind_arg: dict) -> None:
            print("[- test_func -] Called with args:\n\tnumber: "
                  f"{number}\n\ttext: {text}\n\tbind_arg: {bind_arg}")

        И добавленная  следующим образом:
        await conn.bindFunction(
            test_func,                          # ! слушатель
            {"name": "test", "value": True}     # ! bind_arg
        )

        Может быть вызвана со страницы браузера, так:
        py_call("test_func", 1, "testtt");
        """
        if self.py_call_enabled:
            return

        py_call_js = """\
        function py_call(funcName,...args){window[funcName](JSON.stringify(args));}"""
        self._py_call_script_id = await self._connection.Page.addScriptOnLoad(py_call_js)
        await self.injectJS(py_call_js)

    async def pyCallRemoveOnLoad(self) -> None:
        """ Удаляет автоматическое добавление JavaScript, установленного
        pyCallAddOnload().
        """
        if self.py_call_enabled:
            await self._connection.Page.removeScriptOnLoad(self._py_call_script_id)
            self._py_call_script_id = ""

    async def getViewportRect(self) -> ViewportRect:
        """ Возвращает список с длиной и шириной вьюпорта браузера.
        """
        code = "(()=>{return JSON.stringify([window.innerWidth,window.innerHeight]);})();"
        data: tuple[int, int] = Serializer.decode(await self.injectJS(code))
        return ViewportRect(int(data[0]), int(data[1]))

    async def getWindowRect(self) -> WindowRect:
        """ Возвращает список с длиной и шириной окна браузера.
        """
        code = "(()=>{return JSON.stringify([window.outerWidth,window.outerHeight]);})();"
        data: tuple[int, int] = Serializer.decode(await self.injectJS(code))
        return WindowRect(int(data[0]), int(data[1]))

    async def getUrl(self) -> str:
        return (await self._connection.Target.getTargetInfo()).url

    async def getTitle(self) -> str:
        return (await self._connection.Target.getTargetInfo()).title

    async def makeScreenshot(
            self,
            format_: str = "",
            quality: int = -1,
            clip: Optional[dict] = None,
            fromSurface: bool = True
    ) -> bytes:
        """  Сделать скриншот. Возвращает набор байт, представляющий скриншот.
        :param format_:         jpeg или png (по умолчанию png).
        :param quality:         Качество изображения в диапазоне [0..100] (только для jpeg).
        :param clip:            {
                                    "x": "number => X offset in device independent pixels (dip).",
                                    "y": "number => Y offset in device independent pixels (dip).",
                                    "width": "number => Rectangle width in device independent pixels (dip).",
                                    "height": "number => Rectangle height in device independent pixels (dip).",
                                    "scale": "number => Page scale factor."
                                }
        :param fromSurface:     boolean => Capture the screenshot from the surface, rather than the view.
                                    Defaults to true.
        :return:                bytes
        """
        shot = await self._connection.Page.captureScreenshot(format_, quality, clip, fromSurface)
        return base64.b64decode(shot.encode("utf-8"))

    async def selectOption(self, css: str) -> None:
        """ Создаёт фокус и делает выбранным опцию тега <select>
        при помощи JavaScript.
        """
        await self.injectJS(f"let _i_ = document.querySelector(`{css}`); _i_.focus(); _i_.select();")

    async def scrollIntoViewJS(self, selector: str) -> None:
        """ Выполняет плавную прокрутку страницы до выбранного селектора. """
        await self.injectJS(
            "document.querySelector(`" +
            selector +
            "`).scrollIntoView({'behavior':'smooth', 'block': 'center'});"
        )

    async def evalPromise(self, expression: str) -> Any:
        """ Выполняет асинхронный код на странице и дожидается
        получения результата.
        """
        result = await self._connection.Runtime.evaluate(
            expression=expression,
            objectGroup="console",
            includeCommandLineAPI=True,
            silent=False,
            returnByValue=False,
            userGesture=True,
            awaitPromise=False
        )

        response = await self._connection.Runtime.awaitPromise(
            promiseObjectId=result.objectId,
            returnByValue=False,
            generatePreview=False
        )
        return response.value

    async def injectJS(self, expression: str) -> Any:
        """ Выполняет JavaScript-выражение во фрейме верхнего уровня.
        Возвращает только простые типы в естественном виде, для сложных
        используйте сериализацию в JSON, или evaluate() домена Runtime.
        """
        try:
            response = await self._connection.Runtime.evaluate(
                expression=expression,
                objectGroup="console",
                includeCommandLineAPI=True,
                silent=False,
                returnByValue=False,
                userGesture=True,
                awaitPromise=False
            )
        except EvaluateError as error:
            error = str(error)
            if match := re.match(r"^([^:]+):\s?(.*)", error, re.DOTALL):
                error_type, error_message = match.groups()
                if ex := JAVASCRIPT_EXCEPTIONS.get(error_type):
                    raise ex(error_message)
            raise JavaScriptError("JavaScriptError: InjectJS() Exception with "
                                  f"injected code:\n'{expression}'\nDescription:\n{error}")
        return response.value

    async def getGeoInfo(self) -> GeoInfo:
        """ Возвращает информацию о местоположении точки выхода браузера в сеть,
        вычисленному по IP. Не работает на дефолтной странице браузера.
        """
        async_fn_js = """\
        async function get_geo_info() {
            const resp = await fetch('https://time.gologin.com/');
            return await resp.text();
        } get_geo_info();
        """

        promise = """fetch('https://time.gologin.com/').then(res => res.text())"""

        try:
            result: str = await self._connection.extend.evalPromise(promise)
        except PromiseEvaluateError:
            if "://newtab" in await self._connection.extend.getUrl():
                raise RuntimeError("Doesn't work on the default browser page. Please "
                                   "first go to a blank url, or any other address.")
            raise
        data: dict = Serializer.decode(result)
        data.update(
            geo=dict(
                latitude=float(data["ll"][0]),
                longitude=float(data["ll"][1]),
                accuracy=float(data["accuracy"])
            ),
            languages=data["languages"].split(","),
            state_province=data.get("stateProv"),
            proxy_type=(pt := data.get("proxyType"))
        )
        del data["ll"]
        del data["accuracy"]
        del data["stateProv"]
        if pt is not None:
            del data["proxyType"]
        return GeoInfo(**data)
