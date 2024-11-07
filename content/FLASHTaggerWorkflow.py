import streamlit as st
from src.common.common import page_setup, v_space, reset_directory
from src.Workflow import TagWorkflow
from pathlib import Path
import shutil
import numpy as np
from src.parse.tnt import initializeWorkspace, handleInputFiles, parseUploadedFiles, getUploadedFileDF, remove_selected_mzML_files, input_file_types, tool, parsed_df_types


params = page_setup()

wf = TagWorkflow()

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

    st.title("File Upload")

    tabs = st.tabs(["File Upload", "Example Data"])

    # Load Example Data
    with tabs[1]:
        #st.markdown("An example truncated file from the E. coli dataset.")
        _, c2, _ = st.columns(3)
        if c2.button("Load Example Data", type="primary"):
            # loading and copying example files into default workspace
            for filetype, session_name in zip(['*annotated.mzML', '*deconv.mzML', '*tagged.tsv', '*protein.tsv'],
                                            ['anno-mzMLs', 'deconv-mzMLs', 'tags-tsv', 'proteins-tsv']):
                for file in Path("example-data", "flashtagger").glob(filetype):
                    if file.name not in st.session_state[session_name]:
                        shutil.copy(file, Path(st.session_state.workspace, tool, session_name, file.name))
                        st.session_state[session_name].append(file.name)
            # parsing the example files is done in parseUploadedFiles later
            st.success("Example mzML files loaded!")

    # Upload files via upload widget
    with tabs[0]:
        st.subheader("**Upload FLASHDeconv & FLASHTagger output files (\*_annotated.mzML, \*_deconv.mzML, \*_tagged.tsv & \*_protein.tsv)**")
        # Display info how to upload files
        st.info(
            """
        **💡 How to upload files**
        
        1. Browse files on your computer or drag and drops files
        2. Click the **Add files to workspace** button to use them in the viewer
        
        Select data for analysis from the uploaded files shown below.
        
        **💡 Make sure that the same number of deconvolved and annotated mzML and FLASHTagger output files files are uploaded!**
        """
        )
        with st.form('input_mzml', clear_on_submit=True):
            uploaded_file = st.file_uploader(
                "FLASHDeconv & FLASHTagger output files", accept_multiple_files=True
            )
            _, c2, _ = st.columns(3)
            # User needs to click button to upload selected files
            if c2.form_submit_button("Add files to workspace", type="primary"):

                if 'selected_experiment0_tagger' in st.session_state:
                    del(st.session_state['selected_experiment0_tagger'])
                if "saved_layout_setting_tagger" in st.session_state and len(st.session_state["saved_layout_setting_tagger"]) > 1:
                    for exp_index in range(1, len(st.session_state["saved_layout_setting_tagger"])):
                        if f"selected_experiment{exp_index}_tagger" in st.session_state:
                            del(st.session_state[f"selected_experiment{exp_index}_tagger"])

                # Copy uploaded mzML files to deconv-mzML-files directory
                if uploaded_file:
                    # A list of files is required, since online allows only single upload, create a list
                    if type(uploaded_file) != list:
                        uploaded_file = [uploaded_file]

                    # opening file dialog and closing without choosing a file results in None upload
                    handleInputFiles(uploaded_file)
                    st.success("Successfully added uploaded files!")
                else:
                    st.warning("Upload some files before adding them.")

    # parse files if newly uploaded
    st.session_state['progress_bar_space'] = st.container()
    parseUploadedFiles()

    # for error message or list of uploaded files
    deconv_files = sorted(st.session_state["deconv_dfs_tagger"].keys())
    anno_files = sorted(st.session_state["anno_dfs_tagger"].keys())
    tag_files = sorted(st.session_state["tag_dfs_tagger"].keys())
    db_files = sorted(st.session_state["protein_dfs_tagger"].keys())

    # error message if files not exist
    if len(deconv_files) == 0 and len(anno_files) == 0:
        st.info('No mzML added yet!', icon="ℹ️")
    elif len(deconv_files) == 0:
        st.error("FLASHDeconv deconvolved mzML file is not added yet!")
    elif len(anno_files) == 0:
        st.error("FLASHDeconv annotated mzML file is not added yet!")
    elif len(tag_files) == 0:
        st.error("FLASHTagger tag tsv file is not added yet!")
    elif len(db_files) == 0:
        st.error("FLASHTagger protein tsv file is not added yet!")
    elif not np.all(np.array([len(deconv_files), len(tag_files), len(db_files)]) == len(anno_files)):
        st.error("The same number of each file type should be uploaded!")
    else:
        v_space(2)
        st.session_state["experiment-df-tagger"] = getUploadedFileDF(deconv_files, anno_files, tag_files, db_files)
        st.markdown('**Uploaded experiments in current workspace**')
        st.dataframe(st.session_state["experiment-df-tagger"])  # show table
        v_space(1)

        # Remove files
        with st.expander("🗑️ Remove experiments"):
            to_remove = st.multiselect(
                "select experiments", options=st.session_state["experiment-df-tagger"]['Experiment Name']
            )
            c1, c2 = st.columns(2)
            if c2.button(
                    "Remove **selected**", type="primary", disabled=not any(to_remove)
            ):
                params = remove_selected_mzML_files(to_remove, params)
                # save_params(params)
                st.rerun()

            if c1.button("⚠️ Remove **all**", disabled=not any(st.session_state["experiment-df-tagger"])):
                for file_option, df_option in zip(input_file_types, parsed_df_types):
                    if file_option in st.session_state:
                        reset_directory(Path(st.session_state.workspace, tool, file_option))
                        st.session_state[file_option] = []
                    if df_option in st.session_state:
                        st.session_state[df_option] = {}

                        # for k, v in params.items():
                        #     if df_option in k and isinstance(v, list):
                        #         params[k] = []
                st.success("All mzML files removed!")
                del st.session_state["experiment-df-tagger"]  # reset the experiment df table
                # save_params(params)
                st.rerun()
