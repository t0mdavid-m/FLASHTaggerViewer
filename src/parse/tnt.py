import streamlit as st
import pandas as pd
from pathlib import Path
import os
import numpy as np
from src.masstable import parseFLASHDeconvOutput, parseFLASHTaggerOutput


input_file_types = ["deconv-mzMLs", "anno-mzMLs", "tags-tsv", "proteins-tsv"]
parsed_df_types = ["deconv_dfs_tagger", "anno_dfs_tagger", "tag_dfs_tagger", "protein_dfs_tagger"]
tool = 'FLASHTaggerViewer'

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

#@st.cache_data
def getUploadedFileDF(deconv_files, anno_files, tag_files, db_files):
    # leave only names
    deconv_files = [Path(f).name for f in deconv_files]
    anno_files = [Path(f).name for f in anno_files]
    tag_files = [Path(f).name for f in tag_files]
    db_files = [Path(f).name for f in db_files]

    # getting experiment name from annotated file (tsv files can be multiple per experiment)
    experiment_names = [f[0: f.rfind('_')] for f in anno_files]

    df = pd.DataFrame({'Experiment Name': experiment_names,
                       'Deconvolved Files': deconv_files,
                       'Annotated Files': anno_files,
                       'Tag Files' : tag_files,
                       'Protein Files' : db_files})
    return df

def remove_selected_mzML_files(to_remove: list[str], params: dict) -> dict:
    """
    Removes selected mzML files from the mzML directory. (From fileUpload.py)

    Args:
        to_remove (List[str]): List of mzML files to remove.
        params (dict): Parameters.


    Returns:
        dict: parameters with updated mzML files
    """
    for input_type, df_type, file_postfix in zip(input_file_types, parsed_df_types,
                                                 ['_deconv.mzML', '_annotated.mzML', '_tagged.tsv', '_protein.tsv']):
        mzml_dir = Path(st.session_state.workspace, tool, input_type)
        # remove all given files from mzML workspace directory and selected files
        for exp_name in to_remove:
            file_name = exp_name + file_postfix
            Path(mzml_dir, file_name).unlink()
            del st.session_state[df_type][file_name]  # removing key

    # update the experiment df table
    tmp_df = st.session_state["experiment-df-tagger"]
    tmp_df.drop(tmp_df.loc[tmp_df['Experiment Name'].isin(to_remove)].index, inplace=True)
    st.session_state["experiment-df-tagger"] = tmp_df

    st.success("Selected experiments were removed!")
    return params

def showUploadedFilesTable():
    deconv_files = sorted(st.session_state["deconv_dfs_tagger"].keys())
    anno_files = sorted(st.session_state["anno_dfs_tagger"].keys())
    tag_files = sorted(st.session_state["tag_dfs_tagger"].keys())
    db_files = sorted(st.session_state["protein_dfs_tagger"].keys())

    # error message if files not exist
    if len(deconv_files) == 0 and len(anno_files) == 0:
        #st.info('No mzML added yet!', icon="ℹ️")
        return
    elif len(deconv_files) == 0:
        st.error("FLASHDeconv deconvolved mzML file is not added yet!")
    elif len(anno_files) == 0:
        st.error("FLASHDeconv annotated mzML file is not added yet!")
    elif len(tag_files) == 0:
        st.error("FLASHDeconv annotated tag file is not added yet!")
    elif len(db_files) == 0:
        st.error("Protein database file is not added yet!")
    elif np.any(np.array([len(deconv_files), len(anno_files)]) != len(tag_files)) :
        st.error("The same number of deconvolved and annotated files should be uploaded!")
    else:
        st.session_state["experiment-df-tagger"] = getUploadedFileDF(deconv_files, anno_files, tag_files, db_files)
        #st.markdown('**Uploaded experiments**')
        #st.dataframe(st.session_state["experiment-df"])

def handleInputFiles(uploaded_files):
    for file in uploaded_files:
        #file = Path(file)
        if not (file.name.endswith("mzML") or file.name.endswith("tsv") or file.name.endswith("fasta")):
            continue

        session_name = ''
        if file.name.endswith('_deconv.mzML'):
            session_name = 'deconv-mzMLs'
        elif file.name.endswith('_annotated.mzML'):
            session_name = 'anno-mzMLs'
        elif file.name.endswith('_tagged.tsv'):
            session_name = 'tags-tsv'
        elif file.name.endswith('_db.fasta'):
            session_name = 'db-fasta'
        elif file.name.endswith('_protein.tsv'):
            session_name = 'proteins-tsv'

        if file.name not in st.session_state[session_name]:
            with open(
                    Path(st.session_state.workspace, tool, session_name, file.name), "wb"
            ) as f:
                f.write(file.getbuffer())
            st.session_state[session_name].append(file.name)

def parseUploadedFiles(reparse=False):
    # get newly uploaded files
    deconv_files = st.session_state['deconv-mzMLs']
    anno_files = st.session_state['anno-mzMLs']
    tag_files = st.session_state['tags-tsv']
    # db_files = st.session_state['db-fasta']
    protein_files = st.session_state['proteins-tsv']
    # anno_files = Path(st.session_state['anno-mzMLs']).iterdir()
    new_deconv_files = [f for f in deconv_files if f not in st.session_state['deconv_dfs_tagger'] or reparse]
    new_anno_files = [f for f in anno_files if f not in st.session_state['anno_dfs_tagger'] or reparse]
    new_tag_files = [f for f in tag_files if f not in st.session_state['tag_dfs_tagger'] or reparse]
    new_protein_files = [f for f in protein_files if f not in st.session_state['protein_dfs_tagger'] or reparse]
    # new_db_files = [f for f in db_files if f not in st.session_state['protein_db']]

    # TODO: Find better solution when enabling file upload
    all_files = {'_'.join(t.split('_')[:-1]) for t in new_tag_files}
    new_deconv_files = [f for f in new_deconv_files if '_'.join(f.split('_')[:-1]) in all_files]
    new_anno_files = [f for f in new_anno_files if '_'.join(f.split('_')[:-1]) in all_files]
    new_tag_files = [f for f in new_tag_files if '_'.join(f.split('_')[:-1]) in all_files]
    new_protein_files = [f for f in new_protein_files if '_'.join(f.split('_')[:-1]) in all_files]

    # if newly uploaded files are not as needed
    if len(new_deconv_files)==0 and len(new_anno_files)==0 and len(new_tag_files)==0 and len(new_protein_files)==0: # if no newly uploaded files, move on
        return
    elif np.any(np.array([len(new_deconv_files), len(new_anno_files), len(new_protein_files)]) != len(new_tag_files)): # if newly uploaded files doesn't match, write message
        st.error('Added files are not in pair, so not parsed. \n Here are added ones, but not parsed ones:')
        # not_parsed = [f.name for f in new_deconv_files] + [f.name for f in new_anno_files]
        not_parsed = new_deconv_files + new_anno_files + new_tag_files + new_protein_files
        for i in not_parsed:
            st.markdown("- " + i)
        return

    # parse newly uploaded files
    new_deconv_files = sorted(new_deconv_files)
    new_anno_files = sorted(new_anno_files)
    new_tag_files = sorted(new_tag_files)
    # new_db_files = sorted(new_db_files)
    new_protein_files = sorted(new_protein_files)
    parsingWithProgressBar(new_deconv_files, new_anno_files, new_tag_files, new_protein_files)

def parsingWithProgressBar(infiles_deconv, infiles_anno, infiles_tag, infiles_protein):
    successes = []
    with st.session_state['progress_bar_space']:
        for anno_f, deconv_f, tag_f, protein_f in zip(infiles_anno, infiles_deconv, infiles_tag, infiles_protein):
            if not anno_f.endswith('.mzML'):
                continue
            exp_name = anno_f[0: anno_f.rfind('_')]

            with st.spinner('Parsing the experiment %s...'%exp_name):
                spec_df, anno_df, tolerance, massoffset, chargemass,  = parseFLASHDeconvOutput(
                    Path(st.session_state.workspace, tool, "anno-mzMLs", anno_f),
                    Path(st.session_state.workspace, tool, "deconv-mzMLs", deconv_f),
                )
                tag_df, protein_df = parseFLASHTaggerOutput(
                    Path(st.session_state.workspace, tool, "tags-tsv", tag_f),
                    Path(st.session_state.workspace, tool, "proteins-tsv", protein_f)
                )
                # Add tolerance as a new columnn, wasteful but gets the job done..
                spec_df['tol'] = tolerance
                st.session_state['anno_dfs_tagger'][anno_f] = anno_df
                st.session_state['deconv_dfs_tagger'][deconv_f] = spec_df
                st.session_state['tag_dfs_tagger'][tag_f] = tag_df
                # st.session_state['protein_db'][db_f] = db
                st.session_state['protein_dfs_tagger'][protein_f] = protein_df
            successes.append(st.success('Done parsing the experiment %s!'%exp_name))
        for success in successes:
            success.empty()

def content():
    # make directory to store deconv and anno mzML files & initialize data storage
    input_types = ["deconv-mzMLs", "anno-mzMLs", "tags-tsv", "proteins-tsv"]
    parsed_df_types = ["deconv_dfs_tagger", "anno_dfs_tagger", "tag_dfs_tagger", "protein_dfs_tagger"]
    initializeWorkspace(input_types, parsed_df_types)


# for Workflow
def postprocessingAfterUpload_Tagger(uploaded_files: list) -> None:
    initializeWorkspace(input_file_types, parsed_df_types)
    #handleInputFiles(uploaded_files)
    parseUploadedFiles(reparse=True)
    showUploadedFilesTable()
