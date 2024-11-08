import streamlit as st
import sys
import pandas as pd

from src.common.common import page_setup, save_params
from src.masstable import getMSSignalDF, getSpectraTableDF
from src.components import PlotlyHeatmap, PlotlyLineplot, Plotly3Dplot, Tabulator, SequenceView, InternalFragmentMap, \
                           FlashViewerComponent, flash_viewer_grid_component
from src.sequence import getFragmentDataFromSeq, getInternalFragmentDataFromSeq
from src.parse.deconv import initializeWorkspace, parseUploadedFiles, getUploadedFileDF


DEFAULT_LAYOUT = [['ms1_deconv_heat_map'], ['scan_table', 'mass_table'],
                  ['anno_spectrum', 'deconv_spectrum'], ['3D_SN_plot']]


def sendDataToJS(selected_data, layout_info_per_exp, grid_key='flash_viewer_grid'):
    # getting data
    selected_anno_file = selected_data.iloc[0]['Annotated Files']
    selected_deconv_file = selected_data.iloc[0]['Deconvolved Files']

    # getting data from mzML files
    spec_df = st.session_state['deconv_dfs'][selected_deconv_file]
    anno_df = st.session_state['anno_dfs'][selected_anno_file]

    components = []
    data_to_send = {}
    per_scan_contents = {'mass_table': False, 'anno_spec': False, 'deconv_spec': False, '3d': False}
    for row in layout_info_per_exp:
        components_of_this_row = []
        for col_index, comp_name in enumerate(row):
            component_arguments = None

            # prepare component arguments
            if comp_name == 'ms1_raw_heatmap':
                data_to_send['raw_heatmap_df'] = getMSSignalDF(anno_df)
                component_arguments = PlotlyHeatmap(title="Raw MS1 Heatmap")
            elif comp_name == 'ms1_deconv_heat_map':
                data_to_send['deconv_heatmap_df'] = getMSSignalDF(spec_df)
                component_arguments = PlotlyHeatmap(title="Deconvolved MS1 Heatmap")
            elif comp_name == 'scan_table':
                data_to_send['per_scan_data'] = getSpectraTableDF(spec_df)
                component_arguments = Tabulator('ScanTable')
            elif comp_name == 'deconv_spectrum':
                per_scan_contents['deconv_spec'] = True
                component_arguments = PlotlyLineplot(title="Deconvolved Spectrum")
            elif comp_name == 'anno_spectrum':
                per_scan_contents['anno_spec'] = True
                component_arguments = PlotlyLineplot(title="Annotated Spectrum")
            elif comp_name == 'mass_table':
                per_scan_contents['mass_table'] = True
                component_arguments = Tabulator('MassTable')
            elif comp_name == '3D_SN_plot':
                per_scan_contents['3d'] = True
                component_arguments = Plotly3Dplot(title="Precursor Signals")
            elif comp_name == 'sequence_view':
                data_to_send['sequence_data'] = {0: getFragmentDataFromSeq(st.session_state.input_sequence)}
                component_arguments = SequenceView()
            elif comp_name == 'internal_fragment_map':
                data_to_send['internal_fragment_data'] = getInternalFragmentDataFromSeq(st.session_state.input_sequence)
                component_arguments = InternalFragmentMap()

            components_of_this_row.append(FlashViewerComponent(component_arguments))
        components.append(components_of_this_row)

    if any(per_scan_contents.values()):
        scan_table = data_to_send['per_scan_data']
        dfs = [scan_table]
        for key, exist in per_scan_contents.items():
            if not exist: continue

            if key == 'mass_table':
                tmp_df = spec_df[['mzarray', 'intarray', 'MinCharges', 'MaxCharges', 'MinIsotopes', 'MaxIsotopes',
                                  'cos', 'snr', 'qscore']].copy()
                tmp_df.rename(columns={'mzarray': 'MonoMass', 'intarray': 'SumIntensity', 'cos': 'CosineScore',
                                       'snr': 'SNR', 'qscore': 'QScore'},
                              inplace=True)
            elif key == 'deconv_spec':
                if per_scan_contents['mass_table']: continue  # deconv_spec shares same data with mass_table

                tmp_df = spec_df[['mzarray', 'intarray']].copy()
                tmp_df.rename(columns={'mzarray': 'MonoMass', 'intarray': 'SumIntensity'}, inplace=True)
            elif key == 'anno_spec':
                tmp_df = anno_df[['mzarray', 'intarray']].copy()
                tmp_df.rename(columns={'mzarray': 'MonoMass_Anno', 'intarray': 'SumIntensity_Anno'}, inplace=True)
            elif key == '3d':
                tmp_df = spec_df[['PrecursorScan', 'SignalPeaks', 'NoisyPeaks']].copy()
            else:  # shouldn't come here
                continue

            dfs.append(tmp_df)
        data_to_send['per_scan_data'] = pd.concat(dfs, axis=1)

    # if Internal fragment map was selected, but sequence view was not
    if ('internal_fragment_data' in data_to_send) and ('sequence_data' not in data_to_send):
        data_to_send['sequence_data'] = {0 : getFragmentDataFromSeq(st.session_state.input_sequence)}

    flash_viewer_grid_component(components=components, data=data_to_send, component_key=grid_key)


def setSequenceViewInDefaultView():
    if 'input_sequence' in st.session_state and st.session_state.input_sequence:
        global DEFAULT_LAYOUT
        DEFAULT_LAYOUT = DEFAULT_LAYOUT + [['sequence_view']]


def select_experiment():
    st.session_state.selected_experiment0 = st.session_state.selected_experiment_dropdown
    if "saved_layout_setting" in st.session_state and len(st.session_state["saved_layout_setting"]) > 1:
        for exp_index in range(1, len(st.session_state["saved_layout_setting"])):
            st.session_state[f"selected_experiment{exp_index}"] = st.session_state[f'selected_experiment_dropdown_{exp_index}']





# page initialization
params = page_setup()

st.title("FLASHViewer")
setSequenceViewInDefaultView()

# Parse previously uploaded files
input_file_types = ["deconv-mzMLs", "anno-mzMLs", "tsv-files"]
parsed_df_types = ["deconv_dfs", "anno_dfs", "parsed_tsv_files"]
initializeWorkspace(input_file_types, parsed_df_types)
st.session_state['progress_bar_space'] = st.container()
parseUploadedFiles()

deconv_files = sorted(st.session_state["deconv_dfs"].keys())
anno_files = sorted(st.session_state["anno_dfs"].keys())
st.session_state["experiment-df"] = getUploadedFileDF(deconv_files, anno_files)

### if no input file is given, show blank page
if len(st.session_state["experiment-df"]) == 0:
    st.error('No results to show yet. Please run a workflow first!')
    st.stop()

# input experiment file names (for select-box later)
experiment_df = st.session_state["experiment-df"]

# Map names to index
name_to_index = {n : i for i, n in enumerate(experiment_df['Experiment Name'])}

### for only single experiment on one view
st.selectbox(
    "choose experiment", experiment_df['Experiment Name'], 
    key="selected_experiment_dropdown", 
    index=name_to_index[st.session_state.selected_experiment0] if 'selected_experiment0' in st.session_state else None,
    on_change=select_experiment
)

if 'selected_experiment0' in st.session_state:
    selected_exp0 = experiment_df[experiment_df['Experiment Name'] == st.session_state.selected_experiment0]
    layout_info = DEFAULT_LAYOUT
    if "saved_layout_setting" in st.session_state:  # when layout manager was used
        layout_info = st.session_state["saved_layout_setting"][0]
    with st.spinner('Loading component...'):
        sendDataToJS(selected_exp0, layout_info)


### for multiple experiments on one view
if "saved_layout_setting" in st.session_state and len(st.session_state["saved_layout_setting"]) > 1:

    for exp_index, exp_layout in enumerate(st.session_state["saved_layout_setting"]):
        if exp_index == 0: continue  # skip the first experiment

        st.divider()  # horizontal line

        st.selectbox(
            "choose experiment", experiment_df['Experiment Name'], 
            key=f'selected_experiment_dropdown_{exp_index}',
            index = name_to_index[st.session_state[f'selected_experiment{exp_index}']] if f'selected_experiment{exp_index}' in st.session_state else None,
            on_change=select_experiment
        )
        # if #experiment input files are less than #layouts, all the pre-selection will be the first experiment
        if f"selected_experiment{exp_index}" in st.session_state:
            selected_exp = experiment_df[
                experiment_df['Experiment Name'] == st.session_state["selected_experiment%d" % exp_index]]
            layout_info = st.session_state["saved_layout_setting"][exp_index]
            with st.spinner('Loading component...'):
                sendDataToJS(selected_exp, layout_info, 'flash_viewer_grid_%d' % exp_index)

save_params(params)
