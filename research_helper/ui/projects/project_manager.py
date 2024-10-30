import streamlit as st
import os
import json
from dataclasses import dataclass
from typing import Any, List, Dict, Optional

from research_helper.ui.base import Drawable
from research_helper.ui.projects.project_base import Project

CONFIG_FILE = "config.json"

@dataclass
class ProjectConfig:
    project_id: str
    project_name: str


class ProjectManager(Drawable):
    def __init__(self, project_root: str = "./projects") -> None:
        self.project_root = project_root
        self._project_configs = self._load_projects()
        
        self._project = None
    
    def _get_project_config(self, project_id: str) -> Optional[ProjectConfig]:
        try:
            with open(self.project_root+"/"+project_id+"/"+CONFIG_FILE, "r", encoding="utf-8") as fr:
                config = json.load(fr)
            return ProjectConfig(
                project_id=config["project_id"],
                project_name=config["name"],
            )
        except Exception as e:
            return None
    
    def _load_projects(self) -> List[ProjectConfig]:
        project_configs = []
        for task_dir in os.listdir(self.project_root):
            if config:=self._get_project_config(task_dir):
                project_configs.append(config)
        return project_configs
    
    def get_project(self, project_id: str) -> Optional[ProjectConfig]:
        try:
            idx = self.project_ids.index(project_id)
            return self._project_configs[idx]
        except:
            return None
    
    def open(self, project_id: Optional[str]):
        if project_id is None:
            self._project = None
            return
        project_config = self.get_project(project_id)
        project = Project(project_id=project_config.project_id)
        self._project = project

    def create_project(self):
        self._project = Project()
    
    def reload(self):
        self._project_configs = self._load_projects()
    
    def go_home(self):
        self._project = None
    
    def draw(self):
        self.reload()
        
        with st.sidebar:
            st.button("Project Home", icon=":material/home:", key="project_home", on_click=self.go_home)
            st.button("Create New Project", key="project-creator", on_click=self.create_project)
            st.selectbox(
                label="Select a Project", options=range(len(self._project_configs)),
                index=None,
                format_func=lambda idx: self._project_configs[idx].project_name,
                key="project-selector",
                on_change=lambda:
                    self.open(self._project_configs[st.session_state["project-selector"]].project_id)
                    if st.session_state["project-selector"]
                    else self.go_home()
            )
            
        if self._project:
            self._project.draw()
            return
        
        st.header("Research Helper")
        
    
    
    @property
    def project_ids(self):
        return [project_config.project_id for project_config in self._project_configs]
    
    @property
    def project_names(self):
        return [project_config.project_name for project_config in self._project_configs]