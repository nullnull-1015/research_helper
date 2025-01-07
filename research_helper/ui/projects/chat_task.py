import sys
import json
import traceback
import streamlit as st
from typing import Dict, Optional, List
from dataclasses import dataclass

from research_helper.ui.projects.task_base import Task, TaskConfigComponent
from research_helper.ui.components import AddingList, RowComponentFactory, TextInput, ModelUploader
from research_helper.ui.views import ChatView, TableView
from research_helper.ui.views.observer import Request, OnserverBase
from research_helper.ui.views.requests import RUN_MODEL_REQUEST

from research_helper.models import Model
from research_helper.tracer.trace_log import TraceLog, TraceConstantSavingLog
from research_helper.tracer.trace_collector import TraceCollectorCallbackHandler
from research_helper.tracer.ui_stramer import UICallbackHandler


CHAT_LOG_FILE = "chat.log"
@dataclass
class ChatConfig:
    args: List[str]
    model: Model
    config: Dict

class ChatConfigPanel(TaskConfigComponent):
    def __init__(self, task_path: str) -> None:
        super().__init__(task_path)
        
        textinput_factory = RowComponentFactory(row_component_cls=TextInput)
        self.arg_list = AddingList(label="Chat Inputs", row_factory=textinput_factory)
        self.model_uploader = ModelUploader(task_path)
        
        # initialize state
        self.arg_list.set_values(self._config["args"])
        
        self._save_config()
    
    def draw_body(self) -> None:
        left_col, _, right_col = st.columns([0.3, 0.1, 0.6])
        with left_col:
            self._config["args"] = self.arg_list.draw()
        with right_col:
            self.model_uploader.draw()
            
    
    def _load_config(self) -> Dict:
        config = super()._load_config()
        config["task_type"] = "chat"
        if "args" not in config:
            config["args"] = ["input"] # set `input` as default arg_list 
        return config
    
    @property
    def config(self) -> Optional[ChatConfig]:
        args = self.arg_list.get_inputs()
        model = self.model_uploader.model
        return ChatConfig(
            args=args,
            model=model,
            config=self._config
        )

class ChatInputObserver(OnserverBase):
    _targets = [RUN_MODEL_REQUEST]
    
    def __init__(self, chat_task: "ChatTask") -> None:
        super().__init__()
        self.chat_task = chat_task
    
    def _process(self, request: Request):
        self.chat_task.run(request["value"])

class ChatTask(Task):
    task_type: str = "chat-task"
    
    def __init__(self, project_id: str, task_id: str=None) -> None:
        super().__init__(project_id, task_id)
        
        self._chat_log =TraceConstantSavingLog(TraceLog(self.task_path+"/"+CHAT_LOG_FILE))
        
        self._config = ChatConfigPanel(task_path=self.task_path)
        self.chat_view  = ChatView([], trace_log=self._chat_log, observers=[ChatInputObserver(self)])
        self.table_view = TableView(trace_log=self._chat_log)
        
        self.running_config = {
            "callbacks": [
                TraceCollectorCallbackHandler(log=self._chat_log),
                UICallbackHandler(view=self.chat_view),
            ]
        }
    
    def draw(self) -> None:        
        config_tab, chat_tab, table_tab = st.tabs(["Config", "Chat", "Table"])
        with config_tab:
            self._config.draw()
        with chat_tab:
            if self.config.args:
                input_keys = self.config.args
                self.chat_view.set_input_fields(input_fields=input_keys)
            
            self.chat_view.draw()
        with table_tab:
            self.table_view.draw()
            if (df := self.table_view.selected) is not None:
                data_csv = df.to_csv(index=False).encode("utf-8")
                data_jsonl = df.to_json(orient='records', lines=True, force_ascii=False)
            else:
                data_csv = data_jsonl = ""
            
            st.download_button(
                label="Download as CSV",
                data=data_csv,
                file_name=f"{self.config.config['name']}.csv",
                mime="text/csv",
            )
            st.download_button(
                label="Download as JSONL",
                data=data_jsonl,
                file_name=f"{self.config.config['name']}.jsonl",
                mime="application/json",
            )
    
    def run(self, input):
        if not self.config.model:
            return
        try:
            self.config.model.invoke(input, config=self.running_config)
        except:
            # show error in callback
            pass
    
    @property
    def config(self):
        return self._config.config