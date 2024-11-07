import streamlit as st
from pathlib import Path

if __name__ == '__main__':
    pages = {
        "FLASHApp" : [
            st.Page(Path("content", "quickstart.py"), title="Quickstart", icon="👋")
        ],
        "⚡️ FLASHDeconv" : [
            st.Page(Path("content", "FLASHDeconvWorkflow.py"), title="Workflow", icon="⚙️"),
            st.Page(Path("content", "SequenceInput.py"), title="Sequence Input", icon="🧵"),
            st.Page(Path("content", "LayoutManager.py"), title="Layout Manager", icon="📝️"),
            st.Page(Path("content", "FLASHDeconvViewer.py"), title="Viewer", icon="👀"),
            st.Page(Path("content", "FLASHDeconvDownload.py"), title="Download", icon="⬇️"),
            st.Page(Path("content", "FLASHFDR.py"), title="ECDF Plot", icon="📈"),
        ],
        "🧨 FLASHTnT": [
            st.Page(Path("content", "FLASHTaggerWorkflow.py"), title="Workflow", icon="⚙️"),
            st.Page(Path("content", "LayoutManagerTagger.py"), title="Layout Manager", icon="📝️"),
            st.Page(Path("content", "FLASHTaggerViewer.py"), title="Viewer", icon="👀"),
            st.Page(Path("content", "FLASHTaggerDownload.py"), title="Download", icon="⬇️"),
        ],
        "📊 FLASHQuant" : [
            st.Page(Path("content", "FileUpload_FLASHQuant.py"), title="File Upload", icon="📂"),
            st.Page(Path("content", "FLASHQuantViewer.py"), title="Viewer", icon="👀"),
        ],
    }

    pg = st.navigation(pages, expanded=True)
    pg.run()