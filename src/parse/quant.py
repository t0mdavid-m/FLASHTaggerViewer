import streamlit as st
from pathlib import Path
import os
import pandas as pd
from src.flashquant import parseFLASHQuantOutput
from src.flashquant import connectTraceWithResult


@st.cache_data
def getUploadedFileDF(quant_files, trace_files, resolution_files):
    # leave only names
    quant_files = [Path(f).name for f in quant_files]
    trace_files = [Path(f).name for f in trace_files]
    resolution_files = [Path(f).name for f in resolution_files]

    # getting experiment name from annotated file (tsv files can be multiple per experiment)
    experiment_names = [f[0: f.rfind('.fq')] for f in quant_files]

    df = pd.DataFrame({'Experiment Name': experiment_names,
                       'Quant result Files': quant_files,
                       'Mass trace Files': trace_files})
    if resolution_files:
        df['Conflict resolution Files'] = resolution_files

    return df


def remove_selected_experiment_files(to_remove: list[str], params: dict) -> dict:
    """
    Removes selected mzML files from the mzML directory. (From fileUpload.py)

    Args:
        to_remove (List[str]): List of mzML files to remove.
        params (dict): Parameters.

    Returns:
        dict: parameters with updated mzML files
    """
    for input_type, df_type, file_postfix in zip(input_file_types, parsed_df_types,
                                                 ['.fq.tsv', '.fq.mts.tsv', '.fq_shared.tsv']):
        input_type_dir = Path(st.session_state["workspace"], input_type)
        # remove all given files from mzML workspace directory and selected files
        for exp_name in to_remove:
            file_name = exp_name + file_postfix
            Path(input_type_dir, file_name).unlink()
            del st.session_state[df_type][file_name]  # removing key

    # update the experiment df table
    tmp_df = st.session_state["quant-experiment-df"]
    tmp_df.drop(tmp_df.loc[tmp_df['Experiment Name'].isin(to_remove)].index, inplace=True)
    st.session_state["quant-experiment-df"] = tmp_df

    st.success("Selected experiment files removed!")
    return params


def handleInputFiles(uploaded_files):
    for file in uploaded_files:
        if not file.name.endswith("tsv"):
            continue

        session_name = ''
        if file.name.endswith('fq.tsv'):
            session_name = 'quant-files'
        elif file.name.endswith('fq.mts.tsv'):
            session_name = 'trace-files'
        elif file.name.endswith('fq_shared.tsv'):
            session_name = 'conflict-resolution-files'

        if file.name not in st.session_state[session_name]:
            with open(
                    Path(st.session_state["workspace"], session_name, file.name), "wb"
            ) as f:
                f.write(file.getbuffer())
            st.session_state[session_name].append(file.name)


def parseUploadedFiles():
    # get newly uploaded files
    quant_files = st.session_state['quant-files']
    trace_files = st.session_state['trace-files']
    resolution_files = st.session_state['conflict-resolution-files']

    new_quant_files = [f for f in quant_files if f not in st.session_state['quant_dfs']]
    new_trace_files = [f for f in trace_files if f not in st.session_state['trace_dfs']]
    new_resolution_files = [f for f in resolution_files if f not in st.session_state['conflict_resolution_dfs']]

    # if newly uploaded files are not as needed
    if len(new_quant_files) == 0 and len(new_trace_files) == 0:  # if no newly uploaded files, move on
        return
    elif len(new_quant_files) != len(new_trace_files):  # if newly uploaded files doesn't match, write message
        st.error('Added files are not in pair, so not parsed. \n Here are uploaded ones, but not parsed ones:')
        not_parsed = new_quant_files + new_trace_files
        for i in not_parsed:
            st.markdown("- " + i)
        return
    elif (len(new_resolution_files) > 0) & (len(new_quant_files) != len(new_resolution_files)):
        st.error('Added files (including conflict resolution) are not in pair, so not parsed. \n Here are uploaded ones, but not parsed ones:')
        not_parsed = new_quant_files + new_trace_files + new_resolution_files
        for i in not_parsed:
            st.markdown("- " + i)
        return

    # parse newly uploaded files
    new_deconv_files = sorted(new_quant_files)
    new_anno_files = sorted(new_trace_files)
    if new_resolution_files:
        new_resolution_files = sorted(new_resolution_files)
    parsingWithProgressBar(new_deconv_files, new_anno_files, new_resolution_files)


def parsingWithProgressBar(infiles_quant, infiles_trace, infiles_resolution):
    with st.session_state['progress_bar_space']:
        if not infiles_resolution:
            infiles_resolution = [''] * len(infiles_quant)
        for quant_f, trace_f, resolution_f in zip(infiles_quant, infiles_trace, infiles_resolution):
            if not quant_f.endswith('.tsv'):
                continue
            exp_name = quant_f[0: quant_f.rfind('.fq')]

            with st.spinner('Parsing the experiment %s...' % exp_name):
                if resolution_f:
                    quant_df, trace_df, resolution_df = parseFLASHQuantOutput(
                        Path(st.session_state["workspace"], tool, "quant-files", quant_f),
                        Path(st.session_state["workspace"], tool, "trace-files", trace_f),
                        Path(st.session_state["workspace"], tool, "conflict-resolution-files", resolution_f),
                    )
                    st.session_state['conflict_resolution_dfs'][resolution_f] = resolution_df
                else:
                    quant_df, trace_df, _ = parseFLASHQuantOutput(
                        Path(st.session_state["workspace"], "quant-files", quant_f),
                        Path(st.session_state["workspace"], "trace-files", trace_f),
                    )
                st.session_state['quant_dfs'][quant_f] = connectTraceWithResult(quant_df, trace_df)
                st.session_state['trace_dfs'][trace_f] = []  # need key name, so saving only empty array
            st.success('Done parsing the experiment: %s!' % exp_name)


def initializeWorkspace(input_file_types_: list, parsed_df_types_: list) -> None:
    """
    Set up the required directory and session states
    parameter is needed: this method is used in FLASHQuant
    """
    for dirname in input_file_types_:
        Path(st.session_state.workspace, tool, dirname).mkdir(parents=True, exist_ok=True)
        if dirname not in st.session_state:
            # initialization
            st.session_state[dirname] = []
        # sync session state and default-workspace
        st.session_state[dirname] = os.listdir(Path(st.session_state.workspace, tool, dirname))

    # initializing session state for storing data
    for df_type in parsed_df_types_:
        if df_type not in st.session_state:
            st.session_state[df_type] = {}
