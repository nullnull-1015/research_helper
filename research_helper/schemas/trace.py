from typing import List, Union
from pydantic import BaseModel, Field
from langchain_core.tracers.schemas import Run

from research_helper.schemas.run import RunSerializable

class TraceListSerializable(BaseModel):
    traces: List[RunSerializable] = Field(default_factory=list)
    
    def add_trace(self, run: Union[Run, RunSerializable]) -> RunSerializable:
        if isinstance(run, Run):
            run = RunSerializable.from_run(run)
        self.traces.append(run)
        return run