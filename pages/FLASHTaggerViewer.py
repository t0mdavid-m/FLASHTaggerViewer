import json

from src.common import *
from src.masstable import *
from src.components import *
from src.sequence import getFragmentDataFromSeq, getInternalFragmentDataFromSeq
from io import StringIO, BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from pages.FileUploadTagger import handleInputFiles
from pages.FileUploadTagger import parseUploadedFiles
from pages.FileUploadTagger import initializeWorkspace, showUploadedFilesTable
from pyopenms import AASequence

from src.sequence import remove_ambigious

from os.path import join, isfile


DEFAULT_LAYOUT = [
    ['protein_table'], 
    ['sequence_view'], 
    ['tag_table'],
    ['deconv_spectrum']
]
# Sequence View will be replaced with improved component
# Annotated Spectrum will be replaced with new component including tags


def sendDataToJS(selected_data, layout_info_per_exp, grid_key='flash_viewer_grid'):

    selected_anno_file = selected_data.iloc[0]['Annotated Files']
    selected_deconv_file = selected_data.iloc[0]['Deconvolved Files']
    selected_tag_file = selected_data.iloc[0]['Tag Files']
    selected_db_file = selected_data.iloc[0]['Protein Files']

    print(selected_tag_file)

    settings_file = join(
        st.session_state["workspace"],  'FLASHTaggerOutput',
        selected_tag_file.split('_tagged.tsv')[0], 'settings_FLASHTnT.json'
    )
    fragments = ['b', 'y']
    if isfile(settings_file):
        with open(settings_file, 'r') as f:
            tnt_settings = json.load(f)
        if 'tnt:ex:ion_type' in tnt_settings:
            fragments = tnt_settings['tnt:ex:ion_type']


    # getting data from mzML files
    spec_df = st.session_state['deconv_dfs_tagger'][selected_deconv_file]
    anno_df = st.session_state['anno_dfs_tagger'][selected_anno_file]
    tag_df = st.session_state['tag_dfs_tagger'][selected_tag_file]

    # Process tag df into a linear data format
    new_tag_df = {c : [] for c in tag_df.columns}
    for i, row in tag_df.iterrows():
        # No splitting if it is not recognized as string
        if pd.isna(row['ProteoformIndex']):
            row['ProteoformIndex'] = -1
        if isinstance(row['ProteoformIndex'], str) and (';' in row['ProteoformIndex']):
            no_items = row['ProteoformIndex'].count(';') + 1
            for c in new_tag_df.keys():
                if (isinstance(row[c], str)) and (';' in row[c]):
                    new_tag_df[c] += row[c].split(';')
                else:
                    new_tag_df[c] += [row[c]]*no_items
        else:
            for c in new_tag_df.keys():
                new_tag_df[c].append(row[c])
    tag_df = pd.DataFrame(new_tag_df)

    tsv_buffer = StringIO()
    tag_df.to_csv(tsv_buffer, sep='\t', index=False)
    tsv_buffer.seek(0)
    tag_df = pd.read_csv(tsv_buffer, sep='\t')

    # Complete df
    tag_df['Scan'] = 0
    tag_df['StartPosition'] = tag_df['StartPosition'] - 1
    tag_df['EndPos'] = tag_df['StartPosition'] + tag_df['Length'] - 1
    tag_df = tag_df.rename(
        columns={
            'ProteoformIndex' : 'ProteinIndex',
            'DeNovoScore' : 'Score',
            'Masses' : 'mzs',
            'StartPosition' : 'StartPos' 
        }
    )

    protein_df = st.session_state['protein_dfs_tagger'][selected_db_file]
    protein_df['length'] = protein_df['DatabaseSequence'].apply(lambda x : len(x))
    protein_df = protein_df.rename(
        columns={
            'ProteoformIndex' : 'index',
            'ProteinAccession' : 'accession',
            'ProteinDescription' : 'description',
            'DatabaseSequence' : 'sequence'
        }
    )

    sequence_data = {}
    # Compute coverage
    for i, row in protein_df.iterrows():
        pid = row['index']
        sequence = row['sequence']
        coverage = np.zeros(len(sequence), dtype='float')
        for i in range(len(sequence)):
            coverage[i] = np.sum(
                (tag_df['ProteinIndex'] == pid) &
                (tag_df['StartPos'] <= i) &
                (tag_df['EndPos'] >= i)
            )
        p_cov = np.zeros(len(coverage))
        if np.max(coverage) > 0:
            p_cov = coverage/np.max(coverage)

        proteoform_start = row['StartPosition']
        proteoform_end = row['EndPosition']
        start_index = 0 if proteoform_start <= 0 else proteoform_start - 1
        end_index = len(sequence) - 1 if proteoform_end <= 0 else proteoform_end - 1


        if row['ModCount'] > 0:
            mod_masses = [float(m) for m in str(row['ModMass']).split(';')]
            mod_starts = [int(float(s)) for s in str(row['ModStart']).split(';')]
            mod_ends = [int(float(s)) for s in str(row['ModEnd']).split(';')]
            if pd.isna(row['ModID']):
                mod_labels = [''] * row['ModCount']
            else:
                mod_labels = [s[:-1].replace(',', '; ') for s in str(row['ModID']).split(';')]
            print(mod_labels)
        else:
            mod_masses = []
            mod_starts = []
            mod_ends = []
            mod_labels = []
        modifications = []
        for s, e, m in zip(mod_starts, mod_ends, mod_masses):
            modifications.append((s-start_index, e-start_index, m))
        
        sequence = str(sequence)
        sequence_data[pid] = getFragmentDataFromSeq(
            str(sequence)[start_index:end_index+1], p_cov, np.max(coverage), 
            modifications
        )

        sequence_data[pid]['sequence'] = list(sequence)
        sequence_data[pid]['proteoform_start'] = proteoform_start - 1
        sequence_data[pid]['proteoform_end'] = proteoform_end - 1
        sequence_data[pid]['computed_mass'] = row['ProteoformMass']
        sequence_data[pid]['theoretical_mass'] = remove_ambigious(AASequence.fromString(sequence)).getMonoWeight()
        sequence_data[pid]['modifications'] = [
            {
                # Modfications are zero based
                'start' : s - 1,
                'end' : e - 1,
                'mass_diff' : m,
                'labels' : l
            } for s, e, m, l in zip(mod_starts, mod_ends, mod_masses, mod_labels)
        ]

    # empty_row = pd.DataFrame(np.nan, index=[-1], columns=protein_df.columns)
    # protein_df = pd.concat([protein_df, empty_row])
    # protein_df.loc[-1,'index'] = -1
    # protein_df.loc[-1,'accession'] = 'unassigned sequence tags'
    # protein_df.loc[-1,'description'] = 'unassigned sequence tags'


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
                per_scan_contents['anno_spec'] = True
                component_arguments = PlotlyLineplotTagger(title="Deconvolved Spectrum")
            elif comp_name == 'anno_spectrum':
                per_scan_contents['anno_spec'] = True
                component_arguments = PlotlyLineplotTagger(title="Annotated Spectrum")
            elif comp_name == 'mass_table':
                per_scan_contents['mass_table'] = True
                component_arguments = Tabulator('MassTable')
            elif comp_name == 'protein_table':
                data_to_send['protein_table'] = protein_df
                data_to_send['per_scan_data'] = getSpectraTableDF(spec_df)
                component_arguments = Tabulator('ProteinTable')
            elif comp_name == 'tag_table':
                data_to_send['tag_table'] = tag_df
                component_arguments = Tabulator('TagTable')
            elif comp_name == '3D_SN_plot':
                per_scan_contents['3d'] = True
                component_arguments = Plotly3Dplot(title="Precursor Signals")
            elif comp_name == 'sequence_view':
            #    data_to_send['sequence_data'] = getFragmentDataFromSeq(st.session_state.input_sequence)
                component_arguments = SequenceView()
            elif comp_name == 'internal_fragment_map':
            #    data_to_send['internal_fragment_data'] = getInternalFragmentDataFromSeq(st.session_state.input_sequence)
                component_arguments = InternalFragmentMap()

            components_of_this_row.append(FlashViewerComponent(component_arguments))
        components.append(components_of_this_row)
    per_scan_contents['3d'] = True
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

                tmp_df = spec_df[['mzarray', 'intarray', 'CombinedPeaks']].copy()
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

    # Set sequence data
    data_to_send['sequence_data'] = sequence_data
    data_to_send['settings'] = {
        'tolerance' : spec_df['tol'].to_numpy(dtype='float')[0],
        'ion_types' : fragments
    }

    flash_viewer_grid_component(components=components, data=data_to_send, component_key=grid_key)


def setSequenceViewInDefaultView():
    if 'input_sequence' in st.session_state and st.session_state.input_sequence:
        global DEFAULT_LAYOUT
        DEFAULT_LAYOUT = DEFAULT_LAYOUT + [['sequence_view']] + [['internal_fragment_map']]

def select_experiment():
    st.session_state.selected_experiment0_tagger = st.session_state.selected_experiment_dropdown_tagger
    if "saved_layout_setting_tagger" in st.session_state and len(st.session_state["saved_layout_setting_tagger"]) > 1:
        for exp_index in range(1, len(st.session_state["saved_layout_setting_tagger"])):
            st.session_state[f"selected_experiment{exp_index}_tagger"] = st.session_state[f'selected_experiment_dropdown_{exp_index}_tagger']



def content():
    page_setup("TaggerViewer")
    #setSequenceViewInDefaultView()
    st.session_state['progress_bar_space'] = st.container()
    input_types = ["deconv-mzMLs", "anno-mzMLs", "tags-tsv", "proteins-tsv", "tntsettings-json"]
    parsed_df_types = ["deconv_dfs_tagger", "anno_dfs_tagger", "tag_dfs_tagger", "protein_dfs_tagger", 'tntsettings-json']
    initializeWorkspace(input_types, parsed_df_types)
    parseUploadedFiles()
    showUploadedFilesTable()

    ### if no input file is given, show blank page
    if "experiment-df-tagger" not in st.session_state:
        st.error('No results to show yet. Please run a workflow first!')
        return

    # input experiment file names (for select-box later)
    experiment_df = st.session_state["experiment-df-tagger"]

    # Map names to index
    name_to_index = {n : i for i, n in enumerate(experiment_df['Experiment Name'])}


    ### for only single experiment on one view
    st.selectbox(
        "choose experiment", experiment_df['Experiment Name'], 
        key="selected_experiment_dropdown_tagger", 
        index=name_to_index[st.session_state.selected_experiment0_tagger] if 'selected_experiment0_tagger' in st.session_state else None,
        on_change=select_experiment
    )

    if 'selected_experiment0_tagger' in st.session_state:
        selected_exp0 = experiment_df[experiment_df['Experiment Name'] == st.session_state.selected_experiment0_tagger]
        layout_info = DEFAULT_LAYOUT
        if "saved_layout_setting_tagger" in st.session_state:  # when layout manager was used
            layout_info = st.session_state["saved_layout_setting_tagger"][0]
        with st.spinner('Loading component...'):
            sendDataToJS(selected_exp0, layout_info)

    ### for multiple experiments on one view
    if "saved_layout_setting_tagger" in st.session_state and len(st.session_state["saved_layout_setting_tagger"]) > 1:

        for exp_index, exp_layout in enumerate(st.session_state["saved_layout_setting_tagger"]):
            if exp_index == 0: continue  # skip the first experiment

            st.divider() # horizontal line

            st.selectbox(
                "choose experiment", experiment_df['Experiment Name'], 
                key=f'selected_experiment_dropdown_{exp_index}_tagger',
                index = name_to_index[st.session_state[f'selected_experiment{exp_index}_tagger']] if f'selected_experiment{exp_index}_tagger' in st.session_state else None,
                on_change=select_experiment
            )

            # if #experiment input files are less than #layouts, all the pre-selection will be the first experiment
            if f"selected_experiment{exp_index}_tagger" in st.session_state:
                selected_exp = experiment_df[
                    experiment_df['Experiment Name'] == st.session_state["selected_experiment%d_tagger"%exp_index]]
                layout_info = st.session_state["saved_layout_setting_tagger"][exp_index]

                with st.spinner('Loading component...'):
                    sendDataToJS(selected_exp, layout_info, 'flash_viewer_grid_%d' % exp_index)


    # selected_tags = selected_exp0.iloc[0]['Tag Files']
    # selected_proteins = selected_exp0.iloc[0]['Protein Files']
    # tag_df = st.session_state['tag_dfs_tagger'][selected_tags]
    # protein_df = st.session_state['protein_dfs_tagger'][selected_proteins]

    # tag_buffer = StringIO()
    # tag_df.to_csv(tag_buffer, sep='\t', index=False)
    # tag_buffer.seek(0)

    # protein_buffer = StringIO()
    # protein_df.to_csv(protein_buffer, sep='\t', index=False)
    # protein_buffer.seek(0)

    # zip_buffer = BytesIO()
    # with ZipFile(zip_buffer, 'w', ZIP_DEFLATED) as zip_file:
    #     zip_file.writestr('tags.tsv', tag_buffer.getvalue())
    #     zip_file.writestr('proteins.tsv', protein_buffer.getvalue())
    # zip_buffer.seek(0)
    
    # st.download_button("Download ⬇️", zip_buffer, file_name=f'{st.session_state.selected_experiment0}.zip')


if __name__ == "__main__":
    # try:
    content()
    # except:
    #     st.warning(ERRORS["visualization"])
