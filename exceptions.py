class MyBaseException(Exception): pass

class JavaScriptError(MyBaseException): pass

class EvaluateError(MyBaseException): pass

class TargetCrashed(MyBaseException): pass

class PositionOutOfBounds(MyBaseException): pass


exception_store = {
    "Target crashed": TargetCrashed,
    "Position out of bounds": PositionOutOfBounds
}
