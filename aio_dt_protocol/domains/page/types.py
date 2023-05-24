from dataclasses import dataclass, field
from typing import Optional, List, Literal, Union


@dataclass
class LifecycleEventData:
    frameId: str
    loaderId: str
    name: str
    timestamp: float


@dataclass
class AdFrameStatus:
    """ Указывает, был ли frame идентифицирован как реклама и почему. """
    adFrameType: Literal["none", "child", "root"]
    explanations: Optional[List[Literal["ParentIsAd", "CreatedByAdScript", "MatchedBlockingRule"]]] = None


@dataclass
class Frame:
    """ Информация о фрейме на странице """
    id: str
    loaderId: str                               # ? Network.LoaderId
    url: str
    domainAndRegistry: str
    securityOrigin: str
    mimeType: str
    secureContextType: Literal["Secure", "SecureLocalhost", "InsecureScheme", "InsecureAncestor"]
    crossOriginIsolatedContextType: Literal["Isolated", "NotIsolated", "NotIsolatedFeatureDisabled"]
    gatedAPIFeatures: List[Literal[
        "SharedArrayBuffers", "SharedArrayBuffersTransferAllowed", "PerformanceMeasureMemory", "PerformanceProfile"
    ]]
    adFrameStatus: Optional['AdFrameStatus']
    parentId: Optional[str] = None
    name: Optional[str] = None
    urlFragment: Optional[str] = None
    unreachableUrl: Optional[str] = None
    _adFrameStatus: Optional['AdFrameStatus'] = field(init=False, repr=False, default=None)

    @property
    def adFrameStatus(self) -> Union['AdFrameStatus', None]:
        return self._adFrameStatus

    @adFrameStatus.setter
    def adFrameStatus(self, data: dict) -> None:
        self._adFrameStatus = AdFrameStatus(**data) if not isinstance(data, property) else None


@dataclass
class FrameTree:
    """ Информация об иерархии фреймов """
    frame: 'Frame'
    childFrames: Optional[List['FrameTree']]
    _childFrames: Optional[List['FrameTree']] = field(init=False, repr=False, default=None)

    @property
    def frame(self) -> 'Frame':
        return self._frame

    @frame.setter
    def frame(self, data: dict) -> None:
        self._frame = Frame(**data)

    @property
    def childFrames(self) -> Union[List['FrameTree'], None]:
        return self._childFrames

    @childFrames.setter
    def childFrames(self, data: List[dict]) -> None:
        if not isinstance(data, property):
            self._childFrames = [FrameTree(**frame_data) for frame_data in data]
        else:
            self._childFrames = None

    def GetFrameByUrl(self, value: str) -> Union['Frame', None]:
        def search(tree: 'FrameTree', value: str) -> Union['Frame', None]:
            # print("tree.frame.url", tree.frame.url)
            if value in tree.frame.url:
                return tree.frame
            else:
                if tree.childFrames:
                    for child in tree.childFrames:
                        if result := search(child, value):
                            return result
            return None
        return search(self, value)
