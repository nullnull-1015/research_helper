from typing import Any
from langchain_core.tracers import BaseTracer
from langchain_core.tracers.schemas import Run

from research_helper.tracer.trace_log import TraceLogBase

REDANDANT_EVENTS = [
    "new_token",
]

class TraceCollectorCallbackHandler(BaseTracer):
    def __init__(self, log: TraceLogBase, **kwargs: Any):
        super().__init__(**kwargs)
        self._log = log
    
    def _persist_run(self, run: Run) -> None:
        if run.outputs is not None: # if run finished in error, outputs should be None
            self._log.add_trace(self._remove_redandant_events(run))
    
    def _remove_redandant_events(self, run: Run):
        run.events = [event for event in run.events if event["name"] not in REDANDANT_EVENTS]
        if run.child_runs:
            for child_run in run.child_runs:
                self._remove_redandant_events(child_run)
        
        return run