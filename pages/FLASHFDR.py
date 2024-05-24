import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def ecdf(data):
    """Compute ECDF."""
    x = np.sort(data)
    y = np.arange(1, len(data) + 1) / len(data)
    return x, y

def generate_and_display_ecdf_plot(df):
    """Generate and display ECDF plot."""
    # Extract Qscore data
    target_qscores = df[df['TargetDecoyType'] == 0]['QScore']
    decoy_qscores = df[df['TargetDecoyType'] > 0]['QScore']

    # Generate and display the ECDF plot
    plt.figure(figsize=(10, 6))
    x_target, y_target = ecdf(target_qscores)
    x_decoy, y_decoy = ecdf(decoy_qscores)
    plt.plot(x_target, y_target, marker='.', linestyle='none', color='green', label='Target QScores')
    plt.plot(x_decoy, y_decoy, marker='.', linestyle='none', color='red', label='Decoy QScores')
    plt.xlabel('qScore')
    plt.ylabel('ECDF')
    plt.title('ECDF of QScore Distribution')
    plt.legend()
    st.pyplot(plt)

def main():
    st.title('ECDF Plot of QScore Distribution')

    if 'parsed_tsv_files' not in st.session_state or not st.session_state['parsed_tsv_files']:
        st.warning("No TSV files uploaded. Please upload TSV files first.")
        return

    tsv_files = list(st.session_state['parsed_tsv_files'].keys())
    tsv_file = st.selectbox("Select TSV file", tsv_files)

    if tsv_file:
        df = st.session_state['parsed_tsv_files'][tsv_file]
        generate_and_display_ecdf_plot(df)

if __name__ == "__main__":
    main()
