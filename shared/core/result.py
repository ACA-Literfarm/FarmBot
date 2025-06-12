# shared/core/result.py

from typing import Generic, TypeVar, Optional

T = TypeVar("T")

class Result(Generic[T]):
    def __init__(self, success: bool, data: Optional[T] = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error

    def __repr__(self):
        if self.success:
            return f"✅ Success: {self.data}"
        else:
            return f"❌ Error: {self.error}"