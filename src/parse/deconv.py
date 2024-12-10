import pandas as pd

from src.masstable import parseFLASHDeconvOutput

def parseDeconv(deconv_mzML, anno_mzML, out_tsv=None):

    # Parse input files
    deconv_df, anno_df, _, _, _ = parseFLASHDeconvOutput(anno_mzML, deconv_mzML)
    parsed_data = {
        'anno_dfs' : anno_df,
        'deconv_dfs' : deconv_df
    }

    # For the ECDF plot this additional piece of data is required
    if out_tsv is not None:
        df = pd.read_csv(out_tsv, sep='\t')
        if 'IsDecoy' in df.columns:
            parsed_data['parsed_tsv_files'] = df
        
    return parsed_data
