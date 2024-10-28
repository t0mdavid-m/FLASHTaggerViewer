import streamlit as st
from src.common.common import page_setup
from src.Workflow import TagWorkflow


params = page_setup()

wf = TagWorkflow()

st.title(wf.name)

t = st.tabs(["📁 **File Upload**", "⚙️ **Configure**", "🚀 **Run**"])
with t[0]:
    wf.show_file_upload_section()

with t[1]:
    wf.show_parameter_section()

with t[2]:
    wf.show_execution_section()
