import streamlit as st
from pathlib import Path
# For some reason the windows version only works if this is imported here
import pyopenms

if __name__ == '__main__':
    pages = {
        "FLASHApp" : [
            st.Page(Path("content", "quickstart.py"), title="Quickstart", icon="👋")
        ],
        "⚡️ FLASHDeconv" : [
            st.Page(Path("content", "FLASHDeconv", "FLASHDeconvWorkflow.py"), title="Workflow", icon="⚙️"),
            st.Page(Path("content", "FLASHDeconv", "FLASHDeconvSequenceInput.py"), title="Sequence Input", icon="🧵"),
            st.Page(Path("content", "FLASHDeconv", "FLASHDeconvLayoutManager.py"), title="Layout Manager", icon="📝️"),
            st.Page(Path("content", "FLASHDeconv", "FLASHDeconvViewer.py"), title="Viewer", icon="👀"),
            st.Page(Path("content", "FLASHDeconv", "FLASHDeconvDownload.py"), title="Download", icon="⬇️"),
        ],
        "🧨 FLASHTnT": [
            st.Page(Path("content", "FLASHTnT", "FLASHTnTWorkflow.py"), title="Workflow", icon="⚙️"),
            st.Page(Path("content", "FLASHTnT", "FLASHTnTLayoutManager.py"), title="Layout Manager", icon="📝️"),
            st.Page(Path("content", "FLASHTnT", "FLASHTnTViewer.py"), title="Viewer", icon="👀"),
            st.Page(Path("content", "FLASHTnT", "FLASHTnTDownload.py"), title="Download", icon="⬇️"),
        ],
        "📊 FLASHQuant" : [
            st.Page(Path("content", "FLASHQuant", "FLASHQuantFileUpload.py"), title="File Upload", icon="📂"),
            st.Page(Path("content", "FLASHQuant", "FLASHQuantViewer.py"), title="Viewer", icon="👀"),
        ],
    }

    pg = st.navigation(pages, expanded=True)
    pg.run()