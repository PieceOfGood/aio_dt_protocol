from dataclasses import dataclass, field
from typing import Optional
from ..network.types import Request


@dataclass
class EventRequestPaused:
    requestId: str
    frameId: str
    resourceType: str                               # ! Allowed Values: Document, Stylesheet, Image, Media, Font,
                                                    # !     Script, TextTrack, XHR, Fetch, EventSource, WebSocket,
                                                    # !     Manifest, SignedExchange, Ping, CSPViolationReport,
                                                    # !     Preflight, Other
    request: Request
    responseHeaders: list["HeaderEntry"]
    responseErrorReason: Optional[str] = None       # ! Allowed Values: Failed, Aborted, TimedOut, AccessDenied,
                                                    # !     ConnectionClosed, ConnectionReset, ConnectionRefused,
                                                    # !     ConnectionAborted, ConnectionFailed, NameNotResolved,
                                                    # !     InternetDisconnected, AddressUnreachable,
                                                    # !     BlockedByClient, BlockedByResponse
    responseStatusCode: Optional[int] = None
    responseStatusText: Optional[str] = None
    networkId: Optional[str] = None                 # ! id of request
    redirectedRequestId: Optional[str] = None       # ! id запроса вызвавшего редирект
    _request: Request = field(init=False, repr=False, default=None)
    _responseHeaders: Optional[list["HeaderEntry"]] = field(init=False, repr=False, default=None)

    @property
    def request(self) -> Request:
        return self._request

    @request.setter
    def request(self, data: dict) -> None:
        self._request = Request(**data)

    @property
    def responseHeaders(self) -> Optional[list["HeaderEntry"]]:
        return self._responseHeaders

    @responseHeaders.setter
    def responseHeaders(self, data: list[dict[str, str]]) -> None:
        if not isinstance(data, property):
            self._responseHeaders = [HeaderEntry(**item) for item in data]
        else:
            self._responseHeaders = None


@dataclass
class EventAuthRequired:
    requestId: str
    request: Request
    frameId: str
    resourceType: str                               # ! Allowed Values: Document, Stylesheet, Image, Media, Font,
                                                    # !     Script, TextTrack, XHR, Fetch, EventSource, WebSocket,
                                                    # !     Manifest, SignedExchange, Ping, CSPViolationReport,
                                                    # !     Preflight, Other
    authChallenge: "AuthChallenge"
    _authChallenge: "AuthChallenge" = field(init=False, repr=False, default=None)

    @property
    def authChallenge(self) -> "AuthChallenge":
        return self._authChallenge

    @authChallenge.setter
    def authChallenge(self, data: dict) -> None:
        self._authChallenge = AuthChallenge(**data)


@dataclass
class AuthChallenge:
    origin: str
    scheme: str
    realm: str                                      # ! May be empty.
    source: Optional[str] = None


@dataclass
class HeaderEntry:
    name: str
    value: str


@dataclass
class RequestPattern:
    urlPattern: str = "*"                           # ? Подстановочные знаки ( '*'-> ноль или более, '?'-> ровно
                                                    # ?     один) допускаются. Экранирующий символ — обратная
                                                    # ?     косая черта(\).
    resourceType: Optional[str] = None              # ? Если установлено, будут перехватываться только соответствующие
                                                    # ?     указанным типам.
                                                    # ! Allowed Values: Document, Stylesheet, Image, Media, Font,
                                                    # !     Script, TextTrack, XHR, Fetch, EventSource, WebSocket,
                                                    # !     Manifest, SignedExchange, Ping, CSPViolationReport,
                                                    # !     Preflight, Other
    requestStage: Optional[str] = None              # ? Стадия перехвата запроса. Запрос будет перехвачен до того,
                                                    # ?     как запрос будет отправлен. Ответ будет перехвачен после
                                                    # ?     получения ответа (но до получения тела ответа).
                                                    # ! Allowed Values: Request, Response

    def dict(self) -> dict:
        result = {}
        for k, v in self.__dict__.items():
            if v: result[k] = v
        return result
