from abc import ABC, abstractmethod
from typing import Optional, Union, List

class Fetch(ABC):
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Fetch
    """
    __slots__ = ()

    def __init__(self):
        self.fetch_domain_enabled = False

    @property
    def connected(self) -> bool:
        return False

    @property
    def verbose(self) -> bool:
        return False

    @property
    def page_id(self) -> str:
        return ""

    async def FetchEnable(
        self,
        patterns:     Optional[List[dict]] = None,
        handleAuthRequests: Optional[bool] = False,
        fetch_onResponse:   Optional[bool] = False
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
        :param fetch_onResponse:    (optional) Если True - добавляет в шаблон остлеживание
                                        этапа запроса с перехватом в состоянии "ответ".
        :return:
        """
        args = {}; patterns = patterns if patterns is not None else []
        if fetch_onResponse: patterns.append({"requestStage": "Response"})
        if patterns: args.update({"patterns": patterns})
        if handleAuthRequests: args.update({"handleAuthRequests": handleAuthRequests})
        await self.Call("Fetch.enable", args)
        self.fetch_domain_enabled = True

    async def FetchDisable(self) -> None:
        """
        Отключает взаимодействие с доменом.
        https://chromedevtools.github.io/devtools-protocol/tot/Fetch#method-disable
        :return:
        """
        await self.Call("Fetch.disable")
        self.fetch_domain_enabled = False

    async def FailRequest(self, requestId: str, errorReason: str) -> None:
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
        await self.Call("Fetch.failRequest", {"requestId": requestId, "errorReason": errorReason})

    async def FulfillRequest(
            self, requestId: str,
            responseCode:           Optional[int] = 200,
            responseHeaders: Optional[List[dict]] = None,
            binaryResponseHeaders:  Optional[str] = None,
            body:                   Optional[str] = None,
            responsePhrase:         Optional[str] = None,
            wait_for_response:     Optional[bool] = False
    ) -> None:
        """
        Предоставляет ответ на запрос.
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
        if responseHeaders is not None: args.update({"responseHeaders": responseHeaders})
        if binaryResponseHeaders is not None: args.update({"binaryResponseHeaders": binaryResponseHeaders})
        if body is not None: args.update({"body": body})
        if responsePhrase is not None: args.update({"responsePhrase": responsePhrase})
        # print("fulfillRequest args", json.dumps(args, indent=4))
        await self.Call("Fetch.fulfillRequest", args, wait_for_response=wait_for_response)

    async def ContinueRequest(
        self, requestId: str,
        url:                Optional[str] = None,
        method:             Optional[str] = None,
        postData:           Optional[str] = None,
        headers:     Optional[List[dict]] = None,
        wait_for_response: Optional[bool] = False
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
        :param wait_for_response:       (optional) Дожидаться ответа?
        :return:
        """
        args = {"requestId": requestId}
        if url is not None: args.update({"url": url})
        if method is not None: args.update({"method": method})
        if postData is not None: args.update({"postData": postData})
        if headers is not None: args.update({"headers": headers})
        await self.Call("Fetch.continueRequest", args, wait_for_response=wait_for_response)

    async def ContinueWithAuth(self, requestId: str, authChallengeResponse: list) -> None:
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
        await self.Call("Fetch.continueWithAuth", args)

    async def GetResponseBody(self, requestId: str) -> dict:
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
        return await self.Call("Fetch.getResponseBody", {"requestId": requestId})

    async def TakeResponseBodyAsStream(self, requestId: str) -> dict:
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
        return await self.Call("Fetch.takeResponseBodyAsStream", {"requestId": requestId})

    @abstractmethod
    async def Call(
        self, domain_and_method: str,
        params: Optional[dict] = None,
        wait_for_response: Optional[bool] = True
    ) -> Union[dict, None]: raise NotImplementedError("async method Call() — is not implemented")
