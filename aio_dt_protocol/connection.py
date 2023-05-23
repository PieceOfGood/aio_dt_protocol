try:
    import ujson as json
except ModuleNotFoundError:
    import json
import asyncio
import websockets.client

from .exceptions import EvaluateError, get_cdtp_error, highlight_eval_error, PromiseEvaluateError, \
    highlight_promise_error
from .utils import log

from websockets.exceptions import ConnectionClosedError
from inspect import iscoroutinefunction
from typing import Callable, Awaitable, Optional, Union, Tuple, List, Dict
from .data import DomainEvent, Sender, Receiver, CommonCallback
from .extend_connection import Extend

from .domains.browser import Browser
from .domains.css import CSS
from .domains.page import Page
from .domains.fetch import Fetch
from .domains.target import Target


class Connection:
    """ Инстанс страницы должен быть активирован после создания вызовом метода Activate(),
    это создаст подключение по WebSocket и запустит задачи обеспечивающие
    обратную связь. Метод GetPageBy() инстанса браузера, заботится об этом
    по умолчанию.

        Если инстанс страницы более не нужен, например, при перезаписи в него нового
    инстанса, перед этим [-!-] ОБЯЗАТЕЛЬНО [-!-] - вызовите у него метод
    Detach(), или закройте вкладку/страницу браузера, с которой он связан,
    тогда это будет выполнено автоматом. Иначе в цикле событий останутся
    задачи связанные с поддержанием соединения, которое более не востребовано.
    """
    __slots__ = (
        "ws_url", "frontend_url", "callback", "id", "extend",
        "responses", "ws_session", "receiver", "on_detach_listener", "listeners", "listeners_for_event",
        "runtime_enabled", "on_close_event", "context_manager", "_connected", "_conn_id", "_verbose",
        "_browser_name", "_is_headless_mode",

        "Browser", "CSS", "Page", "Fetch", "Target",
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
        :param ws_url:              Адрес WebSocket
        :param conn_id:             Идентификатор страницы
        :param frontend_url:        devtoolsFrontendUrl по которому происходит подключение к дебаггеру
        :param callback:            Колбэк, который будет получать все данные,
                                        приходящие по WebSocket в виде словарей
        :param is_headless_mode:    "Headless" включён?
        :param verbose:             Печатать некие подробности процесса?
        :param browser_name:        Имя браузера
        """

        self.ws_url = ws_url
        self._conn_id = conn_id
        self.frontend_url = frontend_url
        self.callback = callback
        self._is_headless_mode = is_headless_mode

        self._verbose = verbose
        self._browser_name = browser_name

        self.id = 0
        self._connected = False
        self.ws_session = None
        self.receiver = None
        self.on_detach_listener: List[Callable[[any], Awaitable[None]], list, dict] = []
        self.listeners = {}
        self.listeners_for_event = {}
        self.runtime_enabled = False
        self.on_close_event = asyncio.Event()
        self.responses: Dict[int, Optional[Sender[dict]]] = {}

        self.extend = Extend(self)

        self.Browser = Browser(self)
        self.CSS = CSS(self)
        self.Page = Page(self)
        self.Fetch = Fetch(self)
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

    async def Call(
        self, domain_and_method: str,
        params:  Optional[dict] = None,
        wait_for_response: bool = True
    ) -> Optional[dict]:
        self.id += 1
        _id = self.id
        data = {
            "id": _id,
            "params": params if params else {},
            "method": domain_and_method
        }

        if not wait_for_response:
            self.responses[_id] = None
            await self._Send(json.dumps(data))
            return

        que = asyncio.Queue()
        sender, receiver = Sender[dict](que), Receiver[dict](que)
        self.responses[_id] = sender

        await self._Send(json.dumps(data))

        response = await receiver.recv()
        if "error" in response:

            if ex := get_cdtp_error(response['error']['message']):
                raise ex(f"domain_and_method = '{domain_and_method}' | params = '{str(params)}'")

            raise Exception(
                "Browser detect error:\n" +
                f"error code -> '{response['error']['code']}';\n" +
                f"error message -> '{response['error']['message']}'\n"+
                f"domain_and_method = '{domain_and_method}' | params = '{str(params)}'"
            )

        return response["result"]

    async def Eval(
        self, expression: str,
        objectGroup:            str = "console",
        includeCommandLineAPI: bool = True,
        silent:                bool = False,
        returnByValue:         bool = False,
        userGesture:           bool = True,
        awaitPromise:          bool = False
    ) -> dict:
        response = await self.Call(
            "Runtime.evaluate", {
                "expression": expression,
                "objectGroup": objectGroup,
                "includeCommandLineAPI": includeCommandLineAPI,
                "silent": silent,
                "returnByValue": returnByValue,
                "userGesture": userGesture,
                "awaitPromise": awaitPromise
            }
        )
        if "exceptionDetails" in response:
            raise EvaluateError(
                highlight_eval_error(response["result"]["description"], expression)
            )
        return response["result"]

    async def _Send(self, data: str) -> None:
        if self.connected:
            await self.ws_session.send(data)

    async def _Recv(self) -> None:
        while self.connected:
            try:
                data_msg: dict = json.loads(await self.ws_session.recv())
            # ! Браузер разорвал соединение
            except ConnectionClosedError as e:
                if self.verbose: log(f"ConnectionClosedError {e!r}")
                await self.Detach()
                return

            if ("method" in data_msg and data_msg["method"] == "Inspector.detached"
                    and data_msg["params"]["reason"] == "target_closed"):
                self.on_close_event.set()
                await self.Detach()
                return

            # Ожидающие ответов вызовы API получают ответ по id входящих сообщений.
            if sender := self.responses.pop(data_msg.get("id"), None):
                await sender.send(data_msg)

            # Если коллбэк функция была определена, она будет получать все
            #   уведомления из инстанса страницы.
            if self.callback is not None:
                asyncio.create_task(self.callback(data_msg))

            # Достаточно вызвать в контексте страницы следующее:
            # console.info(JSON.stringify({
            #     func_name: "test_func",
            #     args: [1, "test"]
            # }))
            # и если среди зарегистрированных слушателей есть с именем "test_func",
            #   то он немедленно получит распакованный список args[ ... ], вместе
            #   с переданными ему аргументами, если таковые имеются.
            if (method := data_msg.get("method")) == "Runtime.consoleAPICalled":
                # ? Был вызван домен "info"
                if data_msg["params"].get("type") == "info":

                    str_value = data_msg["params"]["args"][0].get("value")
                    try:
                        value: dict = json.loads(str_value)
                    except ValueError as e:
                        if self.verbose:
                            log(f"ValueError {e!r}")
                            log(f"Msg from browser {str_value!r}")
                        raise

                    # ? Есть ожидающие слушатели
                    if self.listeners:

                        # ? Если есть ожидающая корутина
                        if listener := self.listeners.get( value.get("func_name") ):
                            asyncio.create_task(
                                listener["function"](                               # корутина
                                    *(value["args"] if "args" in value else []),    # её список аргументов вызова
                                    *listener["args"]                               # список bind-агрументов
                                )
                            )

            # По этой же схеме будут вызваны все слушатели для обработки
            #   определённого метода, вызванного в контексте страницы,
            #   если для этого метода они зарегистрированы.
            if (    # =============================================================
                    self.listeners_for_event
                            and
                    method in self.listeners_for_event
            ):      # =============================================================
                # Получаем словарь слушателей, в котором ключи — слушатели,
                #   значения — их аргументы.
                listeners: dict = self.listeners_for_event[ method ]
                p = data_msg.get("params")
                for listener, args in listeners.items():
                    asyncio.create_task(
                        listener(                                           # корутина
                            p if p is not None else {},                     # её "params" — всегда передаётся
                            *args                                           # список bind-агрументов
                        )
                    )

    async def EvalPromise(self, script: str) -> dict:
        """ Выполняет асинхронный код на странице и возвращает результат.
        !!! ВАЖНО !!! Выполняемый код не может возвращать какие-либо JS
        типы, поэтому должен возвращать JSON-сериализованный набор данных.
        """
        result = await self.Eval(script)
        args = dict(
            promiseObjectId=result["objectId"],
            returnByValue=False,
            generatePreview=False
        )
        response = await self.Call("Runtime.awaitPromise", args)
        if "exceptionDetails" in response:
            raise PromiseEvaluateError(
                highlight_promise_error(response["result"]["description"]) +
                "\n" + json.dumps(response["exceptionDetails"])
            )
        return json.loads(response["result"]["value"])

    async def WaitForClose(self) -> None:
        """ Дожидается, пока не будет потеряно соединение со страницей. """
        await self.on_close_event.wait()

    async def Detach(self) -> None:
        """
        Отключается от инстанса страницы. Вызывается автоматически при закрытии браузера,
            или инстанса текущей страницы. Принудительный вызов не закрывает страницу,
            а лишь разрывает с ней соединение.
        """
        if not self.connected:
            return

        self.receiver.cancel()
        if self.verbose: log(f"[ DETACH ] {self.conn_id}")
        self._connected = False

        if self.on_detach_listener:
            function, args, kvargs = self.on_detach_listener
            await function(*args, **kvargs)

    def RemoveOnDetach(self) -> None:
        self.on_detach_listener = []

    def SetOnDetach(self, function: Callable[[any], Awaitable[None]], *args, **kvargs) -> bool:
        """
        Регистрирует асинхронный коллбэк, который будет вызван с соответствующими аргументами
            при разрыве соединения со страницей.
        """
        if not iscoroutinefunction(function):
            raise TypeError("OnDetach-listener must be a async callable object!")
        if not self.connected:
            return False
        self.on_detach_listener = [function, args, kvargs]
        return True

    async def Activate(self) -> None:
        self.ws_session = await websockets.client.connect(self.ws_url, ping_interval=None)
        self._connected = True
        self.receiver = asyncio.create_task(self._Recv())
        if self.callback is not None:
            await self.Call("Runtime.enable")
            self.runtime_enabled = True

    async def AddListener(self, listener: Callable[[any], Awaitable[None]], *args: any) -> None:
        """
        Добавляет 'слушателя', который будет ожидать свой вызов по имени функции.
            Вызов слушателей из контекста страницы осуществляется за счёт
            JSON-сериализованного объекта, отправленного сообщением в консоль,
            через домен 'info'. Объект должен содержать два обязательных свойства:
                funcName — имя вызываемого слушателя
                args:    — массив аргументов

            Например, вызов javascript-кода:
                console.info(JSON.stringify({
                    funcName: "test_func",
                    args: [1, "test"]
                }))
            Вызовет следующего Python-слушателя:
                async def test_func(id, text, action):
                    print(id, text, action)
            Зарегистрированного следующим образом:
                await page.AddListener(test_func, "test-action")

            !!! ВНИМАНИЕ !!! В качестве слушателя может выступать ТОЛЬКО асинхронная
                функция, или метод.

        :param listener:        Асинхронная функция.
        :param args:            (optional) любое кол-во аргументов, которые будут переданы
                                    в функцию последними.
        :return:        None
        """
        if not iscoroutinefunction(listener):
            raise TypeError("Listener must be a async callable object!")
        if listener.__name__ not in self.listeners:
            self.listeners[ listener.__name__ ] = {"function": listener, "args": args}
            if not self.runtime_enabled:
                await self.Call("Runtime.enable")
                self.runtime_enabled = True

    async def AddListeners(
            self, *list_of_tuple_listeners_and_args: Tuple[Callable[[any], Awaitable[None]], list]) -> None:
        """
        Делает то же самое, что и AddListener(), но может зарегистрировать сразу несколько слушателей.
            Принимает список кортежей с двумя элементами, вида (async_func_or_method, list_args), где:
                async_func_or_method    - асинхронная фукция или метод
                list_args               - список её аргументов(может быть пустым)
        """
        for action in list_of_tuple_listeners_and_args:
            listener, args = action
            if not iscoroutinefunction(listener):
                raise TypeError("Listener must be a async callable object!")
            if listener.__name__ not in self.listeners:
                self.listeners[listener.__name__] = {"function": listener, "args": args}
                if not self.runtime_enabled:
                    await self.Call("Runtime.enable")
                    self.runtime_enabled = True

    def RemoveListener(self, listener: Callable[[any], Awaitable[None]]) -> None:
        """
        Удаляет слушателя.
        :param listener:        Колбэк-функция.
        :return:        None
        """
        if not iscoroutinefunction(listener):
            raise TypeError("Listener must be a async callable object!")
        if listener.__name__ in self.listeners:
            del self.listeners[ listener.__name__ ]

    async def AddListenerForEvent(
        self, event: Union[str, DomainEvent], listener: Callable[[any], Awaitable[None]], *args) -> None:
        """
        Регистирует слушателя, который будет вызываться при вызове определённых событий
            в браузере. Список таких событий можно посмотреть в разделе "Events" почти
            у каждого домена по адресу: https://chromedevtools.github.io/devtools-protocol/
            Например: 'DOM.attributeModified'
        !Внимание! Каждый такой слушатель должен иметь один обязательный 'data'-аргумент,
            в который будут передаваться параметры случившегося события в виде словаря(dict).

        :param event:           Имя события, для которого регистируется слушатель. Например:
                                    'DOM.attributeModified'.
        :param listener:        Колбэк-функция.
        :param args:            (optional) любое кол-во агрументов, которые будут переданы
                                    в функцию последними.
        :return:        None
        """
        e = event if type(event) is str else event.value
        if not iscoroutinefunction(listener):
            raise TypeError("Listener must be a async callable object!")
        if e not in self.listeners_for_event:
            self.listeners_for_event[ e ]: dict = {}
        self.listeners_for_event[ e ][listener] = args
        if not self.runtime_enabled:
            await self.Call("Runtime.enable")
            self.runtime_enabled = True

    def RemoveListenerForEvent(
            self, event: Union[str, DomainEvent], listener: Callable[[any], Awaitable[None]]) -> None:
        """
        Удаляет регистрацию слушателя для указанного события.
        :param event:           Имя метода, для которого была регистрация.
        :param listener:        Колбэк-функция, которую нужно удалить.
        :return:        None
        """
        e = event if type(event) is str else event.value
        if not iscoroutinefunction(listener):
            raise TypeError("Listener must be a async callable object!")
        if m := self.listeners_for_event.get( e ):
            if listener in m: m.pop(listener)


    def RemoveListenersForEvent(self, event: Union[str, DomainEvent]) -> None:
        """
        Удаляет регистрацию метода и слушателей вместе с ним для указанного события.
        :param event:          Имя метода, для которого была регистрация.
        :return:        None
        """
        e = event if type(event) is str else event.value
        if e in self.listeners_for_event:
            self.listeners_for_event.pop(e)

    def __del__(self) -> None:
        if self.verbose: log(f"[ DELETED ] {self.conn_id}")
