from typing import Optional, List, TypeVar
from dataclasses import dataclass
from enum import Enum
from asyncio import Queue



T = TypeVar("T")


@dataclass
class GeoInfo:
    ip: str
    timezone: str
    geo: dict[str, float]
    country: str
    languages: list[str]
    city: str
    state_province: str
    proxy_type: str


class __Base:
    def __init__(self, que: Queue) -> None:
        self.que = que

class Sender(__Base):
    async def send(self, data: T) -> None:
        await self.que.put(data)

class Receiver(__Base):
    async def recv(self) -> T:
        return await self.que.get()


class DomainEvent(Enum): pass

class ConnectionType(Enum):
    none = "none"; cellular2g = "cellular2g"; cellular3g = "cellular3g"; cellular4g = "cellular4g"
    bluetooth = "bluetooth"; ethernet = "ethernet"; wifi = "wifi"; wimax = "wimax"; other = "other"

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

@dataclass
class TargetConnectionInfo:
    description: str; devtoolsFrontendUrl: str
    id: str; title: str; type: str; url: str; webSocketDebuggerUrl: str
    faviconUrl: str = None; parentId: str = None

class TargetConnectionType(Enum):
    page = "page"
    background_page = "background_page"
    worker = "worker"
    service_worker = "service_worker"
    iframe ="iframe"
    other = "other"

@dataclass
class ProcessInfo:
    type: str           # Тип процесса
    id: int             # Идентификатор процесса
    cpuTime: float      # Совокупное использование ЦП в секундах для всех потоков процесса с момента его запуска.

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
    gpu: GPUInfo
    modelName: str
    modelVersion: str
    commandLine: str

@dataclass
class WindowBounds:
    """ Описывает положение, размер и состояние окна браузера """
    left: Optional[int]        = None       # Смещение от левого края экрана до окна в пикселях.
    top: Optional[int]         = None       # Смещение от верхнего края экрана к окну в пикселях.
    width: Optional[int]       = None       # Ширина окна в пикселях.
    height: Optional[int]      = None       # Высота окна в пикселях.
    windowState: Optional[str] = "normal"   # normal, minimized, maximized, fullscreen
                                            #   minimized, maximized и fullscreen нельзя сочетать с  left, top,
                                            #   width или height. Неопределенные поля останутся без изменений.

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

@dataclass
class WindowInfo:
    windowId: int
    bounds: WindowBounds

@dataclass
class TouchPoint:
    """ Описывает точку прикосновения стилуса для метода DispatchTouchEvent() """
    x: float; y: float                          # Координаты точки касания
    radiusX:            Optional[float] = None  # X-радиус прикосновения(по умолчанию 1.0)
    radiusY:            Optional[float] = None  # Y-радиус прикосновения(по умолчанию 1.0)
    rotationAngle:      Optional[float] = None  # Угол вращения(по умолчанию 0.0)
    force:              Optional[float] = None  # Сила(по умолчанию 1.0)
    tangentialPressure: Optional[float] = None  # Нормализованное тангенциальное давление в
                                                #   диапазоне [-1,1](по умолчанию 0.0)
    tiltX:                Optional[int] = None  # Угол между плоскостью Y-Z и плоскостью,
                                                #   содержащей ось стилуса и ось Y, в градусах
                                                #   диапазона [-90,90], положительный tiltX
                                                #   - наклон вправо (по умолчанию: 0).
    tiltY:                Optional[int] = None  # Угол между плоскостью X-Z и плоскостью,
                                                #   содержащей ось стилуса и ось X, в градусах
                                                #   диапазона [-90,90], положительный tiltY
                                                #   - наклон вниз (по умолчанию: 0).
    twist:                Optional[int] = None  # Поворот стилуса пера по часовой стрелке вокруг
                                                #   своей главной оси в градусах в диапазоне
                                                #   [0,359] (по умолчанию: 0).
    id:                 Optional[float] = None  # Идентификатор, используемый для отслеживания
                                                #   источников касания между событиями, должен
                                                #   быть уникальным в пределах события.

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

@dataclass
class StyleProp:
    """ Описывает имя и значение стиля """
    name: str; value: str

@dataclass
class NodeCenter: x: int; y: int

@dataclass
class NodeRect:
    """ Пространственное положение и размеры узла """
    x: int; y: int; width: int; height: int; left: int; right: int; top: int; bottom: int

@dataclass
class ViewportRect:
    """ Ширина и высота вьюпорта """
    width: int; height: int

@dataclass
class WindowRect:
    """ Ширина и высота окна браузера(outer - свойства) """
    width: int; height: int

@dataclass
class ShapeOutsideInfo:
    bounds: list; shape: list; marginShape: list

@dataclass
class BoxModel:
    content: list; padding: list; border: list; margin: list; width: int; height: int
    shapeOutside: Optional[ShapeOutsideInfo] = None

class KeyModifiers(Enum):
    """ Клавиши-модификаторы """
    none = 0; alt = 1; ctrl = 2; meta = command = 4; shift = 8

@dataclass
class KeyEvents:
    """ https://gist.github.com/jhincapie/8a4c95d5cbe81d79b329ffc37e9f6c97 """
    backspace =           {"code": "Backspace",       "text": "",   "keyIdentifier": "U+0008",  "key": "Backspace", "windowsVirtualKeyCode": 8,   "nativeVirtualKeyCode": 8}
    tab =                 {"code": "Tab",             "text": "",   "keyIdentifier": "U+0009",  "key": "Tab",       "windowsVirtualKeyCode": 9,   "nativeVirtualKeyCode": 9}
    enter =               {"code": "Enter",           "text": "",   "keyIdentifier": "U+000D",  "key": "Enter",     "windowsVirtualKeyCode": 13,  "nativeVirtualKeyCode": 13}
    shift =               {"code": "Shift",           "text": "",   "keyIdentifier": "U+0010",  "key": "Shift",     "windowsVirtualKeyCode": 16,  "nativeVirtualKeyCode": 16}
    shift_left =          {"code": "ShiftLeft",       "text": "",   "keyIdentifier": "U+00A0",  "key": "Shift",     "windowsVirtualKeyCode": 160, "nativeVirtualKeyCode": 160}
    shift_right =         {"code": "ShiftRight",      "text": "",   "keyIdentifier": "U+00A1",  "key": "Shift",     "windowsVirtualKeyCode": 161, "nativeVirtualKeyCode": 161}
    control =             {"code": "Control",         "text": "",   "keyIdentifier": "Control", "key": "Control",   "windowsVirtualKeyCode": 17,  "nativeVirtualKeyCode": 17}
    control_left =        {"code": "ControlLeft",     "text": "",   "keyIdentifier": "U+00A2",  "key": "Control",   "windowsVirtualKeyCode": 162, "nativeVirtualKeyCode": 162}
    control_right =       {"code": "ControlRight",    "text": "",   "keyIdentifier": "U+00A3",  "key": "Control",   "windowsVirtualKeyCode": 163, "nativeVirtualKeyCode": 163}
    alt =                 {"code": "Alt",             "text": "",   "keyIdentifier": "Alt",     "key": "Alt",       "windowsVirtualKeyCode": 18,  "nativeVirtualKeyCode": 18}
    alt_left =            {"code": "AltLeft",         "text": "",   "keyIdentifier": "U+00A4",  "key": "Alt",       "windowsVirtualKeyCode": 164, "nativeVirtualKeyCode": 164}
    alt_right =           {"code": "AltRight",        "text": "",   "keyIdentifier": "U+00A5",  "key": "Alt",       "windowsVirtualKeyCode": 165, "nativeVirtualKeyCode": 165}
    escape =              {"code": "Escape",          "text": "",   "keyIdentifier": "U+001B",  "key": "Escape",    "windowsVirtualKeyCode": 27,  "nativeVirtualKeyCode": 27}
    space =               {"code": "Space",           "text": " ",  "keyIdentifier": "U+0020",  "key": " ",         "windowsVirtualKeyCode": 32,  "nativeVirtualKeyCode": 32}
    arrow_left =          {"code": "ArrowLeft",       "text": "",   "keyIdentifier": "U+0025",  "key": "ArrowLeft", "windowsVirtualKeyCode": 37,  "nativeVirtualKeyCode": 37}
    arrow_up =            {"code": "ArrowUp",         "text": "",   "keyIdentifier": "U+0026",  "key": "ArrowUp",   "windowsVirtualKeyCode": 38,  "nativeVirtualKeyCode": 38}
    arrow_right =         {"code": "ArrowRight",      "text": "",   "keyIdentifier": "U+0027",  "key": "ArrowRight","windowsVirtualKeyCode": 39,  "nativeVirtualKeyCode": 39}
    arrow_down =          {"code": "ArrowDown",       "text": "",   "keyIdentifier": "U+0028",  "key": "ArrowDown", "windowsVirtualKeyCode": 40,  "nativeVirtualKeyCode": 40}
    parentheses_right =   {"code": "Parentheses",     "text": ")",  "keyIdentifier": "U+0030",  "key": ")",         "windowsVirtualKeyCode": 48,  "nativeVirtualKeyCode": 48}
    digit0 =              {"code": "Digit0",          "text": "0",  "keyIdentifier": "U+0030",  "key": "0",         "windowsVirtualKeyCode": 48,  "nativeVirtualKeyCode": 48}
    digit1 =              {"code": "Digit1",          "text": "1",  "keyIdentifier": "U+0031",  "key": "1",         "windowsVirtualKeyCode": 49,  "nativeVirtualKeyCode": 49}
    digit2 =              {"code": "Digit2",          "text": "2",  "keyIdentifier": "U+0032",  "key": "2",         "windowsVirtualKeyCode": 50,  "nativeVirtualKeyCode": 50}
    at =                  {"code": "At",              "text": "@",  "keyIdentifier": "U+0032",  "key": "@",         "windowsVirtualKeyCode": 50,  "nativeVirtualKeyCode": 50}
    digit3 =              {"code": "Digit3",          "text": "3",  "keyIdentifier": "U+0033",  "key": "3",         "windowsVirtualKeyCode": 51,  "nativeVirtualKeyCode": 51}
    hash =                {"code": "Hash",            "text": "#",  "keyIdentifier": "U+0033",  "key": "#",         "windowsVirtualKeyCode": 51,  "nativeVirtualKeyCode": 51}   # #
    number =              {"code": "Number",          "text": "№",  "keyIdentifier": "U+0033",  "key": "№",         "windowsVirtualKeyCode": 51,  "nativeVirtualKeyCode": 51}   # №
    digit4 =              {"code": "Digit4",          "text": "4",  "keyIdentifier": "U+0034",  "key": "4",         "windowsVirtualKeyCode": 52,  "nativeVirtualKeyCode": 52}
    dollar =              {"code": "Dollar",          "text": "$",  "keyIdentifier": "U+0034",  "key": "$",         "windowsVirtualKeyCode": 52,  "nativeVirtualKeyCode": 52}   # $
    digit5 =              {"code": "Digit5",          "text": "5",  "keyIdentifier": "U+0035",  "key": "5",         "windowsVirtualKeyCode": 53,  "nativeVirtualKeyCode": 53}
    percent =             {"code": "Percent",         "text": "%",  "keyIdentifier": "U+0035",  "key": "%",         "windowsVirtualKeyCode": 53,  "nativeVirtualKeyCode": 53}   # %
    digit6 =              {"code": "Digit6",          "text": "6",  "keyIdentifier": "U+0036",  "key": "6",         "windowsVirtualKeyCode": 54,  "nativeVirtualKeyCode": 54}
    angle_up =            {"code": "AngleUp",         "text": "^",  "keyIdentifier": "U+0036",  "key": "^",         "windowsVirtualKeyCode": 54,  "nativeVirtualKeyCode": 54}   # ^
    digit7 =              {"code": "Digit7",          "text": "7",  "keyIdentifier": "U+0037",  "key": "7",         "windowsVirtualKeyCode": 55,  "nativeVirtualKeyCode": 55}
    ampersand =           {"code": "Ampersand",       "text": "&",  "keyIdentifier": "U+0037",  "key": "&",         "windowsVirtualKeyCode": 55,  "nativeVirtualKeyCode": 55}   # &
    digit8 =              {"code": "Digit8",          "text": "8",  "keyIdentifier": "U+0038",  "key": "8",         "windowsVirtualKeyCode": 56,  "nativeVirtualKeyCode": 56}
    digit9 =              {"code": "Digit9",          "text": "9",  "keyIdentifier": "U+0039",  "key": "9",         "windowsVirtualKeyCode": 57,  "nativeVirtualKeyCode": 57}
    parentheses_left =    {"code": "Parentheses",     "text": "(",  "keyIdentifier": "U+0039",  "key": "(",         "windowsVirtualKeyCode": 57,  "nativeVirtualKeyCode": 57}
    keyA =                {"code": "KeyA",            "text": "a",  "keyIdentifier": "U+0041",  "key": "a",         "windowsVirtualKeyCode": 65,  "nativeVirtualKeyCode": 65}
    keyB =                {"code": "KeyB",            "text": "b",  "keyIdentifier": "U+0042",  "key": "b",         "windowsVirtualKeyCode": 66,  "nativeVirtualKeyCode": 66}
    keyC =                {"code": "KeyC",            "text": "c",  "keyIdentifier": "U+0043",  "key": "c",         "windowsVirtualKeyCode": 67,  "nativeVirtualKeyCode": 67}
    keyD =                {"code": "KeyD",            "text": "d",  "keyIdentifier": "U+0044",  "key": "d",         "windowsVirtualKeyCode": 68,  "nativeVirtualKeyCode": 68}
    keyE =                {"code": "KeyE",            "text": "e",  "keyIdentifier": "U+0045",  "key": "e",         "windowsVirtualKeyCode": 69,  "nativeVirtualKeyCode": 69}
    keyF =                {"code": "KeyF",            "text": "f",  "keyIdentifier": "U+0046",  "key": "f",         "windowsVirtualKeyCode": 70,  "nativeVirtualKeyCode": 70}
    keyG =                {"code": "KeyG",            "text": "g",  "keyIdentifier": "U+0047",  "key": "g",         "windowsVirtualKeyCode": 71,  "nativeVirtualKeyCode": 71}
    keyH =                {"code": "KeyH",            "text": "h",  "keyIdentifier": "U+0048",  "key": "h",         "windowsVirtualKeyCode": 72,  "nativeVirtualKeyCode": 72}
    keyI =                {"code": "KeyI",            "text": "i",  "keyIdentifier": "U+0049",  "key": "i",         "windowsVirtualKeyCode": 73,  "nativeVirtualKeyCode": 73}
    keyJ =                {"code": "KeyJ",            "text": "j",  "keyIdentifier": "U+004A",  "key": "j",         "windowsVirtualKeyCode": 74,  "nativeVirtualKeyCode": 74}
    keyK =                {"code": "KeyK",            "text": "k",  "keyIdentifier": "U+004B",  "key": "k",         "windowsVirtualKeyCode": 75,  "nativeVirtualKeyCode": 75}
    keyL =                {"code": "KeyL",            "text": "l",  "keyIdentifier": "U+004C",  "key": "l",         "windowsVirtualKeyCode": 76,  "nativeVirtualKeyCode": 76}
    keyM =                {"code": "KeyM",            "text": "m",  "keyIdentifier": "U+004D",  "key": "m",         "windowsVirtualKeyCode": 77,  "nativeVirtualKeyCode": 77}
    keyN =                {"code": "KeyN",            "text": "n",  "keyIdentifier": "U+004E",  "key": "n",         "windowsVirtualKeyCode": 78,  "nativeVirtualKeyCode": 78}
    keyO =                {"code": "KeyO",            "text": "o",  "keyIdentifier": "U+004F",  "key": "o",         "windowsVirtualKeyCode": 79,  "nativeVirtualKeyCode": 79}
    keyP =                {"code": "KeyP",            "text": "p",  "keyIdentifier": "U+0050",  "key": "p",         "windowsVirtualKeyCode": 80,  "nativeVirtualKeyCode": 80}
    keyQ =                {"code": "KeyQ",            "text": "q",  "keyIdentifier": "U+0051",  "key": "q",         "windowsVirtualKeyCode": 81,  "nativeVirtualKeyCode": 81}
    keyR =                {"code": "KeyR",            "text": "r",  "keyIdentifier": "U+0052",  "key": "r",         "windowsVirtualKeyCode": 82,  "nativeVirtualKeyCode": 82}
    keyS =                {"code": "KeyS",            "text": "s",  "keyIdentifier": "U+0053",  "key": "s",         "windowsVirtualKeyCode": 83,  "nativeVirtualKeyCode": 83}
    keyT =                {"code": "KeyT",            "text": "t",  "keyIdentifier": "U+0054",  "key": "t",         "windowsVirtualKeyCode": 84,  "nativeVirtualKeyCode": 84}
    keyU =                {"code": "KeyU",            "text": "u",  "keyIdentifier": "U+0055",  "key": "u",         "windowsVirtualKeyCode": 85,  "nativeVirtualKeyCode": 85}
    keyV =                {"code": "KeyV",            "text": "v",  "keyIdentifier": "U+0056",  "key": "v",         "windowsVirtualKeyCode": 86,  "nativeVirtualKeyCode": 86}
    keyW =                {"code": "KeyW",            "text": "w",  "keyIdentifier": "U+0057",  "key": "w",         "windowsVirtualKeyCode": 87,  "nativeVirtualKeyCode": 87}
    keyX =                {"code": "KeyX",            "text": "x",  "keyIdentifier": "U+0058",  "key": "x",         "windowsVirtualKeyCode": 88,  "nativeVirtualKeyCode": 88}
    keyY =                {"code": "KeyY",            "text": "y",  "keyIdentifier": "U+0059",  "key": "y",         "windowsVirtualKeyCode": 89,  "nativeVirtualKeyCode": 89}
    keyZ =                {"code": "KeyZ",            "text": "z",  "keyIdentifier": "U+005A",  "key": "z",         "windowsVirtualKeyCode": 90,  "nativeVirtualKeyCode": 90}
    metaLeft =            {"code": "MetaLeft",        "text": "",   "keyIdentifier": "U+005B",  "key": "Meta",      "windowsVirtualKeyCode": 91,  "nativeVirtualKeyCode": 91}
    metaRight =           {"code": "MetaRight",       "text": "",   "keyIdentifier": "U+005D",  "key": "Meta",      "windowsVirtualKeyCode": 93,  "nativeVirtualKeyCode": 93}
    context_menu =        {"code": "ContextMenu",     "text": "",   "keyIdentifier": "U+005D",  "key": "",          "windowsVirtualKeyCode": 93,  "nativeVirtualKeyCode": 93}
    equal =               {"code": "Equal",           "text": "=",  "keyIdentifier": "U+003D",  "key": "=",         "windowsVirtualKeyCode": 61,  "nativeVirtualKeyCode": 61}
    multiply =            {"code": "Multipy",         "text": "*",  "keyIdentifier": "U+006A",  "key": "*",         "windowsVirtualKeyCode": 106, "nativeVirtualKeyCode": 106}   # Numpad *
    oem_plus =            {"code": "Plus",            "text": "+",  "keyIdentifier": "U+00BB",  "key": "+",         "windowsVirtualKeyCode": 187, "nativeVirtualKeyCode": 187}   # OEM_PLUS(+ =)
    numpad_plus =         {"code": "Plus",            "text": "+",  "keyIdentifier": "U+006B",  "key": "+",         "windowsVirtualKeyCode": 107, "nativeVirtualKeyCode": 107}   #
    oem_minus =           {"code": "Minus",           "text": "-",  "keyIdentifier": "U+00BD",  "key": "-",         "windowsVirtualKeyCode": 189, "nativeVirtualKeyCode": 189}   # OEM_MINUS(_ -)
    underscore =          {"code": "Underscore",      "text": "_",  "keyIdentifier": "U+00BD",  "key": "_",         "windowsVirtualKeyCode": 189, "nativeVirtualKeyCode": 189}   # OEM_MINUS(_ -)
    numpad_minus =        {"code": "Minus",           "text": "-",  "keyIdentifier": "U+006D",  "key": "-",         "windowsVirtualKeyCode": 109, "nativeVirtualKeyCode": 109}   #
    bracket_left =        {"code": "BracketLeft",     "text": "[",  "keyIdentifier": "U+005B",  "key": "[",         "windowsVirtualKeyCode": 219, "nativeVirtualKeyCode": 219}
    bracket_right =       {"code": "BracketRight",    "text": "]",  "keyIdentifier": "U+005D",  "key": "]",         "windowsVirtualKeyCode": 221, "nativeVirtualKeyCode": 221}
    brace_left =          {"code": "BraceLeft",       "text": "{",  "keyIdentifier": "U+00DB",  "key": "{",         "windowsVirtualKeyCode": 219, "nativeVirtualKeyCode": 219}
    brace_right =         {"code": "BraceRight",      "text": "}",  "keyIdentifier": "U+00DD",  "key": "}",         "windowsVirtualKeyCode": 221, "nativeVirtualKeyCode": 221}
    pipe =                {"code": "Pipe",            "text": "|",  "keyIdentifier": "U+00DC",  "key": "|",         "windowsVirtualKeyCode": 220, "nativeVirtualKeyCode": 220}
    backslash =           {"code": "Backslash",       "text": "\\", "keyIdentifier": "U+00DC",  "key": "\\",        "windowsVirtualKeyCode": 220, "nativeVirtualKeyCode": 220}
    quote =               {"code": "Quote",           "text": "'",  "keyIdentifier": "U+00DE",  "key": "'",         "windowsVirtualKeyCode": 222, "nativeVirtualKeyCode": 222}
    double_quote =        {"code": "DoubleQuote",     "text": "\"", "keyIdentifier": "U+00DE",  "key": "\"",        "windowsVirtualKeyCode": 222, "nativeVirtualKeyCode": 222}
    exclamation_mark =    {"code": "ExclamationMark", "text": "!",  "keyIdentifier": "U+00DF",  "key": "!",         "windowsVirtualKeyCode": 223, "nativeVirtualKeyCode": 223}  # !
    semicolon =           {"code": "Semicolon",       "text": ";",  "keyIdentifier": "U+00BA",  "key": ";",         "windowsVirtualKeyCode": 186, "nativeVirtualKeyCode": 186}
    colon =               {"code": "Colon",           "text": ":",  "keyIdentifier": "U+00BA",  "key": ":",         "windowsVirtualKeyCode": 186, "nativeVirtualKeyCode": 186}
    comma =               {"code": "Comma",           "text": ",",  "keyIdentifier": "U+002C",  "key": ",",         "windowsVirtualKeyCode": 188, "nativeVirtualKeyCode": 188}
    angle_bracket_left =  {"code": "AngleBracket",    "text": "<",  "keyIdentifier": "U+002C",  "key": "<",         "windowsVirtualKeyCode": 188, "nativeVirtualKeyCode": 188}  # <
    dot =                 {"code": "Dot",             "text": ".",  "keyIdentifier": "U+002E",  "key": ".",         "windowsVirtualKeyCode": 190, "nativeVirtualKeyCode": 190}
    period =              {"code": "Period",          "text": ".",  "keyIdentifier": "U+002E",  "key": ".",         "windowsVirtualKeyCode": 190, "nativeVirtualKeyCode": 190}
    angle_bracket_right = {"code": "AngleBracket",    "text": ">",  "keyIdentifier": "U+002E",  "key": ">",         "windowsVirtualKeyCode": 190, "nativeVirtualKeyCode": 190}  # >
    slash =               {"code": "Slash",           "text": "/",  "keyIdentifier": "U+00BF",  "key": "/",         "windowsVirtualKeyCode": 191, "nativeVirtualKeyCode": 191}
    question_mark =       {"code": "QuestionMark",    "text": "?",  "keyIdentifier": "U+00BF",  "key": "?",         "windowsVirtualKeyCode": 191, "nativeVirtualKeyCode": 191}  # ?
    backquote =           {"code": "Backquote",       "text": "`",  "keyIdentifier": "U+0060",  "key": "`",         "windowsVirtualKeyCode": 192, "nativeVirtualKeyCode": 192}
    tilda =               {"code": "Tilda",           "text": "~",  "keyIdentifier": "U+00C0",  "key": "~",         "windowsVirtualKeyCode": 192, "nativeVirtualKeyCode": 192}



WINDOWS_KEY_SET = {
    'LBUTTON': 1,   # Left mouse button
    'RBUTTON': 2,   # Right mouse button
    'CANCEL': 3,    # Control-break processing
    'MBUTTON': 4,   # Middle mouse button (three-button mouse)
    'XBUTTON1': 5,  # X1 mouse button
    'XBUTTON2': 6,  # X2 mouse button

    'BACK': 8,      # BACKSPACE key
    'BACKSPACE': 8, # BACKSPACE key
    'TAB': 9,       # TAB key
    'CLEAR': 12,    # CLEAR key
    'ENTER': 13,    # ENTER key
    'SHIFT': 16,    # SHIFT key
    'CONTROL': 17,  # CTRL key
    'ALT': 18,      # ALT key
    'PAUSE': 19,    # PAUSE key
    'CAPS': 20,     # CAPS LOCK key

    'KANA': 21,     # IME Kana mode
    'HANGUEL': 21,  # IME Hanguel mode (maintained for compatibility; use VK_HANGUL)
    'HANGUL': 21,   # IME Hangul mode
    'JUNJA': 23,    # IME Junja mode
    'FINAL': 24,    # IME final mode
    'HANJA': 25,    # IME Hanja mode
    'KANJI': 25,    # IME Kanji mode

    'CONVERT': 28,     # IME convert
    'NONCONVERT': 29,  # IME nonconvert
    'ACCEPT': 30,      # IME accept
    'MODECHANGE': 31,  # IME mode change request

    'ESCAPE': 27,    # ESC key
    'ESC': 27,       # ESC key
    'SPACE': 32,     # Пробел
    'PRIOR': 33,     # PAGE UP key
    'NEXT': 34,      # PAGE DOWN key
    'END': 35,       # END key
    'HOME': 36,      # HOME key
    'LEFT': 37,      # LEFT ARROW key
    'UP': 38,        # UP ARROW key
    'RIGHT': 39,     # RIGHT ARROW key
    'DOWN': 40,      # DOWN ARROW key
    'SELECT': 41,    # SELECT key
    'PRINT': 42,     # PRINT key
    'EXECUTE': 43,   # EXECUTE key
    'SNAPSHOT': 44,  # PRINT SCREEN key
    'INSERT': 45,    # INS key
    'DELETE': 46,    # DEL key
    'DEL': 46,       # DEL key
    'HELP': 47,      # HELP key

    '0': 48,  # 0 key
    '1': 49,  # 1 key
    '2': 50,  # 2 key
    '3': 51,  # 3 key
    '4': 52,  # 4 key
    '5': 53,  # 5 key
    '6': 54,  # 6 key
    '7': 55,  # 7 key
    '8': 56,  # 8 key
    '9': 57,  # 9 key
    'A': 65,
    'B': 66,
    'C': 67,
    'D': 68,
    'E': 69,
    'F': 70,
    'G': 71,
    'H': 72,
    'I': 73,
    'J': 74,
    'K': 75,
    'L': 76,
    'M': 77,
    'N': 78,
    'O': 79,
    'P': 80,
    'Q': 81,
    'R': 82,
    'S': 83,
    'T': 84,
    'U': 85,
    'V': 86,
    'W': 87,
    'X': 88,
    'Y': 89,
    'Z': 90,

    'LWIN': 91,        # Left Windows key (Natural keyboard)
    'RWIN': 92,        # Right Windows key (Natural keyboard)
    'APPS': 93,        # Applications key (Natural keyboard)
    'SLEEP': 95,       # Computer Sleep key
    'NUMPAD0': 96,     # Numeric keypad 0 key
    'NUMPAD1': 97,     # Numeric keypad 1 key
    'NUMPAD2': 98,     # Numeric keypad 2 key
    'NUMPAD3': 99,     # Numeric keypad 3 key
    'NUMPAD4': 100,    # Numeric keypad 4 key
    'NUMPAD5': 101,    # Numeric keypad 5 key
    'NUMPAD6': 102,    # Numeric keypad 6 key
    'NUMPAD7': 103,    # Numeric keypad 7 key
    'NUMPAD8': 104,    # Numeric keypad 8 key
    'NUMPAD9': 105,    # Numeric keypad 9 key
    'MULTIPLY': 106,   # Multiply key
    'ADD': 107,        # Add key
    'SEPARATOR': 108,  # Separator key
    'SUBTRACT': 109,   # Subtract key
    'DECIMAL': 110,    # Decimal key
    'DIVIDE': 111,     # Divide key

    'F1':  112,  # F1 key
    'F2':  113,  # F2 key
    'F3':  114,  # F3 key
    'F4':  115,  # F4 key
    'F5':  116,  # F5 key
    'F6':  117,  # F6 key
    'F7':  118,  # F7 key
    'F8':  119,  # F8 key
    'F9':  120,  # F9 key
    'F10': 121,  # F10 key
    'F11': 122,  # F11 key
    'F12': 123,  # F12 key
    'F13': 124,  # F13 key
    'F14': 125,  # F14 key
    'F15': 126,  # F15 key
    'F16': 127,  # F16 key
    'F17': 128,  # F17 key
    'F18': 129,  # F18 key
    'F19': 130,  # F19 key
    'F20': 131,  # F20 key
    'F21': 132,  # F21 key
    'F22': 133,  # F22 key
    'F23': 134,  # F23 key
    'F24': 135,  # F24 key

    'NUMLOCK': 144,              #NUM LOCK key
    'SCROLL': 145,               #SCROLL LOCK key
    'LSHIFT': 160,               #Left SHIFT key
    'RSHIFT': 161,               #Right SHIFT key
    'LCONTROL': 162,             #Left CONTROL key
    'RCONTROL': 163,             #Right CONTROL key
    'LMENU': 164,                #Left MENU key
    'RMENU': 165,                #Right MENU key
    'BROWSER_BACK': 166,         #Browser Back key
    'BROWSER_FORWARD': 167,      #Browser Forward key
    'BROWSER_REFRESH': 168,      #Browser Refresh key
    'BROWSER_STOP': 169,         #Browser Stop key
    'BROWSER_SEARCH': 170,       #Browser Search key
    'BROWSER_FAVORITES': 171,    #Browser Favorites key
    'BROWSER_HOME': 172,         #Browser Start and Home key
    'VOLUME_MUTE': 173,          #Volume Mute key
    'VOLUME_DOWN': 174,          #Volume Down key
    'VOLUME_UP': 175,            #Volume Up key
    'MEDIA_NEXT_TRACK': 176,     #Next Track key
    'MEDIA_PREV_TRACK': 177,     #Previous Track key
    'MEDIA_STOP': 178,           #Stop Media key
    'MEDIA_PLAY_PAUSE': 179,     #Play/Pause Media key
    'LAUNCH_MAIL': 180,          #Start Mail key
    'LAUNCH_MEDIA_SELECT': 181,  #Select Media key
    'LAUNCH_APP1': 182,          #Start Application 1 key
    'LAUNCH_APP2': 183,          #Start Application 2 key

    'OEM_1': 186,       #Used for miscellaneous characters; it can vary by keyboard. For the US standard keyboard, the ';:' key
    'OEM_PLUS': 187,    #For any country/region, the '+' key
    'OEM_COMMA': 188,   #For any country/region, the ',' key
    'OEM_MINUS': 189,   #For any country/region, the '-' key
    'OEM_PERIOD': 190,  #For any country/region, the '.' key
    'OEM_2': 191,       #Used for miscellaneous characters; it can vary by keyboard. For the US standard keyboard, the '/?' key =
    'OEM_3': 192,       #Used for miscellaneous characters; it can vary by keyboard. = For the US standard keyboard, the '`~' key
    'OEM_4': 219,       #Used for miscellaneous characters; it can vary by keyboard. For the US standard keyboard, the '[{' key
    'OEM_5': 220,       #Used for miscellaneous characters; it can vary by keyboard.For the US standard keyboard, the '\|' key
    'OEM_6': 221,       #Used for miscellaneous characters; it can vary by keyboard.For the US standard keyboard, the ']}' key
    'OEM_7': 222,       #Used for miscellaneous characters; it can vary by keyboard.For the US standard keyboard, the 'single-quote/double-quote' key
    'OEM_8': 223,       #Used for miscellaneous characters; it can vary by keyboard.
    'OEM_102': 226,     #Either the angle bracket key or the backslash key on the RT 102-key keyboard 0xE3-E4 OEM specific

    'PROCESSKEY': 229,  #IME PROCESS key 0xE6 = OEM specific #
    'PACKET': 231,      #Used to pass Unicode characters as if they were keystrokes. The VK_PACKET key is the low word of a 32-bit Virtual "key" value used for non-keyboard input methods. For more information, see Remark in KEYBDINPUT, SendInput, WM_KEYDOWN, and WM_KEYUP #-
    'ATTN': 246,        #Attn key
    'CRSEL': 247,       #CrSel key
    'EXSEL': 248,       #ExSel key
    'EREOF': 249,       #Erase EOF key
    'PLAY': 250,        #Play key
    'ZOOM': 251,        #Zoom key
    'NONAME': 252,      #Reserved
    'PA1': 253,         #PA1 key
    'OEM_CLEAR': 254,   #
}

if __name__ == '__main__':
    s = ""
    for field in KeyEvents.__dict__:
        if "__" in field: continue
        key: dict = getattr(KeyEvents, field)
        # print(field, key)

        s += f"""    pub {field}: KeyEvent,\n"""
        # s += f"""    {field}: KeyEvent{{ code: "{key['code']}", text: "{key['text']}", key_identifier: "{key['keyIdentifier']}", key: "{key['key']}", windows_virtual_key_code: {key['windowsVirtualKeyCode']}, native_virtual_key_code: {key['nativeVirtualKeyCode']} }},\n"""

    print(s)
