from typing import Any, Optional, Dict, List, TypeVar
from typing_extensions import Annotated
from pydantic import BaseModel, Field, PlainValidator, PlainSerializer
from datetime import datetime
from uuid import UUID
from langchain_core.tracers.schemas import Run
from langchain_core.load import Serializable, load, dumpd

Self = TypeVar("Self", bound="RunSerializable")

serializable = Annotated[
    Serializable,
    PlainValidator(load),
    PlainSerializer(dumpd)
]

class RunSerializable(BaseModel):
    id: UUID
    name: str
    start_time: datetime
    run_type: str
    end_time: Optional[datetime] = None
    extra: Optional[Dict] = None
    error: Optional[str] = None
    serialized: Optional[Dict] = None
    events: List[Dict[str, Any]] = Field(default_factory=list)
    inputs: Dict[Any, serializable] = Field(default_factory=dict)
    outputs: Optional[Dict[Any, serializable]] = Field(default=None)
    reference_example_id: Optional[UUID] = None
    parent_run_id: Optional[UUID] = None
    child_runs: List["RunSerializable"] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)
    trace_id: Optional[UUID] = None
    dotted_order: Optional[str] = None
    
    @classmethod
    def from_run(cls: Self, run: Run) -> Self:
        return cls(
            id=run.id,
            name=run.name,
            start_time=run.start_time,
            run_type=run.run_type,
            end_time=run.end_time,
            extra=run.extra,
            error=run.error,
            serialized=run.serialized,
            events=run.events,
            inputs=run.inputs,
            outputs=run.outputs,
            reference_example_id=run.reference_example_id,
            parent_run_id=run.parent_run_id,
            child_runs=[
                RunSerializable.from_run(run=child_run)
                for child_run in run.child_runs
            ],
            tags=run.tags,
            trace_id=run.trace_id,
            dotted_order=run.dotted_order,
        )
