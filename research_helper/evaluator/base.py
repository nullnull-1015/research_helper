from abc import ABC, abstractmethod
from typing import TypeVar, Generic

Value = TypeVar('Value')
Result = TypeVar('Result')

class EvaluatorBase(ABC, Generic[Value, Result]):
    name: str = "base_evaluator"
    def evaluate(self, output: Value, example: Value) -> Result:
        pass
    
    @property
    @abstractmethod
    def default(self) -> Result:
        pass