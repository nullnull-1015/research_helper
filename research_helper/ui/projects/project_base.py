import os
import json
import streamlit as st
from typing import Optional, Any, Dict, List
from uuid import UUID, uuid4

from research_helper.ui.base import Drawable
from research_helper.ui.components import ComponentBase
from research_helper.ui.projects.task_base import Task
from research_helper.ui.projects.task_manager import TaskManager

PROJECT_BASE_PATH = "projects"
CONFIG_FILE = "config.json"

class Project(Drawable):
    def __init__(self, project_id: Optional[str] = None) -> None:
        super().__init__()
        
        if project_id is None:
            project_id = f"project_{uuid4()}"
        self.project_id = project_id
        
        self.project_path = f"{PROJECT_BASE_PATH}/{self.project_id}"
        if not os.path.isdir(self.project_path):
            os.makedirs(self.project_path)
        
        self._task_manager = TaskManager(self.project_path)
        self._task: Task = None
        
        self._config = self._load_config()
    
    def _load_config(self):
        default_config = {
            "name": self.project_id,
            "project_id": self.project_id
        }
        try:
            with open(self.project_path+"/"+CONFIG_FILE, "r", encoding="utf-8") as fr:
                default_config.update(json.load(fr))
        except:
            """ if failed to load, don't update default_config """
        finally:
            return default_config
    
    def _save_config(self):
        with open(self.project_path+"/"+CONFIG_FILE, "w", encoding="utf-8") as fw:
            json.dump(self._config, fw)
    
    def open(self):
        self._task = None
    
    def draw(self) -> None:        
        if self._task:
            _, right_col = st.columns([12, 1])
            with right_col:
                st.button(":material/home:", key="home-button", on_click=self.open)
            self._task.draw()
            return
        
        self.draw_body()
        
        self._task_manager.reload()
        self._save_config()
    
    def draw_body(self):
        st.header(self._config["name"])
        st.text_input(
            "Project Name",
            value=self._config["name"],
            key="project-namer",
            on_change=lambda: self._update_config("name", st.session_state["project-namer"])
        )
        
        left_col, right_col = st.columns(2)
        with left_col:
            st.button("Start New Chat", key="chat-creater", on_click=lambda: self.create_task("chat"))
            st.button("Start New Eval", key="eval-creater", on_click=lambda: self.create_task("eval"))
        
        with right_col:
            st.selectbox(
                label="Select a Task", options=range(len(self._task_manager._task_configs)),
                index=None,
                format_func=lambda idx: self._task_manager._task_configs[idx].task_name,
                key="task-selector",
                on_change=lambda: self.set_task(self._task_manager._task_configs[st.session_state["task-selector"]].task_id)
            )
    
    
    def _update_config(self, key: str, val: Any):
        self._config[key] = val
    
    def set_task(self, task_id: str):
        self._task = self._task_manager.open(task_id=task_id)
    
    def create_task(self, task_type: str):
        self._task = self._task_manager.create_task(task_type=task_type)
    
