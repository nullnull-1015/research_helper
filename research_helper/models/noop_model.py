from research_helper.models.base import Model

from langchain_core.runnables import RunnableLambda


class NoopModel(Model):
    def __init__(self) -> None:
        self._model = RunnableLambda(lambda input: input)
    
    def _invoke(self, input, config=None):
        return self._model.invoke(input, config)
