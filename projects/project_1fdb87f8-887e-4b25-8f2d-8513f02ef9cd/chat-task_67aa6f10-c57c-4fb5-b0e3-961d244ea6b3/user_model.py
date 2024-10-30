from langchain_core.runnables import RunnableParallel, RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.config import RunnableConfig
from research_helper.models.base import Model

class TestModel(Model):
    name: str = "entry_point"
    
    def __init__(self) -> None:
        super().__init__()
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Please respond to the user's request only based on the given context."),
            ("user", "Question: {question}\nContext: {context}")
        ])

        chain_a = RunnableLambda(lambda input: f"A:{input}") | StrOutputParser()
        chain_b = RunnableLambda(lambda input: f"B:{input}") | StrOutputParser()
        body = RunnableParallel({"A": chain_a, "B": chain_b})
        self._chain = prompt | body
    
    def _invoke(self, input, config: RunnableConfig = None):
        return self._chain.invoke(input, config)