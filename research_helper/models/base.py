from abc import ABC, abstractmethod
from typing import Optional

from langchain_core.runnables.base import Input, Output, Runnable
from langchain_core.runnables.config import RunnableConfig

class Model(Runnable):
    """
        adaptor to make your model runnable
    """
    # if you want to force your model as entry point, set name as "entry_point" in your Model
    # name: str = "entry_point"
    
    def invoke(self, input: Input, config: Optional[RunnableConfig]=None) -> Output:
        return self._call_with_config(self._invoke, input, config)
    
    
    @abstractmethod
    def _invoke(self, input: Input, config:Optional[RunnableConfig]=None) -> Output:
        pass
