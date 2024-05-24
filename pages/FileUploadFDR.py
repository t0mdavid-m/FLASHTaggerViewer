import shutil
from pathlib import Path

import pandas as pd
import streamlit as st


def initializeWorkspace():
    """
    Set up the required directory and session states.
    """
    Path(st.session_state.workspace, "tsv-files").mkdir(parents=True, exist_ok=True)
    if "tsv-files" not in st.session_state:
        st.session_state["tsv-files"] = []

def handleInputFiles(uploaded_files):
    for file in uploaded_files:
        file = Path(file)
        if not file.name.endswith(".tsv"):
            continue

        if file.name not in st.session_state["tsv-files"]:
            with open(Path(st.session_state.workspace, "tsv-files", file.name), "wb") as f:
                f.write(file.getbuffer())
            st.session_state["tsv-files"].append(file.name)

def parseUploadedFiles():
    tsv_files = st.session_state['tsv-files']
    new_tsv_files = [f for f in tsv_files if f not in st.session_state['parsed_tsv_files']]

    if len(new_tsv_files) == 0:
        return

    for tsv_file in new_tsv_files:
        df = pd.read_csv(Path(st.session_state.workspace, "tsv-files", tsv_file), sep='\t')
        st.session_state['parsed_tsv_files'][tsv_file] = df

def load_example_data():
    example_files = ['FDR_deconv.tsv']
    for example_file in example_files:
        source_path = Path("example-data", 'flashdeconv', example_file)
        dest_path = Path(st.session_state.workspace, "tsv-files", example_file)
        if not dest_path.exists():
            shutil.copy(source_path, dest_path)
            st.session_state["tsv-files"].append(example_file)

def content():
    initializeWorkspace()
    if 'parsed_tsv_files' not in st.session_state:
        st.session_state['parsed_tsv_files'] = {}

    st.title("Upload TSV Files for ECDF Plotting")

    tabs = st.tabs(["File Upload", "Example Data"])

    with tabs[0]:
        with st.form('input_tsv', clear_on_submit=True):
            uploaded_files = st.file_uploader("Upload TSV files", accept_multiple_files=True, type=["tsv"])
            if st.form_submit_button("Add TSV files to workspace"):
                if uploaded_files:
                    handleInputFiles(uploaded_files)
                    st.success("Successfully added uploaded files!")
                else:
                    st.warning("Upload some files before adding them.")

    with tabs[1]:
        st.markdown("An example TSV file.")
        _, c2, _ = st.columns(3)
        if c2.button("Load Example Data", type="primary"):
            load_example_data()
            st.success("Example TSV file loaded!")

    parseUploadedFiles()

    tsv_files = sorted(st.session_state["parsed_tsv_files"].keys())

    if len(tsv_files) == 0:
        st.info("No TSV files added yet!", icon="ℹ️")
    else:
        st.markdown("**Uploaded TSV files in current workspace**")
        for tsv_file in tsv_files:
            st.markdown(f"- {tsv_file}")

    if st.button("Go to ECDF Plot"):
        st.session_state['navigate_to_ecdf'] = True

if __name__ == "__main__":
    content()
