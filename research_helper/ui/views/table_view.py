from typing import Any, Dict, List, Optional, Callable, Sequence
import streamlit as st
import pandas as pd

from langchain_core.messages.base import BaseMessage
from langchain_core.prompt_values import PromptValue

from research_helper.tracer.trace_log import TraceLogBase
from research_helper.schemas.run import RunSerializable
from research_helper.ui.views.base import RunViewBase
from research_helper.ui.views.observer import OnserverBase, Request

def get_recursively(run: RunSerializable, target: str, prefix="", default: Callable=lambda x: x):
    # get target from current run
    targets = getattr(run, target)
    prefix += run.name if prefix=="" else f"-{run.name}"
    
    items = {}
    if isinstance(targets, dict):
        for key, item in targets.items():
            items[prefix+"_"+target+"-"+key] = default(item)
    else:
        items[prefix+"_"+target] = default(targets)
    
    # aquire target from children
    for child in run.child_runs:
        items.update(get_recursively(run=child, target=target, prefix=prefix, default=default))
    
    return items

def serialize(target: Any) -> str:
    if isinstance(target, str):
        return target
    elif isinstance(target, BaseMessage):
        return target.pretty_repr()
    elif isinstance(target, PromptValue):
        return target.to_string()
    elif isinstance(target, Sequence):
        return [serialize(t) for t in target]
    else:
        return str(target)

class TableView(RunViewBase):
    SELECT_COLUMN = "__selected"
    
    def __init__(self, trace_log: TraceLogBase) -> None:
        super().__init__(trace_log)
        self._table: pd.DataFrame = None
    
    def draw(self) -> None:
        runs_df = self.table
        self._table = st.data_editor(
            runs_df,
            column_config={
                TableView.SELECT_COLUMN: st.column_config.CheckboxColumn(
                    "selected",
                    help="Select to pick out.",
                    default=True,
                )
            },
            disabled=[column for column in runs_df.columns if column != TableView.SELECT_COLUMN],
            hide_index=True,
        )
    
    @property
    def selected(self) -> Optional[pd.DataFrame]:
        if TableView.SELECT_COLUMN not in self._table.columns: return None
        return self._table[self._table[TableView.SELECT_COLUMN]==True]
    
    @property
    def table(self) -> pd.DataFrame:
        return pd.DataFrame(data=[
            {
                TableView.SELECT_COLUMN: True,
                "id": run.id,
                **get_recursively(run, "inputs", default=serialize),
                **get_recursively(run, "outputs", default=serialize),
            }
            for run in self.trace_log.get_trace()
        ])
        