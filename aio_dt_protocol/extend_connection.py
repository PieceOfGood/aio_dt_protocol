try:
    import ujson as json
except ModuleNotFoundError:
    import json

from .actions import Actions
from .data import ViewportRect, WindowRect, GeoInfo

import base64, re
from typing import Optional

from .exceptions import EvaluateError, JavaScriptError, NullProperty


class Extend:
    """ Расширение для 'Page' некоторыми полезными методами.
    """
    __slots__ = ("_connection", "action")

    def __init__(self, conn) -> None:

        from .connection import Connection

        self._connection: Connection = conn
        self.action = Actions(conn)             # Совершает действия на странице. Клики;
                                                # движения мыши; события клавиш
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
        py_call_js = """\
        function py_call(funcName,...args){eval(funcName+"(`"+JSON.stringify(args)+"`)");}"""
        await self._connection.Page.addScriptOnLoad(py_call_js)
        await self.injectJS(py_call_js)

    async def getViewportRect(self) -> ViewportRect:
        """
        Возвращает список с длиной и шириной вьюпорта браузера.
        """
        code = "(()=>{return JSON.stringify([window.innerWidth,window.innerHeight]);})();"
        data = json.loads(await self.injectJS(code))
        return ViewportRect(int(data[0]), int(data[1]))

    async def getWindowRect(self) -> WindowRect:
        """
        Возвращает список с длиной и шириной окна браузера.
        """
        code = "(()=>{return JSON.stringify([window.outerWidth,window.outerHeight]);})();"
        data = json.loads(await self.injectJS(code))
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
        """
        Сделать скриншот. Возвращает набор байт, представляющий скриншот.
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

    async def evalPromise(self, expression: str) -> dict:
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

        return json.loads(response.value)

    async def injectJS(self, expression: str) -> any:
        """ Выполняет JavaScript-выражение во фрейме верхнего уровня. """
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
            if "of null" in error:
                if match := re.match(r"[\w\s:]+['|\"]([^'\"]+)", error):
                    prop = match.group(1)
                else:
                    prop = "unmatched error: " + error
                raise NullProperty("InjectJS() Exception with injected code:"
                                   f"\n'{expression}'\nNull property:\n{prop}")

            raise JavaScriptError("JavaScriptError: InjectJS() Exception with "
                                  f"injected code:\n'{expression}'\nDescription:\n{error}")

        return response.value

    async def getGeoInfo(self) -> GeoInfo:
        """ Возвращает информацию о местоположении точки выхода браузера в сеть,
        вычисленному по IP.
        """
        async_fn_js = """\
        async function get_geo_info() {
            const resp = await fetch('https://time.gologin.com/');
            return await resp.text();
        } get_geo_info();
        """

        promise = """fetch('https://time.gologin.com/').then(res => res.text())"""

        result: dict = await self._connection.extend.evalPromise(promise)
        result.update(
            geo=dict(
                latitude=float(result["ll"][0]),
                longitude=float(result["ll"][1]),
                accuracy=float(result["accuracy"])
            ),
            languages=result["languages"].split(","),
            state_province=result.get("stateProv"),
            proxy_type=(pt:=result.get("proxyType"))
        )
        del result["ll"]
        del result["accuracy"]
        del result["stateProv"]
        if pt is not None:
            del result["proxyType"]
        return GeoInfo(**result)