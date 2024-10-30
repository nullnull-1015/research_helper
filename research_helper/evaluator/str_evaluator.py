from typing import Any
from research_helper.evaluator.base import EvaluatorBase

class FullMatchEvaluator(EvaluatorBase):
    name = "full_match_evaluator"
    
    def evaluate(self, output: str, example: str) -> bool:
        return output == example
    
    @property
    def default(self) -> bool:
        return False

class PartialMatchEvaluator(EvaluatorBase):
    name = "partial_match_evaluator"
    
    def evaluate(self, output: str, example: str) -> bool:
        return output in example
    
    @property
    def default(self) -> bool:
        return False