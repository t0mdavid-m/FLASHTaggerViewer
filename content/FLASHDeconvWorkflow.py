import streamlit as st
from src.common.common import page_setup
from src.Workflow import DeconvWorkflow

from pathlib import Path
import shutil

from src.common.common import page_setup, reset_directory
from src.parse.deconv import initializeWorkspace, handleInputFiles, parseUploadedFiles, showUploadedFilesTable, remove_selected_mzML_files, input_file_types, parsed_df_types, tool

    
params = page_setup()

wf = DeconvWorkflow()

st.title(wf.name)

t = st.tabs(["📁 **File Upload**", "⚙️ **Configure**", "🚀 **Run**", "💡 **Manual Result Upload**"])
with t[0]:
    wf.show_file_upload_section()

with t[1]:
    wf.show_parameter_section()

with t[2]:
    wf.show_execution_section()
with t[3]:

    # make directory to store deconv and anno mzML files & initialize data storage
    initializeWorkspace(input_file_types, parsed_df_types)

    tabs = st.tabs(["File Upload", "Example Data"])

    # Load Example Data
    with tabs[1]:
        st.markdown("An example truncated file from the ThermoFisher Pierce Intact Protein Standard Mix dataset.")
        _, c2, _ = st.columns(3)
        if c2.button("Load Example Data", type="primary"):
            # loading and copying example files into default workspace
            for filename_postfix, input_file_session_name in zip(['*deconv.mzML', '*annotated.mzML', '*.tsv'],
                                                                input_file_types):
                for file in Path("example-data/flashdeconv").glob(filename_postfix):
                    if file.name not in st.session_state[input_file_session_name]:
                        shutil.copy(file, Path(st.session_state.workspace, tool, input_file_session_name, file.name))
                        st.session_state[input_file_session_name].append(file.name)
            # parsing the example files is done in parseUploadedFiles later
            st.success("Example mzML files loaded!")

    with tabs[0]:
        st.subheader("**Upload FLASHDeconv output files (\*_annotated.mzML & \*_deconv.mzML) or TSV files (ECDF Plot only)**")
        st.info(
            """
            **💡 How to upload files**

            1. Browse files on your computer or drag and drops files
            2. Click the **Add the uploaded files** button to use them in the workflows

            Select data for analysis from the uploaded files shown below.

            **💡 Make sure that the same number of deconvolved and annotated mzML files are uploaded!**
            """
        )
        with st.form('input_files', clear_on_submit=True):
            uploaded_file = st.file_uploader(
                "FLASHDeconv output mzML files or TSV files", accept_multiple_files=True, type=["mzML", "tsv"]
            )
            _, c2, _ = st.columns(3)
            if c2.form_submit_button("Add files to workspace", type="primary"):
                # Copy uploaded mzML files to deconv-mzML-files directory
                if 'selected_experiment0' in st.session_state:
                    del(st.session_state['selected_experiment0'])
                if "saved_layout_setting" in st.session_state and len(st.session_state["saved_layout_setting"]) > 1:
                    for exp_index in range(1, len(st.session_state["saved_layout_setting"])):
                        if f"selected_experiment{exp_index}" in st.session_state:
                            del(st.session_state[f"selected_experiment{exp_index}"])


                if uploaded_file:
                    # A list of files is required, since online allows only single upload, create a list
                    if type(uploaded_file) != list:
                        uploaded_file = [uploaded_file]

                    # opening file dialog and closing without choosing a file results in None upload
                    handleInputFiles(uploaded_file)
                    st.success("Successfully added uploaded files!")
                else:
                    st.warning("Upload some files before adding them.")

    st.session_state['progress_bar_space'] = st.container()
    parseUploadedFiles()

    if showUploadedFilesTable():
        # Remove files
        with st.expander("🗑️ Remove mzML files"):
            to_remove = st.multiselect(
                "select files", options=st.session_state["experiment-df"]['Experiment Name']
            )
            c1, c2 = st.columns(2)
            if c2.button(
                    "Remove **selected**", type="primary", disabled=not any(to_remove)
            ):
                params = remove_selected_mzML_files(to_remove, params)
                st.rerun()

            if c1.button("⚠️ Remove **all**", disabled=not any(st.session_state["experiment-df"])):
                for file_option, df_option in zip(input_file_types, parsed_df_types):
                    if file_option in st.session_state:
                        reset_directory(Path(st.session_state.workspace, tool, file_option))
                        st.session_state[file_option] = []
                    if df_option in st.session_state:
                        st.session_state[df_option] = {}
                st.success("All files removed!")
                del st.session_state["experiment-df"]  # reset the experiment df table
                st.rerun()
