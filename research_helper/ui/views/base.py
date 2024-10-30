from abc import ABC, abstractmethod
from typing import Any, Dict, List

from research_helper.tracer.trace_log import TraceLogBase
from research_helper.ui.views.observer import OnserverBase, Request
from research_helper.ui.base import Drawable

class RunViewBase(Drawable):
    def __init__(self, trace_log: TraceLogBase) -> None:
        self.trace_log = trace_log
    
    @abstractmethod
    def draw(self) -> None:
        pass

class InteractiveRunViewBase(RunViewBase):
    def __init__(self, input_field_keys: List[str], trace_log: TraceLogBase, observers: List[OnserverBase] = []) -> None:
        super().__init__(trace_log)
        self.input_field_keys = input_field_keys
        self.observers = observers
    
    @abstractmethod
    def write(self, key: str, contents: Any):
        """ write into writing field """
    
    @abstractmethod
    def error(self, error: str):
        """ show error message in writing field and handle them if needed """

    @abstractmethod
    def update(self):
        """ update writing field """
    
    def notify(self, request: Request):
        for observer in self.observers:
            observer.notify(request)
    
    def set_input_fields(self, input_fields: List[str]):
        self.input_field_keys = input_fields