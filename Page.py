import asyncio
import websockets
from websockets.exceptions import ConnectionClosedError
import json
from typing import Callable, Optional, Union

class Page:
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

    def __init__(
            self,
            ws_url:           str,
            page_id:          str,
            callback:         callable,
            is_headless_mode: bool,
            verbose:          bool,
            browser_name:     str
    ) -> None:
        """
        :param ws_url:              Адрес WebSocket
        :param page_id:             Идентификатор страницы
        :param callback:            Колбэк, который будет получать все данные,
                                        приходящие по WebSocket в виде словарей
        :param is_headless_mode:    "Headless" включён?
        :param verbose:             Печатать некие подробности процесса?
        :param browser_name:        Имя браузера
        """
        self.ws_url            = ws_url
        self.page_id           = page_id
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
        self.listeners_for_method = {}
        self.runtime_enabled      = False

    async def Call(
            self, domain_and_method: str,
                       params: Optional[dict] = None,
            wait_for_response: Optional[bool] = True
    ) -> Union[dict, None]:
        self.id += 1
        _id = self.id
        data = {
            "id": _id,
            "params": params if params else {},
            "method": domain_and_method
        }

        await self._Send(json.dumps(data))
        if not wait_for_response: return

        self.responses[ _id ] = None
        while not self.responses[ _id ]:
            await asyncio.sleep(.01)

        response = self.responses.pop( _id )
        if "error" in response:
            raise Exception(
                "Browser detect error:\n" +
                f"error code -> '{response['error']['code']}';\n" +
                f"error message -> '{response['error']['message']}'\n"+
                f"domain_and_method = '{domain_and_method}' | params = '{str(params)}'"
            )
        return response["result"]

    async def Eval(
            self, expression: str,
                      objectGroup:  Optional[str] = "console",
            includeCommandLineAPI: Optional[bool] = True,
                           silent: Optional[bool] = False,
                    returnByValue: Optional[bool] = False,
                      userGesture: Optional[bool] = True,
                     awaitPromise: Optional[bool] = False
    ) -> dict:
        response = await self.Call(
            "Runtime.evaluate",
            {
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
            raise Exception(str(response["result"]["description"]) + " => " + str(response["exceptionDetails"]))
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
                data_msg = {}
                self.Detach()

            if ("method" in data_msg and data_msg["method"] == "Inspector.detached"
                    and data_msg["params"]["reason"] == "target_closed"):
                self.Detach()

            # Ожидающие ответов вызовы API получают ответ по id входящих сообщений.
            if "id" in data_msg and data_msg["id"] in self.responses:
                self.responses[data_msg["id"]] = data_msg

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
            method = data_msg.get("method")
            if (    # =============================================================
                    self.listeners
                            and
                    method == "Runtime.consoleAPICalled"
                            and
                    data_msg["params"].get("type") == "info"
            ):      # =============================================================
                value = json.loads(data_msg["params"]["args"][0].get("value"))
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
                    self.listeners_for_method
                            and
                    method in self.listeners_for_method
            ):      # =============================================================
                # Получаем словарь слушателей, в котором ключи — слушатели
                #   значения — их аргументы.
                listeners: dict = self.listeners_for_method[ method ]
                p = data_msg.get("params")
                for listener, args in listeners.items():
                    asyncio.create_task(
                        listener(                                           # корутина
                            p if p is not None else [],                     # её список аргументов вызова
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
        self.ws_session = await websockets.connect(self.ws_url, ping_interval=None)
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
                def test_func(id, text):
                    print(id, text)

        :param listener:        Колбэк-функция.
        :param args:            (optional) любое кол-во агрументов, которые будут переданы
                                    в функцию последними.
        :return:        None
        """
        if listener.__name__ not in self.listeners:
            self.listeners[ listener.__name__ ] = {"function": listener, "args": args}
            if not self.runtime_enabled:
                await self.Call("Runtime.enable")
                self.runtime_enabled = True

    def RemoveListener(self, listener: Callable) -> None:
        """
        Удаляет слушателя.
        :param listener:        Колбэк-функция.
        :return:        None
        """
        if listener.__name__ in self.listeners:
            del self.listeners[ listener.__name__ ]

    async def AddListenerForEvent(
            self, event: str, listener: Callable, *args: Optional[any]) -> None:
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
        if event not in self.listeners_for_method:
            self.listeners_for_method[event]: dict = {}
        self.listeners_for_method[ event][listener] = args
        if not self.runtime_enabled:
            await self.Call("Runtime.enable")
            self.runtime_enabled = True

    def RemoveListenerForEvent(self, event: str, listener: Callable) -> None:
        """
        Удаляет регистрацию слушателя для указанного метода.
        :param event:           Имя метода, для которого была регистрация.
        :param listener:        Колбэк-функция, которую нужно удалить.
        :return:        None
        """
        if m := self.listeners_for_method.get(event):
            if listener in m: m.pop(listener)


    def RemoveListenersForEvent(self, event: str) -> None:
        """
        Удаляет регистрацию метода и слушателей вместе с ним для указанного метода.
        :param event:          Имя метода, для которого была регистрация.
        :return:        None
        """
        self.listeners_for_method.pop(event)

    def __del__(self) -> None:
        if self.verbose: print("[<- V ->] [ DELETED ]", self.page_id)
