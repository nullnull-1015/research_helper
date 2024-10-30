from abc import ABC, abstractmethod
from typing import Any, List, TypedDict

class Request(TypedDict):
    name: str
    value: Any

class OnserverBase(ABC):
    _targets: List[str] # set target event you want to handle in your observer
    
    def _is_target(self, request: Request):
        return request['name'] in self._targets
    
    @abstractmethod
    def _process(self, request: Request):
        # actual action when the target order is given
        pass
    
    def notify(self, request: Request):
        if self._is_target(request):
            return self._process(request)