import streamlit as st
from pathlib import Path

# Set the page title
st.title("📖 User Guide")

# Define paths
md_file = Path("content", "USER_GUIDE.md")
image_folder = Path("static", "Images")

# Read the User Guide Markdown file
if md_file.exists():
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.readlines()  # Read as list to process line by line
else:
    st.error(f"🚨 Error: Could not find {md_file}")
    content = []

# Process Markdown content and replace image references
for line in content:
    if line.strip().startswith("!["):
        # Extract image filename from Markdown
        start = line.find("(") + 1
        end = line.find(")")
        image_name = line[start:end].split("/")[-1]  # Get only the filename

        # Construct full image path
        image_path = image_folder / image_name

        if image_path.exists():
            st.image(str(image_path), caption=image_name, use_container_width=True)
        else:
            st.warning(f"⚠️ Missing image: {image_name}")
    else:
        st.markdown(line)  # Render normal markdown text






