from typing import Optional, List, TYPE_CHECKING
from ...data import DomainEvent
from .types import ConnectionType, LoadNetworkResourcePageResult, Cookie
if TYPE_CHECKING:
    from ...connection import Connection


class Network:
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Network
    """
    __slots__ = ("_connection", "enabled")

    def __init__(self, conn) -> None:
        self._connection: Connection = conn
        self.enabled   = False


    async def enable(
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
        if not self.enabled:
            args = {}
            if maxTotalBufferSize is not None: args.update({"maxTotalBufferSize": maxTotalBufferSize})
            if maxResourceBufferSize is not None: args.update({"maxResourceBufferSize": maxResourceBufferSize})
            if maxPostDataSize is not None: args.update({"maxPostDataSize": maxPostDataSize})
            await self._connection.call("Network.enable", args)
            self.enabled = True

    async def disable(self) -> None:
        """
        Отключает отслеживание сети, запрещает отправку сетевых событий клиенту.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-disable
        :return:
        """
        if self.enabled:
            await self._connection.call("Network.disable")
            self.enabled = False

    async def emulateNetworkConditions(
        self, latency: int,
        downloadThroughput: int = -1,
        uploadThroughput:   int = -1,
        offline:           bool = False,
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
        await self._connection.call("Network.emulateNetworkConditions", args)

    async def clearBrowserCache(self) -> None:
        """
        Clears browser cache.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-clearBrowserCache
        :return:
        """
        await self._connection.call("Network.clearBrowserCache")

    async def clearBrowserCookies(self) -> None:
        """
        Clears browser cookies.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-clearBrowserCookies
        :return:
        """
        await self._connection.call("Network.clearBrowserCookies")

    async def setBlockedURLs(self, urls: List[str]) -> None:
        """
        (EXPERIMENTAL)
        Блокирует загрузку URL-адресов.
        !!!ВНИМАНИЕ!!! Требует активации доменов Page и Network!
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-setBlockedURLs
        :param urls:            Шаблоны URL для блокировки. Подстановочные знаки ('*') разрешены.
        :return:
        """
        if not self.enabled:
            await self.enable()
        await self._connection.call("Network.setBlockedURLs", {"urls": urls})

    async def setCacheDisabled(self, cacheDisabled: bool = True) -> None:
        """
        Включает игнорирование кеша для каждого запроса. Если 'true', кеш не будет использоваться.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-setCacheDisabled
        :param cacheDisabled:    Состояние.
        :return:
        """
        await self._connection.call("Network.setCacheDisabled", {"cacheDisabled": cacheDisabled})

    async def getAllCookies(self) -> List[Cookie]:
        """
        Возвращает все куки браузера. В зависимости от поддержки бэкэнда, вернет подробную
            информацию о куки в поле куки.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-getAllCookies
        :return: cookies -> (array Cookie) Array of cookie objects.
        """
        cookies = []
        for c in (await self._connection.call("Network.getAllCookies"))["cookies"]:
            cookies.append(Cookie(**c))
        return cookies

    async def getCookies(self, urls: Optional[list] = None) -> List[Cookie]:
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
        for c in (await self._connection.call("Network.getCookies", args))["cookies"]:
            cookies.append(Cookie(**c))
        return cookies

    async def deleteCookies(
            self, name: str,
            url:    str = "",
            domain: str = "",
            path:   str = ""
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
        await self._connection.call("Network.deleteCookies", args)

    async def setCookie(
            self, name: str, value: str,
            url:       str = "",
            domain:    str = "",
            path:      str = "",
            secure:   Optional[bool] = None,
            httpOnly: Optional[bool] = None,
            sameSite:  str = "",
            expires:   int = -1,
            priority:  str = ""
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
        return (await self._connection.call("Network.setCookie", args))["success"]

    async def setCookies(self, list_cookies: list) -> None:
        """
        Устанавливает сразу список кук
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-setCookies
        :param list_cookies:        список куки-параметров
        :return:
        """
        await self._connection.call("Network.setCookies", {"cookies": list_cookies})

    async def setExtraHTTPHeaders(self, headers: dict) -> None:
        """
        Устанавливает дополнительные заголовки, которые всегда будут отправляться в запросах
            от инстанса текущей страницы.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-setExtraHTTPHeaders
        :param headers:        Заголовки запроса / ответа в виде ключей / значений объекта JSON.
        :return:
        """
        await self._connection.call("Network.setExtraHTTPHeaders", {"headers": headers})

    async def setUserAgentOverride(
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
        await self._connection.call("Network.setUserAgentOverride", args)

    async def loadNetworkResource(
        self,
        url:      Optional[str] = None,
        options: Optional[dict] = None,
        frameId:  Optional[str] = None
    ) -> LoadNetworkResourcePageResult:
        """
        Выбирает ресурс и возвращает контент.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-loadNetworkResource
        :param url:             (optional) URL ресурса, для которого нужно получить контент.
        :param options:         (optional) Опции запроса
        :param frameId:         (optional) Идентификатор фрейма
        :return:
        """
        if url is None: url = await self._connection.extend.getUrl()
        if options is None: options = {"disableCache": False, "includeCredentials": True}
        if frameId is None: frameId = self._connection.conn_id
        args = { "url": url, "options": options, "frameId": frameId }
        resource = (await self._connection.call("Network.loadNetworkResource", args))["resource"]
        return LoadNetworkResourcePageResult(**resource)


class NetworkEvent(DomainEvent):
    dataReceived = "Network.dataReceived"
    eventSourceMessageReceived = "Network.eventSourceMessageReceived"
    loadingFailed = "Network.loadingFailed"
    loadingFinished = "Network.loadingFinished"
    requestServedFromCache = "Network.requestServedFromCache"
    requestWillBeSent = "Network.requestWillBeSent"
    responseReceived = "Network.responseReceived"
    webSocketClosed = "Network.webSocketClosed"
    webSocketCreated = "Network.webSocketCreated"
    webSocketFrameError = "Network.webSocketFrameError"
    webSocketFrameReceived = "Network.webSocketFrameReceived"
    webSocketFrameSent = "Network.webSocketFrameSent"
    webSocketHandshakeResponseReceived = "Network.webSocketHandshakeResponseReceived"
    webSocketWillSendHandshakeRequest = "Network.webSocketWillSendHandshakeRequest"
    webTransportClosed = "Network.webTransportClosed"
    webTransportConnectionEstablished = "Network.webTransportConnectionEstablished"
    webTransportCreated = "Network.webTransportCreated"
    reportingApiEndpointsChangedForOrigin = "Network.reportingApiEndpointsChangedForOrigin"
    reportingApiReportAdded = "Network.reportingApiReportAdded"
    reportingApiReportUpdated = "Network.reportingApiReportUpdated"
    requestWillBeSentExtraInfo = "Network.requestWillBeSentExtraInfo"
    resourceChangedPriority = "Network.resourceChangedPriority"
    responseReceivedExtraInfo = "Network.responseReceivedExtraInfo"
    signedExchangeReceived = "Network.signedExchangeReceived"
    subresourceWebBundleInnerResponseError = "Network.subresourceWebBundleInnerResponseError"
    subresourceWebBundleInnerResponseParsed = "Network.subresourceWebBundleInnerResponseParsed"
    subresourceWebBundleMetadataError = "Network.subresourceWebBundleMetadataError"
    subresourceWebBundleMetadataReceived = "Network.subresourceWebBundleMetadataReceived"
    trustTokenOperationDone = "Network.trustTokenOperationDone"
    requestIntercepted = "Network.requestIntercepted"
