import streamlit as st
from research_helper.ui.projects.project_manager import ProjectManager

project_manager = st.session_state.get("project-manager")
if project_manager is None:
    project_manager = ProjectManager()
    st.session_state["project-manager"] = project_manager

project_manager.draw()