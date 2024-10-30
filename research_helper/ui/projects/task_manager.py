import streamlit as st
import os
import json
from uuid import uuid4
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, List, Dict, Optional

from research_helper.ui.projects.task_base import Task
from research_helper.ui.projects.chat_task import ChatTask
from research_helper.ui.projects.eval_task import EvalTask

CONFIG_FILE = "config.json"

@dataclass
class TaskConfig:
    task_id: str
    task_type: str
    task_name: str

class TaskManager:
    def __init__(self, project_path: str) -> None:
        self._project_path = project_path
        self._project_id = os.path.basename(self._project_path)
        self._task_configs = self._load_tasks()
    
    def _get_task_config(self, task_id: str) -> Optional[TaskConfig]:
        try:
            with open(self._project_path+"/"+task_id+"/"+CONFIG_FILE, "r", encoding="utf-8") as fr:
                config = json.load(fr)
            return TaskConfig(
                task_id=config["task_id"],
                task_type=config["task_type"],
                task_name=config["name"]
            )
        except Exception as e:
            return None
    
    def _load_tasks(self) -> List[TaskConfig]:
        task_ids = []
        for task_dir in os.listdir(self._project_path):
            if config:=self._get_task_config(task_dir):
                task_ids.append(config)
        return task_ids
    
    def get_task(self, task_id: str) -> Optional[TaskConfig]:
        try:
            idx = self.task_ids.index(task_id)
            return self._task_configs[idx]
        except:
            return None
    
    def open(self, task_id: str):
        task_config = self.get_task(task_id)
        if task_config.task_type == "chat":
            return ChatTask(project_id=self._project_id, task_id=task_id)
        elif task_config.task_type == "eval":
            return EvalTask(project_id=self._project_id, task_id=task_id)

    def create_task(self, task_type: str):
        if task_type == "chat":
            new_task = ChatTask(project_id=self._project_id)
            return new_task
        elif task_type == "eval":
            new_task = EvalTask(project_id=self._project_id)
            return new_task
    
    def reload(self):
        self._task_configs = self._load_tasks()
    
    @property
    def task_ids(self):
        return [task_config.task_id for task_config in self._task_configs]
    
    @property
    def task_names(self):
        return [task_config.task_name for task_config in self._task_configs]
