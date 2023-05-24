from typing import List
from ...data import DomainEvent


class CSS:
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Log
    #   LogEntry -> https://chromedevtools.github.io/devtools-protocol/tot/Log#type-LogEntry
    """
    __slots__ = ("_connection", "enabled", "_style_sheets")

    def __init__(self, conn) -> None:

        from ...connection import Connection

        self._connection: Connection = conn
        self.enabled = False
        self._style_sheets: List[str] = []  # Если домен CSS активирован, сюда попадут все 'styleSheetId' страницы

    @property
    def style_sheets(self) -> List[str]:
        return self._style_sheets

    @style_sheets.setter
    def style_sheets(self, value) -> None:
        self._style_sheets = value

    async def _CSS_sheet_catcher(self, data: dict) -> None:
        """
        Колбэк вызываемый для каждого 'CSS.styleSheetAdded'-события, если
            включён агент домена 'CSS'.
        """
        self._style_sheets.append(data["header"]["styleSheetId"])

    async def CSSEnable(self) -> None:
        """
        Включает агент CSS. Клиент не должен предполагать, что агент CSS включен,
            пока не будет получен результат этой команды.
        https://chromedevtools.github.io/devtools-protocol/tot/CSS/#method-disable
        :return:
        """
        if not self.enabled:
            await self._connection.addListenerForEvent("CSS.styleSheetAdded", self._CSS_sheet_catcher)
            await self._connection.call("CSS.enable")
            self.enabled = True

    async def CSSDisable(self) -> None:
        """
        Отключает агент CSS.
        https://chromedevtools.github.io/devtools-protocol/tot/CSS/#method-disable
        :return:
        """
        if self.enabled:
            self._connection.removeListenerForEvent("CSS.styleSheetAdded", self._CSS_sheet_catcher)
            await self._connection.call("CSS.disable")
            self.style_sheets = []
            self.enabled = False

    async def AddRule(
        self, styleSheetId: str, ruleText: str,
        startLine:   int = 0,
        startColumn: int = 0,
        endLine:     int = 0,
        endColumn:   int = 0
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
        return (await self._connection.call("CSS.addRule", args))["rule"]

    async def CollectClassNames(self, styleSheetId: str) -> List[str]:
        """
        Возвращает список всех имён классов для указанного ID.
        https://chromedevtools.github.io/devtools-protocol/tot/CSS/#method-collectClassNames
        :param styleSheetId:            Идентификатор стилей.
        :return:
        """
        return (await self._connection.call("CSS.collectClassNames", {"styleSheetId": styleSheetId}))["classNames"]

    async def CreateStyleSheet(self, frameId: str = None) -> str:
        """
        Создает новую специальную таблицу стилей через "инспектор" во фрейме с заданным frameId.
            Если frameId не указан, будет использован frameId главного фрейма текущей страницы.
            Возвращает ID созданного styleSheet.
        https://chromedevtools.github.io/devtools-protocol/tot/CSS/#method-createStyleSheet
        :param frameId:                 Идентификатор фрейма, в котором будет создан styleSheet.
        :return:                styleSheetId
        """
        frameId = frameId if frameId else self._connection.conn_id
        styleSheetId = (await self._connection.call("CSS.createStyleSheet", {"frameId": frameId}))["styleSheetId"]
        self._style_sheets.append(styleSheetId)
        return styleSheetId

    async def GetStyleSheetText(self, styleSheetId: str) -> str:
        """
        Возвращает текстовый контент стилей для указанного ID.
        https://chromedevtools.github.io/devtools-protocol/tot/CSS/#method-getStyleSheetText
        :param styleSheetId:            Идентификатор стилей.
        :return:
        """
        return (await self._connection.call("CSS.getStyleSheetText", {"styleSheetId": styleSheetId}))["text"]

class CSSEvent(DomainEvent):
    fontsUpdated = "CSS.fontsUpdated"
    mediaQueryResultChanged = "CSS.mediaQueryResultChanged"
    styleSheetAdded = "CSS.styleSheetAdded"
    styleSheetChanged = "CSS.styleSheetChanged"
    styleSheetRemoved = "CSS.styleSheetRemoved"
