from abc import ABC, abstractmethod
from typing import Union, Dict, List, Any
import json
from langchain_core.tracers.schemas import Run

from research_helper.schemas.trace import RunSerializable, TraceListSerializable

class TraceLogBase(ABC):
    @abstractmethod
    def add_trace(self, run: Run) -> Union[RunSerializable, None]:
        ...
    
    @abstractmethod
    def get_trace(self) -> List[RunSerializable]:
        ...
        
    @abstractmethod
    def save(self) -> None:
        ...
    
    @property
    @abstractmethod
    def _serialized(self) -> str:
        """ serilaized log """
        ...

class TraceLog(TraceLogBase):
    def __init__(self, file_path: str) -> None:
        self._file_path = file_path
        self._trace_list = TraceListSerializable(**self._load_log())
    
    def add_trace(self, run: Run) -> Union[RunSerializable, None]:
        if not self._is_trace(run):
            return None
        return self._trace_list.add_trace(run)
    
    def _is_trace(self, run: Run):
        return run.parent_run_id is None
    
    def get_trace(self) -> List[RunSerializable]:
        return self._trace_list.traces
    
    def save(self) -> None:
        with open(self._file_path, mode="w", encoding="utf-8") as log_file:
            log_file.write(self._serialized)
    
    def _load_log(self) -> Dict[str, Any]:
        try:
            with open(self._file_path, mode="r", encoding="utf-8") as log_file:
                return json.load(log_file)
        except:
            return {'traces': []}
    
    @property
    def _serialized(self) -> str:
        return self._trace_list.model_dump_json(indent=2)


class TraceLogDecorator(TraceLogBase):
    def __init__(self, component: TraceLogBase) -> None:
        self._component = component
        
    def get_trace(self) -> List[RunSerializable]:
        return self._component.get_trace()
    
    def save(self) -> None:
        return self._component.save()
    
    @property
    def _serialized(self) -> str:
        return self._component._serialized

class TraceConstantSavingLog(TraceLogDecorator):
    def __init__(self, component, interval=1) -> None:
        super().__init__(component)
        
        self._interval  = interval
        self._update_count = 0
    
    def add_trace(self, run: Run) -> Union[RunSerializable, None]:
        added_run = self._component.add_trace(run)
        
        # save
        if added_run:
            self._update_count+=1
        if self._update_count % self._interval == 0:
            self.save()
        
        return added_run
