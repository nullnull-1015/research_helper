from typing import Any, Optional, Union, Dict, List
from collections import deque
from streamlit.delta_generator import DeltaGenerator
import streamlit as st

from research_helper.schemas.trace import RunSerializable
from research_helper.tracer.trace_log import TraceLogBase
from research_helper.ui.components import CSVTmpUploader
from research_helper.ui.views.base import InteractiveRunViewBase
from research_helper.ui.views.observer import OnserverBase, Request
from research_helper.ui.views.requests import RUN_MODEL_REQUEST

class ChatView(InteractiveRunViewBase):
    def __init__(self, input_field_keys: List[str], trace_log: TraceLogBase, observers: List[OnserverBase] = []) -> None:
        super().__init__(input_field_keys, trace_log, observers)
        
        # state
        self._output_fields: Dict[str, DeltaGenerator] = {}
        
        self._input_queue = deque()
        
        # components
        self._chat_container = None
        self._output_container: Optional[DeltaGenerator] = None
        self._csv_tmp_uploader = CSVTmpUploader(columns=self.input_field_keys)
    
    def draw(self) -> None:
        self._chat_container = st.container(height=480, border=False)
        
        # Field: Chat
        self._draw_chat(self._chat_container)
        
        # Field: User Input
        ## render from tab
        form_tab, file_tab = st.tabs(["Form", "File"])
        with form_tab:
            with st.form("input_form", clear_on_submit=True):
                for input_key in self.input_field_keys:
                    st.text_input(input_key, placeholder=input_key, key=input_key)

                placeholder, submit_button = st.columns([0.9, 0.1])
                with submit_button:
                    st.form_submit_button(":material/send:", on_click=self._on_submit)
        
        ## render file tab
        with file_tab:
            self._csv_tmp_uploader.draw()
            
            placeholder, submit_button = st.columns([0.9, 0.1])
            with submit_button:
                st.button(":material/send:", on_click=self._on_file_submit)
    
    def _draw_chat(self, parent: DeltaGenerator):
        # show chat history
        self._write_runs(parent)
        # show new dialog
        self._write_current_dialog(parent)
    
    def _on_submit(self):
        # get inputs from input field and push it into queue
        inputs = {}
        for input_key in self.input_field_keys:
            if input_key in st.session_state:
                inputs[input_key] = st.session_state[input_key]
        
        self._input_queue.append(inputs)
    
    def _on_file_submit(self):
        # get inputs from csv file and push them into queue
        if self._csv_tmp_uploader.df is not None:
            keys = [key for key in self.input_field_keys if key in self._csv_tmp_uploader.df.columns]
            inputs = self._csv_tmp_uploader.df[keys]
            # input_template = {key: "" for key in self.input_field_keys}
            input_template = {}
            for idx, new_input in inputs.iterrows():
                input = input_template.copy()
                input.update(new_input.to_dict())
                self._input_queue.append(input)
    
    def write(self, outputs: Dict):
        if not self._output_container: return
        
        for key, output in outputs.items():
            if key not in self._output_fields:
                self._output_fields[key] = self._write_ai_message(parent=self._output_container, outputs=output, model_name=key if len(outputs)>1 else "")
            else:
                self._output_fields[key].markdown(output)
    
    def error(self, error: str):
        if not self._output_container: return
        
        with self._output_container.chat_message("assistant"):
            st.error(error)
        
        # ファイルによる入力は同様のエラーを起こし得るデータが入っている可能性が高い
        # -> 一度キューをリセットする
        self._input_queue.clear()
    
    def update(self):
        self._write_current_dialog(parent=self._chat_container)
    
    def _write_run(self, parent: DeltaGenerator, run: RunSerializable):
        self._write_user_message(parent=parent, inputs=run.inputs)
        for model_name, output in run.outputs.items():
            self._write_ai_message(parent=parent, outputs=output, model_name=model_name if len(run.outputs)>1 else "")
        
    def _write_runs(self, parent: DeltaGenerator):
        for trace in self.trace_log.get_trace():
            self._write_run(parent=parent, run=trace)
    
    def _write_current_dialog(self, parent: DeltaGenerator):
        if not len(self._input_queue)>0: return
        
        with parent:
            input = self._input_queue.popleft()
            self._write_user_message(parent=parent, inputs=input)
            self._output_fields = {} # clear previous output_fields
            self._output_container = st.container() # placeholder for ai putput
            
            # send request to run the language model
            self.notify(
                Request(
                    name=RUN_MODEL_REQUEST,
                    value=input,
                )
            )
    
    def _write_user_message(self, parent: DeltaGenerator, inputs: Dict) -> DeltaGenerator:
        if inputs := self._parse_inputs(inputs):
            with parent.chat_message("user"):
                return st.markdown(inputs)
        return st.empty()
    
    def _write_ai_message(self, parent: DeltaGenerator, outputs: Union[str, Dict], model_name: str="") -> DeltaGenerator:
        if outputs := self._parse_outputs(outputs):
            with parent.chat_message("assistant"):
                with st.container(border=True):
                    if model_name: st.text(model_name)
                    return st.markdown(outputs)
        return st.empty()
    
    def _parse_inputs(self, inputs: Union[str, Dict]):
        inputs = {"input": inputs} if not isinstance(inputs, dict) else inputs
        if len(inputs) == 1:
            return list(inputs.values())[0]
        if len(self.input_field_keys) == 1 and self.input_field_keys[0] in inputs:
            return inputs[self.input_field_keys[0]]
        
        return inputs
    
    def _parse_outputs(self, outputs: Union[str, Dict]):
        return outputs