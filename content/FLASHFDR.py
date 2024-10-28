import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go

def ecdf(data):
    """Compute ECDF."""
    x = np.sort(data)
    y = np.arange(1, len(data) + 1) / len(data)
    return x, y

def generate_and_display_plots(df):
    """Generate and display ECDF and density plots."""
    # Extract Qscore data
    target_qscores = df[df['TargetDecoyType'] == 0]['Qscore']
    decoy_qscores = df[df['TargetDecoyType'] > 0]['Qscore']

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

def main():
    st.title('ECDF and Density Plot of QScore Distribution of Targets and Decoys')

    if 'parsed_tsv_files' not in st.session_state or not st.session_state['parsed_tsv_files']:
        st.warning("No TSV files uploaded. Please upload TSV files first.")
        return

    tsv_files = list(st.session_state['parsed_tsv_files'].keys())
    tsv_file = st.selectbox("Select TSV file", tsv_files)

    if tsv_file:
        df = st.session_state['parsed_tsv_files'][tsv_file]
        generate_and_display_plots(df)

if __name__ == "__main__":
    main()





