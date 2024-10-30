from .base import EvaluatorBase
from .str_evaluator import FullMatchEvaluator, PartialMatchEvaluator
from .manual_evaluator import ManualEvaluator

evaluators = [
    FullMatchEvaluator,
    PartialMatchEvaluator,
    ManualEvaluator,
]