from dataclasses import dataclass
from typing import Optional


@dataclass
class RemoteLocation:
    host: str; port: int


@dataclass
class TargetInfo:
    targetId: str; type: str; title: str; url: str; attached: bool
    openerId:         Optional[str] = None
    canAccessOpener: Optional[bool] = None
    openerFrameId:    Optional[str] = None
    browserContextId: Optional[str] = None
