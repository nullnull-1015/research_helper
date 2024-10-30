from typing import Any, Optional, Coroutine, Dict
from uuid import UUID
from langchain_core.tracers.base import BaseTracer
from langchain_core.tracers.schemas import Run

from research_helper.ui.views.base import InteractiveRunViewBase

class UICallbackHandler(BaseTracer):
    """ Copied only streaming part from StreamlitCallbackHandler """
    
    def __init__(self, view: InteractiveRunViewBase, **kwargs) -> None:
        super().__init__(**kwargs)
        self._view = view

    def _persist_run(self, run: Run) -> None:
        if run.outputs is not None:
            self._view.write(run.outputs)
        else: # if an error occured, outputs should be None
            self._view.error(run.error)
        self._view.update()
        

class UIStreamingCallbackHandler(UICallbackHandler):
    """ Copied only streaming part from StreamlitCallbackHandler """
    
    def __init__(self, name: str, view: InteractiveRunViewBase, **kwargs) -> None:
        super().__init__(**kwargs)
        self.name = name
        self._view = view
        self._tokens_stream = ""
    
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """ Run on new LLM token. Only available when streaming is enabled. """
        self._tokens_stream += token
        self._view.write({self.name: self._tokens_stream})
