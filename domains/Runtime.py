import json
from abc import ABC, abstractmethod
from typing import Optional, Union


class Runtime(ABC):
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Runtime
    """
    __slots__ = ()

    def __init__(self):
        self.runtime_enabled = False

    @property
    def connected(self) -> bool:
        return False

    @property
    def verbose(self) -> bool:
        return False

    @property
    def page_id(self) -> str:
        return ""

    async def AwaitPromise(
            self, promiseObjectId: str, returnByValue: bool = False, generatePreview: bool = False
    ) -> any:
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
            raise Exception(response["result"]["description"] + "\n" + json.dumps(response["exceptionDetails"]))
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
        :param awaitPromise:            (optional) Решено ли выполнение awaitдля полученного значения
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

    async def RuntimeEnable(self) -> None:
        """
        Включает создание отчетов о создании контекстов выполнения с помощью события executeContextCreated.
            При включении, событие будет отправлено немедленно для каждого существующего контекста выполнения.

        Позволяет так же организовать обратную связь со страницей, посылая из её контекста, данные, в консоль.
            В этом случае будет генерироваться событие 'Runtime.consoleAPICalled':
            https://chromedevtools.github.io/devtools-protocol/tot/Runtime#event-consoleAPICalled
            {
                'method': 'Runtime.consoleAPICalled',
                params': {
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
        :return:
        """
        await self.Call("Runtime.enable")
        self.runtime_enabled = True

    async def RuntimeDisable(self) -> None:
        """
        Отключает создание отчетов о создании контекстов выполнения.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-disable
        :return:
        """
        await self.Call("Runtime.disable")
        self.runtime_enabled = False

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
            sourceURL: Optional[str] = "",
            persistScript: Optional[bool] = True,
            executionContextId: Optional[int] = None
    ) -> dict:
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

    async def RunScript(
            self, scriptId: str,
            executionContextId: Optional[int] = None,
            objectGroup: Optional[str] = "console",
            silent: Optional[bool] = False,
            includeCommandLineAPI: Optional[bool] = True,
            returnByValue: Optional[bool] = False,
            generatePreview: Optional[bool] = False,
            awaitPromise: Optional[bool] = True
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

    async def AddBinding(self, name: str, executionContextId: Optional[int] = None) -> None:
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
        :param executionContextId:      (optional) Идентификатор контекста исполнения.
        :return:
        """
        args = {"name": name}
        if executionContextId is not None:
            args.update({"executionContextId": executionContextId})

        await self.Call("Runtime.addBinding", args)

    @abstractmethod
    async def Call(
            self, domain_and_method: str,
            params: Optional[dict] = None,
            wait_for_response: Optional[bool] = True
    ) -> Union[dict, None]: raise NotImplementedError("async method Call() — is not implemented")
