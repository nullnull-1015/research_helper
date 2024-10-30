from typing import Any, Dict, Literal
from langchain_core.tracers import BaseTracer
from langchain_core.tracers.schemas import Run
import pandas as pd


class CsvLogger(BaseTracer):
    def __init__(self, path, _schema_format: Literal['original'] | Literal['streaming_events'] | Literal['original+chat'] = "original", **kwargs: Any) -> None:
        super().__init__(_schema_format=_schema_format, **kwargs)
        
        self._path = path
    
    def _persist_run(self, run: Run) -> None:
        self.save(run)
    
    def save(self, run: Run) -> None:
        """ serialize and save """
    
    def _parse(self) -> Dict:
        """"""