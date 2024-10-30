from abc import ABC, abstractmethod
from typing import Any, Dict


class Model(ABC):
    @abstractmethod
    def invoke(self, input: Any):
        pass
    
    @abstractmethod
    def format_input(self, input: Any) -> Dict[str, Any]:
        """ returns formatted input like {column_name: output} """
        pass
    
    @abstractmethod
    def format_output(self, output: Any) -> Dict[str, Any]:
        """ returns formatted output like {column_name: output} """
        pass