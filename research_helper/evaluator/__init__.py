from .base import EvaluatorBase
from .str_evaluator import FullMatchEvaluator, PartialMatchEvaluator, MultiFullMatchEvaluator, MultiPartialMatchEvaluator
from .manual_evaluator import ManualEvaluator

evaluators = [
    FullMatchEvaluator,
    PartialMatchEvaluator,
    ManualEvaluator,
    MultiFullMatchEvaluator,
    MultiPartialMatchEvaluator,
]