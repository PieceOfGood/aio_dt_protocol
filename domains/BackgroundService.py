from abc import ABC, abstractmethod
from typing import Optional, Union

class BackgroundService(ABC):
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/BackgroundService
    """
    __slots__ = ()

    def __init__(self):
        self.observing_started = False
        self.recording_started = False

    @property
    def connected(self) -> bool:
        return False

    @property
    def verbose(self) -> bool:
        return False

    @property
    def page_id(self) -> str:
        return ""

    async def BackgroundClearEvents(self, service: str) -> None:
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
        await self.Call("BackgroundService.clearEvents", {"service": service})

    async def BackgroundSetRecording(self, shouldRecord: bool, service: str) -> None:
        """
        Включает, или выключает запись для service.
        https://chromedevtools.github.io/devtools-protocol/tot/BackgroundService/#method-setRecording
        :param shouldRecord:    True == включить
        :param service:         ---------------------
        :return:
        """
        await self.Call("BackgroundService.clearEvents", {"shouldRecord": shouldRecord, "service": service})
        self.recording_started = shouldRecord

    async def BackgroundStartObserving(self, service: str) -> None:
        """
        Включает обновления событий для service.
        https://chromedevtools.github.io/devtools-protocol/tot/BackgroundService/#method-startObserving
        :param service:         ---------------------
        :return:
        """
        if not self.observing_started:
            await self.Call("BackgroundService.startObserving", {"service": service})
            self.observing_started = True

    async def BackgroundStopObserving(self, service: str) -> None:
        """
        Выключает обновления событий для service.
        https://chromedevtools.github.io/devtools-protocol/tot/BackgroundService/#method-stopObserving
        :param service:         ---------------------
        :return:
        """
        if self.observing_started:
            await self.Call("BackgroundService.stopObserving", {"service": service})
            self.observing_started = False

    @abstractmethod
    async def Call(
            self, domain_and_method: str,
            params: Optional[dict] = None,
            wait_for_response: Optional[bool] = True
    ) -> Union[dict, None]: raise NotImplementedError("async method Call() — is not implemented")
