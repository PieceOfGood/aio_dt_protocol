from abc import ABC, abstractmethod
from typing import Optional, Union, List
from aio_dt_protocol.Data import SystemData, GPUInfo, ProcessInfo

class SystemInfo(ABC):
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/SystemInfo/
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

    async def GetSystemInfo(self) -> SystemData:
        """
        Возвращает информацию о системе.
        https://chromedevtools.github.io/devtools-protocol/tot/SystemInfo/#method-getInfo
        :return:
        """
        result = await self.Call("SystemInfo.getInfo")
        return SystemData(
            gpu=GPUInfo(**result["gpu"]), modelName=result["modelName"],
            modelVersion=result["modelVersion"], commandLine=result["commandLine"]
        )

    async def GetProcessInfo (self) -> List[ProcessInfo]:
        """
        Возвращает информацию обо всех запущенных в системе процессах.
        https://chromedevtools.github.io/devtools-protocol/tot/SystemInfo/#method-getProcessInfo
        :return:
        """
        result = await self.Call("SystemInfo.getProcessInfo")
        return [ProcessInfo(**i) for i in result]

    @abstractmethod
    async def Call(
            self, domain_and_method: str,
            params: Optional[dict] = None,
            wait_for_response: Optional[bool] = True
    ) -> Union[dict, None]: raise NotImplementedError("async method Call() — is not implemented")
