import streamlit as st
from pathlib import Path
import shutil
from src.common.common import v_space, page_setup, reset_directory, save_params
from src.parse.quant import initializeWorkspace, handleInputFiles, parseUploadedFiles, getUploadedFileDF, remove_selected_experiment_files, tool, input_file_types, parsed_df_types

# page initialization
params = page_setup()

# make directory to store files & initialize data storage
initializeWorkspace(input_file_types, parsed_df_types)

st.title("File Upload")

tabs = st.tabs(["File Upload", "Example Data"])

# Load Example Data
with tabs[1]:
    st.markdown("An example truncated file from the E. coli & ThermoFisher Pierce Intact Protein Standard Mix dataset.")
    _, c2, _ = st.columns(3)
    if c2.button("Load Example Data", type="primary"):
        # loading and copying example files into default workspace
        for filetype, session_name in zip(['*fq.tsv', '*fq.mts.tsv', '*fq_shared.tsv'],
                                          input_file_types):
            for file in Path("example-data/flashquant").glob(filetype):
                if file.name not in st.session_state[session_name]:
                    shutil.copy(file, Path(st.session_state["workspace"], tool, session_name, file.name))
                    st.session_state[session_name].append(file.name)
        # parsing the example files is done in parseUploadedFiles later
        st.success("Example mzML files loaded!")

# Upload files via upload widget
with tabs[0]:
    # Upload files via upload widget
    st.subheader("**Upload FLASHQuant output files**")

    # Display info how to upload files
    st.info(
        """
    **💡 How to upload files**
    
    1. Browse files on your computer or drag and drops files
    2. Click the **Add the uploaded quant files** button to use them in the workflows
    
    Select data for analysis from the uploaded files shown below.
    
    **💡 Make sure that the same number of FLASHQuant result files (\*fq.tsv and \*fq.mts.tsv) are uploaded!**
    
    **💡 To visualize conflict resolution, \*fq_shared.tsv files should be uploaded**
    """
    )
    with st.form('files_uploader_form', clear_on_submit=True):
        uploaded_file = st.file_uploader(
            "FLASHQuant output files", accept_multiple_files=True
        )
        _, c2, _ = st.columns(3)
        # User needs to click button to upload selected files
        if c2.form_submit_button("Add the tsv files", type="primary"):
            # Copy uploaded files to *-files directory
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
quant_files = sorted(st.session_state["quant_dfs"].keys())
trace_files = sorted(st.session_state["trace_dfs"].keys())
res_files = sorted(st.session_state["conflict_resolution_dfs"].keys())

# error message if files not exist
if len(quant_files) == 0 and len(trace_files) == 0:
    st.info('No mzML added yet!', icon="ℹ️")
elif len(quant_files) == 0:
    st.error("FLASHQuant result file is not added yet!")
elif len(trace_files) == 0:
    st.error("FLASHQuant mass trace file is not added yet!")
elif len(quant_files) != len(trace_files):
    st.error("The same number of quant result and trace tsv file should be uploaded!")
else:
    v_space(2)
    st.session_state["quant-experiment-df"] = getUploadedFileDF(quant_files, trace_files, res_files)
    st.markdown('**Uploaded experiments in current workspace**')
    st.dataframe(st.session_state["quant-experiment-df"])  # show table
    v_space(1)

    # Remove files
    with st.expander("🗑️ Remove uploaded files"):
        to_remove = st.multiselect(
            "select uploaded experiments", options=st.session_state["quant-experiment-df"]['Experiment Name']
        )
        c1, c2 = st.columns(2)
        if c2.button(
                "Remove **selected**", type="primary", disabled=not any(to_remove)
        ):
            params = remove_selected_experiment_files(to_remove, params)
            st.rerun()

        if c1.button("⚠️ Remove **all**", disabled=not any(st.session_state["quant-experiment-df"])):
            for file_option, df_option in zip(input_file_types, parsed_df_types):
                if file_option in st.session_state:
                    reset_directory(Path(st.session_state.workspace, file_option))
                    st.session_state[file_option] = []
                if df_option in st.session_state:
                    st.session_state[df_option] = {}

            st.success("All experiment files removed!")
            del st.session_state["quant-experiment-df"]  # reset the experiment df table
            st.rerun()

save_params(params)
