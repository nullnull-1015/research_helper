import streamlit as st
import os
import json
from uuid import uuid4
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, List, Dict, Optional

from research_helper.ui.base import Drawable
from research_helper.ui.components import ComponentBase

CONFIG_FILE = "config.json"

class TaskConfigComponent(ComponentBase):
    def __init__(self, task_path: str) -> None:
        super().__init__()
        self.task_path = task_path
        
        self._auto_save = True
        self._config = self._load_config()
        self._cache  = {}
    
    def draw(self) -> Any:
        st.header(self._config["name"])
        st.text_input(
            "Task Name",
            value=self._config["name"],
            key="task-namer",
            on_change=lambda: self._update_config("name", st.session_state["task-namer"])
        )
        st.text_area(
            "Discription",
            value=self._config["discription"],
            key="task-discriptor",
            on_change=lambda: self._update_config("discription", st.session_state["task-discriptor"])
        )
        
        self.draw_body()
        
        if self._auto_save:
            self._save_config()

    def _update_config(self, key: str, val: Any):
        self._config[key] = val
    
    @abstractmethod
    def draw_body(self):
        pass
    
    def _save_config(self):
        if self._config == self._cache: return
        
        self._cache = self._config.copy()
        with open(self.task_path+"/"+CONFIG_FILE, "w", encoding="utf-8") as fw:
            json.dump(self._cache, fw)
    
    def _load_config(self) -> Dict:
        default_config = {
            "name": self.task_id,
            "discription": "",
            "task_id": self.task_id
        }
        try:
            with open(self.task_path+"/"+CONFIG_FILE, "r", encoding="utf-8") as fr:
                default_config.update(json.load(fr))
        except:
            """ if failed to load, don't update default_config """
        finally:
            return default_config
    
    @property
    def task_id(self):
        return os.path.basename(self.task_path)

class Task(Drawable):
    task_type: str = "task"
    
    def __init__(self, project_id: str, task_id: Optional[str] = None) -> None:
        super().__init__()
        
        self.project_id = project_id
        if task_id is None:
            task_id = f"{self.task_type}_{uuid4()}"
        self.task_id = task_id
        
        self.task_path = f"projects/{project_id}/{self.task_id}"
        if not os.path.isdir(self.task_path):
            os.makedirs(self.task_path)
