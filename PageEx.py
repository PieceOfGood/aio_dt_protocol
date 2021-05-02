
from aio_dt_protocol.Page import Page
from aio_dt_protocol.Actions import Actions
from aio_dt_protocol.DOMElement import Node

import asyncio
import json, base64
from typing import List, Optional, Union

from aio_dt_protocol.domains.Browser import Browser as BrowserDomain
from aio_dt_protocol.domains.DOM import DOM as DOMDomain
from aio_dt_protocol.domains.Emulation import Emulation as EmulationDomain
from aio_dt_protocol.domains.Log import Log as LogDomain
from aio_dt_protocol.domains.Network import Network as NetworkDomain
from aio_dt_protocol.domains.Page import Page as PageDomain
from aio_dt_protocol.domains.Runtime import Runtime as RuntimeDomain
from aio_dt_protocol.domains.Target import Target as TargetDomain
from aio_dt_protocol.domains.Console import Console as ConsoleDomain
from aio_dt_protocol.domains.Overlay import Overlay as OverlayDomain
from aio_dt_protocol.domains.CSS import CSS as CSSDomain
from aio_dt_protocol.domains.DeviceOrientation import DeviceOrientation as DeviceOrientationDomain
from aio_dt_protocol.domains.Fetch import Fetch as FetchDomain


class PageEx(
    Page, BrowserDomain, DOMDomain, EmulationDomain, LogDomain, NetworkDomain,
    PageDomain, RuntimeDomain, TargetDomain, ConsoleDomain, OverlayDomain,
    CSSDomain, DeviceOrientationDomain, FetchDomain
):
    """
    Расширение для 'Page'. Включает сборку наиболее востребованных методов для работы
        с API 'ChromeDevTools Protocol'.
    """
    __slots__ = (
        "ws_url", "page_id", "callback", "is_headless_mode", "verbose", "browser_name", "id", "responses",
        "connected", "ws_session", "receiver", "listeners", "listeners_for_method", "runtime_enabled",
        "storage", "action", "_root", "style_sheets", "loading_state", "dom_domain_enabled", "targets_discovered",
        "log_domain_enabled", "network_domain_enabled", "console_domain_enabled", "page_domain_enabled",
        "fetch_domain_enabled", "css_domain_enabled", "overlay_domain_enabled"
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

        self.storage = {}
        self.action = Actions(self)
        self._root: Union[Node, None] = None
        self.style_sheets = []                  # Если домен CSS активирован, сюда попадут все 'styleSheetId' страницы

        self.loading_state = ""

        self.dom_domain_enabled       = False
        self.targets_discovered       = False
        self.log_domain_enabled       = False
        self.network_domain_enabled   = False
        self.console_domain_enabled   = False
        self.page_domain_enabled      = False
        self.fetch_domain_enabled     = False
        self.css_domain_enabled       = False
        self.overlay_domain_enabled   = False


    # region [ |>*<|=== Domains ===|>*<| ] Other [ |>*<|=== Domains ===|>*<| ]
    #

    async def GetDocumentRect(self) -> List[int]:
        """
        Возвращает список с длиной и шириной вьюпорта браузера.
        """
        code = "(() => { return JSON.stringify([document.documentElement.clientWidth, document.documentElement.clientHeight]); })();"
        return json.loads(await self.InjectJS(code))

    async def GetUrl(self):
        return (await self.GetTargetInfo())["url"]

    async def GetTitle(self):
        return (await self.GetTargetInfo())["title"]

    async def MakeScreenshot(
            self,
                 format_: Optional[str] = "",
                 quality: Optional[int] = -1,
                   clip: Optional[dict] = None,
            fromSurface: Optional[bool] = True
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

    async def ScrollIntoViewJS(self, selector: str):
        await self.InjectJS(
            "document.querySelector(\"" +
            selector +
            "\").scrollIntoView({'behavior':'smooth', 'block': 'center'});"
        )

    async def InjectJS(self, code: str):
        try:
            result = await self.Eval(code)
        except Exception as error:
            print("InjectJS() Exception with injected code ->\n", code, "\n")
            raise
        return result.get('value')

    async def CatchMetaForUrl(self, url: str, uniq_key: Optional[str] = None) -> None:
        """
        Получает заголовки запроса, ответа, а так же cookie для конкретного url и сохраняет их
            в виде словарей в поле собственного инстанса, доступного как:
            page_instance.storage[uniq_key]. Если 'uniq_key' не указан, в его качестве будет
            использован 'url'.

        Для работы будет активирован домен Fetch со значением "True" для "fetch_onResponse".
        :param url:             Адрес ресурса, или его уникальная часть.
        :param uniq_key:        Идентификатор, под которым будут сохраняться данные перехвата.
        :return:
        """
        if not self.fetch_domain_enabled:
            await self.FetchEnable(fetch_onResponse=True)
        key = uniq_key if uniq_key else url
        await self.AddListenerForEvent("Fetch.requestPaused", catch_headers_for_url, self, url, self.storage, key)


    # endregion

async def catch_headers_for_url(data: dict, instance: 'PageEx', url: str, storage: dict, storage_key: str) -> None:
    """
    Получает заголовки запроса, ответа, а так же cookie для конкретного url и сохраняет их
    в виде словарей в переданном по ссылке 'storage'. Требует активации домена Fetch со значением
    "True" для "fetch_onResponse", после чего, инстансу страницы, эта корутина добавляется как
     слушатель транслирующий через 'data' параметры перехваченных запросов. Например:
            await page.FetchEnable( fetch_onResponse=True )
            await page.AddListenerForEvent(
                "Fetch.requestPaused",
                catch_headers_for_url,
                page,
                "persistentBadging",
                GLOBAL_STORAGE,
                "storage_key"
            )
    Структура сохранённых данных: (dict) {
        "request_url":      (str) - полный url перехваченного запроса,
        "request_headers":  (dict) - {"hdr_name": "hdr_value", "hdr_name": "hdr_value", ... },
        "response_headers": (dict) - {"hdr_name": "hdr_value", "hdr_name": "hdr_value", ... },
        "response_cookies": (dict) - {"cook_name": "cook_value", "cook_name": "cook_value", ... },
        "full_cookie_data": (list[ dict ]) - [
            {
                "name": "cookie name",
                "value": "cookie value",
                "domain": ".instagram.com",
                "path": "/",
                "expires": -1,
                "size": 149,
                "httpOnly": true,
                "secure": true,
                "session": true,
                "priority": "Medium"
            }, { ... }
        ]
    }
    :param data:            Содержимое перехваченного запроса. Эти данные будут переданы в слушатель из браузера.
                                Структура: {
                                    requestId: (str),
                                    request: {
                                        url: (str),
                                        method: (str),
                                        headers: (dict) — Все заголовки запроса включая куки,
                                        postData: (str) — payload POST-запросов,
                                        initialPriority: (str),
                                        referrerPolicy: (str),
                                        Возможно какие-то ещё ...
                                    },
                                    frameId: (str) — like "75ED3620550E8F5E16B8F6D1FF2EE4D1",
                                    resourceType: (str) — like "XHR",
                                    responseStatusCode: (int) — like 200,
                                    responseHeaders: (List[dict]) — заголовки ответа, не включая куки:
                                        [ {'name': 'content-type', 'value': '"application/json; charset=utf-8'}, ... ]
                                }
    :param instance:        Инстанс страницы, от лица которой происходит перехват.
    :param url:             Адрес ресурса, или его уникальная часть.
    :param storage:         Ссылка на словарь, в который будет сохранён результат.
    :param storage_key:     Идентификатор, под которым сохранится запись в 'storage'.
    :return:    None
    """
    asyncio.create_task(instance.ContinueRequest(data["requestId"]))
    if url in data["request"]["url"]:
        response_headers = {}; response_cookies = {}
        for item in data["responseHeaders"]: response_headers[item["name"]] = item["value"]
        full_cookie_data = await instance.GetCookies()
        for item in full_cookie_data:
            response_cookies[item["name"]] = item["value"]
        storage[storage_key] = {
            "request_url":      data["request"]["url"],
            "request_headers":  data["request"]["headers"],
            "response_headers": response_headers,
            "response_cookies": response_cookies,
            "full_cookie_data": full_cookie_data
        }
