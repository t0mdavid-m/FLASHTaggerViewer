import pandas as pd
import numpy as np
import streamlit as st


@st.cache_data
def parseFLASHQuantOutput(quant_file, trace_file, resolution_file=None):
    quant_df = pd.read_csv(quant_file, delimiter='\t')
    trace_df = pd.read_csv(trace_file, delimiter='\t')

    res_df = None
    if resolution_file:
        res_df = pd.read_csv(resolution_file, delimiter='\t')

    # trim quant data
    quant_df = quant_df[['FeatureGroupIndex', 'MonoisotopicMass', 'AverageMass',
                         'StartRetentionTime(FWHM)', 'EndRetentionTime(FWHM)',
                         'HighestApexRetentionTime',
                         'FeatureGroupQuantity', 'AllAreaUnderTheCurve',
                         'MinCharge', 'MaxCharge', 'MostAbundantFeatureCharge',
                         'IsotopeCosineScore']]

    # counter = 0
    # for index, row in quant_df.iterrows():
    #     this_mass = row['MonoisotopicMass']
    #
    #     corresponding_traces = trace_df[trace_df['Mass'] == this_mass]
    #     if len(corresponding_traces) > 0:
    #         counter+=1
    # print('how many? ', counter, len(quant_df))

    return quant_df, trace_df, res_df


@st.cache_data
def connectTraceWithResult(quant_df, trace_df):
    charges, isotopes, centroidmzs, rts, mzs, intensities = [], [], [], [], [], []
    for index, row in quant_df.iterrows():
        traces = trace_df[trace_df['FeatureGroupID'] == row['FeatureGroupIndex']]
        charges.append(np.array(traces['Charge'], dtype='int'))
        isotopes.append(np.array(traces['IsotopeIndex'], dtype='int'))
        centroidmzs.append(np.array(traces['CentroidMz'], dtype='float'))
        rts.append(list(traces['RTs']))
        mzs.append(list(traces['MZs']))
        intensities.append(list(traces['Intensities']))
    collected_df = pd.DataFrame(zip(charges, isotopes, centroidmzs, rts, mzs, intensities),
                                columns=['Charges', 'IsotopeIndices', 'CentroidMzs', 'RTs', 'MZs', 'Intensities'])
    out_df = pd.concat([quant_df, collected_df], axis=1)
    return out_df
