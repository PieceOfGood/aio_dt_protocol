from typing import Optional, List, Callable, Awaitable
from ...data import DomainEvent
from .types import EventRequestPaused, EventAuthRequired, HeaderEntry, RequestPattern


class Fetch:
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Fetch
    """
    __slots__ = ("_connection", "enabled")

    def __init__(self, conn) -> None:

        from ...connection import Connection

        self._connection: Connection = conn
        self.enabled = False

    async def enable(
        self,
        patterns: Optional[List[RequestPattern]] = None,
        handleAuthRequests: bool = False,
        on_pause: Optional[Callable[[EventRequestPaused], Awaitable[None]]] = None,
        on_auth:  Optional[Callable[[EventAuthRequired], Awaitable[None]]] = None,
    ) -> None:
        """
        Включает выдачу событий requestPaused. Запрос будет приостановлен до тех пор,
            пока клиент не вызовет одну из функций failRequest, fulfillRequest или
            continueRequest / continueWithAuth.
        https://chromedevtools.github.io/devtools-protocol/tot/Fetch#method-enable
        :param patterns:            (optional) Если указано, только запросы,
                                        соответствующие любому из этих шаблонов, будут
                                        вызывать событие fetchRequested и будут
                                        приостановлены до ответа клиента. Если не
                                        установлен, все запросы будут затронуты.
                                            https://chromedevtools.github.io/devtools-protocol/tot/Fetch#type-RequestPattern
        :param handleAuthRequests:  (optional) Если True - события authRequired будут
                                        выдаваться и запросы будут приостановлены в
                                        ожидании вызова continueWithAuth.
        :param on_pause:            (optional) Корутина, которая будет получать все события "requestPaused".
        :param on_auth:             (optional) Корутина, которая будет получать все события "authRequired".
        :return:
        """

        async def on_pause_decorator(params: dict) -> None:
            await on_pause(EventRequestPaused(**params))

        async def on_auth_decorator(params: dict) -> None:
            await on_auth(EventAuthRequired(**params))

        if on_pause is not None:
            await self._connection.addListenerForEvent(
                FetchEvent.requestPaused, on_pause_decorator)

        if on_auth is not None:
            await self._connection.addListenerForEvent(
                FetchEvent.authRequired, on_auth_decorator)

        if not self.enabled:
            args = {}
            patterns = patterns if patterns is not None else []
            if patterns:
                args.update({"patterns": [p.dict() for p in patterns]})
            if handleAuthRequests: args.update({"handleAuthRequests": handleAuthRequests})
            await self._connection.call("Fetch.enable", args)
            self.enabled = True

    async def disable(self) -> None:
        """
        Отключает взаимодействие с доменом.
        https://chromedevtools.github.io/devtools-protocol/tot/Fetch#method-disable
        :return:
        """
        if self.enabled:
            await self._connection.call("Fetch.disable")
            self.enabled = False

    async def failRequest(self, requestId: str, errorReason: str) -> None:
        """
        Вызывает сбой запроса по указанной причине.
        https://chromedevtools.github.io/devtools-protocol/tot/Fetch#method-failRequest
        :param requestId:           Идентификатор, полученный клиентом в событии requestPaused.
        :param errorReason:         Причина сбоя выборки на уровне сети. Возможные значения:
                                        Failed, Aborted, TimedOut, AccessDenied,
                                        ConnectionClosed, ConnectionReset,
                                        ConnectionRefused, ConnectionAborted,
                                        ConnectionFailed, NameNotResolved,
                                        InternetDisconnected, AddressUnreachable,
                                        BlockedByClient, BlockedByResponse
        :return:
        """
        await self._connection.call("Fetch.failRequest", {"requestId": requestId, "errorReason": errorReason})

    async def fulfillRequest(
            self, requestId: str,
            responseCode:                     int = 200,
            responseHeaders: Optional[List[HeaderEntry]] = None,
            binaryResponseHeaders:  Optional[str] = None,
            body:                   Optional[str] = None,
            responsePhrase:         Optional[str] = None,
            wait_for_response:               bool = False
    ) -> None:
        """
        Предоставляет браузеру ответ на запрос.
        https://chromedevtools.github.io/devtools-protocol/tot/Fetch#method-fulfillRequest
        :param requestId:               Идентификатор, полученный клиентом в событии requestPaused.
        :param responseCode:            Код ответа HTTP(например - 200).
        :param responseHeaders:         (optional) Заголовки ответа. Например:
                                            [
                                                { "name": "User-Agent", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36" },
                                                { "name": "Content-Type", "value": "application/json; charset=UTF-8" }
                                            ]
        :param binaryResponseHeaders:   (optional) Альтернативный способ указания заголовков ответа в
                                            виде разделенных \0 серий пар имя-значение. Описанный выше
                                            метод предпочтительней, если вам не нужно представлять
                                            некоторые значения, отличные от UTF8, которые не могут быть
                                            переданы по протоколу, в виде текста.
        :param body:                    (optional) Тело ответа, кодированное в строку формата base64.
        :param responsePhrase:          (optional) Текстовое представление responseCode. Если
                                            отсутствует, используется стандартная фраза,
                                            соответствующая responseCode.
        :param wait_for_response:       (optional) Дожидаться ответа?
        :return:
        """
        args = {"requestId": requestId, "responseCode": responseCode}
        if responseHeaders is not None:
            headers = [h.__dict__ for h in responseHeaders]
            args.update({"responseHeaders": headers})

        if binaryResponseHeaders is not None: args.update({"binaryResponseHeaders": binaryResponseHeaders})
        if body is not None: args.update({"body": body})
        if responsePhrase is not None: args.update({"responsePhrase": responsePhrase})
        # print("fulfillRequest args", json.dumps(args, indent=4))
        await self._connection.call("Fetch.fulfillRequest", args, wait_for_response=wait_for_response)

    async def continueRequest(
        self, requestId: str,
        url:                Optional[str] = None,
        method:             Optional[str] = None,
        postData:           Optional[str] = None,
        headers:     Optional[List[dict]] = None,
        interceptResponse: Optional[bool] = None,
        wait_for_response:           bool = False
    ) -> None:
        """
        Продолжает запрос, дополнительно изменяя некоторые его параметры.
        https://chromedevtools.github.io/devtools-protocol/tot/Fetch#method-continueRequest
        :param requestId:           Идентификатор, полученный клиентом в событии requestPaused.
        :param url:                 (optional) Если установлено, URL-адрес запроса будет изменен так,
                                        чтобы страница не наблюдалась.
        :param method:              (optional) Переопределяет метод запроса переданным значением.
        :param postData:            (optional) Переопределяет данные запроса переданными.
        :param headers:             (optional) Переопределяет заголовки запроса переданными. . Например:
                                        [
                                            { "name": "User-Agent", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36" },
                                            { "name": "Content-Type", "value": "application/json; charset=UTF-8" }
                                        ]
        :param interceptResponse:   (optional) Если установлено, переопределяет поведение перехвата ответа для этого запроса.
        :param wait_for_response:   (optional) Дожидаться ответа?
        :return:
        """
        args = {"requestId": requestId}
        if url is not None: args.update({"url": url})
        if method is not None: args.update({"method": method})
        if postData is not None: args.update({"postData": postData})
        if headers is not None: args.update({"headers": headers})
        if interceptResponse is not None: args.update({"interceptResponse": interceptResponse})
        await self._connection.call("Fetch.continueRequest", args, wait_for_response=wait_for_response)

    async def continueWithAuth(self, requestId: str, authChallengeResponse: list) -> None:
        """
        Продолжает запрос, предоставляющий authChallengeResponse после события authRequired.
        https://chromedevtools.github.io/devtools-protocol/tot/Fetch#method-continueWithAuth
        :param requestId:               Идентификатор, полученный клиентом в событии requestPaused.
        :param authChallengeResponse:   Ответ с помощью authChallenge.
                                            {
                                                "response": str(), -> Решение о том, что делать в ответ
                                                    на запрос авторизации. По умолчанию означает
                                                    использование стандартного поведения сетевого стека,
                                                    что, скорее всего, приведет к отмене проверки
                                                    подлинности или появлению всплывающего диалогового
                                                    окна. Возможные значения:
                                                        Default, CancelAuth, ProvideCredentials
                                                "username": str(), -> (optional) Имя пользователя для
                                                    предоставления, может быть пустым. Устанавливается,
                                                    только если ответом является ProvideCredentials.
                                                "password": str(), -> (optional) Пароль пользователя для
                                                    предоставления, может быть пустым. Устанавливается,
                                                    только если ответом является ProvideCredentials.
                                            }
        :return:
        """
        args = {"requestId": requestId, "authChallengeResponse": authChallengeResponse}
        await self._connection.call("Fetch.continueWithAuth", args)

    async def getResponseBody(self, requestId: str) -> dict:
        """
        Вызывает тело ответа, получаемого от сервера и возвращаемого в виде одной строки. Может
            выдаваться только для запроса, который приостановлен на этапе ответа и является
            взаимоисключающим с "takeResponseBodyForInterceptionAsStream". Вызов других методов,
            влияющих на запрос, или отключение домена выборки до получения тела приводит к
            неопределенному поведению.
        https://chromedevtools.github.io/devtools-protocol/tot/Fetch#method-getResponseBody
        :param requestId:               Идентификатор перехваченного запроса для получения его тела.
        :return:                        {
                                            "body": str(),        -> Тело ответа.
                                            "base64Encoded": bool -> True - если контент кодирован
                                                                        как base64.
                                        }
        """
        return await self._connection.call("Fetch.getResponseBody", {"requestId": requestId})

    async def takeResponseBodyAsStream(self, requestId: str) -> dict:
        """
        Возвращает дескриптор потока, представляющего тело ответа. Запрос должен быть приостановлен
            на этапе HeadersReceived. Обратите внимание, что после этой команды запрос не может быть
            продолжен как есть - клиент должен либо отменить его, либо предоставить тело ответа.
            Поток поддерживает только последовательное чтение, IO.read потерпит неудачу, если указана
            позиция. Этот метод является взаимоисключающим с getResponseBody. Вызов других методов,
            влияющих на запрос, или отключение домена выборки до получения тела приводит к
            неопределенному поведению.
        https://chromedevtools.github.io/devtools-protocol/tot/Fetch#method-takeResponseBodyAsStream
        :param requestId:               Идентификатор перехваченного запроса для получения его тела.
        :return:                        {
                                            "stream": str(), -> Это либо получается из другого метода,
                                                либо указывается как blob <uuid> это UUID Blob.
                                                    IO.StreamHandle:
                                                    https://chromedevtools.github.io/devtools-protocol/tot/IO#type-StreamHandle
                                        }
        """
        return await self._connection.call("Fetch.takeResponseBodyAsStream", {"requestId": requestId})


class FetchEvent(DomainEvent):
    authRequired = "Fetch.authRequired"
    requestPaused = "Fetch.requestPaused"
