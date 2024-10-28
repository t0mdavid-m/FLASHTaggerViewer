import streamlit as st
import multiprocessing
import json
import sys
import time
from .workflow.WorkflowManager import WorkflowManager

from os.path import join, splitext, basename, exists, dirname
from os import makedirs
from shutil import copyfile, rmtree


DEFAULT_THREADS = 8

class TagWorkflow(WorkflowManager):

    def __init__(self) -> None:
        # Initialize the parent class with the workflow name.
        super().__init__("FLASHTnT", st.session_state["workspace"])
        self.tool_name = 'FLASHTaggerViewer'


    def upload(self)-> None:
        t = st.tabs(["MS data", "Database"])
        with t[0]:
            example_data = ['example-data/flashtagger/example_spectrum_%d.mzML' % n for n in [1, 2]]
            self.ui.upload_widget(key="mzML-files", name="MS data", file_type="mzML", fallback=example_data)
        with t[1]:
            self.ui.upload_widget(key="fasta-file", name="Database", file_type="fasta", enable_directory=False,
                                  fallback='example-data/flashtagger/example_database.fasta')


    @st.fragment
    def configure(self) -> None:
        # Input File Selection
        self.ui.select_input_file("mzML-files", multiple=True)
        self.ui.select_input_file("fasta-file", multiple=False)

        # Number of threads cannot be selected in online mode
        if 'local' in sys.argv:
            self.ui.input_widget(
                'threads', name='threads', default=multiprocessing.cpu_count(),
                help='The number of threads that should be used to run the tools.'
            )

        # Decoy database size toggle
        self.ui.input_widget(
            'few_proteins', name='Do you expect <100 Proteins?', widget_type='checkbox', default=True,
            help='If set, the decoy database will be 10 times larger than the target database for better FDR estimation resolution. This increases the runtime significantly.'
        )

        # Create tabs for different analysis steps
        t = st.tabs(
            ["**FLASHDeconv**", "**FLASHTnT**"]
        )
        with t[0]:
            # FLASHDeconv Configuration
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
            # FLASHTnT Configuration
            self.ui.input_TOPP('FLASHTnT', display_subsections=True)


    def execution(self) -> None:
        # Get input files
        try:      
            in_mzmls = self.file_manager.get_files(self.params["mzML-files"])
        except ValueError:
            st.error('Please select at least one mzML file.')  
            return
        try: 
            database = self.file_manager.get_files(self.params["fasta-file"])
        except ValueError:
            st.error('Please select a database.')  
            return
        
        # Make sure output directory exists
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
        
        # Set number of threads
        if 'threads' in self.executor.parameter_manager.get_parameters_from_json():
            threads = self.executor.parameter_manager.get_parameters_from_json()['threads']
        else:
            threads = DEFAULT_THREADS

        # Process files in sequence
        for in_mzml in in_mzmls:
            
            # Generate output folder
            current_base = splitext(basename(in_mzml))[0]
            current_time = time.strftime("%Y%m%d-%H%M%S")
            folder_path = join(base_path, 'FLASHTaggerOutput', '%s_%s'%(current_base, current_time))
            if exists(folder_path):
                rmtree(folder_path)
            makedirs(folder_path)

            # Define output paths for viewer
            out_db = join(base_path, self.tool_name, 'db-fasta', f'{current_base}_{current_time}_db.fasta')
            out_anno = join(base_path, self.tool_name, 'anno-mzMLs', f'{current_base}_{current_time}_annotated.mzML')
            out_deconv = join(base_path, self.tool_name, 'deconv-mzMLs', f'{current_base}_{current_time}_deconv.mzML')
            out_tag = join(base_path, self.tool_name, 'tags-tsv', f'{current_base}_{current_time}_tagged.tsv')
            out_protein = join(base_path, self.tool_name, 'proteins-tsv', f'{current_base}_{current_time}_protein.tsv')

            # Additional outputs are directly written to download folder
            out_tsv = join(folder_path, f'out.tsv')
            out_spec1 = join(folder_path, f'spec1.tsv')
            out_spec2 = join(folder_path, f'spec2.tsv')
            out_spec3 = join(folder_path, f'spec3.tsv')
            out_spec4 = join(folder_path, f'spec4.tsv')
            out_quant = join(folder_path, f'quant.tsv')
            out_msalign1 = join(folder_path, f'toppic_ms1.msalign')
            out_msalign2 = join(folder_path, f'toppic_ms2.msalign')
            out_feature1 = join(folder_path, f'toppic_ms1.feature')
            out_feature2 = join(folder_path, f'toppic_ms2.feature')
            out_prsm = join(folder_path, f'prsms.tsv')

            # Check if a decoy database needs to be generated
            tagger_params = self.executor.parameter_manager.get_parameters_from_json()['FLASHTnT']
            if ((tagger_params.get('tnt:prsm_fdr', 1) < 1) or (tagger_params.get('tnt:pro_fdr', 1) < 1)):
                # If few proteins are present increase decoy size
                if self.executor.parameter_manager.get_parameters_from_json()['few_proteins']:
                    ratio = 10
                else:
                    ratio = 1

                # Run decoy database
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
                # If no decoy database is needed the database file is copied as is
                copyfile(database[0], out_db)
            
            # Run FLASHDeconv (1/2)
            self.executor.run_topp(
                'FLASHDeconv',
                input_output={
                    'in' : [in_mzml],
                    'out' : [out_tsv],
                    'out_spec1' : [out_spec1],
                    'out_spec2' : [out_spec2],
                    'out_spec3' : [out_spec3],
                    'out_spec4' : [out_spec4],
                    'out_mzml' : [out_deconv],
                    'out_quant' : [out_quant],
                    'out_annotated_mzml' : [out_anno],
                    'out_msalign1' : [out_msalign1],
                    'out_msalign2' : [out_msalign2],
                    'out_feature1' : [out_feature1],
                    'out_feature2' : [out_feature2],
                },
                params_manual = {
                    'threads' : threads
                }
            )

            # Run FLASHTnT (2/2)
            self.executor.run_topp(
                'FLASHTnT',
                input_output={
                    'in' : [out_deconv],
                    'fasta' : [out_db],
                    'out_tag' :  [out_tag],
                    'out_pro' :  [out_protein],
                    'out_prsm' : [out_prsm]
                },
                params_manual = {
                    'threads' : threads
                }
            )

            # Copy generated files to output
            copyfile(out_db, join(folder_path, 'database.fasta'))
            copyfile(out_anno, join(folder_path, 'annotated.mzML'))
            copyfile(out_deconv, join(folder_path, 'out.mzML'))
            copyfile(out_tag, join(folder_path, 'tags.tsv'))
            copyfile(out_protein, join(folder_path, 'proteins.tsv'))
            
            # Store settings
            for tool in ['FLASHDeconv', 'FLASHTnT']:
                with open(join(folder_path, f'settings_{tool}.json'), 'w') as f:
                    json.dump(
                        self.executor.parameter_manager.get_parameters_from_json()[tool], f,
                        indent='\t'
                    )



class DeconvWorkflow(WorkflowManager):

    def __init__(self) -> None:
        # Initialize the parent class with the workflow name.
        super().__init__("FLASHDeconv", st.session_state["workspace"])
        self.tool_name = 'FLASHDeconvViewer'


    def upload(self)-> None:
        self.ui.upload_widget(key="mzML-files", name="MS data", file_type="mzML",
                              fallback=['example-data/flashdeconv/example_fd.mzML'])


    def configure(self) -> None:
        # Input File Selection
        self.ui.select_input_file("mzML-files", multiple=True)

        # Number of threads cannot be selected in online mode
        if 'local' in sys.argv:
            self.ui.input_widget(
                'threads', name='threads', default=multiprocessing.cpu_count(),
                help='The number of threads that should be used to run the tools.'
            )


        # FLASHDeconv Configuration
        self.ui.input_TOPP(
            'FLASHDeconv', exclude_parameters = ['ida_log'], display_subsections=True
        )


    def execution(self) -> None:
        # Get input files
        try:      
            in_mzmls = self.file_manager.get_files(self.params["mzML-files"])
        except ValueError:
            st.error('Please select at least one mzML file.')  
            return
        
        # Make sure output directory exists
        base_path = dirname(self.workflow_dir)
        if not exists(join(base_path, self.tool_name, 'anno-mzMLs')):
            makedirs(join(base_path, self.tool_name, 'anno-mzMLs'))
        if not exists(join(base_path, self.tool_name, 'deconv-mzMLs')):
            makedirs(join(base_path, self.tool_name, 'deconv-mzMLs'))
        if not exists(join(base_path, self.tool_name, 'tsv-files')):
            makedirs(join(base_path, self.tool_name, 'tsv-files'))

        # Set number of threads
        if 'threads' in self.executor.parameter_manager.get_parameters_from_json():
            threads = self.executor.parameter_manager.get_parameters_from_json()['threads']
        else:
            threads = DEFAULT_THREADS

        # Process files in sequence
        for in_mzml in in_mzmls:

            # Generate output folder
            current_base = splitext(basename(in_mzml))[0]
            current_time = time.strftime("%Y%m%d-%H%M%S")
            folder_path = join(base_path, 'FLASHDeconvOutput', '%s_%s'%(current_base, current_time))
            if exists(folder_path):
                rmtree(folder_path)
            makedirs(folder_path)

            # Define output paths for viewer
            out_tsv = join(base_path, self.tool_name, 'tsv-files', f'{current_base}_{current_time}.tsv')
            out_deconv = join(base_path, self.tool_name, 'deconv-mzMLs', f'{current_base}_{current_time}_deconv.mzML')
            out_anno = join(base_path, self.tool_name, 'anno-mzMLs', f'{current_base}_{current_time}_annotated.mzML')

            # Additional outputs are directly written to download folder
            out_spec1 = join(folder_path, f'spec1.tsv')
            out_spec2 = join(folder_path, f'spec2.tsv')
            out_spec3 = join(folder_path, f'spec3.tsv')
            out_spec4 = join(folder_path, f'spec4.tsv')
            out_quant = join(folder_path, f'quant.tsv')
            out_msalign1 = join(folder_path, f'toppic_ms1.msalign')
            out_msalign2 = join(folder_path, f'toppic_ms2.msalign')
            out_feature1 = join(folder_path, f'toppic_ms1.feature')
            out_feature2 = join(folder_path, f'toppic_ms2.feature')

            # Run FLASHDeconv
            self.executor.run_topp(
                'FLASHDeconv',
                input_output={
                    'in' : [in_mzml],
                    'out' : [out_tsv],
                    'out_spec1' : [out_spec1],
                    'out_spec2' : [out_spec2],
                    'out_spec3' : [out_spec3],
                    'out_spec4' : [out_spec4],
                    'out_mzml' : [out_deconv],
                    'out_quant' : [out_quant],
                    'out_annotated_mzml' : [out_anno],
                    'out_msalign1' : [out_msalign1],
                    'out_msalign2' : [out_msalign2],
                    'out_feature1' : [out_feature1],
                    'out_feature2' : [out_feature2],
                },
                params_manual = {
                    'threads' : threads
                }
            )

            # Copy generated files to output            
            copyfile(out_deconv, join(folder_path, f'out_deconv.mzML'))
            copyfile(out_anno, join(folder_path, f'anno_annotated.mzML'))
            copyfile(out_tsv, join(folder_path, f'out.tsv'))
            
            # Store settings
            with open(join(folder_path, f'settings_FLASHDeconv.json'), 'w') as f:
                json.dump(
                    self.executor.parameter_manager.get_parameters_from_json()['FLASHDeconv'], f,
                    indent='\t'
                )
