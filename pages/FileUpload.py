import shutil
from pathlib import Path
import pandas as pd
import streamlit as st
import os
from src.masstable import parseFLASHDeconvOutput
from src.common import page_setup, v_space, save_params, reset_directory

# Define input and parsed file types for both mzML and TSV files
input_file_types = ["deconv-mzMLs", "anno-mzMLs", "tsv-files"]
parsed_df_types = ["deconv_dfs", "anno_dfs", "parsed_tsv_files"]

def initializeWorkspace(input_file_types_: list, parsed_df_types_: list) -> None:
    """
    Set up the required directory and session states.
    """
    if 'workspace' not in st.session_state:
        st.error("Workspace is not set in the session state.")
        return

    for dirname in input_file_types_:
        Path(st.session_state.workspace, dirname).mkdir(parents=True, exist_ok=True)
        if dirname not in st.session_state:
            st.session_state[dirname] = []
        st.session_state[dirname] = os.listdir(Path(st.session_state.workspace, dirname))

    for df_type in parsed_df_types_:
        if df_type not in st.session_state:
            st.session_state[df_type] = {}

@st.cache_data
def getUploadedFileDF(deconv_files_, anno_files_, tsv_files_):
    deconv_files_ = [Path(f).name for f in deconv_files_]
    anno_files_ = [Path(f).name for f in anno_files_]
    tsv_files_ = [Path(f).name for f in tsv_files_]

    experiment_names = [f[0: f.rfind('_')] for f in anno_files_]

    df = pd.DataFrame({'Experiment Name': experiment_names,
                       'Deconvolved Files': deconv_files_,
                       'Annotated Files': anno_files_,
                       'TSV Files': tsv_files_})
    return df

def remove_selected_files(to_remove: list[str], params: dict) -> dict:
    for input_type, df_type, file_postfix in zip(input_file_types, parsed_df_types,
                                                 ['_deconv.mzML', '_annotated.mzML', '.tsv']):
        file_dir = Path(st.session_state["workspace"], input_type)
        for exp_name in to_remove:
            file_name = exp_name + file_postfix
            Path(file_dir, file_name).unlink()
            del st.session_state[df_type][file_name]

    tmp_df = st.session_state["experiment-df"]
    tmp_df.drop(tmp_df.loc[tmp_df['Experiment Name'].isin(to_remove)].index, inplace=True)
    st.session_state["experiment-df"] = tmp_df

    st.success("Selected files removed!")
    return params

def handleInputFiles(uploaded_files):
    for file in uploaded_files:
        if file.name.endswith("mzML"):
            session_name = 'deconv-mzMLs' if file.name.endswith('_deconv.mzML') else 'anno-mzMLs'
        elif file.name.endswith("tsv"):
            session_name = 'tsv-files'
        else:
            continue

        if file.name not in st.session_state[session_name]:
            with open(Path(st.session_state.workspace, session_name, file.name), "wb") as f:
                f.write(file.getbuffer())
            st.session_state[session_name].append(file.name)

def parseUploadedFiles():
    deconv_files = st.session_state['deconv-mzMLs']
    anno_files = st.session_state['anno-mzMLs']
    tsv_files = st.session_state['tsv-files']
    new_deconv_files = [f for f in deconv_files if f not in st.session_state['deconv_dfs']]
    new_anno_files = [f for f in anno_files if f not in st.session_state['anno_dfs']]
    new_tsv_files = [f for f in tsv_files if f not in st.session_state['parsed_tsv_files']]

    if len(new_deconv_files) == 0 and len(new_anno_files) == 0 and len(new_tsv_files) == 0:
        return
    elif len(new_deconv_files) != len(new_anno_files):
        st.error('Added files are not in pair, so not parsed. \n Here are uploaded ones, but not parsed ones:')
        not_parsed = new_deconv_files + new_anno_files
        for i in not_parsed:
            st.markdown("- " + i)
        return

    new_deconv_files = sorted(new_deconv_files)
    new_anno_files = sorted(new_anno_files)

    with st.session_state['progress_bar_space']:
        for anno_f, deconv_f in zip(new_anno_files, new_deconv_files):
            if not anno_f.endswith('.mzML'):
                continue
            exp_name = anno_f[0: anno_f.rfind('_')]

            with st.spinner('Parsing the experiment %s...' % exp_name):
                spec_df, anno_df, tolerance, massoffset, chargemass = parseFLASHDeconvOutput(
                    Path(st.session_state["workspace"], "anno-mzMLs", anno_f),
                    Path(st.session_state["workspace"], "deconv-mzMLs", deconv_f)
                )
                st.session_state['anno_dfs'][anno_f] = anno_df
                st.session_state['deconv_dfs'][deconv_f] = spec_df
            st.success('Done parsing the experiment %s!' % exp_name)

    for tsv_file in new_tsv_files:
        df = pd.read_csv(Path(st.session_state.workspace, "tsv-files", tsv_file), sep='\t')
        st.session_state['parsed_tsv_files'][tsv_file] = df

def showUploadedFilesTable() -> bool:
    deconv_files = sorted(st.session_state["deconv_dfs"].keys())
    anno_files = sorted(st.session_state["anno_dfs"].keys())
    tsv_files = sorted(st.session_state["parsed_tsv_files"].keys())

    if len(deconv_files) == 0 and len(anno_files) == 0 and len(tsv_files) == 0:
        st.info('No files added yet!', icon="ℹ️")
    elif len(deconv_files) == 0:
        st.error("FLASHDeconv deconvolved mzML file is not added yet!")
    elif len(anno_files) == 0:
        st.error("FLASHDeconv annotated mzML file is not added yet!")
    elif len(deconv_files) != len(anno_files):
        st.error("The same number of deconvolved and annotated mzML file should be uploaded!")
    else:
        v_space(2)
        st.session_state["experiment-df"] = getUploadedFileDF(deconv_files, anno_files, tsv_files)
        st.markdown('**Uploaded experiments in current workspace**')
        st.dataframe(st.session_state["experiment-df"])  # show table
        v_space(1)
        return True
    return False

def load_example_data():
    example_files = {
        'deconv-mzMLs': ['example_deconv.mzML'],
        'anno-mzMLs': ['example_annotated.mzML'],
        'tsv-files': ['FDR_deconv.tsv']
    }
    for session_key, files in example_files.items():
        for example_file in files:
            source_path = Path("example-data", 'flashdeconv', example_file)
            dest_path = Path(st.session_state.workspace, session_key, example_file)
            if not dest_path.exists():
                shutil.copy(source_path, dest_path)
                st.session_state[session_key].append(example_file)

# for Workflow
def postprocessingAfterUpload_FD(uploaded_files: list) -> None:
    initializeWorkspace(input_file_types, parsed_df_types)
    parseUploadedFiles()
    showUploadedFilesTable()

if __name__ == '__main__':
    # page initialization
    params = page_setup()

    if 'workspace' not in st.session_state:
        st.session_state['workspace'] = 'default_workspace'  # Initialize workspace

    initializeWorkspace(input_file_types, parsed_df_types)

    st.title("FLASHDeconv output files Upload")

    tabs = st.tabs(["File Upload", "Example Data"])

    with tabs[1]:
        st.markdown("An example truncated file from the ThermoFisher Pierce Intact Protein Standard Mix dataset.")
        _, c2, _ = st.columns(3)
        if c2.button("Load Example Data", type="primary"):
            # loading and copying example files into default workspace
            for filename_postfix, input_file_session_name in zip(['*deconv.mzML', '*annotated.mzML', '*.tsv'],
                                                                input_file_types):
                for file in Path("example-data/flashdeconv").glob(filename_postfix):
                    if file.name not in st.session_state[input_file_session_name]:
                        shutil.copy(file, Path(st.session_state["workspace"], input_file_session_name, file.name))
                        st.session_state[input_file_session_name].append(file.name)
            # parsing the example files is done in parseUploadedFiles later
            st.success("Example mzML files loaded!")

    with tabs[0]:
        st.subheader("**Upload FLASHDeconv output files (\*_annotated.mzML & \*_deconv.mzML) or TSV files**")
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
            uploaded_files = st.file_uploader(
                "FLASHDeconv output mzML files or TSV files", accept_multiple_files=True, type=["mzML", "tsv"]
            )
            _, c2, _ = st.columns(3)
            if c2.form_submit_button("Add files to workspace", type="primary"):
                if uploaded_files:
                    handleInputFiles(uploaded_files)
                    st.success("Successfully added uploaded files!")
                else:
                    st.warning("Upload some files before adding them.")

    st.session_state['progress_bar_space'] = st.container()
    parseUploadedFiles()

    if showUploadedFilesTable():
        with st.expander("🗑️ Remove files"):
            to_remove = st.multiselect(
                "select files", options=st.session_state["experiment-df"]['Experiment Name']
            )
            c1, c2 = st.columns(2)
            if c2.button(
                    "Remove **selected**", type="primary", disabled=not any(to_remove)
            ):
                params = remove_selected_files(to_remove, params)
                st.rerun()

            if c1.button("⚠️ Remove **all**", disabled=not any(st.session_state["experiment-df"])):
                for file_option, df_option in zip(input_file_types, parsed_df_types):
                    if file_option in st.session_state:
                        reset_directory(Path(st.session_state.workspace, file_option))
                        st.session_state[file_option] = []
                    if df_option in st.session_state:
                        st.session_state[df_option] = {}
                st.success("All files removed!")
                del st.session_state["experiment-df"]
                st.rerun()

    save_params(params)


