

class DeviceOrientation:
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/DeviceOrientation
    """
    __slots__ = ("_connection",)

    def __init__(self, conn) -> None:
        from ...connection import Connection

        self._connection: Connection = conn

    async def clearDeviceOrientationOverride(self) -> None:
        """
        Очищает переопределенную ориентацию устройства.
        https://chromedevtools.github.io/devtools-protocol/tot/DeviceOrientation/#method-clearDeviceOrientationOverride
        :return:
        """
        await self._connection.call("DeviceOrientation.clearDeviceOrientationOverride")

    async def setDeviceOrientationOverride(self, alpha: float, beta: float, gamma: float) -> None:
        """
        Переопределяет ориентацию устройства, принудительно изменяя значения сенсоров, котоые так же
            можно найти в консоли браузера по Ctrl+Shift+P и в поиске ввести 'Show Sensors'.
        https://chromedevtools.github.io/devtools-protocol/tot/DeviceOrientation/#method-setDeviceOrientationOverride
        :return:
        """
        args = {"alpha": alpha, "beta": beta, "gamma": gamma}
        await self._connection.call("DeviceOrientation.setDeviceOrientationOverride", args)
