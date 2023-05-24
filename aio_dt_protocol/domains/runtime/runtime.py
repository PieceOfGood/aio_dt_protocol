try:
    import ujson as json
except ModuleNotFoundError:
    import json

from typing import Optional, List
from .types import PropertyDescriptor, ContextManager, ContextDescription, Script
from ...data import DomainEvent
from ...exceptions import PromiseEvaluateError, highlight_promise_error


class Runtime:
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Runtime
    """
    __slots__ = ("_connection", "enabled", "context_manager")

    def __init__(self, conn) -> None:

        from ...connection import Connection

        self._connection: Connection = conn
        self.enabled = False
        self.context_manager = ContextManager()

    async def getProperties(
            self, objectId: str,
            skip_complex_types: bool = True,
            ownProperties: Optional[bool] = None,
            accessorPropertiesOnly: Optional[bool] = None,
            generatePreview: Optional[bool] = None,
            nonIndexedPropertiesOnly: Optional[bool] = None,
    ) -> List[PropertyDescriptor]:
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
        response = await self._connection.call("Runtime.getProperties", args)
        if "exceptionDetails" in response:
            raise PromiseEvaluateError(
                highlight_promise_error(response["result"]["description"]) +
                "\n" + json.dumps(response["exceptionDetails"])
            )
        if not skip_complex_types:
            return [PropertyDescriptor(**p) for p in response["result"]]

        result = []
        for p in response["result"]:
            if (subtype := p["value"].get("type")) and subtype == "function":
                continue
            result.append(PropertyDescriptor(**p))
        return result


    async def awaitPromise(
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
        response = await self._connection.call("Runtime.awaitPromise", args)
        if "exceptionDetails" in response:
            raise PromiseEvaluateError(
                highlight_promise_error(response["result"]["description"]) +
                "\n" + json.dumps(response["exceptionDetails"])
            )
        return response["result"]

    async def callFunctionOn(
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
        response = await self._connection.call("Runtime.callFunctionOn", args)
        if "exceptionDetails" in response:
            raise Exception(response["result"]["description"] + "\n" + json.dumps(response["exceptionDetails"]))
        return response["result"]

    async def enable(self, watch_for_execution_contexts: bool = False) -> None:
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
        if not self.enabled:
            await self._connection.call("Runtime.enable")
            self.enabled = True

        if watch_for_execution_contexts and not self.context_manager.is_watch:
            await self._connection.addListenerForEvent(
                RuntimeEvent.executionContextCreated, self.context_manager.on_create)
            await self._connection.addListenerForEvent(
                RuntimeEvent.executionContextsCleared, self.context_manager.on_clear)
            await self._connection.addListenerForEvent(
                RuntimeEvent.executionContextDestroyed, self.context_manager.on_destroy)
            self.context_manager.is_watch = True

    async def disable(self) -> None:
        """
        Отключает создание отчетов о создании контекстов выполнения.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-disable
        :return:
        """
        if self.enabled:
            await self._connection.call("Runtime.disable")
            self.enabled = False

        if self.context_manager.is_watch:
            self._connection.removeListenerForEvent(
                RuntimeEvent.executionContextCreated, self.context_manager.on_create)
            self._connection.removeListenerForEvent(
                RuntimeEvent.executionContextsCleared, self.context_manager.on_clear)
            self._connection.removeListenerForEvent(
                RuntimeEvent.executionContextDestroyed, self.context_manager.on_destroy)
            self.context_manager.is_watch = False

    async def discardConsoleEntries(self) -> None:
        """
        Отбрасывает собранные исключения и вызовы API консоли.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-discardConsoleEntries
        :return:
        """
        await self._connection.call("Runtime.discardConsoleEntries")

    async def releaseObjectGroup(self, objectGroup: str) -> None:
        """
        Освобождает все удаленные объекты, принадлежащие данной группе.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-releaseObjectGroup
        :param objectGroup:             Символическое имя группы.
        :return:
        """
        await self._connection.call("Runtime.releaseObjectGroup", {"objectGroup": objectGroup})

    async def compileScript(
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

        response = await self._connection.call("Runtime.compileScript", args)
        if "exceptionDetails" in response:
            raise Exception(response["exceptionDetails"]["text"] + "\n" + json.dumps(response["exceptionDetails"]))
        return response["scriptId"]

    async def buildScript(self, expression: str, context: Optional[ContextDescription] = None) -> Script:
        return Script(self._connection, expression, context)

    async def runIfWaitingForDebugger(self) -> None:
        """
        Сообщает инспектируемой странице, что можно запуститься, если она ожидает этого после
            Target.setAutoAttach.
        """
        await self._connection.call("Runtime.runIfWaitingForDebugger")

    async def runScript(
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

        response = await self._connection.call("Runtime.runScript", args)
        if "exceptionDetails" in response:
            raise Exception(response["result"]["description"] + "\n" + json.dumps(response["exceptionDetails"]))
        return response["result"]

    async def addBinding(self, name: str, executionContextName: Optional[int] = None) -> None:
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

        await self._connection.call("Runtime.addBinding", args)


class RuntimeEvent(DomainEvent):
    consoleAPICalled = "Runtime.consoleAPICalled"
    exceptionRevoked = "Runtime.exceptionRevoked"
    exceptionThrown = "Runtime.exceptionThrown"
    executionContextCreated = "Runtime.executionContextCreated"
    executionContextDestroyed = "Runtime.executionContextDestroyed"
    executionContextsCleared = "Runtime.executionContextsCleared"
    inspectRequested = "Runtime.inspectRequested"
    bindingCalled = "Runtime.bindingCalled"                       # ! EXPERIMENTAL
