"""
Main page for the OpenMS Template App.

This module sets up and displays the Streamlit app for the OpenMS Template App.
It includes:
- Setting the app title.
- Displaying a description.
- Providing a download button for the Windows version of the app.

Usage:
Run this script to launch the OpenMS Template App.

Note:
- If run in local mode, the CAPTCHA control is not applied.
- If not in local mode, CAPTCHA control is applied to verify the user.

Returns:
    None
"""

import sys
import streamlit as st
from pathlib import Path
from src.captcha_ import captcha_control
from src.common import page_setup, save_params
#added for FDR
import random


def create_dummy_fdr_data():
    # Create some dummy q-score data for testing
    target_qscores = [random.uniform(0, 1) for _ in range(100)]
    decoy_qscores = [random.uniform(0, 1) for _ in range(80)]

    # Store the data in session state for Vue component access
    st.session_state['fdr_data'] = {
        'target_qscores': target_qscores,
        'decoy_qscores': decoy_qscores
    }



def onToolChange():
    # Check if the tool has been set before
    if 'changed_tool_name' not in st.session_state:
        return

    # Save parameter - changed_tool_name is bound to the checkbox and
    # will be deleted after rerun
    st.session_state.current_tool_name = st.session_state.changed_tool_name

    # Only rerender the page if the sidebar has changed
    if ('changed_tool_name' in st.session_state) and (st.session_state.prev_tool_name != st.session_state.current_tool_name):
        st.session_state.prev_tool_name = st.session_state.current_tool_name
        st.rerun()  # reload the page to sync the change


def main():
    """
    Display main page content.
    """

    tools = ['FLASHDeconv', 'FLASHTnT', 'FLASHQuant']
    tool_indices = {t : i for i, t in enumerate(tools)}

    # sidebar to toggle between tools
    if 'current_tool_name' not in st.session_state:
        st.session_state.changed_tool_name = 'FLASHDeconv'
        st.session_state.current_tool_name = 'FLASHDeconv'
        st.session_state.prev_tool_name = 'FLASHDeconv'
        st.rerun()


    # Call the dummy data function
    create_dummy_fdr_data()

    # main content
    st.markdown('#### FLASHViewer visualizes outputs from FLASH\* tools.')

    st.info("""
        **💡 How to run FLASHViewer**
        1. Go to the **⚙️ Workflow** page through the sidebar and run your analysis.\
            OR, go to the **📁 File Upload** page through the sidebar and upload FLASHDeconv output files (\*_annotated.mzML & \*_deconv.mzML)
        2. Click the **👀 Viewer** page on the sidebar to view the results in detail.
            
            **\***Download of results is supported.only for FLASHDeconv
        """)

    # when entered into other page, key is resetting (emptied) - thus set the value with index
    st.selectbox("Choose a tool", tools, index=tool_indices[st.session_state.current_tool_name],
                 on_change=onToolChange(), key='changed_tool_name')


    if Path("OpenMS-App.zip").exists():
        st.text("")
        st.text("")
        st.markdown("""
        Download the latest version for Windows by clicking the button below.
        """)
        with open("OpenMS-App.zip", "rb") as file:
            st.download_button(
                label="Download for Windows",
                data=file,
                file_name="OpenMS-App.zip",
                mime="archive/zip",
                type="primary",
            )
            
    save_params(params)



if __name__ == '__main__':

    params = page_setup(page="main")

    # Check if the script is run in local mode (e.g., "streamlit run app.py local")
    if "local" in sys.argv:

        # In local mode, run the main function without applying captcha
        main()

    # If not in local mode, assume it's hosted/online mode
    else:
        if ("controllo" not in st.session_state) or (st.session_state["controllo"] is False):
            # Apply captcha control to verify the user
            captcha_control()
        else:
            # Run the main function
            main()
