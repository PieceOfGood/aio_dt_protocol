from abc import ABC, abstractmethod
from typing import Optional, Union, List
from aio_dt_protocol.Data import Cookie, ConnectionType

class Network(ABC):
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Network
    """
    __slots__ = ()

    def __init__(self):
        self.network_domain_enabled   = False

    @property
    def connected(self) -> bool:
        return False

    @property
    def verbose(self) -> bool:
        return False

    @property
    def page_id(self) -> str:
        return ""

    async def NetworkEnable(
            self,
            maxTotalBufferSize:    Optional[int] = None,
            maxResourceBufferSize: Optional[int] = None,
            maxPostDataSize:       Optional[int] = None
    ) -> None:
        """
        Включает отслеживание сети, сетевые события теперь будут доставляться клиенту.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-enable
        :param maxTotalBufferSize:      (optional, EXPERIMENTAL) Размер буфера в байтах для использования
                                            при сохранении полезных данных сети (XHR и т. Д.).
        :param maxResourceBufferSize:   (optional, EXPERIMENTAL) Размер буфера для каждого ресурса в
                                            байтах для использования при сохранении полезных данных сети
                                            (XHR и т. Д.).
        :param maxPostDataSize:         (optional) Самый длинный размер тела сообщения (в байтах),
                                            который будет включен в уведомление "requestWillBeSent".
        :return:
        """
        args = {}
        if maxTotalBufferSize is not None: args.update({"maxTotalBufferSize": maxTotalBufferSize})
        if maxResourceBufferSize is not None: args.update({"maxResourceBufferSize": maxResourceBufferSize})
        if maxPostDataSize is not None: args.update({"maxPostDataSize": maxPostDataSize})
        await self.Call("Network.enable", args)
        self.network_domain_enabled = True

    async def NetworkDisable(self) -> None:
        """
        Отключает отслеживание сети, запрещает отправку сетевых событий клиенту.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-disable
        :return:
        """
        await self.Call("Network.disable")
        self.network_domain_enabled = False

    async def EmulateNetworkConditions(
        self, latency: int,
        downloadThroughput: Optional[int] = -1,
        uploadThroughput:   Optional[int] = -1,
        offline:           Optional[bool] = False,
        connectionType: Optional[ConnectionType] = None
    ) -> None:
        """
        Активирует эмуляцию состояния сети.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-emulateNetworkConditions
        :param latency:             Минимальная задержка от запроса, отправленного полученным заголовкам
                                        ответа (мс).
        :param downloadThroughput:  (optional) Максимальная агрегированная скорость скачивания (байт / с).
                                        -1 отключает регулирование.
        :param uploadThroughput:    (optional) Максимальная агрегированная скорость загрузки (байт / с).
                                        -1 отключает регулирование.
        :param offline:             (optional) 'True' — эмулирует отключение от интернета.
        :param connectionType:      (optional) Основная технология подключения, которую, предположительно
                                        использует браузер.
                                        Allowed values: none, cellular2g, cellular3g, cellular4g,
                                        bluetooth, ethernet, wifi, wimax, other
        :return:
        """
        args = {"latency": latency, "offline": offline}
        if downloadThroughput > -1: args.update({"downloadThroughput": downloadThroughput})
        if uploadThroughput > -1: args.update({"uploadThroughput": uploadThroughput})
        if connectionType: args.update({"connectionType": connectionType.value})
        await self.Call("Network.emulateNetworkConditions", args)

    async def ClearBrowserCache(self) -> None:
        """
        Clears browser cache.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-clearBrowserCache
        :return:
        """
        await self.Call("Network.clearBrowserCache")

    async def ClearBrowserCookies(self) -> None:
        """
        Clears browser cookies.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-clearBrowserCookies
        :return:
        """
        await self.Call("Network.clearBrowserCookies")

    async def SetBlockedURLs(self, urls: List[str]) -> None:
        """
        (EXPERIMENTAL)
        Блокирует загрузку URL-адресов.
        !!!ВНИМАНИЕ!!! Требует активации доменов Page и Network!
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-setBlockedURLs
        :param urls:            Шаблоны URL для блокировки. Подстановочные знаки ('*') разрешены.
        :return:
        """
        if not self.network_domain_enabled:
            await self.NetworkEnable()
        await self.Call("Network.setBlockedURLs", {"urls": urls})

    async def SetCacheDisabled(self, cacheDisabled: Optional[bool] = True) -> None:
        """
        Включает игнорирование кеша для каждого запроса. Если 'true', кеш не будет использоваться.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-setCacheDisabled
        :param cacheDisabled:    Состояние.
        :return:
        """
        await self.Call("Network.setCacheDisabled", {"cacheDisabled": cacheDisabled})

    async def GetAllCookies(self) -> List[Cookie]:
        """
        Возвращает все куки браузера. В зависимости от поддержки бэкэнда, вернет подробную
            информацию о куки в поле куки.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-getAllCookies
        :return: cookies -> (array Cookie) Array of cookie objects.
        """
        cookies = []
        for c in (await self.Call("Network.getAllCookies"))["cookies"]:
            cookies.append(Cookie(**c))
        return cookies

    async def GetCookies(self, urls: Optional[list] = None) -> List[Cookie]:
        """
        Возвращает все куки браузера для текущего URL. В зависимости от поддержки бэкэнда,
            вернет подробную информацию о куки в поле куки.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-getCookies
        :param urls: список строк содержащих адреса, для которых будут извлечены Cookies [ "https://google.com", ... ]
        :return: cookies -> (array Cookie) Array of cookie objects.
        """
        args = {}
        if urls: args.update({"urls": urls})
        cookies = []
        for c in (await self.Call("Network.getCookies", args))["cookies"]:
            cookies.append(Cookie(**c))
        return cookies

    async def DeleteCookies(
            self, name: str,
            url:    Optional[str] = "",
            domain: Optional[str] = "",
            path:   Optional[str] = ""
    ) -> None:
        """
        Удаляет файлы cookie браузера с соответствующими именами и URL-адресами или парой домен / путь.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-deleteCookies
        :param name:    Имя куки для удаления.
        :param url:     (optional) Если указан, удаляет все куки с указанным именем, где 'domain' и
                            'path' соответствуют указанному URL.
        :param domain:  (optional) Если указан, удаляет только те куки, что точно соответствуют 'domain'.
        :param path:    (optional) Если указан, удаляет только те куки, что точно соответствуют 'path'.
        :return:
        """
        args = {"name": name}
        if url: args.update({"url": url})
        if domain: args.update({"domain": domain})
        if path: args.update({"path": path})
        await self.Call("Network.deleteCookies", args)

    async def SetCookie(
            self, name: str, value: str,
            url:       Optional[str] = "",
            domain:    Optional[str] = "",
            path:      Optional[str] = "",
            secure:   Optional[bool] = None,
            httpOnly: Optional[bool] = None,
            sameSite:  Optional[str] = "",
            expires:   Optional[int] = -1,
            priority:  Optional[str] = ""
    ) -> bool:
        """
        Устанавливает cookie с указанными данными cookie. Если они существуют, то будут перезаписаны.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-setCookie
        :param name:        Cookie name.
        :param value:       Cookie value.
        :param url:         (optional) The request-URI to associate with the setting of
                                the cookie. This value can affect the default domain and
                                path values of the created cookie.
        :param domain:      (optional) Cookie domain.
        :param path:        (optional) Cookie path.
        :param secure:      (optional) True if cookie is secure.
        :param httpOnly:    (optional) True if cookie is http-only.
        :param sameSite:    (optional) Cookie SameSite type. Represents the cookie's 'SameSite'
                                status: https://tools.ietf.org/html/draft-west-first-party-cookies
                                Allowed values: Strict, Lax, None
        :param expires:     (optional) Cookie expiration date, session cookie if not set.
                                UTC time in seconds, counted from January 1, 1970.
        :param priority:    (optional, EXPERIMENTAL) Cookie Priority type. Represents the cookie's 'Priority'
                                status: https://tools.ietf.org/html/draft-west-cookie-priority-00
                                Allowed values: Low, Medium, High
        :return:            True if successfully set cookie.
        """
        args = {"name": name, "value": value}
        if url: args.update({"url": url})
        if domain: args.update({"domain": domain})
        if path: args.update({"path": path})
        if secure is not None: args.update({"secure": secure})
        if secure is not None: args.update({"httpOnly": httpOnly})
        if sameSite: args.update({"sameSite": sameSite})
        if expires > -1: args.update({"expires": expires})
        if priority: args.update({"priority": priority})
        return (await self.Call("Network.setCookie", args))["success"]

    async def SetCookies(self, list_cookies: list) -> None:
        """
        Устанавливает сразу список кук
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-setCookies
        :param list_cookies:        список куки-параметров
        :return:
        """
        await self.Call("Network.setCookies", {"cookies": list_cookies})

    async def SetExtraHeaders(self, headers: dict) -> None:
        """
        Устанавливает дополнительные заголовки, которые всегда будут отправляться в запросах
            от инстанса текущей страницы.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-setExtraHTTPHeaders
        :param headers:        Заголовки запроса / ответа в виде ключей / значений объекта JSON.
        :return:
        """
        await self.Call("Network.setExtraHTTPHeaders", {"headers": headers})

    async def NetworkSetUserAgent(
        self, userAgent: str,
        acceptLanguage:     Optional[str] = None,
        platform:           Optional[str] = None,
        userAgentMetadata: Optional[dict] = None
    ) -> None:
        """
        Позволяет переопределить пользовательский агент с заданной строкой. Функционал ничем не
            отличается от одноимённого метода домена 'Emulation'.
        https://chromedevtools.github.io/devtools-protocol/tot/Network/#method-setUserAgentOverride
        :param userAgent:           Новый юзер-агент.
        :param acceptLanguage:      (optional) Язык браузера для эмуляции.
        :param platform:            (optional) Платформа браузера, которую возвращает
                                        "navigator.platform".
                                        https://www.w3schools.com/jsref/prop_nav_platform.asp
        :param userAgentMetadata:   (optional, EXPERIMENTAL) Для отправки в заголовках Sec-CH-UA- * и возврата в
                                        navigator.userAgentData. Ожидатся словарь вида:
                                        {
                                            "brands": [{"brand": "brand name", "version": "brand version"}, { ... }, ... ],
                                            "fullVersion": "full version",
                                            "platform": "platform name",
                                            "platformVersion": "platform version",
                                            "architecture": "devise architecture",
                                            "model": "model",
                                            "mobile": boolean,
                                        }
        :return:            None
        """
        args = {"userAgent": userAgent}
        if acceptLanguage: args.update({"acceptLanguage": acceptLanguage})
        if platform: args.update({"platform": platform})
        if userAgentMetadata: args.update({"userAgentMetadata": userAgentMetadata})
        await self.Call("Network.setUserAgentOverride", args)

    async def LoadNetworkResource(
        self,
        url:      Optional[str] = None,
        options: Optional[dict] = None,
        frameId:  Optional[str] = None
    ) -> dict:
        """
        Выбирает ресурс и возвращает контент.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-loadNetworkResource
        :param url:             (optional) URL ресурса, для которого нужно получить контент.
        :param options:         (optional) Опции запроса
        :param frameId:         (optional) Идентификатор фрейма
        :return:
        """
        if url is None: url = await self.GetUrl()
        if options is None: options = {"disableCache": False, "includeCredentials": True}
        if frameId is None: frameId = self.page_id
        args = { "url": url, "options": options, "frameId": frameId }
        return (await self.Call("Network.loadNetworkResource", args))["resource"]

    @abstractmethod
    async def GetUrl(self) -> str:
        raise NotImplementedError("async method GetUrl() — is not implemented")

    @abstractmethod
    async def Call(
        self, domain_and_method: str,
        params:            Optional[dict] = None,
        wait_for_response: Optional[bool] = True
    ) -> Union[dict, None]: raise NotImplementedError("async method Call() — is not implemented")
