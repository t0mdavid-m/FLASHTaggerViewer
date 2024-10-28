import streamlit as st
from src.common.common import page_setup
from src.Workflow import DeconvWorkflow


# The rest of the page can, but does not have to be changed
    
params = page_setup()

#wf = Workflow()
wf = DeconvWorkflow()

st.title(wf.name)

t = st.tabs(["📁 **File Upload**", "⚙️ **Configure**", "🚀 **Run**"])
with t[0]:
    wf.show_file_upload_section()

with t[1]:
    wf.show_parameter_section()

with t[2]:
    wf.show_execution_section()
