from abc import ABC, abstractmethod
from typing import Optional, Union
from ..data import DomainEvent

class Log(ABC):
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Log
    #   LogEntry -> https://chromedevtools.github.io/devtools-protocol/tot/Log#type-LogEntry
    """
    __slots__ = ()

    def __init__(self):
        self.log_domain_enabled = False

    @property
    def connected(self) -> bool:
        return False

    @property
    def verbose(self) -> bool:
        return False

    @property
    def page_id(self) -> str:
        return ""

    async def LogEnable(self) -> None:
        """
        Включает 'Log' домен, отправляет записи лога, собранные на данный момент, посредством
            события 'entryAdded'.
        https://chromedevtools.github.io/devtools-protocol/tot/Log#method-enable
        :return:
        """
        await self.Call("Log.enable")
        self.log_domain_enabled = True

    async def LogDisable(self) -> None:
        """
        Выключает 'Log' домен, останавливая отправку сообщений.
        https://chromedevtools.github.io/devtools-protocol/tot/Log#method-disable
        :return:
        """
        await self.Call("Log.disable")
        self.log_domain_enabled = False

    async def ClearLog(self) -> None:
        """
        Очищает список ранее опубликованных сообщений лога.
        https://chromedevtools.github.io/devtools-protocol/tot/Log#method-clear
        :return:
        """
        await self.Call("Log.clear")

    @abstractmethod
    async def Call(
            self, domain_and_method: str,
            params: Optional[dict] = None,
            wait_for_response: bool = True
    ) -> Union[dict, None]: raise NotImplementedError("async method Call() — is not implemented")

class LogEvent(DomainEvent):
    entryAdded = "Log.entryAdded"
