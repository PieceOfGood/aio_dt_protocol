import asyncio
from websockets.client import WebSocketClientProtocol, connect
from websockets.exceptions import ConnectionClosedError
from inspect import iscoroutinefunction
from typing import Callable, Optional, Union, Tuple, Dict, Any, Iterable, Coroutine

from .exceptions import get_cdtp_error
from .utils import log

from .data import DomainEvent, Sender, Receiver, CommonCallback, Serializer
from .extend_connection import Extend

from .domains.background_service import BackgroundService
from .domains.browser import Browser
from .domains.css import CSS
from .domains.device_orientation import DeviceOrientation
from .domains.dom import DOM
from .domains.emulation import Emulation
from .domains.fetch import Fetch
from .domains.input import Input
from .domains.log import Log
from .domains.network import Network
from .domains.overlay import Overlay
from .domains.page import Page
from .domains.runtime import Runtime
from .domains.system_info import SystemInfo
from .domains.target import Target

CoroTypeNone = Coroutine[Any, Any, None]


class Connection:
    """ Если инстанс страницы более не нужен, например, при перезаписи в него нового
    инстанса, перед этим [-!-] ОБЯЗАТЕЛЬНО [-!-] - вызовите у него метод
    Detach(), или закройте вкладку/страницу браузера, с которой он связан,
    тогда это будет выполнено автоматом. Иначе в цикле событий останутся
    задачи связанные с поддержанием соединения, которое более не востребовано.
    """
    __slots__ = (
        "ws_url", "frontend_url", "callback", "_id", "extend", "_bindings",
        "responses", "_ws_session", "_receiver_loop", "_on_detach_listener", "_listeners_for_event",
        "on_close_event", "context_manager", "_connected", "_conn_id", "_verbose",
        "_browser_name", "_is_headless_mode",

        "BackgroundService", "Browser", "CSS", "DeviceOrientation", "DOM", "Emulation", "Fetch", "Input",
        "Log", "Network", "Overlay", "Page", "Runtime", "SystemInfo", "Target",
    )

    def __init__(
            self,
            ws_url: str,
            conn_id: str,
            frontend_url: str,
            callback: CommonCallback,
            is_headless_mode: bool,
            verbose: bool,
            browser_name: str
    ) -> None:
        """
        :param ws_url:              Адрес WebSocket.
        :param conn_id:             Идентификатор страницы.
        :param frontend_url:        devtoolsFrontendUrl по которому происходит подключение к дебаггеру.
        :param callback:            Колбэк, который будет получать все данные,
                                        приходящие по WebSocket в виде словарей.
        :param is_headless_mode:    "Headless" включён?
        :param verbose:             Печатать некие подробности процесса?
        :param browser_name:        Имя браузера.
        """

        self.ws_url = ws_url
        self.frontend_url = frontend_url
        self.callback = callback
        self._is_headless_mode = is_headless_mode
        self._conn_id = conn_id
        self._verbose = verbose
        self._browser_name = browser_name
        self._id = 0
        self._connected = False
        self._ws_session: Optional[WebSocketClientProtocol] = None
        self._receiver_loop: Optional[asyncio.Task] = None
        self._on_detach_listener: Optional[Tuple[Callable[[any], CoroTypeNone], list, dict]] = None
        self._bindings: Dict[str, Tuple[Callable[[any], CoroTypeNone], Tuple[Any, ...]]] = {}
        self._listeners_for_event: Dict[
            str, Dict[
                Callable[[dict, tuple], CoroTypeNone],
                Tuple[Any, ...]
            ]
        ] = {}
        self.on_close_event = asyncio.Event()
        self.responses: Dict[int, Optional[Sender[dict]]] = {}

        self.extend = Extend(self)

        self.BackgroundService = BackgroundService(self)
        self.Browser = Browser(self)
        self.CSS = CSS(self)
        self.DeviceOrientation = DeviceOrientation(self)
        self.DOM = DOM(self)
        self.Emulation = Emulation(self)
        self.Fetch = Fetch(self)
        self.Input = Input(self)
        self.Log = Log(self)
        self.Network = Network(self)
        self.Overlay = Overlay(self)
        self.Page = Page(self)
        self.Runtime = Runtime(self)
        self.SystemInfo = SystemInfo(self)
        self.Target = Target(self)

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def conn_id(self) -> str:
        return self._conn_id

    @property
    def verbose(self) -> bool:
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool) -> None:
        self._verbose = value

    @property
    def browser_name(self) -> str:
        return self._browser_name

    @property
    def is_headless_mode(self) -> bool:
        return self._is_headless_mode

    def __str__(self) -> str:
        return f"<Connection targetId={self.conn_id!r}>"

    def __eq__(self, other: "Connection") -> bool:
        return self.conn_id == other.conn_id

    def __hash__(self) -> int:
        return hash(self.conn_id)

    async def call(
        self, domain_and_method: str,
        params:  Optional[dict] = None
    ) -> Optional[dict]:
        """ Низкоуровневый метод, позволяющий вызывать методы протокола.
        :param domain_and_method:   Название домена и метода через точку,
            как это описано в протоколе. Например: "Page.enable"
        :param params:              Параметры
        """
        self._id += 1
        _id = self._id
        data = {
            "id": _id,
            "params": params if params else {},
            "method": domain_and_method
        }

        que = asyncio.Queue()
        sender, receiver = Sender[dict](que), Receiver[dict](que)
        self.responses[_id] = sender

        await self._send(Serializer.encode(data))

        response = await receiver.recv()
        if "error" in response:

            if ex := get_cdtp_error((e := response['error'])['message']):
                raise ex(
                    f"\n\t\x1b[37mdomain_and_method: '\x1b[91m{domain_and_method}\x1b[37m'"
                    f"\n\tparams: '\x1b[91m{str(params)}\x1b[37m'\x1b[0m"
                )

            raise Exception(
                "\x1b[36mBrowser detect error:\x1b[37m\t\n" +
                f"Error code: '\x1b[91m{e['code']}\x1b[37m'\t\n" +
                f"Error message: '\x1b[91m{e['message']}\x1b[37m'\t\n" +
                f"domain_and_method: '\x1b[91m{domain_and_method}\x1b[37m'\t\n" +
                f"params: '\x1b[91m{params}\x1b[37m'\x1b[0m"
            )

        return response["result"]

    async def _send(self, data: str) -> None:
        if self.connected:
            await self._ws_session.send(data)

    async def _recv(self) -> None:
        while self.connected:
            try:
                data_msg: dict = Serializer.decode(await self._ws_session.recv())
            # ! Браузер разорвал соединение
            except ConnectionClosedError as e:
                if self.verbose:
                    log(f"ConnectionClosedError {e!r}")
                await self._detach()
                return

            # Ожидающие ответов вызовы API получают ответ по id входящих сообщений.
            if sender := self.responses.pop(data_msg.get("id"), None):
                await sender.send(data_msg)

            if ((method := data_msg.get("method")) == "Inspector.detached"
                    and data_msg["params"]["reason"] == "target_closed"):
                await self._detach()
                return

            # Если коллбэк функция была определена, она будет получать все
            #   уведомления из инстанса страницы.
            if self.callback is not None:
                _ = asyncio.create_task(self.callback(data_msg))

            # ? Был вызов из контекста страницы
            if method == "Runtime.bindingCalled":
                name: str = data_msg["params"]["name"]
                payload: str = data_msg["params"]["payload"]

                # ? Есть вызываемый объект с таким именем
                if handle := self._bindings.get(name):
                    function, args = handle
                    _ = asyncio.create_task(
                        function(
                            *Serializer.decode(payload),
                            *args
                        )
                    )

            if listeners := self._listeners_for_event.get(method):
                p = data_msg.get("params") or {}
                for listener, largs in listeners.items():
                    _ = asyncio.create_task(
                        listener(       # корутина
                            p,          # её "params" — всегда передаётся
                            *largs      # список bind-аргументов
                        )
                    )

    async def waitForClose(self) -> None:
        """ Дожидается, пока не будет потеряно соединение со страницей. """
        if self.verbose: log(f"Wait wor close connection {self.conn_id}")
        await self.on_close_event.wait()
        if self.verbose: log(f"Wait for close connection done {self.conn_id}")

    async def activate(self) -> None:
        self._ws_session = await connect(self.ws_url, ping_interval=None)
        self._connected = True
        self._receiver_loop = asyncio.create_task(self._recv())
        await self.Runtime.enable()

    async def disconnect(self) -> None:
        """ Принудительно разрывает соединение. """
        if not self.connected:
            return
        if self.verbose: log(f"[ DISCONNECT ] {self.conn_id}")
        if not self._ws_session.closed:
            await self._ws_session.close()


    async def _detach(self) -> None:
        """  Отключается от страницы. Вызывается автоматически при закрытии браузера,
        или текущей страницы.
        """
        if not self.connected:
            return

        self._receiver_loop.cancel()
        if self.verbose: log(f"[ DETACH ] {self.conn_id}")
        self._connected = False

        if self._on_detach_listener:
            function, args, kvargs = self._on_detach_listener
            await function(*args, **kvargs)

        self.on_close_event.set()

    def clearOnDetach(self) -> None:
        self._on_detach_listener = tuple()

    def setOnDetach(self, function: Callable[[any], CoroTypeNone], *args, **kvargs) -> bool:
        """  Регистрирует асинхронный коллбэк, который будет вызван с соответствующими аргументами
        при разрыве соединения со страницей.
        """
        if not iscoroutinefunction(function):
            raise TypeError("OnDetach-listener must be a async callable object!")
        if not self.connected:
            return False
        self._on_detach_listener = function, args, kvargs
        return True

    async def bindFunction(self, function: Callable[[any], CoroTypeNone], *args: Any) -> None:
        """ Регистрирует имя в глобальном контексте страницы. Это имя затем используется
        в вызове функции, принимающей ровно один, строковый аргумент, который передаётся
        в тело события `Runtime.bindingCalled`.
        """
        if not iscoroutinefunction(function):
            raise TypeError("Listener must be a async callable object!")

        self._bindings[function.__name__] = function, args
        await self.Runtime.addBinding(function.__name__)
        await self.extend.pyCallAddOnload()

    async def bindFunctions(
            self, *handlers_n_args: Tuple[Callable[[any], CoroTypeNone], Iterable]) -> None:
        """ Выполняет множественную регистрацию.
        :param handlers_n_args:     Список двухэлементных последовательностей,
        в которых:
            - первый элемент: awaitable-объект
            - второй элемент: последовательность аргументов любой длины, которая
                будет передана первому элементу в последнюю очередь.
        """
        for function, args in handlers_n_args:
            await self.bindFunction(function, *args)
        await self.extend.pyCallAddOnload()

    async def unbindFunctions(self, *functions: Union[Callable[[any], CoroTypeNone], str]) -> None:
        """ Прекращает генерацию событий `Runtime.bindingCalled` для указанных имён.
        :param functions:  Список функций, или их имён.
        """
        for function in functions:
            name = function if type(function) is str else function.__name__
            self._bindings.pop(name)
            await self.Runtime.removeBinding(name)

    async def addListenerForEvent(
        self, event: Union[str, DomainEvent], listener: Callable[[dict, tuple], CoroTypeNone], *args) -> None:
        """ Регистрирует слушателя, который будет вызываться при генерации определённых событий
        в браузере. Список таких событий можно посмотреть в разделе "Events" почти
        у каждого домена по адресу: https://chromedevtools.github.io/devtools-protocol/
        Например: 'DOM.attributeModified'

        :param event:           Имя события, для которого регистируется слушатель. Например:
                                    'DOM.attributeModified'.
        :param listener:        Колбэк-функция.
        :param args:            (optional) любое кол-во агрументов, которые будут переданы
                                    в функцию последними.
        :return:        None
        """
        if not iscoroutinefunction(listener):
            raise TypeError("Listener must be a async callable object!")

        e: str = event if type(event) is str else event.value
        if e not in self._listeners_for_event:
            self._listeners_for_event[e]: dict = {}
        self._listeners_for_event[e][listener] = args

    def removeListenerForEvent(
            self, event: Union[str, DomainEvent], listener: Callable[[dict, tuple], CoroTypeNone]) -> None:
        """  Удаляет регистрацию слушателя для указанного события.
        :param event:           Имя метода, для которого была регистрация.
        :param listener:        Колбэк-функция, которую нужно удалить.
        :return:        None
        """
        e = event if type(event) is str else event.value
        if not iscoroutinefunction(listener):
            raise TypeError("Listener must be a async callable object!")
        if m := self._listeners_for_event.get(e):
            if listener in m:
                m.pop(listener)


    def removeListenersForEvent(self, event: Union[str, DomainEvent]) -> None:
        """
        Удаляет регистрацию метода и слушателей вместе с ним для указанного события.
        :param event:          Имя метода, для которого была регистрация.
        :return:        None
        """
        e = event if type(event) is str else event.value
        if e in self._listeners_for_event:
            self._listeners_for_event.pop(e)

    def __del__(self) -> None:
        if self.verbose: log(f"[ DELETED ] {self.conn_id}")
