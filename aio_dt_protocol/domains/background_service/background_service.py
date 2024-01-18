from ...data import DomainEvent
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ...connection import Connection


class BackgroundService:
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/BackgroundService
    """
    __slots__ = ("_connection", "observing_started", "recording_started")

    def __init__(self, conn) -> None:
        self._connection: Connection = conn
        self.observing_started = False
        self.recording_started = False

    async def backgroundClearEvents(self, service: str) -> None:
        """
        Удаляет все сохраненные данные для service.
        https://chromedevtools.github.io/devtools-protocol/tot/BackgroundService/#method-clearEvents
        :param service:         Фоновая служба, которая будет связана с командами / событиями. Каждая фоновая
                                    служба работает независимо, но использует один и тот же API.
                                Допустимые значения:
                                    backgroundFetch, backgroundSync, pushMessaging, notifications,
                                    paymentHandler,periodicBackgroundSync
        :return:
        """
        await self._connection.call("BackgroundService.clearEvents", {"service": service})

    async def backgroundSetRecording(self, shouldRecord: bool, service: str) -> None:
        """
        Включает, или выключает запись для service.
        https://chromedevtools.github.io/devtools-protocol/tot/BackgroundService/#method-setRecording
        :param shouldRecord:    True == включить
        :param service:         ---------------------
        :return:
        """
        await self._connection.call("BackgroundService.clearEvents", {"shouldRecord": shouldRecord, "service": service})
        self.recording_started = shouldRecord

    async def backgroundStartObserving(self, service: str) -> None:
        """
        Включает обновления событий для service.
        https://chromedevtools.github.io/devtools-protocol/tot/BackgroundService/#method-startObserving
        :param service:         ---------------------
        :return:
        """
        if not self.observing_started:
            await self._connection.call("BackgroundService.startObserving", {"service": service})
            self.observing_started = True

    async def backgroundStopObserving(self, service: str) -> None:
        """
        Выключает обновления событий для service.
        https://chromedevtools.github.io/devtools-protocol/tot/BackgroundService/#method-stopObserving
        :param service:         ---------------------
        :return:
        """
        if self.observing_started:
            await self._connection.call("BackgroundService.stopObserving", {"service": service})
            self.observing_started = False


class BackgroundServiceEvent(DomainEvent):
    backgroundServiceEventReceived = "BackgroundService.backgroundServiceEventReceived"
    recordingStateChanged = "BackgroundService.recordingStateChanged"
