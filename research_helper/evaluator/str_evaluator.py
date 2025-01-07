from typing import Any, List
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
        return example in output
    
    @property
    def default(self) -> bool:
        return False

class MultiFullMatchEvaluator(EvaluatorBase):
    name = "multi_full_match_evaluator"
    
    def evaluate(self, output: str, example: List[str]) -> bool:
        if isinstance(example, str): example = [example]
        return any(output == item for item in example)
    
    @property
    def default(self) -> bool:
        return False

class MultiPartialMatchEvaluator(EvaluatorBase):
    name = "multi_partial_match_evaluator"
    
    def evaluate(self, output: str, example: List[str]) -> bool:
        if isinstance(example, str): example = [example]
        return any(item in output for item in example)
    
    @property
    def default(self) -> bool:
        return False

