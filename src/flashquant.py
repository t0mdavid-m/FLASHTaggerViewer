import pandas as pd
import streamlit as st


@st.cache_data
def parseFLASHQuantOutput(quant_file, trace_file):
    quant_df = pd.read_csv(quant_file, delimiter='\t')
    trace_df = pd.read_csv(trace_file, delimiter='\t')

    # trim quant data
    quant_df = quant_df[['FeatureGroupIndex', 'MonoisotopicMass', 'AverageMass',
                         'StartRetentionTime(FWHM)', 'EndRetentionTime(FWHM)',
                         'HighestApexRetentionTime',
                         'FeatureGroupQuantity', 'AllAreaUnderTheCurve',
                         'MinCharge', 'MaxCharge', 'MostAbundantFeatureCharge',
                         'IsotopeCosineScore']]

    return quant_df, trace_df


@st.cache_data
def connectTraceWithResult(quant_df, trace_df):
    charges, isotopes, centroidmzs, rts, mzs, intensities = [], [], [], [], [], []
    for index, row in quant_df.iterrows():
        traces = trace_df[trace_df['FeatureGroupID'] == row['FeatureGroupIndex']]
        charges.append(traces['Charge'])
        isotopes.append(traces['IsotopeIndex'])
        centroidmzs.append(traces['CentroidMz'])
        rts.append(traces['RTs'])
        mzs.append(traces['MZs'])
        intensities.append(traces['Intensities'])
    collected_df = pd.DataFrame(zip(charges, isotopes, centroidmzs, rts, mzs, intensities),
                                columns=['Charges', 'IsotopeIndices', 'CentroidMzs', 'RTs', 'MZs', 'Intensities'])
    out_df = pd.concat([quant_df, collected_df], axis=1)
    return out_df
