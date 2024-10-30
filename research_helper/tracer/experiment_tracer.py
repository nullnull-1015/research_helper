from typing import Any, Union, Coroutine
from langchain_core.tracers import BaseTracer
from langchain_core.tracers.schemas import Run

class ExperimentTracer(BaseTracer):
    def __init__(
        self, **kwargs: Any
    ) -> None:
        """
        Initialize the RunCollectorCallbackHandler.

        Parameters
        ----------
        example_id : Optional[Union[UUID, str]], default=None
            The ID of the example being traced. It can be either a UUID or a string.
        **kwargs : Any
            Additional keyword arguments
        """
        super().__init__(**kwargs)
        self.traced_runs: list[Run] = []

    
    def _on_llm_start(self, run: Run) -> Union[None, Coroutine[Any, Any, None]]:
        print(run.outputs)
        return super()._on_llm_start(run)

    def _on_llm_end(self, run: Run) -> Union[None, Coroutine[Any, Any, None]]:
        print(run.outputs)
        return super()._on_llm_end(run)
    
    def _on_chain_start(self, run: Run) -> Union[None, Coroutine[Any, Any, None]]:
        print(run.outputs)
        return super()._on_chain_start(run)
    
    def _on_chain_end(self, run: Run) -> Union[None, Coroutine[Any, Any, None]]:
        print(run.outputs)
        return super()._on_chain_end(run)
    
    def _persist_run(self, run: Run) -> None:
        """
        Persist a run by adding it to the traced_runs list.

        Parameters
        ----------
        run : Run
            The run to be persisted.
        """
        run_ = run.copy()
        self.traced_runs.append(run_)

# class ExperimentTracerManager()