from abc import ABC, abstractmethod
from typing import Optional, Union, List, Awaitable, Callable
from aio_dt_protocol.Data import DomainEvent
from dataclasses import dataclass

class Target(ABC):
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Target
    """
    __slots__ = ()

    def __init__(self):
        self.targets_discovered = False

    @property
    def connected(self) -> bool:
        return False

    @property
    def verbose(self) -> bool:
        return False

    @property
    def is_headless_mode(self) -> bool:
        return False

    @property
    def page_id(self) -> str:
        return ""

    async def CreateBrowserContext(
        self,
        disposeOnDetach: Optional[bool] = None,
        proxyServer: Optional[str]      = None,
        proxyBypassList: Optional[str]  = None
    ) -> str:
        """
        Создает новый пустой BrowserContext. Аналогичен профилю в режиме инкогнито, но их может быть несколько.
        https://chromedevtools.github.io/devtools-protocol/tot/Target/#method-createBrowserContext
        :param disposeOnDetach:     Если True — удаляет контекст при отключении сеанса отладки.
        :param proxyServer:         Прокси-сервер, аналогичный тому, который передан --proxy-server.
        :param proxyBypassList:     Список обхода прокси, аналогичный тому, который передается в --proxy-bypass-list.
        :return:                Browser.BrowserContextID
        """
        args = {}
        if disposeOnDetach is not None: args.update(disposeOnDetach=disposeOnDetach)
        if proxyServer is not None: args.update(proxyServer=proxyServer)
        if proxyBypassList is not None: args.update(proxyBypassList=proxyBypassList)
        return (await self.Call("Target.createBrowserContext", args))["browserContextId"]

    async def GetBrowserContexts(self) -> List[str]:
        """
        Возвращает все контексты браузера, созданные с помощью метода Target.createBrowserContext.
        https://chromedevtools.github.io/devtools-protocol/tot/Target/#method-getBrowserContexts
        :return:                [ Browser.BrowserContextID, Browser.BrowserContextID, ... ]
        """
        return (await self.Call("Target.getBrowserContexts"))["browserContextIds"]

    async def DisposeBrowserContext(self, browserContextId: str) -> None:
        """
        Удаляет BrowserContext. Все соответствующие страницы будут закрыты без вызова их хуков beforeunload.
        https://chromedevtools.github.io/devtools-protocol/tot/Target/#method-disposeBrowserContext
        :param browserContextId:    Идентификатор контекста браузера.
        :return:
        """
        await self.Call("Target.disposeBrowserContext", {"browserContextId": browserContextId})

    async def GetTargetInfo(self, targetId: Optional[str] = None) -> 'TargetInfo':
        """
        (EXPERIMENTAL)
        Возвращает информацию о "target", или о себе, если идентификатор не передан.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-getTargetInfo
        :param targetId:            Идентификатор страницы/сервиса/воркера/...
        :return:                    targetInfo -> {
                                        "targetId":         str,
                                        "type":             str,
                                        "title":            str,
                                        "url":              str,
                                        "attached":         bool,
                                        "openerId":         str,
                                        "browserContextId": str,
                                    }
        """
        if targetId is None: targetId = self.page_id
        return TargetInfo(**((await self.Call("Target.getTargetInfo", {"targetId": targetId}))["targetInfo"]))

    async def GetTargets(self) -> List['TargetInfo']:
        """
        Возвращает список 'targetInfo' о доступных 'targets'.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-getTargets
        :return:                [ targetInfo, targetInfo, ... ]
        """
        result = (await self.Call("Target.getTargets"))["targetInfos"]
        return [TargetInfo(**info) for i, info in enumerate(result)]

    async def AttachToBrowserTarget(self) -> str:
        """
        Присоединяется к target браузера, использует только режим flat sessionId.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-attachToBrowserTarget
        :return:                    sessionId
        """
        return (await self.Call("Target.attachToBrowserTarget"))["sessionId"]

    async def AttachToTarget(self, targetId: str, flatten: Optional[bool] = None) -> str:
        """
        Присоединяется к 'target' по указанному 'targetId'.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-attachToTarget
        :param targetId:        Строка, представляющая идентификатор созданной страницы.
        :param flatten:         (optional) Разрешает "flat" доступ к сеансу с помощью указания атрибута
                                    sessionId в командах.
        :return:                sessionId -> Идентификатор, назначенный сеансу.
        """
        args = {"targetId": targetId}
        if flatten is not None: args.update({"flatten": flatten})
        return (await self.Call("Target.attachToTarget", args))["sessionId"]

    async def DetachFromTarget(self, sessionId: Optional[str] = "", targetId: Optional[str] = "") -> None:
        """
        Отключается от сессии переданного 'sessionId'.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-detachFromTarget
        :param sessionId:       (optional) Строка, представляющая идентификатор сессии.
        :param targetId:        (optional) Строка, представляющая идентификатор созданной страницы.
        :return:
        """
        args = {}
        if sessionId: args.update({"sessionId": sessionId})
        elif targetId: args.update({"targetId": targetId})
        else: raise ValueError("At least one parameter must be specified 'sessionId' or 'targetId'")
        await self.Call("Target.detachFromTarget", args)

    async def SetAutoAttach(self, autoAttach: bool, waitForDebuggerOnStart: bool) -> None:
        """
        Определяет, следует ли автоматически присоединяться к новым целям, которые считаются связанными
            с этой. При включении также присоединяется ко всем существующим связанным целям. При
            выключении автоматически отсоединяется от всех присоединенных в данный момент целей. Это
            также удаляет все цели, добавленные autoAttachRelated из списка целей, чтобы отслеживать
            создание связанных целей.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-setAutoAttach
        :param autoAttach:                  Следует ли присоединяться к связанным targets.
        :param waitForDebuggerOnStart:      Приостанавливать ли новые targets при присоединении к ним.
                                                Используйте Runtime.runIfWaitingForDebugger для запуска
                                                приостановленных targets.
        :return:
        """
        args = {"autoAttach": autoAttach, "waitForDebuggerOnStart": waitForDebuggerOnStart}
        await self.Call("Target.setAutoAttach", args)

    async def CreateTarget(
        self,
        url: Optional[str]                      = "about:blank",
        width: Optional[int]                    = None,
        height: Optional[int]                   = None,
        browserContextId: Optional[str]         = None,
        enableBeginFrameControl: Optional[bool] = False,
        newWindow: Optional[bool]               = False,
        background: Optional[bool]              = False
    ) -> str:
        """
        Создаёт новую страницу и возвращает её идентификатор. Чтобы затем управлять новой
            вкладкой, воспользуйтесь методом инстанса самого браузера GetPageByID(), или
            сразу методом CreatePage(), который проделывает все эти операции под капотом
            и возвращает готовый инстанс новой страницы.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-createTarget
        :param url:                         Адрес будет открыт при создании.
        :param width:                       Ширина в Density-independent Pixels(DIP). Chrome Headless only!
        :param height:                      Высота в (DIP). Chrome Headless only!
        :param browserContextId:            Контекст браузера, которому предназначается создание target.
        :param enableBeginFrameControl:     Будет ли BeginFrames для этой цели контролироваться с помощью DevTools
                                                (только безголовый хром, пока не поддерживается в MacOS, по
                                                умолчанию false).
        :param newWindow:                   Если 'True' — страница будет открыта в новом окне.
        :param background:                  Если 'True' — страница будет открыта в фоне.
        :return:                targetId -> строка, представляющая идентификатор созданной страницы.
        """
        args = {
            "url": url, "enableBeginFrameControl": enableBeginFrameControl,
            "newWindow": False if self.is_headless_mode else newWindow,
            "background": False if self.is_headless_mode else background
        }
        if width is not None: args.update(width=width)
        if height is not None: args.update(height=height)
        if browserContextId is not None: args.update(browserContextId=browserContextId)
        return (await self.Call("Target.createTarget", args))["targetId"]

    async def CloseTarget(self, targetId: Optional[str] = None) -> None:
        """
        Закрывает вкладку указанного идентификатора, или завершает собственный инстанс,
            если идентификатор не передан.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-closeTarget
        :param targetId:        Строка, представляющая идентификатор созданной страницы.
        :return:                None
        """
        if targetId is None: targetId = self.page_id
        await self.Call("Target.closeTarget", {"targetId": targetId})

    async def Close(self) -> None:
        """
        Закрывает вкладку.
        """
        await self.CloseTarget()

    async def SetDiscoverTargets(
        self, discover: bool,
        message:   Optional[Callable[[str, str], Awaitable[None]]] = None,
        created:   Optional[Callable[['TargetInfo'], Awaitable[None]]] = None,
        crashed:   Optional[Callable[[str, str, int], Awaitable[None]]] = None,
        changed:   Optional[Callable[['TargetInfo'], Awaitable[None]]] = None,
        destroyed: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> None:
        """
        Управляет обнаружением доступных 'targets' уведомляя об их состоянии с помощью событий
            targetCreated / targetInfoChanged / targetDestroyed.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-setDiscoverTargets
        :param discover:            'True' — включает эту надстройку, 'False' — выключает.
        :param message:             Корутина вызываемая для события 'Target.receivedMessageFromTarget'.
        :param created:             Корутина вызываемая для события 'Target.targetCreated'.
        :param crashed:             Корутина вызываемая для события 'Target.targetCrashed'.
        :param changed:             Корутина вызываемая для события 'Target.targetInfoChanged'.
        :param destroyed:           Корутина вызываемая для события 'Target.targetDestroyed'.
        :return:
        """
        async def message_decor(params: dict, func: Callable[[str, str], Awaitable[None]]) -> None:
            await func(params["sessionId"], params["message"])

        async def crash_decor(params: dict, func: Callable[[str, str, int], Awaitable[None]]) -> None:
            await func(params["targetId"], params["status"], params["errorCode"])

        async def decorator(params: dict, func: Callable[[TargetInfo], Awaitable[None]]) -> None:
            await func(TargetInfo(**params["targetInfo"]))

        async def destroy_decor(params: dict, func: Callable[[str], Awaitable[None]]) -> None:
            await func(params["targetId"])

        if discover:
            if message is not None: await self.AddListenerForEvent(TargetEvent.receivedMessageFromTarget, message_decor, message)
            if created is not None: await self.AddListenerForEvent(TargetEvent.targetCreated, decorator, created)
            if crashed is not None: await self.AddListenerForEvent(TargetEvent.targetCrashed, crash_decor, crashed)
            if changed is not None: await self.AddListenerForEvent(TargetEvent.targetInfoChanged, decorator, changed)
            if destroyed is not None: await self.AddListenerForEvent(TargetEvent.targetDestroyed, destroy_decor, destroyed)
        else:
            for event in [
                'Target.receivedMessageFromTarget',
                'Target.targetCreated',
                'Target.targetCrashed',
                'Target.targetInfoChanged',
                'Target.targetDestroyed'
            ]:
                self.RemoveListenersForEvent(event)
        self.targets_discovered = discover
        await self.Call("Target.setDiscoverTargets", {"discover": discover})

    @abstractmethod
    async def Call(
        self, domain_and_method: str,
        params: Optional[dict]            = None,
        wait_for_response: Optional[bool] = True
    ) -> Union[dict, None]: raise NotImplementedError("async method Call() — is not implemented")

    @abstractmethod
    async def AddListenerForEvent(
            self, event: Union[str, DomainEvent], listener: Callable, *args: Optional[any]) -> None:
        raise NotImplementedError("async method AddListenerForEvent() — is not implemented")

    @abstractmethod
    def RemoveListenersForEvent(self, event: str) -> None:
        raise NotImplementedError("method RemoveListenersForEvent() — is not implemented")


class TargetEvent(DomainEvent):
    receivedMessageFromTarget = "Target.receivedMessageFromTarget"
    targetCrashed = "Target.targetCrashed"
    targetCreated = "Target.targetCreated"
    targetDestroyed = "Target.targetDestroyed"
    targetInfoChanged = "Target.targetInfoChanged"
    attachedToTarget = "Target.attachedToTarget"                        # ! EXPERIMENTAL
    detachedFromTarget = "Target.detachedFromTarget"                    # ! EXPERIMENTAL


@dataclass
class RemoteLocation:
    host: str
    port: int


@dataclass
class TargetInfo:
    targetId: str; type: str; title: str; url: str; attached: bool
    openerId:         Optional[str] = None
    canAccessOpener: Optional[bool] = None
    openerFrameId:    Optional[str] = None
    browserContextId: Optional[str] = None
