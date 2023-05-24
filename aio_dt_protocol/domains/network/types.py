from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union


class ConnectionType(Enum):
    none = "none"
    cellular2g = "cellular2g"
    cellular3g = "cellular3g"
    cellular4g = "cellular4g"
    bluetooth = "bluetooth"
    ethernet = "ethernet"
    wifi = "wifi"
    wimax = "wimax"
    other = "other"


@dataclass
class LoadNetworkResourcePageResult:
    success: bool
    netError: Optional[int] = None
    netErrorName: Optional[str] = None
    httpStatusCode: Optional[int] = None
    stream: Optional[str] = None                # ! IO.StreamHandle
    headers: Optional[dict] = None


@dataclass
class Request:
    url: str
    method: str
    headers: dict
    initialPriority: str                        # ! Allowed Values: VeryLow, Low, Medium, High, VeryHigh
    referrerPolicy: str                         # ! Allowed Values: unsafe-url, no-referrer-when-downgrade,
                                                # !     no-referrer, origin, origin-when-cross-origin, same-origin,
                                                # !     strict-origin, strict-origin-when-cross-origin
    trustTokenParams: Optional["TrustTokenParams"]
    postDataEntries: Optional[list["PostDataEntry"]]
    urlFragment: Optional[str] = None
    postData: Optional[str] = None
    hasPostData: Optional[bool] = None          # ! true if postData is present
    _postDataEntries: Optional[list["PostDataEntry"]] = field(init=False, repr=False, default=None)
    mixedContentType: Optional[str] = None      # ! Allowed Values: blockable, optionally-blockable, none
    isLinkPreload: Optional[bool] = None
    _trustTokenParams: Optional["TrustTokenParams"] = field(init=False, repr=False, default=None)
    isSameSite: Optional[bool] = None

    @property
    def postDataEntries(self) -> list["PostDataEntry"]:
        return self._postDataEntries

    @postDataEntries.setter
    def postDataEntries(self, data: list[dict[str, Union[str, None]]]) -> None:
        if not isinstance(data, property):
            self._postDataEntries = [PostDataEntry(**item) for item in data]
        else:
            self._postDataEntries = None

    @property
    def trustTokenParams(self) -> "TrustTokenParams":
        return self._trustTokenParams

    @trustTokenParams.setter
    def trustTokenParams(self, data: dict) -> None:
        self._trustTokenParams = TrustTokenParams(**data) if not isinstance(data, property) else None


@dataclass
class PostDataEntry:
    bytes: Optional[str] = None


@dataclass
class TrustTokenParams:
    type: str                                   # ! Allowed Values: Issuance, Redemption, Signing
    refreshPolicy: str                          # ! Allowed Values: UseCached, Refresh
    issuers: Optional[list[str]] = None



@dataclass
class Cookie:
    name: str
    value: str
    domain: str
    path: str
    expires: float
    size: int
    httpOnly: bool
    secure: bool
    session: bool
    priority: str                       # Allowed Values: Low, Medium, High
    sameParty: bool
    sourceScheme: str                   # Allowed Values: Unset, NonSecure, Secure
    sourcePort: int                     # Valid values are {-1, [1, 65535]}, -1 indicates an unspecified port.
    sameSite: Optional[str] = None      # Allowed status Values: Strict, Lax, None
    partitionKey: Optional[str] = None
    partitionKeyOpaque: Optional[bool] = None
