from ...data import DomainEvent


class Overlay:
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Overlay
    """
    __slots__ = ("_connection", "enabled")

    def __init__(self, conn) -> None:
        from ...connection import Connection

        self._connection: Connection = conn
        self.enabled = False

    async def enable(self) -> None:
        """
        Включает отправку уведомлений домена 'Overlay'.
        https://chromedevtools.github.io/devtools-protocol/tot/Overlay#method-enable
        :return:
        """
        if not self.enabled:
            await self._connection.call("Overlay.enable")
            self.enabled = True

    async def disable(self) -> None:
        """
        Выключает 'Overlay' домен, останавливая отправку сообщений.
        https://chromedevtools.github.io/devtools-protocol/tot/Overlay#method-disable
        :return:
        """
        if self.enabled:
            await self._connection.call("Overlay.disable")
            self.enabled = False

    async def setShowFPSCounter(self) -> None:
        """
        Запрашивает показ счетчика FPS.
        https://chromedevtools.github.io/devtools-protocol/tot/Overlay#method-setShowFPSCounter
        :return:
        """
        await self._connection.call("Overlay.setShowFPSCounter")


class OverlayEvent(DomainEvent):
    inspectModeCanceled = "Overlay.inspectModeCanceled"
    inspectNodeRequested = "Overlay.inspectNodeRequested"
    nodeHighlightRequested = "Overlay.nodeHighlightRequested"
    screenshotRequested = "Overlay.screenshotRequested"
