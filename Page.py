try:
    import ujson as json
except ModuleNotFoundError:
    import json
import asyncio
import websockets.client

from aio_dt_protocol.exceptions import EvaluateError, exception_store

from websockets.exceptions import ConnectionClosedError
from inspect import iscoroutinefunction
from typing import Callable, Optional, Union, Tuple
from abc import ABC
from aio_dt_protocol.Data import DomainEvent

class AbsPage(ABC):
    __slots__ = (
        "ws_url", "page_id", "frontend_url", "callback", "is_headless_mode", "verbose", "browser_name", "id",
        "responses", "connected", "ws_session", "receiver", "listeners", "listeners_for_event", "runtime_enabled",
        "_connected", "_page_id", "_verbose", "_browser_name", "_is_headless_mode"
    )

    def __init__(
        self,
        ws_url:           str,
        page_id:          str,
        frontend_url:     str,
        callback:         callable,
        is_headless_mode: bool,
        verbose:          bool,
        browser_name:     str
    ) -> None:
        self.ws_url            = ws_url
        self.page_id           = page_id
        self.frontend_url      = frontend_url
        self.callback          = callback
        self.is_headless_mode  = is_headless_mode

        self.verbose           = verbose
        self.browser_name      = browser_name

        self.id                = 0
        self.responses         = {}
        self.connected         = False
        self.ws_session        = None
        self.receiver          = None
        self.listeners         = {}
        self.listeners_for_event = {}
        self.runtime_enabled     = False


class Page(AbsPage):
    """
    Инстанс страницы должен быть активирован после создания вызовом метода Activate(),
        это создаст подключение по WebSocket и запустит задачи обеспечивающие
        обратную связь. Метод GetPageBy() инстанса браузера, заботится об этом
        по умолчанию.

    Если инстанс страницы более не нужен, например, при перезаписи в него нового
        инстанса, перед этим [-!-] ОБЯЗАТЕЛЬНО [-!-] - вызовите у него метод
        Detach(), или закройте вкладку/страницу браузера, с которой он связан,
        тогда это будет выполнено автоматом. Иначе в цикле событий останутся
        задачи связанные с поддержанием соединения, которое более не востребовано.
    """
    __slots__ = ()

    def __init__(
        self,
        ws_url:           str,
        page_id:          str,
        frontend_url:     str,
        callback:         callable,
        is_headless_mode: bool,
        verbose:          bool,
        browser_name:     str
    ) -> None:
        """
        :param ws_url:              Адрес WebSocket
        :param page_id:             Идентификатор страницы
        :param frontend_url:        devtoolsFrontendUrl по которому происходит подключение к дебаггеру
        :param callback:            Колбэк, который будет получать все данные,
                                        приходящие по WebSocket в виде словарей
        :param is_headless_mode:    "Headless" включён?
        :param verbose:             Печатать некие подробности процесса?
        :param browser_name:        Имя браузера
        """
        AbsPage.__init__(self, ws_url, page_id, frontend_url, callback, is_headless_mode, verbose, browser_name)

    @property
    def connected(self) -> bool: return self._connected

    @connected.setter
    def connected(self, value) -> None: self._connected = value

    @property
    def page_id(self) -> str: return self._page_id

    @page_id.setter
    def page_id(self, value) -> None: self._page_id = value

    @property
    def verbose(self) -> bool: return self._verbose

    @verbose.setter
    def verbose(self, value) -> None: self._verbose = value

    @property
    def browser_name(self) -> str: return self._browser_name

    @browser_name.setter
    def browser_name(self, value) -> None: self._browser_name = value

    @property
    def is_headless_mode(self) -> bool: return self._is_headless_mode

    @is_headless_mode.setter
    def is_headless_mode(self, value) -> None: self._is_headless_mode = value

    async def Call(
        self, domain_and_method: str,
        params:            Optional[dict] = None,
        wait_for_response: Optional[bool] = True
    ) -> Union[dict, None]:
        self.id += 1
        _id = self.id
        data = {
            "id": _id,
            "params": params if params else {},
            "method": domain_and_method
        }

        if wait_for_response:
            self.responses[_id] = None

        await self._Send(json.dumps(data))

        if not wait_for_response:
            return

        while not self.responses[ _id ]:
            await asyncio.sleep(.01)

        response = self.responses.pop( _id )
        if "error" in response:

            for title, ex in exception_store.items():
                if title in response['error']['message']:
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
        objectGroup:            Optional[str] = "console",
        includeCommandLineAPI: Optional[bool] = True,
        silent:                Optional[bool] = False,
        returnByValue:         Optional[bool] = False,
        userGesture:           Optional[bool] = True,
        awaitPromise:          Optional[bool] = False
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
            raise EvaluateError(response["result"]["description"])
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
                if self.verbose: print(f"[<- V ->] | ConnectionClosedError '{e}'")
                self.Detach()
                return

            if ("method" in data_msg and data_msg["method"] == "Inspector.detached"
                    and data_msg["params"]["reason"] == "target_closed"):
                self.Detach()
                return

            # Ожидающие ответов вызовы API получают ответ по id входящих сообщений.
            if (data_id := data_msg.get("id")) and data_id in self.responses:
                self.responses[data_id] = data_msg

            # Если коллбэк функция была определена, она будет получать все
            #   уведомления из инстанса страницы.
            if self.callback is not None:
                asyncio.create_task(self.callback(data_msg))

            # Достаточно вызвать в контексте страницы следующее:
            # console.info(JSON.stringify({
            #     funcName: "testFunc",
            #     args: [1, "test"]
            # }))
            # и если среди зарегистрированных слушателей есть с именем "testFunc",
            #   то он немедленно получит распакованный список args[ ... ], вместе
            #   с переданными ему аргументами, если таковые имеются.
            method: str = data_msg.get("method")
            if (    # =============================================================
                    self.listeners
                            and
                    method == "Runtime.consoleAPICalled"
                            and
                    data_msg["params"].get("type") == "info"
            ):      # =============================================================
                str_value = data_msg["params"]["args"][0].get("value")
                try:
                    value = json.loads(str_value)
                except ValueError as e:
                    if self.verbose:
                        print("[<- V ->] | ValueError", e)
                        print("[<- V ->] | Msg from browser", str_value)
                else:
                    if listener := self.listeners.get( value.get("funcName") ):
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


    def Detach(self) -> None:
        """
        Отключается от инстанса страницы. Вызывается автоматически при закрытии браузера,
            или инстанса текущей страницы. Принудительный вызов не закрывает страницу,
            а лишь разрывает с ней соединение.
        """
        if not self.connected:
            return

        self.receiver.cancel()
        if self.verbose: print("[<- V ->] [ DETACH ]", self.page_id)
        self.connected = False

    async def Activate(self) -> None:
        self.ws_session = await websockets.client.connect(self.ws_url, ping_interval=None)
        self.connected = True
        self.receiver = asyncio.create_task(self._Recv())
        if self.callback is not None and not self.runtime_enabled:
            await self.Call("Runtime.enable")
            self.runtime_enabled = True

    async def AddListener(self, listener: Callable, *args: Optional[any]) -> None:
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

        :param listener:        Асинхронная колбэк-функция.
        :param args:            (optional) любое кол-во агрументов, которые будут переданы
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

    async def AddListeners(self, *list_of_tuple_listeners_and_args: Tuple[Callable, list]) -> None:
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

    def RemoveListener(self, listener: Callable) -> None:
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
        self, event: Union[str, DomainEvent], listener: Callable, *args) -> None:
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

    def RemoveListenerForEvent(self, event: Union[str, DomainEvent], listener: Callable) -> None:
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


    def RemoveListenersForEvent(self, event: str) -> None:
        """
        Удаляет регистрацию метода и слушателей вместе с ним для указанного события.
        :param event:          Имя метода, для которого была регистрация.
        :return:        None
        """
        if event in self.listeners_for_event:
            self.listeners_for_event.pop(event)

    def __del__(self) -> None:
        if self.verbose: print("[<- V ->] [ DELETED ]", self.page_id)
