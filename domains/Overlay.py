from abc import ABC, abstractmethod
from typing import Optional, Union
from aio_dt_protocol.Data import DomainEvent

class Overlay(ABC):
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Overlay
    """
    __slots__ = ()

    def __init__(self):
        self.overlay_domain_enabled = False

    @property
    def connected(self) -> bool:
        return False

    @property
    def verbose(self) -> bool:
        return False

    @property
    def page_id(self) -> str:
        return ""

    async def OverlayEnable(self) -> None:
        """
        Включает отправку уведомлений домена 'Overlay'.
        https://chromedevtools.github.io/devtools-protocol/tot/Overlay#method-enable
        :return:
        """
        await self.Call("Overlay.enable")
        self.overlay_domain_enabled = True

    async def OverlayDisable(self) -> None:
        """
        Выключает 'Overlay' домен, останавливая отправку сообщений.
        https://chromedevtools.github.io/devtools-protocol/tot/Overlay#method-disable
        :return:
        """
        await self.Call("Overlay.disable")
        self.overlay_domain_enabled = False

    async def SetShowFPSCounter(self) -> None:
        """
        Запрашивает бэкэнд показ счетчика FPS.
        https://chromedevtools.github.io/devtools-protocol/tot/Overlay#method-setShowFPSCounter
        :return:
        """
        await self.Call("Overlay.setShowFPSCounter")

    @abstractmethod
    async def Call(
            self, domain_and_method: str,
            params: Optional[dict] = None,
            wait_for_response: Optional[bool] = True
    ) -> Union[dict, None]: raise NotImplementedError("async method Call() — is not implemented")

class OverlayEvent(DomainEvent):
    inspectModeCanceled = "Overlay.inspectModeCanceled"
    inspectNodeRequested = "Overlay.inspectNodeRequested"
    nodeHighlightRequested = "Overlay.nodeHighlightRequested"
    screenshotRequested = "Overlay.screenshotRequested"
