from pathlib import Path
import streamlit as st

from src.common.common import page_setup, v_space

page_setup(page="main")

st.markdown("# 👋 Quick Start")
st.markdown("## FLASHApp")


# main content
st.markdown('#### FLASHApp: A Platform for Your Favorite FLASH\* Tools!')

st.info("""
    **💡 How to run FLASHApp**
    1. Go to the **⚙️ Workflow** page through the sidebar and run your analysis.\
        OR, go to the **📁 File Upload** page through the sidebar and upload FLASHDeconv output files (\*_annotated.mzML & \*_deconv.mzML)
    2. Click the **👀 Viewer** page on the sidebar to view the results in detail.
    """)

if Path("OpenMS-App.zip").exists():
    st.subheader(
        """
Download the latest version for Windows here by clicking the button below.
"""
    )
    with open("OpenMS-App.zip", "rb") as file:
        st.download_button(
            label="Download for Windows",
            data=file,
            file_name="OpenMS-App.zip",
            mime="archive/zip",
            type="primary",
        )
    st.markdown(
        """
Extract the zip file and run the installer (.msi) file to install the app. The app can then be launched using the corresponding desktop icon.
"""
    )

c1, c2 = st.columns(2)
c1.markdown(
    """
## ⭐ New
       
- FLASHViewer is now FLASHApp
- Want to save your progress or share it with your team? Simply bookmark / share the URL!
"""
)
c2.image("assets/pyopenms_transparent_background.png", width=300)
