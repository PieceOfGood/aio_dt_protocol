class MyBaseException(Exception): pass

class JavaScriptError(MyBaseException): pass

class NullProperty(MyBaseException): pass

class EvaluateError(MyBaseException): pass

class TargetCrashed(MyBaseException): pass

class PositionOutOfBounds(MyBaseException): pass

class CouldNotFindNodeWithGivenID(MyBaseException): pass

class RootIDNoLongerExists(MyBaseException): pass                       # ! для QuerySelector-методов


exception_store = {
    "Target crashed": TargetCrashed,
    "Position out of bounds": PositionOutOfBounds,
    "Could not find node with given id": CouldNotFindNodeWithGivenID
}
