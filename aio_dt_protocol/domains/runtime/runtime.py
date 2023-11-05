from typing import Optional, List, Dict, Union, TYPE_CHECKING
from .types import (
    PropertyDescriptor,
    ContextManager,
    ContextDescription,
    Script,
    SerializationOptions,
    RemoteObject,
)
from ...data import DomainEvent, Serializer
from ...exceptions import (
    PromiseEvaluateError,
    highlight_promise_error,
    EvaluateError,
    highlight_eval_error
)
if TYPE_CHECKING:
    from ...connection import Connection


class Runtime:
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Runtime
    """
    __slots__ = ("_connection", "enabled", "context_manager")

    def __init__(self, conn) -> None:
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
                "\n" + Serializer.encode(response["exceptionDetails"])
            )
        if not skip_complex_types:
            return [PropertyDescriptor(**p) for p in response["result"]]

        result = []
        for p in response["result"]:
            if (subtype := p["value"].get("type")) and subtype == "function":
                continue
            result.append(PropertyDescriptor(**p))
        return result

    async def evaluate(
            self, expression: str,
            objectGroup: Optional[str] = None,
            includeCommandLineAPI: Optional[bool] = None,
            silent: Optional[bool] = None,
            contextId: Optional[int] = None,
            returnByValue: Optional[bool] = None,
            generatePreview: Optional[bool] = None,
            userGesture: Optional[bool] = None,
            awaitPromise: Optional[bool] = None,
            throwOnSideEffect: Optional[bool] = None,
            timeout: Optional[float] = None,
            disableBreaks: Optional[bool] = None,
            replMode: Optional[bool] = None,
            allowUnsafeEvalBlockedByCSP: Optional[bool] = None,
            uniqueContextId: Optional[str] = None,
            serializationOptions: Optional[SerializationOptions] = None,
    ) -> RemoteObject:
        """ Выполняет JavaScript-выражение в глобальном контексте.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime/#method-evaluate
        :param expression:  JavaScript-выражение.
        :param objectGroup: Символическое имя группы, которое можно использовать
            для освобождения нескольких объектов.
        :param includeCommandLineAPI:   Определяет, должен ли быть доступен API
            командной строки во время выполнения выражения.
        :param silent:  В автоматическом режиме исключения, возникающие во время
            выполнения выражения, не сообщаются и не приостанавливают выполнение.
            Переопределяет setPauseOnException состояние.
        :param contextId:   Указывает, в каком контексте выполнения выполнять выражение.
            Если параметр опущен, оценка будет выполняться в контексте проверяемой
            страницы. Это взаимоисключающее свойство uniqueContextId, которое предлагает
            альтернативный способ определения контекста выполнения, более надежный в
            многопроцессорной среде.
        :param returnByValue:   Ожидается ли, что результат будет объектом JSON, который
            должен быть отправлен по значению.
        :param generatePreview: Должен ли быть создан предварительный просмотр для результата.
        :param userGesture: Следует ли рассматривать выполнение как инициированное
            пользователем в пользовательском интерфейсе.
        :param awaitPromise:    Должно ли выполнение выражения ожидать результирующего
            значения и возвращаться после завершения промиса.
        :param throwOnSideEffect:   Выбрасывать ли исключение, если во время выполнения
            выражения нельзя исключить побочный эффект. Это подразумевает использование
             disableBreaks аргумента.
        :param timeout: Прервать выполнение по истечении времени ожидания (количество миллисекунд).
        :param disableBreaks:   Отключите точки останова во время выполнения выражения.
        :param replMode:    Установка этого флага в значение true разрешает повторное
            объявление переменных используя 'let', а так же вызов awaitable инструкций
            в top-level контекста. Обратите внимание, что переменные let могут быть
            повторно объявлены только в том случае, если они сами происходят из replMode.
        :param allowUnsafeEvalBlockedByCSP: Политика безопасности содержимого (CSP)
            для target может блокировать «unsafe-eval», который включает eval(),
            Function(), setTimeout() и setInterval() при вызове с аргументами, которые
            нельзя вызывать. Этот флаг обходит CSP для этой оценки и разрешает
            небезопасную оценку. По умолчанию true.
        :param uniqueContextId: Альтернативный способ указать контекст выполнения
            для выполнения выражения. По сравнению с contextId, который может повторно
            использоваться в процессах, он гарантированно уникален для системы, поэтому
            его можно использовать для предотвращения случайного вычисления выражения
            в контексте, отличном от предполагаемого (например, в результате навигации
            через границы процесса). Это взаимоисключающее значение с contextId.
        :param serializationOptions:    Указывает сериализацию результата. Если указано,
            переопределяет generatePreview, returnByValue.
        :return:
        """
        args = {"expression": expression}
        if objectGroup is not None: args.update(objectGroup=objectGroup)
        if includeCommandLineAPI is not None:
            args.update(includeCommandLineAPI=includeCommandLineAPI)
        if silent is not None: args.update(silent=silent)
        if contextId is not None: args.update(contextId=contextId)
        if returnByValue is not None: args.update(returnByValue=returnByValue)
        if generatePreview is not None: args.update(generatePreview=generatePreview)
        if userGesture is not None: args.update(userGesture=userGesture)
        if awaitPromise is not None: args.update(awaitPromise=awaitPromise)
        if throwOnSideEffect is not None: args.update(throwOnSideEffect=throwOnSideEffect)
        if timeout is not None: args.update(timeout=timeout)
        if disableBreaks is not None: args.update(disableBreaks=disableBreaks)
        if replMode is not None: args.update(replMode=replMode)
        if allowUnsafeEvalBlockedByCSP is not None:
            args.update(allowUnsafeEvalBlockedByCSP=allowUnsafeEvalBlockedByCSP)
        if uniqueContextId is not None: args.update(uniqueContextId=uniqueContextId)
        if serializationOptions is not None:
            args.update(serializationOptions=serializationOptions.as_dict())

        response = await self._connection.call("Runtime.evaluate", args)
        if "exceptionDetails" in response:
            raise EvaluateError(
                highlight_eval_error(response["result"]["description"], expression)
            )

        return RemoteObject(**response["result"])

    async def awaitPromise(
            self, promiseObjectId: str, returnByValue: bool = False, generatePreview: bool = False
    ) -> RemoteObject:
        """ Дожидается выполнения промиса с указанным promiseObjectId.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-awaitPromise
        :param promiseObjectId:     Идентификатор промиса.
        :param returnByValue:       (optional) Ожидается ли результат в виде объекта JSON,
                                        который должен быть отправлен по значению.
        :param generatePreview:     (optional) Должен ли предварительный просмотр
                                        генерироваться для результата.
        :return:
        """
        args = {"promiseObjectId": promiseObjectId, "returnByValue": returnByValue, "generatePreview": generatePreview}
        response = await self._connection.call("Runtime.awaitPromise", args)
        if "exceptionDetails" in response:
            raise PromiseEvaluateError(
                highlight_promise_error(response["result"]["description"]) +
                "\n" + Serializer.encode(response["exceptionDetails"])
            )
        return RemoteObject(**response["result"])

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
            objectGroup: Optional[str] = None,
            throwOnSideEffect: Optional[bool] = None,
            uniqueContextId: Optional[str] = None,
            serializationOptions: Optional[SerializationOptions] = None
    ) -> RemoteObject:
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
        :param throwOnSideEffect:   Выбрасывать ли исключение, если во время выполнения функции
            нельзя исключить побочный эффект.
        :param uniqueContextId: Альтернативный способ указать контекст выполнения
            для выполнения выражения. По сравнению с contextId, который может повторно
            использоваться в процессах, он гарантированно уникален для системы, поэтому
            его можно использовать для предотвращения случайного вычисления выражения
            в контексте, отличном от предполагаемого (например, в результате навигации
            через границы процесса). Это взаимоисключающее значение с contextId.
        :param serializationOptions:    Указывает сериализацию результата. Если указано,
            переопределяет generatePreview, returnByValue.
        :return:
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
        if throwOnSideEffect is not None:
            args.update(throwOnSideEffect=throwOnSideEffect)
        if uniqueContextId is not None:
            args.update(uniqueContextId=uniqueContextId)
        if serializationOptions is not None:
            args.update(serializationOptions=serializationOptions.as_dict())
        response = await self._connection.call("Runtime.callFunctionOn", args)
        if "exceptionDetails" in response:
            raise EvaluateError(
                highlight_eval_error(response["result"]["description"], functionDeclaration)
            )
        return RemoteObject(**response["result"])

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
        """ Отбрасывает собранные исключения и вызовы API консоли.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-discardConsoleEntries
        :return:
        """
        await self._connection.call("Runtime.discardConsoleEntries")

    async def releaseObjectGroup(self, objectGroup: str) -> None:
        """ Освобождает все удаленные объекты, принадлежащие данной группе.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-releaseObjectGroup
        :param objectGroup:             Символическое имя группы.
        :return:
        """
        await self._connection.call("Runtime.releaseObjectGroup", dict(objectGroup=objectGroup))

    async def releaseObject(self, objectId: str) -> None:
        """  Освобождает удаленный объект, с указанным objectId.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-releaseObject
        :param objectId:             Символическое имя группы.
        :return:
        """
        await self._connection.call("Runtime.releaseObject", dict(objectId=objectId))

    async def compileScript(
            self, expression: str,
            sourceURL: str = "",
            persistScript: bool = True,
            executionContextId: Optional[int] = None
    ) -> str:
        """ Компилирует выражение.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-compileScript
        :param expression:              Выражение для компиляции.
        :param sourceURL:               Исходный URL для скрипта.
        :param persistScript:           Указывает, следует ли сохранить скомпилированный скрипт.
        :param executionContextId:      (optional) Указывает, в каком контексте выполнения выполнять сценарий.
                                            Если параметр не указан, выражение будет выполняться в контексте
                                            проверяемой страницы.
        :return:
        """
        args: Dict[str, Union[int, str, bool]] = dict(
            expression=expression, sourceURL=sourceURL, persistScript=persistScript)
        if executionContextId is not None:
            args.update(executionContextId=executionContextId)

        response = await self._connection.call("Runtime.compileScript", args)
        if "exceptionDetails" in response:
            raise EvaluateError(
                highlight_eval_error(response["result"]["description"], expression)
            )
        return response["scriptId"]

    async def buildScript(self, expression: str, context: Optional[ContextDescription] = None) -> Script:
        return Script(self._connection, expression, context)

    async def runIfWaitingForDebugger(self) -> None:
        """ Сообщает инспектируемой странице, что можно запуститься, если она ожидает этого после
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
    ) -> RemoteObject:
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
            raise EvaluateError(
                highlight_eval_error(response["result"]["description"], "scriptId: " + scriptId)
            )
        return RemoteObject(**response["result"])

    async def addBinding(self, name: str, executionContextName: Optional[str] = None) -> None:
        """ Делает доступным переданное имя в качестве имени функции, доступной глобально. Вызов
        такой функции принимает ровно один аргумент типа `string`, иначе возбуждается исключение
        с текстом `Invalid arguments: should be exactly one string.`. Каждый вызов функции по
        этому имени создает уведомление Runtime.bindingCalled, в теле которого, поле `payload`
        будет содержать строку, переданную в качестве аргумента вызванной функции.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-addBinding
        :param name:                    Имя вызываемой функции.
        :param executionContextName:    (optional) Имя контекста исполнения.
        :return:
        """
        args = {"name": name}
        if executionContextName is not None:
            args.update({"executionContextName": executionContextName})

        await self._connection.call("Runtime.addBinding", args)

    async def removeBinding(self, name: str) -> None:
        """ Удаляет привязку по имени. Функцию всё ещё можно будет вызвать, но событие
        'Runtime.bindingCalled' возбуждаться  не будет.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-removeBinding
        :param name:                    Имя вызываемой функции.
        :return:
        """
        await self._connection.call("Runtime.removeBinding", dict(name=name))


class RuntimeEvent(DomainEvent):
    consoleAPICalled = "Runtime.consoleAPICalled"
    exceptionRevoked = "Runtime.exceptionRevoked"
    exceptionThrown = "Runtime.exceptionThrown"
    executionContextCreated = "Runtime.executionContextCreated"
    executionContextDestroyed = "Runtime.executionContextDestroyed"
    executionContextsCleared = "Runtime.executionContextsCleared"
    inspectRequested = "Runtime.inspectRequested"
    bindingCalled = "Runtime.bindingCalled"                       # ! EXPERIMENTAL
