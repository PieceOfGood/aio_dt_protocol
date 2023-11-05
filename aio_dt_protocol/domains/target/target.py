from typing import Optional, List, Awaitable, Callable, TYPE_CHECKING
from ...data import DomainEvent
from .types import TargetInfo
if TYPE_CHECKING:
    from ...connection import Connection


class Target:
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Target
    """
    __slots__ = ("_connection", "targets_discovered")

    def __init__(self, conn) -> None:
        self._connection: Connection = conn
        self.targets_discovered = False

    async def activateTarget(self, targetId: Optional[str] = None) -> None:
        """
        Активирует (создаёт фокус) "target".
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-activateTarget
        :param targetId:        Строка, представляющая идентификатор созданной страницы.
        :return:
        """
        if targetId is None: targetId = self._connection.conn_id
        await self._connection.call("Target.activateTarget", {"targetId": targetId})

    async def createBrowserContext(
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
        return (await self._connection.call("Target.createBrowserContext", args))["browserContextId"]

    async def getBrowserContexts(self) -> List[str]:
        """
        Возвращает все контексты браузера, созданные с помощью метода Target.createBrowserContext.
        https://chromedevtools.github.io/devtools-protocol/tot/Target/#method-getBrowserContexts
        :return:                [ Browser.BrowserContextID, Browser.BrowserContextID, ... ]
        """
        return (await self._connection.call("Target.getBrowserContexts"))["browserContextIds"]

    async def disposeBrowserContext(self, browserContextId: str) -> None:
        """
        Удаляет BrowserContext. Все соответствующие страницы будут закрыты без вызова их хуков beforeunload.
        https://chromedevtools.github.io/devtools-protocol/tot/Target/#method-disposeBrowserContext
        :param browserContextId:    Идентификатор контекста браузера.
        :return:
        """
        await self._connection.call("Target.disposeBrowserContext", {"browserContextId": browserContextId})

    async def getTargetInfo(self, targetId: Optional[str] = None) -> TargetInfo:
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
        if targetId is None: targetId = self._connection.conn_id
        return TargetInfo(
            **((await self._connection.call("Target.getTargetInfo", {"targetId": targetId}))["targetInfo"]))

    async def getTargets(self) -> List[TargetInfo]:
        """
        Возвращает список 'targetInfo' о доступных 'targets'.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-getTargets
        :return:                [ targetInfo, targetInfo, ... ]
        """
        result = (await self._connection.call("Target.getTargets"))["targetInfos"]
        return [TargetInfo(**info) for i, info in enumerate(result)]

    async def attachToTarget(self, targetId: str, flatten: Optional[bool] = None) -> str:
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
        return (await self._connection.call("Target.attachToTarget", args))["sessionId"]

    async def detachFromTarget(self, sessionId: str = "", targetId: str = "") -> None:
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
        await self._connection.call("Target.detachFromTarget", args)

    async def setAutoAttach(
            self, autoAttach: bool, waitForDebuggerOnStart: bool, flatten: Optional[bool] = None) -> None:
        """
        Определяет, следует ли автоматически присоединяться к новым target, которые считаются связанными
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
        if flatten is not None: args.update(flatten=flatten)
        await self._connection.call("Target.setAutoAttach", args)

    async def createTarget(
        self,
        url: str                        = "about:blank",
        width: Optional[int]            = None,
        height: Optional[int]           = None,
        browserContextId: Optional[str] = None,
        enableBeginFrameControl: bool   = False,
        newWindow: bool                 = False,
        background: bool                = False
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
            "newWindow": False if self._connection.is_headless_mode else newWindow,
            "background": False if self._connection.is_headless_mode else background
        }
        if width is not None: args.update(width=width)
        if height is not None: args.update(height=height)
        if browserContextId is not None: args.update(browserContextId=browserContextId)
        return (await self._connection.call("Target.createTarget", args))["targetId"]

    async def closeTarget(self, targetId: Optional[str] = None) -> None:
        """
        Закрывает вкладку указанного идентификатора, или завершает собственный инстанс,
            если идентификатор не передан.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-closeTarget
        :param targetId:        Строка, представляющая идентификатор созданной страницы.
        :return:                None
        """
        if targetId is None: targetId = self._connection.conn_id
        await self._connection.call("Target.closeTarget", {"targetId": targetId})

    async def close(self) -> None:
        """
        Закрывает вкладку.
        """
        await self.closeTarget()

    async def setDiscoverTargets(
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
        async def on_message(params: dict) -> None:
            await message(params["sessionId"], params["message"])

        async def on_crashed(params: dict) -> None:
            await crashed(params["targetId"], params["status"], params["errorCode"])

        async def on_created(params: dict) -> None:
            await created(TargetInfo(**params["targetInfo"]))

        async def on_changed(params: dict) -> None:
            await changed(TargetInfo(**params["targetInfo"]))

        async def on_destroyed(params: dict) -> None:
            await destroyed(params["targetId"])

        if self.targets_discovered != discover:
            if discover:
                if message is not None:
                    await self._connection.addListenerForEvent(
                        TargetEvent.receivedMessageFromTarget, on_message)
                if created is not None:
                    await self._connection.addListenerForEvent(
                        TargetEvent.targetCreated, on_created)
                if crashed is not None:
                    await self._connection.addListenerForEvent(
                        TargetEvent.targetCrashed, on_crashed)
                if changed is not None:
                    await self._connection.addListenerForEvent(
                        TargetEvent.targetInfoChanged, on_changed)
                if destroyed is not None:
                    await self._connection.addListenerForEvent(
                        TargetEvent.targetDestroyed, on_destroyed)
            else:
                for event in [
                    'Target.receivedMessageFromTarget',
                    'Target.targetCreated',
                    'Target.targetCrashed',
                    'Target.targetInfoChanged',
                    'Target.targetDestroyed'
                ]:
                    self._connection.removeListenersForEvent(event)
            self.targets_discovered = discover
            await self._connection.call("Target.setDiscoverTargets", {"discover": discover})


class TargetEvent(DomainEvent):
    receivedMessageFromTarget = "Target.receivedMessageFromTarget"
    targetCrashed = "Target.targetCrashed"
    targetCreated = "Target.targetCreated"
    targetDestroyed = "Target.targetDestroyed"
    targetInfoChanged = "Target.targetInfoChanged"
    attachedToTarget = "Target.attachedToTarget"                        # ! EXPERIMENTAL
    detachedFromTarget = "Target.detachedFromTarget"                    # ! EXPERIMENTAL
