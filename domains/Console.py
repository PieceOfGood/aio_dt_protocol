from abc import ABC, abstractmethod
from typing import Optional, Union

class Console(ABC):
    """
    #   Этот домен является устаревшим. Используйте Runtime или Log вместо него.
    #   https://chromedevtools.github.io/devtools-protocol/tot/Console/
    """
    __slots__ = ()

    def __init__(self):
        self.console_domain_enabled   = False

    @property
    def connected(self) -> bool:
        return False

    @property
    def verbose(self) -> bool:
        return False

    @property
    def page_id(self) -> str:
        return ""

    async def ConsoleEnable(self) -> None:
        """
        Включает у домена 'Console', отправку клиенту собранные на данный момент сообщения посредством
            'messageAdded' уведомления.
        https://chromedevtools.github.io/devtools-protocol/tot/Console#method-enable
        :return:
        """
        await self.Call("Console.enable")
        self.console_domain_enabled = True

    async def ConsoleDisable(self) -> None:
        """
        Выключает 'Console' домен, останавливая отправку сообщений.
        https://chromedevtools.github.io/devtools-protocol/tot/Console#method-disable
        :return:
        """
        await self.Call("Console.disable")
        self.console_domain_enabled = False

    async def ClearConsole(self) -> None:
        """
        Ничего не делает.
        https://chromedevtools.github.io/devtools-protocol/tot/Console#method-clearMessages
        :return:
        """
        await self.Call("Console.clearMessages")

    @abstractmethod
    async def Call(
            self, domain_and_method: str,
            params: Optional[dict] = None,
            wait_for_response: Optional[bool] = True
    ) -> Union[dict, None]: raise NotImplementedError("async method Call() — is not implemented")
