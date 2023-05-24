from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ProcessInfo:
    type: str  # Тип процесса
    id: int  # Идентификатор процесса
    cpuTime: float  # Совокупное использование ЦП в секундах для всех потоков процесса с момента его запуска.


@dataclass
class GPUInfo:
    devices: List[dict]
    driverBugWorkarounds: List[str]
    videoDecoding: List[dict]
    videoEncoding: List[dict]
    imageDecoding: List[dict]
    auxAttributes: Optional[dict] = None
    featureStatus: Optional[dict] = None


@dataclass
class SystemData:
    gpu: "GPUInfo"
    modelName: str
    modelVersion: str
    commandLine: str
