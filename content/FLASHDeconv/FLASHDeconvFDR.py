import streamlit as st
import plotly.express as px
import numpy as np
import plotly.graph_objects as go

from pathlib import Path

from src.workflow.FileManager import FileManager


def ecdf(data):
    """Compute ECDF."""
    x = np.sort(data)
    y = np.arange(1, len(data) + 1) / len(data)
    return x, y

def generate_and_display_plots(df):
    """Generate and display ECDF and density plots."""
    # Extract Qscore data
    target_qscores = df[df['IsDecoy'] == 0]['Qscore']
    decoy_qscores = df[df['IsDecoy'] > 0]['Qscore']

    # Generate ECDF data
    x_target, y_target = ecdf(target_qscores)
    x_decoy, y_decoy = ecdf(decoy_qscores)

    # Create ECDF Plotly figure
    fig_ecdf = px.line(title='ECDF of QScore Distribution')
    fig_ecdf.add_scatter(x=x_target, y=y_target, mode='markers', name='Target QScores', marker=dict(color='green'))
    fig_ecdf.add_scatter(x=x_decoy, y=y_decoy, mode='markers', name='Decoy QScores', marker=dict(color='red'))
    fig_ecdf.update_layout(
        xaxis_title='qScore',
        yaxis_title='ECDF',
        legend_title='QScore Type'
    )

    # Create Density Plotly figure without area fill
    fig_density = go.Figure()
    fig_density.add_trace(go.Histogram(x=target_qscores, histnorm='density', name='Targets', opacity=0.75, marker_color='green'))
    fig_density.add_trace(go.Histogram(x=decoy_qscores, histnorm='density', name='Decoys', opacity=0.75, marker_color='red'))
    fig_density.update_traces(opacity=0.75)
    fig_density.update_layout(
        title='Density Plot of QScore Distribution',
        xaxis_title='qScore',
        yaxis_title='Density',
        barmode='overlay',
        legend_title='QScore Type'
    )

    # Display plots
    st.plotly_chart(fig_ecdf)
    st.plotly_chart(fig_density)

st.title('ECDF and Density Plot of QScore Distribution of Targets and Decoys')

# Get available results
file_manager = FileManager(
    st.session_state["workspace"],
    Path(st.session_state['workspace'], 'flashdeconv', 'cache')
)
experiments = file_manager.get_results_list(['parsed_tsv_files'])

if len(experiments) == 0:
    st.warning("No TSV files uploaded. Please upload TSV files first.")
    st.stop()

experiment = st.selectbox("Select TSV file", experiments)

if experiment:
    df = file_manager.get_results(
        experiment, ['parsed_tsv_files']
    )['parsed_tsv_files']
    generate_and_display_plots(df)




