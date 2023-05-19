try:
    import ujson as json
except ModuleNotFoundError:
    import json

from .Page import Page
from .Actions import Actions
from .DOMElement import Node
from .Data import ViewportRect, WindowRect, GeoInfo

import base64, re
from typing import Optional, Union

from .exceptions import EvaluateError, JavaScriptError, NullProperty

from .domains.BackgroundService import BackgroundService as BackgroundServiceDomain
from .domains.Browser import Browser as BrowserDomain
from .domains.DOM import DOM as DOMDomain
from .domains.Emulation import Emulation as EmulationDomain
from .domains.Log import Log as LogDomain
from .domains.Network import Network as NetworkDomain
from .domains.Page import Page as PageDomain
from .domains.Runtime import Runtime as RuntimeDomain
from .domains.Target import Target as TargetDomain
from .domains.Console import Console as ConsoleDomain
from .domains.Overlay import Overlay as OverlayDomain
from .domains.CSS import CSS as CSSDomain
from .domains.DeviceOrientation import DeviceOrientation as DeviceOrientationDomain
from .domains.Fetch import Fetch as FetchDomain
from .domains.SystemInfo import SystemInfo as SystemInfoDomain

class PageEx(
    Page, BrowserDomain, DOMDomain, EmulationDomain, LogDomain, NetworkDomain,
    PageDomain, RuntimeDomain, TargetDomain, ConsoleDomain, OverlayDomain,
    CSSDomain, DeviceOrientationDomain, FetchDomain, SystemInfoDomain, BackgroundServiceDomain
):
    """
    Расширение для 'Page'. Включает сборку наиболее востребованных методов для работы
        с API 'ChromeDevTools Protocol', а так же дополняет некоторыми полезными методами.
    """
    __slots__ = (
        "ws_url", "page_id", "frontend_url", "callback", "is_headless_mode", "verbose", "browser_name", "id",
        "responses", "connected", "ws_session", "receiver", "on_detach_listener", "listeners", "listeners_for_method",
        "runtime_enabled", "on_close_event", "storage", "action", "_root", "style_sheets", "loading_state",
        "observing_started", "recording_started", "dom_domain_enabled", "targets_discovered", "log_domain_enabled",
        "network_domain_enabled", "console_domain_enabled", "page_domain_enabled", "fetch_domain_enabled",
        "css_domain_enabled", "overlay_domain_enabled"
    )

    def __init__(self, *args):
        Page.__init__(self, *args)

        BrowserDomain.__init__(self)
        DOMDomain.__init__(self)
        EmulationDomain.__init__(self)
        LogDomain.__init__(self)
        NetworkDomain.__init__(self)
        PageDomain.__init__(self)
        RuntimeDomain.__init__(self)
        TargetDomain.__init__(self)
        ConsoleDomain.__init__(self)
        OverlayDomain.__init__(self)
        CSSDomain.__init__(self)
        DeviceOrientationDomain.__init__(self)
        FetchDomain.__init__(self)
        SystemInfoDomain.__init__(self)
        BackgroundServiceDomain.__init__(self)

        self.storage = {}
        self.action = Actions(self)             # Совершает действия на странице. Клики; движения мыши; события клавиш
        self._root: Union[Node, None] = None
        self.style_sheets = []                  # Если домен CSS активирован, сюда попадут все 'styleSheetId' страницы

        self.loading_state = ""                 # Состояние загрузки страницы(основного фрейма). Отслеживается, если
                                                #   включены уведомления домена Page. Может иметь значения:
                                                # |  started; navigated; stopped; do_navigate; do_reload |

    def __eq__(self, other: "PageEx") -> bool:
        return self.page_id == other.page_id

    def __hash__(self) -> int:
        return hash(self.page_id)

    # region [ |>*<|=== Domains ===|>*<| ] Other [ |>*<|=== Domains ===|>*<| ]
    #

    async def PyExecAddOnload(self) -> None:
        """ Включает автоматически добавляющийся JavaScript, вызывающий слушателей
        клиента, добавленных на страницу с помощью await <Page>.AddListener(...) и
        await <Page>.AddListeners(...).

        Например, `test_func()` объявленная и добавленная следующим образом:

        async def test_func(number: int, text: str, bind_arg: dict) -> None:
            print("[- test_func -] Called with args:\n\tnumber: "
                  f"{number}\n\ttext: {text}\n\tbind_arg: {bind_arg}")

        await page.AddListener(
            test_func,                          # ! слушатель
            {"name": "test", "value": True}     # ! bind_arg
        )

        Может быть вызвана со страницы браузера, так:
        py_exec("test_func", 1, "testtt");
        """
        py_exec_js = """function py_exec(funcName, ...args) {
            console.info(JSON.stringify({ func_name: funcName, args: args })); }"""
        await self.AddScriptOnLoad(py_exec_js)

    async def GetViewportRect(self) -> ViewportRect:
        """
        Возвращает список с длиной и шириной вьюпорта браузера.
        """
        code = "(()=>{return JSON.stringify([window.innerWidth,window.innerHeight]);})();"
        data = json.loads(await self.InjectJS(code))
        return ViewportRect(int(data[0]), int(data[1]))

    async def GetWindowRect(self) -> WindowRect:
        """
        Возвращает список с длиной и шириной окна браузера.
        """
        code = "(()=>{return JSON.stringify([window.outerWidth,window.outerHeight]);})();"
        data = json.loads(await self.InjectJS(code))
        return WindowRect(int(data[0]), int(data[1]))

    async def GetUrl(self) -> str:
        return (await self.GetTargetInfo()).url

    async def GetTitle(self) -> str:
        return (await self.GetTargetInfo()).title

    async def MakeScreenshot(
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
        shot = await self.CaptureScreenshot(format_, quality, clip, fromSurface)
        return base64.b64decode(shot.encode("utf-8"))

    async def SelectInputContentBy(self, css: str) -> None:
        await self.InjectJS(f"let _i_ = document.querySelector('{css}'); _i_.focus(); _i_.select();")

    async def ScrollIntoViewJS(self, selector: str) -> None:
        await self.InjectJS(
            "document.querySelector(\"" +
            selector +
            "\").scrollIntoView({'behavior':'smooth', 'block': 'center'});"
        )

    async def InjectJS(self, code: str) -> any:
        """ Выполняет JavaScript-выражение во фрейме верхнего уровня. """
        try:
            result = await self.Eval(code)
        except EvaluateError as error:
            error = str(error)
            if "of null" in error:
                if match := re.match(r"[\w\s:]+['|\"]([^'\"]+)", error):
                    prop = match.group(1)
                else:
                    prop = "unmatched error: " + error
                raise NullProperty(f"InjectJS() Exception with injected code:\n'{code}'\nNull property:\n{prop}")

            raise JavaScriptError(f"JavaScriptError: InjectJS() Exception with injected code:\n'{code}'\nDescription:\n{error}")

        return result.get('value')

    async def GetGeoInfo(self) -> GeoInfo:
        """
        Возвращает информацию о Вашем местоположении, вычисленному по IP.
        """
        async_fn_js = """\
        async function get_geo_info() {
            const resp = await fetch('https://time.gologin.com/');
            return await resp.text();
        } get_geo_info();
        """

        promise = """fetch('https://time.gologin.com/').then(res => res.text())"""

        result: dict = await self.EvalPromise(promise)
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


    # endregion
