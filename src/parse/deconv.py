import pandas as pd

from src.masstable import parseFLASHDeconvOutput

def parseDeconv(out_deconv_mzML, anno_annotated_mzML, spec1_tsv=None, spec2_tsv=None):

    # Parse input files
    deconv_df, anno_df, _, _, _ = parseFLASHDeconvOutput(anno_annotated_mzML, out_deconv_mzML)
    parsed_data = {
        'anno_dfs' : anno_df,
        'deconv_dfs' : deconv_df
    }

    # For the ECDF plot this additional piece of data is required
    if spec1_tsv is not None:
        df = pd.read_csv(spec1_tsv, sep='\t')
        if 'TargetDecoyType' in df.columns:
            parsed_data['parsed_tsv_file_ms1'] = df
    if spec2_tsv is not None:
        df = pd.read_csv(spec2_tsv, sep='\t')
        if 'TargetDecoyType' in df.columns:
            parsed_data['parsed_tsv_file_ms2'] = df
        
    return parsed_data
