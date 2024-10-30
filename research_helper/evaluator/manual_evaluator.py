from research_helper.evaluator.base import EvaluatorBase

class ManualEvaluator(EvaluatorBase):
    def evaluate(self, output: str, example: str) -> bool:
        return self.default # 自動評価ではデフォルトを設定し、後から人手で更新する
    
    @property
    def default(self) -> bool:
        return False