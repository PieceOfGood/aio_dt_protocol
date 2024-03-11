from dataclasses import dataclass, field
from typing import Literal, Optional, List, Union, Dict


@dataclass
class BindingCalledData:
    name: str
    payload: str
    executionContextId: int


@dataclass
class SerializationOptions:
    serialization: Literal["deep", "json", "idOnly"]
    maxDepth: Optional[int] = None

    def as_dict(self) -> Dict[str, Union[str, int]]:
        result = {"serialization": self.serialization}
        if self.maxDepth is not None:
            result.update({"maxDepth": self.maxDepth})
        return result


@dataclass
class PropertyPreview:
    name: str
    type: Literal["object", "function", "undefined", "string", "number", "boolean", "symbol", "accessor", "bigint"]
    valuePreview: Optional['ObjectPreview']
    value: Optional[str] = None
    _valuePreview: Optional['ObjectPreview'] = field(init=False, repr=False, default=None)
    subtype: Literal[
        "array", "null", "node", "regexp", "date", "map", "set", "weakmap", "weakset", "iterator", "generator",
        "error", "proxy", "promise", "typedarray", "arraybuffer", "dataview", "webassemblymemory", "wasmvalue"] = None

    @property
    def valuePreview(self) -> 'ObjectPreview':
        return self._valuePreview

    @valuePreview.setter
    def valuePreview(self, data: dict) -> None:
        self._valuePreview = ObjectPreview(**data) if not isinstance(data, property) else None


@dataclass
class EntryPreview:
    _value: 'ObjectPreview'
    _key: Optional['ObjectPreview']

    @property
    def key(self) -> 'ObjectPreview':
        return self._key

    @key.setter
    def key(self, data: dict) -> None:
        self._key = ObjectPreview(**data)

    @property
    def value(self) -> 'ObjectPreview':
        return self._value

    @value.setter
    def value(self, data: dict) -> None:
        self._value = ObjectPreview(**data)


@dataclass
class CustomPreview:
    header: str
    bodyGetterId: Optional[str] = None


@dataclass
class ObjectPreview:
    type: Literal["object", "function", "undefined", "string", "number", "boolean", "symbol", "bigint"]
    overflow: bool
    properties: List['PropertyPreview']
    entries: List['EntryPreview']
    subtype: Optional[Literal[
        "array", "null", "node", "regexp", "date", "map", "set", "weakmap", "weakset", "iterator", "generator",
        "error", "proxy", "promise", "typedarray", "arraybuffer", "dataview", "webassemblymemory", "wasmvalue"]] = None
    description: Optional[str] = None
    _entries: List['EntryPreview'] = field(init=False, repr=False, default=None)

    @property
    def properties(self) -> List['PropertyPreview']:
        return self._properties

    @properties.setter
    def properties(self, data: List[dict]) -> None:
        self._properties = [PropertyPreview(**item) for item in data]

    @property
    def entries(self) -> List['EntryPreview']:
        return self._entries

    @entries.setter
    def entries(self, data: List[dict]) -> None:
        self._entries = [EntryPreview(**item) for item in data] if not isinstance(data, property) else None


@dataclass
class RemoteObject:
    """
    Зеркальный объект, ссылающийся на исходный объект JavaScript.
    # https://chromedevtools.github.io/devtools-protocol/tot/Runtime/#type-RemoteObject
    """
    type: Literal["object", "function", "undefined", "string", "number", "boolean", "symbol", "bigint"]
    preview: Optional["ObjectPreview"]
    customPreview: Optional["CustomPreview"]
    subtype: Optional[Literal[
        "array", "null", "node", "regexp", "date", "map", "set", "weakmap", "weakset", "iterator", "generator",
        "error", "proxy", "promise", "typedarray", "arraybuffer", "dataview", "webassemblymemory", "wasmvalue"]] = None
    className: Optional[str] = None
    value: Optional[any] = None
    unserializableValue: Optional[str] = None   # ? Примитивное значение, которое не может быть преобразовано в строку
                                                # ?     JSON, не имеет value, но получает это свойство.
    description: Optional[str] = None
    objectId: Optional[str] = None
    _preview: Optional['ObjectPreview'] = field(init=False, repr=False, default=None)
    _customPreview: Optional['CustomPreview'] = field(init=False, repr=False, default=None)

    @property
    def preview(self) -> 'ObjectPreview':
        return self._preview

    @preview.setter
    def preview(self, data: dict) -> None:
        self._vpreview = ObjectPreview(**data) if not isinstance(data, property) else None

    @property
    def customPreview(self) -> 'CustomPreview':
        return self._customPreview

    @customPreview.setter
    def customPreview(self, data: dict) -> None:
        self._customPreview = CustomPreview(**data) if not isinstance(data, property) else None


@dataclass
class AuxData:
    isDefault: bool
    type: str
    frameId: str


@dataclass
class ContextDescription:
    id: int
    origin: str     # url
    name: str
    uniqueId: str
    auxData: 'AuxData'

    @property
    def auxData(self) -> 'AuxData':
        return self._auxData

    @auxData.setter
    def auxData(self, data: dict) -> None:
        self._auxData = AuxData(**data)

@dataclass
class PropertyDescriptor:
    name: str
    configurable: bool
    enumerable: bool
    value: Optional['RemoteObject'] = None
    writable: Optional[bool] = None
    get: Optional['RemoteObject'] = None
    set: Optional['RemoteObject'] = None
    wasThrown: Optional[bool] = None
    isOwn: Optional[bool] = None
    symbol: Optional['RemoteObject'] = None



class Script:
    """
    Упаковывает вызываемое в контексте указанного фрейма выражение. Если контекст не указан, в его качестве
        будет выбран фрейм верхнего уровня. Выражение можно заменить при вызове.
    """
    def __init__(
            self, conn, expression: str,
            context: Optional[Union['ContextDescription', str]] = None):
        self._connection = conn
        self.expression = expression
        self.unique_context_id = context if type(context) is str else context.uniqueId if context is not None else None

    async def Call(
            self, expression: Optional[str] = None, returnByValue: Optional[bool] = None) -> 'RemoteObject':
        if expression:
            self.expression = expression
        args = {"expression": self.expression}
        if returnByValue is not None:
            args.update(returnByValue=returnByValue)
        if self.unique_context_id is not None:
            args.update(uniqueContextId=self.unique_context_id)
        result: dict = await self._connection.call("Runtime.evaluate", args)
        return RemoteObject(**result.get("result"))


class ContextManager:
    contexts: List['ContextDescription'] = []
    is_watch: bool = False

    async def on_create(self, data: dict, _) -> None:
        self.contexts.append(ContextDescription(**data.get("context")))

    async def on_clear(self, data: dict, _) -> None:
        self.contexts = []

    async def on_destroy(self, data: dict, _) -> None:
        context_id: int = data.get("executionContextId")
        ii = -1
        for i, ctx in enumerate(self.contexts):
            if ctx.id == context_id:
                ii = i
                break

        if ii > -1: self.contexts.pop(ii)

    def GetDefaultContext(self, frameId: str) -> Union['ContextDescription', None]:
        for ctx in self.contexts:
            print("frameId", frameId)
            print("Runtime context", ctx, len(self.contexts))
            if ctx.auxData.frameId == frameId and ctx.auxData.isDefault:
                return ctx
        return None
