from abc import ABC, abstractmethod
from typing import Optional, Union

class DeviceOrientation(ABC):
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/DeviceOrientation
    """
    __slots__ = ()

    @property
    def connected(self) -> bool:
        return False

    @property
    def verbose(self) -> bool:
        return False

    @property
    def page_id(self) -> str:
        return ""

    async def ClearDeviceOrientationOverride(self) -> None:
        """
        Очищает переопределенную ориентацию устройства.
        https://chromedevtools.github.io/devtools-protocol/tot/DeviceOrientation/#method-clearDeviceOrientationOverride
        :return:
        """
        await self.Call("DeviceOrientation.clearDeviceOrientationOverride")

    async def SetDeviceOrientationOverride(self, alpha: float, beta: float, gamma: float) -> None:
        """
        Переопределяет ориентацию устройства, принудительно изменяя значения сенсоров, котоые так же
            можно найти в консоли браузера по Ctrl+Shift+P и в поиске ввести 'Show Sensors'.
        https://chromedevtools.github.io/devtools-protocol/tot/DeviceOrientation/#method-setDeviceOrientationOverride
        :return:
        """
        args = {"alpha": alpha, "beta": beta, "gamma": gamma}
        await self.Call("DeviceOrientation.setDeviceOrientationOverride", args)

    @abstractmethod
    async def Call(
            self, domain_and_method: str,
            params: Optional[dict] = None,
            wait_for_response: bool = True
    ) -> Union[dict, None]: raise NotImplementedError("async method Call() — is not implemented")
