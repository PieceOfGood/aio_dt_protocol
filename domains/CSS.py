from abc import ABC, abstractmethod
from typing import Optional, Union, Callable, List

class CSS(ABC):
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Log
    #   LogEntry -> https://chromedevtools.github.io/devtools-protocol/tot/Log#type-LogEntry
    """
    __slots__ = ()

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

    async def AddRule(
        self, styleSheetId: str, ruleText: str,
        startLine:   Optional[int] = 0,
        startColumn: Optional[int] = 0,
        endLine:     Optional[int] = 0,
        endColumn:   Optional[int] = 0
    ) -> dict:
        """
        Вставляет новое правило с заданным ruleText в таблицу стилей с заданным styleSheetId в позицию,
            указанную с помощью location.
        https://chromedevtools.github.io/devtools-protocol/tot/CSS/#method-addRule
        :param styleSheetId:            Идентификатор стилей.
        :param ruleText:                Текст правила (например: 'body { background: red }').

        Текстовый диапазон в ресурсе. Все числа отсчитываются от нуля.
        :param startLine:               (optional) - Стартовая линия диапазона.
        :param startColumn:             (optional) - Начальный столбец диапазона (включительно).
        :param endLine:                 (optional) - Конечная строка диапазона.
        :param endColumn:               (optional) - Конечный столбец диапазона (исключая).
        :return:    https://chromedevtools.github.io/devtools-protocol/tot/CSS/#type-CSSRule
        """
        location = {"startLine": startLine, "startColumn": startColumn, "endLine": endLine, "endColumn": endColumn}
        args = {
            "styleSheetId": styleSheetId,
            "ruleText": ruleText,
            "location": location
        }
        return (await self.Call("CSS.addRule", args))["rule"]

    async def CollectClassNames(self, styleSheetId: str) -> List[str]:
        """
        Возвращает список всех имён классов для указанного ID.
        https://chromedevtools.github.io/devtools-protocol/tot/CSS/#method-collectClassNames
        :param styleSheetId:            Идентификатор стилей.
        :return:
        """
        return (await self.Call("CSS.collectClassNames", {"styleSheetId": styleSheetId}))["classNames"]

    async def CreateStyleSheet(self, frameId: str = None) -> str:
        """
        Создает новую специальную таблицу стилей через "инспектор" во фрейме с заданным frameId.
            Если frameId не указан, будет использован frameId главного фрейма текущей страницы.
            Возвращает ID созданного styleSheet.
        https://chromedevtools.github.io/devtools-protocol/tot/CSS/#method-createStyleSheet
        :param frameId:                 Идентификатор фрейма, в котором будет создан styleSheet.
        :return:                styleSheetId
        """
        frameId = frameId if frameId else self.page_id
        styleSheetId = (await self.Call("CSS.createStyleSheet", {"frameId": frameId}))["styleSheetId"]
        self.style_sheets.append(styleSheetId)
        return styleSheetId

    async def GetStyleSheetText(self, styleSheetId: str) -> str:
        """
        Возвращает текстовый контент стилей для указанного ID.
        https://chromedevtools.github.io/devtools-protocol/tot/CSS/#method-getStyleSheetText
        :param styleSheetId:            Идентификатор стилей.
        :return:
        """
        return (await self.Call("CSS.getStyleSheetText", {"styleSheetId": styleSheetId}))["text"]

    @abstractmethod
    async def AddListenerForEvent(
            self, event: str, listener: Callable, *args: Optional[any]) -> None:
        raise NotImplementedError("async method AddListenerForEvent() — is not implemented")

    @abstractmethod
    def RemoveListenerForEvent(self, event: str, listener: Callable) -> None:
        raise NotImplementedError("method RemoveListenerForEvent() — is not implemented")

    @abstractmethod
    async def Call(
            self, domain_and_method: str,
            params: Optional[dict] = None,
            wait_for_response: Optional[bool] = True
    ) -> Union[dict, None]: raise NotImplementedError("async method Call() — is not implemented")
