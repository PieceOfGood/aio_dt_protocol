from ...data import DomainEvent


class Log:
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Log
    #   LogEntry -> https://chromedevtools.github.io/devtools-protocol/tot/Log#type-LogEntry
    """
    __slots__ = ("_connection", "enabled")

    def __init__(self, conn) -> None:
        from ...connection import Connection

        self._connection: Connection = conn
        self.enabled = False

    async def enable(self) -> None:
        """
        Включает 'Log' домен, отправляет записи лога, собранные на данный момент, посредством
            события 'entryAdded'.
        https://chromedevtools.github.io/devtools-protocol/tot/Log#method-enable
        :return:
        """
        if not self.enabled:
            await self._connection.call("Log.enable")
            self.enabled = True

    async def disable(self) -> None:
        """
        Выключает 'Log' домен, останавливая отправку сообщений.
        https://chromedevtools.github.io/devtools-protocol/tot/Log#method-disable
        :return:
        """
        if self.enabled:
            await self._connection.call("Log.disable")
            self.enabled = False

    async def clear(self) -> None:
        """
        Очищает список ранее опубликованных сообщений лога.
        https://chromedevtools.github.io/devtools-protocol/tot/Log#method-clear
        :return:
        """
        await self._connection.call("Log.clear")

class LogEvent(DomainEvent):
    entryAdded = "Log.entryAdded"
