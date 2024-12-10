from src.masstable import parseFLASHDeconvOutput, parseFLASHTaggerOutput


def parseTnT(deconv_mzML, anno_mzML, tag_tsv, protein_tsv):
    deconv_df, anno_df, tolerance, _, _,  = parseFLASHDeconvOutput(
        anno_mzML, deconv_mzML
    )
    tag_df, protein_df = parseFLASHTaggerOutput(tag_tsv, protein_tsv)

    # Add tolerance as a new columnn, wasteful but gets the job done..
    deconv_df['tol'] = tolerance
    
    return {
        'anno_dfs' : anno_df,
        'deconv_dfs' : deconv_df,
        'tag_dfs' : tag_df,
        'protein_dfs' : protein_df
    }
