import streamlit as st
import time
from .workflow.WorkflowManager import WorkflowManager
from pages.FileUploadTagger import postprocessingAfterUpload_Tagger
from pages.FileUpload import postprocessingAfterUpload_FD

from os.path import join, splitext, basename, exists, dirname
from os import makedirs
from shutil import copyfile, rmtree
from pathlib import Path

class Workflow(WorkflowManager):
    # Setup pages for upload, parameter, execution and results.
    # For layout use any streamlit components such as tabs (as shown in example), columns, or even expanders.
    def __init__(self) -> None:
        # Initialize the parent class with the workflow name.
        super().__init__("TOPP Workflow", st.session_state["workspace"])

    def upload(self)-> None:
        t = st.tabs(["MS data", "Example with fallback data"])
        with t[0]:
            # Use the upload method from StreamlitUI to handle mzML file uploads.
            self.ui.upload_widget(key="mzML-files", name="MS data", file_type="mzML")
        with t[1]:
            # Example with fallback data (not used in workflow)
            self.ui.upload_widget(key="image", file_type="png", fallback="assets/OpenMS.png")

    def configure(self) -> None:
        # Allow users to select mzML files for the analysis.
        self.ui.select_input_file("mzML-files", multiple=True)

        # Create tabs for different analysis steps.
        t = st.tabs(
            ["**Feature Detection**", "**Adduct Detection**", "**SIRIUS Export**", "**Python Custom Tool**"]
        )
        with t[0]:
            # Parameters for FeatureFinderMetabo TOPP tool.
            self.ui.input_TOPP("FeatureFinderMetabo")
        with t[1]:
            # A single checkbox widget for workflow logic.
            self.ui.input_widget("run-adduct-detection", False, "Adduct Detection")
            # Paramters for MetaboliteAdductDecharger TOPP tool.
            self.ui.input_TOPP("MetaboliteAdductDecharger")
        with t[2]:
            # Paramters for SiriusExport TOPP tool
            self.ui.input_TOPP("SiriusExport")
        with t[3]:
            # Generate input widgets for a custom Python tool, located at src/python-tools.
            # Parameters are specified within the file in the DEFAULTS dictionary.
            self.ui.input_python("example")

    def execution(self) -> None:
        # Get mzML input files from self.params.
        # Can be done without file manager, however, it ensures everything is correct.
        in_mzML = self.file_manager.get_files(self.params["mzML-files"])
        
        # Log any messages.
        self.logger.log(f"Number of input mzML files: {len(in_mzML)}")

        # Prepare output files for feature detection.
        out_ffm = self.file_manager.get_files(in_mzML, "featureXML", "feature-detection")

        # Run FeatureFinderMetabo tool with input and output files.
        self.executor.run_topp(
            "FeatureFinderMetabo", input_output={"in": in_mzML, "out": out_ffm}
        )

        # Check if adduct detection should be run.
        if self.params["run-adduct-detection"]:
        
            # Run MetaboliteAdductDecharger for adduct detection, with disabled logs.
            # Without a new file list for output, the input files will be overwritten in this case.
            self.executor.run_topp(
                "MetaboliteAdductDecharger", {"in": out_ffm, "out_fm": out_ffm}, write_log=False
            )

        # Example for a custom Python tool, which is located in src/python-tools.
        self.executor.run_python("example", {"in": in_mzML})

        # Prepare output file for SiriusExport.
        out_se = self.file_manager.get_files("sirius.ms", set_results_dir="sirius-export")
        self.executor.run_topp("SiriusExport", {"in": self.file_manager.get_files(in_mzML, collect=True),
                                                "in_featureinfo": self.file_manager.get_files(out_ffm, collect=True),
                                                "out": out_se})

    def results(self) -> None:
        st.warning("Not implemented yet.")




class TagWorkflow(WorkflowManager):

    def __init__(self) -> None:
        # Initialize the parent class with the workflow name.
        super().__init__("FLASHTnT", st.session_state["workspace"])
        self.tool_name = 'FLASHTaggerViewer'


    def upload(self)-> None:
        t = st.tabs(["MS data", "Database"])
        with t[0]:
            example_data = ['example-data/flashtagger/example_spectrum_%d.mzML' % n for n in [1, 2]]
            # Use the upload method from StreamlitUI to handle mzML file uploads.
            self.ui.upload_widget(key="mzML-files", name="MS data", file_type="mzML", fallback=example_data)
        with t[1]:
            # Example with fallback data (not used in workflow)
            self.ui.upload_widget(key="fasta-file", name="Database", file_type="fasta", enable_directory=False,
                                  fallback='example-data/flashtagger/example_database.fasta')


    def configure(self) -> None:
        # Allow users to select mzML files for the analysis.
        self.ui.select_input_file("mzML-files", multiple=True)
        self.ui.select_input_file("fasta-file", multiple=False)

        self.ui.input_widget(
            'few_proteins', name='Do you expect <100 Proteins?', widget_type='checkbox', default=True,
            help='If set, the decoy database will be 100 times larger than the target database for better FDR estimation resolution. This increases the runtime significantly.'
        )

        # Create tabs for different analysis steps.
        t = st.tabs(
            ["**FLASHDeconv**", "**FLASHTnT**"]
        )
        with t[0]:
            # Parameters for FeatureFinderMetabo TOPP tool.
            self.ui.input_TOPP(
                'FLASHDeconv',
                exclude_parameters = [
                    'ida_log',
                    'write_detail', 'report_FDR', 'quant_method',
                    'mass_error_ppm', 'min_sample_rate', 'min_trace_length',
                    'max_trace_length', 'min_cos', 'type', 'isotope_correction',
                    'reporter_mz_tol', 'only_fully_quantified'
                ],
                display_subsections=True
            )
        with t[1]:
            # Parameters for FeatureFinderMetabo TOPP tool.
            self.ui.input_TOPP(
                'FLASHTnT', 
                #exclude_parameters = [
                #    'min_mz', 'max_mz', 'min_rt', 'max_rt', 'max_ms_level',
                #    'use_RNA_averagine', 'tol', 'min_mass', 'max_mass',
                #    'min_charge', 'max_charge', 'precursor_charge',
                #    'precursor_mz', 'min_cos', 'min_snr'
                #],
                display_subsections=True
            )

    def pp(self) -> None:

        if 'selected_experiment0_tagger' in st.session_state:
            del(st.session_state['selected_experiment0_tagger'])
        if "saved_layout_setting_tagger" in st.session_state and len(st.session_state["saved_layout_setting_tagger"]) > 1:
            for exp_index in range(1, len(st.session_state["saved_layout_setting_tagger"])):
                if f"selected_experiment{exp_index}_tagger" in st.session_state:
                    del(st.session_state[f"selected_experiment{exp_index}_tagger"])

        st.session_state['progress_bar_space'] = st.container()
        
        try:
            in_mzMLs = self.file_manager.get_files(self.params["mzML-files"])
        except:
            st.error('Please select at least one mzML file.')
            return

        base_path = dirname(self.workflow_dir)

        uploaded_files = []
        for in_mzML in in_mzMLs:
            current_base = splitext(basename(in_mzML))[0]
            current_time = time.strftime("%Y%m%d-%H%M%S")

            #out_db = join(base_path, 'db-fasta', f'{current_base}_db.fasta')
            out_anno = join(base_path, self.tool_name, 'anno-mzMLs', f'{current_base}_{current_time}_annotated.mzML')
            out_deconv = join(base_path, self.tool_name, 'deconv-mzMLs', f'{current_base}_{current_time}_deconv.mzML')
            out_tag = join(base_path, self.tool_name, 'tags-tsv', f'{current_base}_{current_time}_tagged.tsv')
            out_protein = join(base_path, self.tool_name, 'proteins-tsv', f'{current_base}_{current_time}_protein.tsv')

            if not exists(out_tag):
                continue

            #uploaded_files.append(out_db)
            uploaded_files.append(out_anno)
            uploaded_files.append(out_deconv)
            uploaded_files.append(out_tag)
            uploaded_files.append(out_protein)


        # make directory to store deconv and anno mzML files & initialize data storage
        postprocessingAfterUpload_Tagger(uploaded_files)


    
    def execution(self) -> None:
        # Get mzML input files from self.params.
        # Can be done without file manager, however, it ensures everything is correct.
        try:      
            in_mzMLs = self.file_manager.get_files(self.params["mzML-files"])
        except ValueError:
            st.error('Please select at least one mzML file.')  
            return
        try: 
            database = self.file_manager.get_files(self.params["fasta-file"])
        except ValueError:
            st.error('Please select a database.')  
            return
        #temp_path = self.file_manager._create_results_sub_dir()
        
        base_path = dirname(self.workflow_dir)

        if not exists(join(base_path, self.tool_name, 'db-fasta')):
            makedirs(join(base_path, self.tool_name, 'db-fasta'))
        if not exists(join(base_path, self.tool_name, 'anno-mzMLs')):
            makedirs(join(base_path, self.tool_name, 'anno-mzMLs'))
        if not exists(join(base_path, self.tool_name, 'deconv-mzMLs')):
            makedirs(join(base_path, self.tool_name, 'deconv-mzMLs'))
        if not exists(join(base_path, self.tool_name, 'tags-tsv')):
            makedirs(join(base_path, self.tool_name, 'tags-tsv'))
        if not exists(join(base_path, self.tool_name, 'proteins-tsv')):
            makedirs(join(base_path, self.tool_name, 'proteins-tsv'))
            
        # # Log any messages.
        #self.logger.log(f"Number of input mzML files: {in_mzMLs}")
        #self.logger.log(f"Number of input mzML files: {database}")

        #self.logger.log(self.file_manager.workflow_dir)


        uploaded_files = []
        for in_mzML in in_mzMLs:
            current_base = splitext(basename(in_mzML))[0]
            current_time = time.strftime("%Y%m%d-%H%M%S")

            out_db = join(base_path, self.tool_name, 'db-fasta', f'{current_base}_{current_time}_db.fasta')
            out_anno = join(base_path, self.tool_name, 'anno-mzMLs', f'{current_base}_{current_time}_annotated.mzML')
            out_deconv = join(base_path, self.tool_name, 'deconv-mzMLs', f'{current_base}_{current_time}_deconv.mzML')
            out_tag = join(base_path, self.tool_name, 'tags-tsv', f'{current_base}_{current_time}_tagged.tsv')
            out_protein = join(base_path, self.tool_name, 'proteins-tsv', f'{current_base}_{current_time}_protein.tsv')
            #decoy_db = join(temp_path, f'{current_base}_db.fasta')

            # Get folder name
            folder_path = join(base_path, 'FLASHTaggerOutput', '%s_%s'%(current_base, current_time))

            if exists(folder_path):
                rmtree(folder_path)
            makedirs(folder_path)

            tagger_params = self.executor.parameter_manager.get_parameters_from_json()['FLASHTnT']
            if ('Tagger:fdr' in tagger_params) and (tagger_params['Tagger:fdr'] < 1):
                if self.executor.parameter_manager.get_parameters_from_json()['few_proteins']:
                    ratio = 100
                else:
                    ratio = 1
                self.executor.run_topp(
                    'DecoyDatabase',
                    {
                        'in' : [database[0]],
                        'out' : [out_db],
                    },
                    params_manual = {
                        'method' : 'shuffle',
                        'shuffle_decoy_ratio' : ratio,
                        'enzyme' : 'no cleavage',
                    }
                )
            else:
                copyfile(database[0], out_db)

            self.executor.run_topp(
                'FLASHDeconv',
                input_output={
                    'in' : [in_mzML],
                    'out' : ['_.tsv'],
                    'out_annotated_mzml' :  [out_anno],
                    'out_mzml' :  [out_deconv],
                }
            )

            self.executor.run_topp(
                'FLASHTnT',
                input_output={
                    'in' : [out_deconv],
                    'fasta' : [out_db],
                    'out_tag' :  [out_tag],
                    'out_pro' :  [out_protein]
                },
            )

            uploaded_files.append(out_db)
            uploaded_files.append(out_anno)
            uploaded_files.append(out_deconv)
            uploaded_files.append(out_tag)
            uploaded_files.append(out_protein)

            copyfile(out_db, join(folder_path, 'database.fasta'))
            copyfile(out_anno, join(folder_path, 'annotated.mzML'))
            copyfile(out_deconv, join(folder_path, 'out.mzML'))
            copyfile(out_tag, join(folder_path, 'tags.tsv'))
            copyfile(out_protein, join(folder_path, 'proteins.tsv'))


        # make directory to store deconv and anno mzML files & initialize data storage
        # input_types = ["deconv-mzMLs", "anno-mzMLs", "tags-tsv", "db-fasta"]
        # parsed_df_types = ["deconv_dfs", "anno_dfs", "tag_dfs", "protein_db"]
        # initializeWorkspace(input_types, parsed_df_types)
        
        # handleInputFiles(uploaded_files)
        # parseUploadedFiles()



        # # Prepare output files for feature detection.
        # out_ffm = self.file_manager.get_files(in_mzML, "featureXML", "feature-detection")

        # # Run FeatureFinderMetabo tool with input and output files.
        # self.executor.run_topp(
        #     "FeatureFinderMetabo", input_output={"in": in_mzML, "out": out_ffm}
        # )

        # # Check if adduct detection should be run.
        # if self.params["run-adduct-detection"]:
        
        #     # Run MetaboliteAdductDecharger for adduct detection, with disabled logs.
        #     # Without a new file list for output, the input files will be overwritten in this case.
        #     self.executor.run_topp(
        #         "MetaboliteAdductDecharger", {"in": out_ffm, "out_fm": out_ffm}, write_log=False
        #     )

        # # Example for a custom Python tool, which is located in src/python-tools.
        # self.executor.run_python("example", {"in": in_mzML})

        # # Prepare output file for SiriusExport.
        # out_se = self.file_manager.get_files("sirius.ms", set_results_dir="sirius-export")
        # self.executor.run_topp("SiriusExport", {"in": self.file_manager.get_files(in_mzML, collect=True),
        #                                         "in_featureinfo": self.file_manager.get_files(out_ffm, collect=True),
        #                                         "out": out_se})




class DeconvWorkflow(WorkflowManager):

    def __init__(self) -> None:
        # Initialize the parent class with the workflow name.
        super().__init__("FLASHDeconv", st.session_state["workspace"])
        self.tool_name = 'FLASHDeconvViewer'


    def upload(self)-> None:
        # Use the upload method from StreamlitUI to handle mzML file uploads.
        self.ui.upload_widget(key="mzML-files", name="MS data", file_type="mzML",
                              fallback=['example-data/flashdeconv/example_fd.mzML'])

    def configure(self) -> None:
        # Allow users to select mzML files for the analysis.
        self.ui.select_input_file("mzML-files", multiple=True)

        self.ui.input_TOPP(
            'FLASHDeconv',
            exclude_parameters = [
                'ida_log'
            ],
            display_subsections=True
        )


    def pp(self) -> None:

        if 'selected_experiment0' in st.session_state:
            del(st.session_state['selected_experiment0'])
        if "saved_layout_setting" in st.session_state and len(st.session_state["saved_layout_setting"]) > 1:
            for exp_index in range(1, len(st.session_state["saved_layout_setting"])):
                if f"selected_experiment{exp_index}" in st.session_state:
                    del(st.session_state[f"selected_experiment{exp_index}"])

        st.session_state['progress_bar_space'] = st.container()

        try:
            in_mzMLs = self.file_manager.get_files(self.params["mzML-files"])
        except:
            st.error('Please select at least one mzML file.')
            return

        base_path = dirname(self.workflow_dir)

        uploaded_files = []
        for in_mzML in in_mzMLs:
            current_base = splitext(basename(in_mzML))[0]
            current_time = time.strftime("%Y%m%d-%H%M%S")

            out_anno = Path(join(base_path, self.tool_name, 'anno-mzMLs', f'{current_base}_{current_time}_annotated.mzML'))
            out_deconv = Path(join(base_path, self.tool_name, 'deconv-mzMLs', f'{current_base}_{current_time}_deconv.mzML'))

            uploaded_files.append(out_anno)
            uploaded_files.append(out_deconv)
            
            if  'deconv-mzMLs' not in st.session_state:
                st.session_state['deconv-mzMLs'] = []
            if  'anno-mzMLs' not in st.session_state:
                st.session_state['anno-mzMLs'] = []
            st.session_state['deconv-mzMLs'].append(out_deconv.name)
            st.session_state['anno-mzMLs'].append(out_anno.name)

        # make directory to store deconv and anno mzML files & initialize data storage
        postprocessingAfterUpload_FD(uploaded_files)

    def execution(self) -> None:
        # Get mzML input files from self.params.
        # Can be done without file manager, however, it ensures everything is correct.
        try:      
            in_mzMLs = self.file_manager.get_files(self.params["mzML-files"])
        except ValueError:
            st.error('Please select at least one mzML file.')  
            return
        
        # Make sure output directory exists
        base_path = dirname(self.workflow_dir)
        if not exists(join(base_path, 'FLASHDeconvOutput')):
            makedirs(join(base_path, 'FLASHDeconvOutput'))

        for in_mzML in in_mzMLs:
            # Get folder name
            file_name = splitext(basename(in_mzML))[0]
            current_time = time.strftime("%Y%m%d-%H%M%S")
            folder_path = join(base_path, 'FLASHDeconvOutput', '%s_%s'%(file_name, current_time))
            folder_path_anno = join(base_path, self.tool_name, 'anno-mzMLs')
            folder_path_deconv = join(base_path, self.tool_name, 'deconv-mzMLs')
            folder_path_tsv = join(base_path, self.tool_name, 'tsv-files')

            if exists(folder_path):
                rmtree(folder_path)
            makedirs(folder_path)
            if not exists(folder_path_anno):
                makedirs(folder_path_anno)
            if not exists(folder_path_deconv):
                makedirs(folder_path_deconv)
            if not exists(folder_path_tsv):
                makedirs(folder_path_tsv)
            
            out_tsv = join(folder_path, f'out.tsv')
            out_tsv_fdr = join(folder_path_tsv, f'{file_name}_{current_time}.tsv')
            out_spec1 = join(folder_path, f'spec1.tsv')
            out_spec2 = join(folder_path, f'spec2.tsv')
            out_spec3 = join(folder_path, f'spec3.tsv')
            out_spec4 = join(folder_path, f'spec4.tsv')
            out_mzml = join(folder_path, f'out_deconv.mzML')
            out_deconv_mzml_viewer = join(folder_path_deconv, f'{file_name}_{current_time}_deconv.mzML')
            out_quant = join(folder_path, f'quant.tsv')
            out_annotated_mzml = join(folder_path, f'anno_annotated.mzML')
            out_annotated_mzml_viewer = join(folder_path_anno, f'{file_name}_{current_time}_annotated.mzML')
            out_msalign1 = join(folder_path, f'toppic_ms1.msalign')
            out_msalign2 = join(folder_path, f'toppic_ms2.msalign')
            out_feature1 = join(folder_path, f'toppic_ms1.feature')
            out_feature2 = join(folder_path, f'toppic_ms2.feature')
            all_outputs = [
                out_tsv, out_spec1, out_spec2, out_spec3, out_spec4, 
                out_mzml, out_quant, out_annotated_mzml, out_msalign1,
                out_msalign2, out_feature1, out_feature2
            ]

            self.executor.run_topp(
                'FLASHDeconv',
                input_output={
                    'in' : [in_mzML],
                    'out' : [out_tsv],
                    'out_spec1' : [out_spec1],
                    'out_spec2' : [out_spec2],
                    'out_spec3' : [out_spec3],
                    'out_spec4' : [out_spec4],
                    'out_mzml' : [out_mzml],
                    'out_quant' : [out_quant],
                    'out_annotated_mzml' : [out_annotated_mzml],
                    'out_msalign1' : [out_msalign1],
                    'out_msalign2' : [out_msalign2],
                    'out_feature1' : [out_feature1],
                    'out_feature2' : [out_feature2],
                }
            )

            for file, target in zip(
                (out_mzml, out_annotated_mzml, out_tsv),
                (out_deconv_mzml_viewer, out_annotated_mzml_viewer, out_tsv_fdr)
            ):
                if not exists(file):
                    continue
                copyfile(file, target)
