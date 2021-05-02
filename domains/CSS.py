from abc import ABC, abstractmethod
from typing import Optional, Union, Callable

class CSS(ABC):
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Log
    #   LogEntry -> https://chromedevtools.github.io/devtools-protocol/tot/Log#type-LogEntry
    """

    def __init__(self):
        self.css_domain_enabled = False
        self.style_sheets = []  # Если домен CSS активирован, сюда попадут все 'styleSheetId' страницы

    @property
    def connected(self) -> bool:
        return False

    @property
    def verbose(self) -> bool:
        return False

    @property
    def page_id(self) -> str:
        return ""

    @property
    def style_sheets(self) -> list:
        return self._style_sheets

    @style_sheets.setter
    def style_sheets(self, value) -> None:
        self._style_sheets = value

    async def _CSS_sheet_catcher(self, data: dict) -> None:
        """
        Колбэк вызываемый для каждого 'CSS.styleSheetAdded'-события, если
            включён агент домена 'CSS'.
        """
        self.style_sheets.append(data["header"]["styleSheetId"])

    async def CSSEnable(self) -> None:
        """
        Включает агент CSS. Клиент не должен предполагать, что агент CSS включен,
            пока не будет получен результат этой команды.
        https://chromedevtools.github.io/devtools-protocol/tot/CSS/#method-disable
        :return:
        """
        if not self.css_domain_enabled:
            await self.AddListenerForEvent("CSS.styleSheetAdded", self._CSS_sheet_catcher)
            await self.Call("CSS.enable")
            self.css_domain_enabled = True

    async def CSSDisable(self) -> None:
        """
        Отключает агент CSS.
        https://chromedevtools.github.io/devtools-protocol/tot/CSS/#method-disable
        :return:
        """
        if self.css_domain_enabled:
            self.RemoveListenerForEvent("CSS.styleSheetAdded", self._CSS_sheet_catcher)
            await self.Call("CSS.disable")
            self.css_domain_enabled = False

    @abstractmethod
    async def AddListenerForEvent(
            self, event: str, listener: Callable, *args: Optional[any]) -> None:
        raise NotImplementedError("async method AddListenerForEvent() — is not implemented")

    @abstractmethod
    def RemoveListenerForEvent(self, event: str, listener: Callable) -> None:
        raise NotImplementedError("async method RemoveListenerForEvent() — is not implemented")

    @abstractmethod
    async def Call(
            self, domain_and_method: str,
            params: Optional[dict] = None,
            wait_for_response: Optional[bool] = True
    ) -> Union[dict, None]: raise NotImplementedError("async method Call() — is not implemented")
