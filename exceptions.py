class MyBaseException(Exception): pass

class JavaScriptError(MyBaseException): pass

class NullProperty(MyBaseException): pass

class EvaluateError(MyBaseException): pass

class NodeNotResolved(MyBaseException): pass

class NodeNotDescribed(MyBaseException): pass

class StateError(MyBaseException): pass

class FlagArgumentContainError(MyBaseException): pass


class TargetCrashed(MyBaseException): pass

class PositionOutOfBounds(MyBaseException): pass

class CouldNotFindNodeWithGivenID(MyBaseException): pass

class RootIDNoLongerExists(MyBaseException): pass                       # ! для QuerySelector-методов

class CouldNotComputeContentQuads(MyBaseException): pass

class NoDialogIsShowing(MyBaseException): pass                          # ! при перехвате диалоговых окон

class NoTargetWithGivenIdFound(MyBaseException): pass

class NoScriptWithGivenId(MyBaseException): pass

class UniqueContextIdNotFound(MyBaseException): pass

class AnotherLocaleOverrideIsAlreadyInEffect(MyBaseException): pass     # ! при установке той же локали

class FontFamiliesCanOnlyBeSetOnce(MyBaseException): pass               # ! при установке тех же шрифтов


exception_store = {
    "Target crashed": TargetCrashed,
    "Position out of bounds": PositionOutOfBounds,
    "Could not find node with given id": CouldNotFindNodeWithGivenID,
    "Could not compute content quads": CouldNotComputeContentQuads,
    "No dialog is showing": NoDialogIsShowing,
    "No target with given id found": NoTargetWithGivenIdFound,
    "No script with given id": NoScriptWithGivenId,
    "uniqueContextId not found": UniqueContextIdNotFound,
    "Another locale override is already in effect": AnotherLocaleOverrideIsAlreadyInEffect,
    "Font families can only be set once": FontFamiliesCanOnlyBeSetOnce
}
