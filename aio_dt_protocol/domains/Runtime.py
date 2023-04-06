try:
    import ujson as json
except ModuleNotFoundError:
    import json
from abc import ABC, abstractmethod
from typing import Optional, Union, List, Literal, Callable
from dataclasses import dataclass, field
from ..Data import DomainEvent
from ..exceptions import PromiseEvaluateError, highlight_promise_error


class Runtime(ABC):
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Runtime
    """
    __slots__ = ()

    def __init__(self):
        self.runtime_enabled = False
        self.context_manager = ContextManager()

    @property
    def connected(self) -> bool:
        return False

    @property
    def verbose(self) -> bool:
        return False

    @property
    def page_id(self) -> str:
        return ""

    async def GetProperties(
            self, objectId: str,
            skip_complex_types: bool = True,
            ownProperties: Optional[bool] = None,
            accessorPropertiesOnly: Optional[bool] = None,
            generatePreview: Optional[bool] = None,
            nonIndexedPropertiesOnly: Optional[bool] = None,
    ) -> List["RuntimeType.PropertyDescriptor"]:
        """ Возвращает свойства заданного объекта. Группа объектов результата наследуется
        от целевого объекта.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime/#method-getProperties
        :param objectId:                    Идентификатор объекта, для которого возвращаются свойства.
        :param ownProperties:               Если true, возвращает свойства, принадлежащие только самому
                                                элементу, а не его цепочке прототипов.
        :param accessorPropertiesOnly:      Если true, возвращает только свойства доступа (с геттером/сеттером);
                                                внутренние свойства также не возвращаются.
        :param generatePreview:             Должен ли быть создан предварительный просмотр для результатов.
        :param nonIndexedPropertiesOnly:    Если true, возвращает только неиндексированные свойства.
        :return:    {
            "result": array[ PropertyDescriptor ],
            "internalProperties":  list[ InternalPropertyDescriptor ],
            "privateProperties":  list[ PrivatePropertyDescriptor ],
            "exceptionDetails": dict{ ExceptionDetails }
        }
        """
        args = {"objectId": objectId}
        if ownProperties: args.update({"ownProperties": ownProperties})
        if accessorPropertiesOnly: args.update({"accessorPropertiesOnly": accessorPropertiesOnly})
        if generatePreview: args.update({"generatePreview": generatePreview})
        if nonIndexedPropertiesOnly: args.update({"nonIndexedPropertiesOnly": nonIndexedPropertiesOnly})
        response = await self.Call("Runtime.getProperties", args)
        if "exceptionDetails" in response:
            raise PromiseEvaluateError(
                highlight_promise_error(response["result"]["description"]) +
                "\n" + json.dumps(response["exceptionDetails"])
            )
        if not skip_complex_types:
            return [RuntimeType.PropertyDescriptor(**p) for p in response["result"]]

        result = []
        for p in response["result"]:
            if (subtype := p["value"].get("type")) and subtype == "function":
                continue
            result.append(RuntimeType.PropertyDescriptor(**p))
        return result


    async def AwaitPromise(
            self, promiseObjectId: str, returnByValue: bool = False, generatePreview: bool = False
    ) -> dict:
        """
        Добавляет обработчик к промису с переданным идентификатором.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-awaitPromise
        :param promiseObjectId:     Идентификатор промиса.
        :param returnByValue:       (optional) Ожидается ли результат в виде объекта JSON,
                                        который должен быть отправлен по значению.
        :param generatePreview:     (optional) Должен ли предварительный просмотр
                                        генерироваться для результата.
        :return:                    {
                                        "result": dict(https://chromedevtools.github.io/devtools-protocol/tot/Runtime#type-RemoteObject)
                                        "exceptionDetails": dict(https://chromedevtools.github.io/devtools-protocol/tot/Runtime#type-ExceptionDetails)
                                    }
        """
        args = {"promiseObjectId": promiseObjectId, "returnByValue": returnByValue, "generatePreview": generatePreview}
        response = await self.Call("Runtime.awaitPromise", args)
        if "exceptionDetails" in response:
            raise PromiseEvaluateError(
                highlight_promise_error(response["result"]["description"]) +
                "\n" + json.dumps(response["exceptionDetails"])
            )
        return response["result"]

    async def CallFunctionOn(
            self, functionDeclaration: str,
            objectId: Optional[str] = None,
            arguments: Optional[list] = None,
            silent: Optional[bool] = None,
            returnByValue: Optional[bool] = None,
            generatePreview: Optional[bool] = None,
            userGesture: Optional[bool] = None,
            awaitPromise: Optional[bool] = None,
            executionContextId: Optional[int] = None,
            objectGroup: Optional[str] = None
    ) -> dict:
        """
        Вызывает функцию с заданным объявлением для данного объекта. Группа объектов результата
            наследуется от целевого объекта.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-callFunctionOn
        :param functionDeclaration:     Объявление функции для вызова.
        :param objectId:                (optional) Идентификатор объекта для вызова функции.
                                            Должен быть указан либо objectId, либо executeContextId.
        :param arguments:               (optional) Аргументы. Все аргументы вызова должны
                                            принадлежать тому же миру JavaScript, что и целевой
                                            объект.
        :param silent:                  (optional) В тихом режиме исключения, выданные во время оценки,
                                            не регистрируются и не приостанавливают выполнение.
                                            Переопределяет 'setPauseOnException' состояние.
        :param returnByValue:           (optional) Ожидается ли результат в виде объекта JSON,
                                            который должен быть отправлен по значению.
        :param generatePreview:         (optional, EXPERIMENTAL) Должен ли предварительный
                                            просмотр генерироваться для результата.
        :param userGesture:             (optional) Должно ли выполнение рассматриваться как
                                            инициированное пользователем в пользовательском интерфейсе.
        :param awaitPromise:            (optional) Решено ли выполнение await для полученного значения
                                            и возврата после ожидаемого обещания.
        :param executionContextId:      (optional) Определяет контекст выполнения, в котором будет
                                            использоваться глобальный объект для вызова функции.
                                            Должен быть указан либо executeContextId, либо objectId.
        :param objectGroup:             (optional) Символическое имя группы, которое можно
                                            использовать для освобождения нескольких объектов. Если
                                            objectGroup не указан, а objectId равен, objectGroup
                                            будет унаследован от объекта.
        :return:                        { ... } - https://chromedevtools.github.io/devtools-protocol/tot/Runtime/#type-RemoteObject
        """
        args = {"functionDeclaration": functionDeclaration}
        if objectId is not None:
            args.update({"objectId": objectId})
        if arguments is not None:
            args.update({"arguments": arguments})
        if silent is not None:
            args.update({"silent": silent})
        if returnByValue is not None:
            args.update({"returnByValue": returnByValue})
        if generatePreview is not None:
            args.update({"generatePreview": generatePreview})
        if userGesture is not None:
            args.update({"userGesture": userGesture})
        if awaitPromise is not None:
            args.update({"awaitPromise": awaitPromise})
        if executionContextId is not None:
            args.update({"executionContextId": executionContextId})
        if objectGroup is not None:
            args.update({"objectGroup": objectGroup})
        response = await self.Call("Runtime.callFunctionOn", args)
        if "exceptionDetails" in response:
            raise Exception(response["result"]["description"] + "\n" + json.dumps(response["exceptionDetails"]))
        return response["result"]

    async def RuntimeEnable(self, watch_for_execution_contexts: bool = False) -> None:
        """
        Включает создание отчетов о создании контекстов выполнения с помощью события executeContextCreated.
            При включении, событие будет отправлено немедленно для каждого существующего контекста выполнения.

        Позволяет так же организовать обратную связь со страницей, посылая из её контекста, данные, в консоль.
            В этом случае будет генерироваться событие 'Runtime.consoleAPICalled':
            https://chromedevtools.github.io/devtools-protocol/tot/Runtime#event-consoleAPICalled
            {
                'method': 'Runtime.consoleAPICalled',
                'params': {
                    'type': 'log',
                    'args': [{'type': 'string', 'value': 'you console data passed was be here'}],
                    'executionContextId': 2,
                    'timestamp': 1583582949679.153,
                    'stackTrace': {
                        'callFrames': [{'functionName': '', 'scriptId': '48', 'url': '', 'lineNumber': 0, 'columnNumber': 8}]
                    }
                }
            }

        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-enable
        :param watch_for_execution_contexts:    Регистрирует слушателей, ожидающих события создания/уничтожения
                                                    контекстов, которые можно запрашивать через
                                                    page_instance.context_manager.GetDefaultContext(frameId: str).
                                                    Должен быть включён ПЕРЕД переходом на целевой адрес.
        :return:
        """
        if not self.runtime_enabled:
            await self.Call("Runtime.enable")
            self.runtime_enabled = True

        if watch_for_execution_contexts and not self.context_manager.is_watch:
            await self.AddListenerForEvent(RuntimeEvent.executionContextCreated, self.context_manager.on_create)
            await self.AddListenerForEvent(RuntimeEvent.executionContextsCleared, self.context_manager.on_clear)
            await self.AddListenerForEvent(RuntimeEvent.executionContextDestroyed, self.context_manager.on_destroy)
            self.context_manager.is_watch = True

    async def RuntimeDisable(self) -> None:
        """
        Отключает создание отчетов о создании контекстов выполнения.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-disable
        :return:
        """
        if self.runtime_enabled:
            await self.Call("Runtime.disable")
            self.runtime_enabled = False

        if self.context_manager.is_watch:
            self.RemoveListenerForEvent(RuntimeEvent.executionContextCreated, self.context_manager.on_create)
            self.RemoveListenerForEvent(RuntimeEvent.executionContextsCleared, self.context_manager.on_clear)
            self.RemoveListenerForEvent(RuntimeEvent.executionContextDestroyed, self.context_manager.on_destroy)
            self.context_manager.is_watch = False

    async def DiscardConsoleEntries(self) -> None:
        """
        Отбрасывает собранные исключения и вызовы API консоли.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-discardConsoleEntries
        :return:
        """
        await self.Call("Runtime.discardConsoleEntries")

    async def ReleaseObjectGroup(self, objectGroup: str) -> None:
        """
        Освобождает все удаленные объекты, принадлежащие данной группе.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-releaseObjectGroup
        :param objectGroup:             Символическое имя группы.
        :return:
        """
        await self.Call("Runtime.releaseObjectGroup", {"objectGroup": objectGroup})

    async def CompileScript(
            self, expression: str,
            sourceURL: str = "",
            persistScript: bool = True,
            executionContextId: Optional[int] = None
    ) -> str:
        """
        Компилирует выражение.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-compileScript
        :param expression:              Выражение для компиляции.
        :param sourceURL:               Исходный URL для скрипта.
        :param persistScript:           Указывает, следует ли сохранить скомпилированный скрипт.
        :param executionContextId:      (optional) Указывает, в каком контексте выполнения выполнять сценарий.
                                            Если параметр не указан, выражение будет выполняться в контексте
                                            проверяемой страницы.
        :return:                        {
                                            "scriptId": str()
                                            "exceptionDetails": dict(https://chromedevtools.github.io/devtools-protocol/tot/Runtime#type-ExceptionDetails)
                                        }
        """
        args = {"expression": expression, "sourceURL": sourceURL, "persistScript": persistScript}
        if executionContextId is not None:
            args.update({"executionContextId": executionContextId})

        response = await self.Call("Runtime.compileScript", args)
        if "exceptionDetails" in response:
            raise Exception(response["exceptionDetails"]["text"] + "\n" + json.dumps(response["exceptionDetails"]))
        return response["scriptId"]

    async def BuildScript(self, expression: str, context: Optional['RuntimeType.ContextDescription'] = None) -> 'Script':
        return Script(self, expression, context)

    async def RunIfWaitingForDebugger(self) -> None:
        """
        Сообщает инспектируемой странице, что можно запуститься, если она ожидает этого после
            Target.setAutoAttach.
        """
        await self.Call("Runtime.runIfWaitingForDebugger")

    async def RunScript(
            self, scriptId: str,
            executionContextId: Optional[int] = None,
            objectGroup: str = "console",
            silent: bool = False,
            includeCommandLineAPI: bool = True,
            returnByValue: bool = False,
            generatePreview: bool = False,
            awaitPromise: bool = True
    ) -> dict:
        """
        Запускает скрипт с заданным идентификатором в заданном контексте.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-runScript
        :param scriptId:                ID сценария для запуска.
        :param executionContextId:      (optional) Указывает, в каком контексте выполнения выполнять сценарий.
                                            Если параметр не указан, выражение будет выполняться в контексте
                                            проверяемой страницы.
        :param objectGroup:             (optional) Символическое имя группы, которое можно использовать для
                                            освобождения нескольких объектов.
        :param silent:                  (optional) В тихом режиме исключения, выданные во время оценки, не
                                            сообщаются и не приостанавливают выполнение. Переопределяет
                                            состояние setPauseOnException.
        :param includeCommandLineAPI:   (optional) Определяет, должен ли API командной строки быть доступным
                                            во время оценки.
        :param returnByValue:           (optional) Ожидается ли результат в виде объекта JSON, который должен
                                            быть отправлен по значению.
        :param generatePreview:         (optional) Должен ли предварительный просмотр генерироваться для результата.
        :param awaitPromise:            (optional) Будет ли выполнено ожидание выполнения для полученного значения
                                            и возврата после ожидаемого 'promise'.
        :return:                        {
                                            "result": dict(https://chromedevtools.github.io/devtools-protocol/tot/Runtime#type-RemoteObject)
                                            "exceptionDetails": dict(https://chromedevtools.github.io/devtools-protocol/tot/Runtime#type-ExceptionDetails)
                                        }
        """
        args = {
            "scriptId": scriptId, "objectGroup": objectGroup, "silent": silent,
            "includeCommandLineAPI": includeCommandLineAPI, "returnByValue": returnByValue,
            "generatePreview": generatePreview, "awaitPromise": awaitPromise
        }
        if executionContextId is not None:
            args.update({"executionContextId": executionContextId})

        response = await self.Call("Runtime.runScript", args)
        if "exceptionDetails" in response:
            raise Exception(response["result"]["description"] + "\n" + json.dumps(response["exceptionDetails"]))
        return response["result"]

    async def AddBinding(self, name: str, executionContextName: Optional[int] = None) -> None:
        """
        (EXPERIMENTAL)
        Если executeContextId пуст, добавляет привязку с заданным именем к глобальным объектам всех
            проверенных контекстов, включая созданные позже, привязки переживают перезагрузки. Если
            указан executeContextId, добавляет привязку только к глобальному объекту данного
            контекста выполнения. Функция привязки принимает ровно один аргумент, этот аргумент
            должен быть строкой, в случае любого другого ввода функция выдает исключение. Каждый
            вызов функции привязки создает уведомление Runtime.bindingCalled.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-addBinding
        :param name:                    Имя привязки.
        :param executionContextName:      (optional) Идентификатор контекста исполнения.
        :return:
        """
        args = {"name": name}
        if executionContextName is not None:
            args.update({"executionContextName": executionContextName})

        await self.Call("Runtime.addBinding", args)

    @abstractmethod
    async def Call(
            self, domain_and_method: str,
            params: Optional[dict] = None,
            wait_for_response: bool = True
    ) -> Union[dict, None]: raise NotImplementedError("async method Call() — is not implemented")

    @abstractmethod
    async def AddListenerForEvent(
            self, event: Union[str, DomainEvent], listener: Callable, *args: any) -> None:
        raise NotImplementedError("async method AddListenerForEvent() — is not implemented")

    @abstractmethod
    def RemoveListenerForEvent(self, event: Union[str, DomainEvent], listener: Callable) -> None:
        raise NotImplementedError("async method RemoveListenerForEvent() — is not implemented")


class RuntimeEvent(DomainEvent):
    consoleAPICalled = "Runtime.consoleAPICalled"
    exceptionRevoked = "Runtime.exceptionRevoked"
    exceptionThrown = "Runtime.exceptionThrown"
    executionContextCreated = "Runtime.executionContextCreated"
    executionContextDestroyed = "Runtime.executionContextDestroyed"
    executionContextsCleared = "Runtime.executionContextsCleared"
    inspectRequested = "Runtime.inspectRequested"
    bindingCalled = "Runtime.bindingCalled"                       # ! EXPERIMENTAL


class RuntimeType:

    @dataclass
    class PropertyPreview:
        name: str
        type: Literal["object", "function", "undefined", "string", "number", "boolean", "symbol", "accessor", "bigint"]
        valuePreview: Optional['RuntimeType.ObjectPreview']
        value: Optional[str] = None
        _valuePreview: Optional['RuntimeType.ObjectPreview'] = field(init=False, repr=False, default=None)
        subtype: Literal[
            "array", "null", "node", "regexp", "date", "map", "set", "weakmap", "weakset", "iterator", "generator",
            "error", "proxy", "promise", "typedarray", "arraybuffer", "dataview", "webassemblymemory", "wasmvalue"] = None

        @property
        def valuePreview(self) -> 'RuntimeType.ObjectPreview':
            return self._valuePreview

        @valuePreview.setter
        def valuePreview(self, data: dict) -> None:
            self._valuePreview = RuntimeType.ObjectPreview(**data) if not isinstance(data, property) else None


    @dataclass
    class EntryPreview:
        _value: 'RuntimeType.ObjectPreview'
        _key: Optional['RuntimeType.ObjectPreview']

        @property
        def key(self) -> 'RuntimeType.ObjectPreview':
            return self._key

        @key.setter
        def key(self, data: dict) -> None:
            self._key = RuntimeType.ObjectPreview(**data)

        @property
        def value(self) -> 'RuntimeType.ObjectPreview':
            return self._value

        @value.setter
        def value(self, data: dict) -> None:
            self._value = RuntimeType.ObjectPreview(**data)


    @dataclass
    class CustomPreview:
        header: str
        bodyGetterId: Optional[str] = None


    @dataclass
    class ObjectPreview:
        type: Literal["object", "function", "undefined", "string", "number", "boolean", "symbol", "bigint"]
        overflow: bool
        properties: List['RuntimeType.PropertyPreview']
        entries: List['RuntimeType.EntryPreview']
        subtype: Optional[Literal[
            "array", "null", "node", "regexp", "date", "map", "set", "weakmap", "weakset", "iterator", "generator",
            "error", "proxy", "promise", "typedarray", "arraybuffer", "dataview", "webassemblymemory", "wasmvalue"]] = None
        description: Optional[str] = None
        _entries: List['RuntimeType.EntryPreview'] = field(init=False, repr=False, default=None)

        @property
        def properties(self) -> List['RuntimeType.PropertyPreview']:
            return self._properties

        @properties.setter
        def properties(self, data: List[dict]) -> None:
            self._properties = [RuntimeType.PropertyPreview(**item) for item in data]

        @property
        def entries(self) -> List['RuntimeType.EntryPreview']:
            return self._entries

        @entries.setter
        def entries(self, data: List[dict]) -> None:
            self._entries = [RuntimeType.EntryPreview(**item) for item in data] if not isinstance(data, property) else None


    @dataclass
    class RemoteObject:
        """
        Зеркальный объект, ссылающийся на исходный объект JavaScript.
        # https://chromedevtools.github.io/devtools-protocol/tot/Runtime/#type-RemoteObject
        """
        type: Literal["object", "function", "undefined", "string", "number", "boolean", "symbol", "bigint"]
        preview: Optional['RuntimeType.ObjectPreview']
        customPreview: Optional['RuntimeType.CustomPreview']
        subtype: Optional[Literal[
            "array", "null", "node", "regexp", "date", "map", "set", "weakmap", "weakset", "iterator", "generator",
            "error", "proxy", "promise", "typedarray", "arraybuffer", "dataview", "webassemblymemory", "wasmvalue"]] = None
        className: Optional[str] = None
        value: Optional[any] = None
        unserializableValue: Optional[str] = None   # ? Примитивное значение, которое не может быть преобразовано в строку
                                                    # ?     JSON, не имеет value, но получает это свойство.
        description: Optional[str] = None
        objectId: Optional[str] = None
        _preview: Optional['RuntimeType.ObjectPreview'] = field(init=False, repr=False, default=None)
        _customPreview: Optional['RuntimeType.CustomPreview'] = field(init=False, repr=False, default=None)

        @property
        def preview(self) -> 'RuntimeType.ObjectPreview':
            return self._preview

        @preview.setter
        def preview(self, data: dict) -> None:
            self._vpreview = RuntimeType.ObjectPreview(**data) if not isinstance(data, property) else None

        @property
        def customPreview(self) -> 'RuntimeType.CustomPreview':
            return self._customPreview

        @customPreview.setter
        def customPreview(self, data: dict) -> None:
            self._customPreview = RuntimeType.CustomPreview(**data) if not isinstance(data, property) else None


    @dataclass
    class AuxData:
        isDefault: bool
        type: str
        frameId: str


    @dataclass
    class ContextDescription:
        id: int
        origin: str     # url
        name: str
        uniqueId: str
        auxData: 'RuntimeType.AuxData'

        @property
        def auxData(self) -> 'RuntimeType.AuxData':
            return self._auxData

        @auxData.setter
        def auxData(self, data: dict) -> None:
            self._auxData = RuntimeType.AuxData(**data)

    @dataclass
    class PropertyDescriptor:
        name: str
        configurable: bool
        enumerable: bool
        value: Optional['RuntimeType.RemoteObject'] = None
        writable: Optional[bool] = None
        get: Optional['RuntimeType.RemoteObject'] = None
        set: Optional['RuntimeType.RemoteObject'] = None
        wasThrown: Optional[bool] = None
        isOwn: Optional[bool] = None
        symbol: Optional['RuntimeType.RemoteObject'] = None



class Script:
    """
    Упаковывает вызываемое в контексте указанного фрейма выражение. Если контекст не указан, в его качестве
        будет выбран фрейм верхнего уровня. Выражение можно заменить при вызове.
    """
    def __init__(
            self, page_instance, expression: str,
            context: Optional[Union['RuntimeType.ContextDescription', str]] = None):
        self.page_instance = page_instance
        self.expression = expression
        self.unique_context_id = context if type(context) is str else context.uniqueId if context is not None else None

    async def Call(
            self, expression: Optional[str] = None, returnByValue: Optional[bool] = None) -> 'RuntimeType.RemoteObject':
        if expression:
            self.expression = expression
        args = {"expression": self.expression}
        if returnByValue is not None:
            args.update(returnByValue=returnByValue)
        if self.unique_context_id is not None:
            args.update(uniqueContextId=self.unique_context_id)
        result: dict = await self.page_instance.Call("Runtime.evaluate", args)
        return RuntimeType.RemoteObject(**result.get("result"))


class ContextManager:
    contexts: List['RuntimeType.ContextDescription'] = []
    is_watch: bool = False

    async def on_create(self, data: dict) -> None:
        self.contexts.append(RuntimeType.ContextDescription(**data.get("context")))

    async def on_clear(self, data: dict) -> None:
        self.contexts = []

    async def on_destroy(self, data: dict) -> None:
        context_id: int = data.get("executionContextId")
        ii = -1
        for i, ctx in enumerate(self.contexts):
            if ctx.id == context_id:
                ii = i
                break

        if ii > -1: self.contexts.pop(ii)

    def GetDefaultContext(self, frameId: str) -> Union['RuntimeType.ContextDescription', None]:
        for ctx in self.contexts:
            print("frameId", frameId)
            print("Runtime context", ctx, len(self.contexts))
            if ctx.auxData.frameId == frameId and ctx.auxData.isDefault:
                return ctx
        return None