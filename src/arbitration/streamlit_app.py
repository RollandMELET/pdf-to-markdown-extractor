"""
PDF-to-Markdown Extractor - Streamlit Arbitration Interface (Feature #88).

Human arbitration interface for resolving extraction divergences.
"""

import streamlit as st
from pathlib import Path

# Feature #88: Streamlit app skeleton with basic layout

st.set_page_config(
    page_title="PDF Extractor - Arbitration",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar
with st.sidebar:
    st.title("⚙️ Configuration")

    st.subheader("Extraction Settings")
    strategy = st.selectbox(
        "Strategy",
        ["fallback", "parallel_local", "parallel_all", "hybrid"],
        index=1,
    )

    similarity_threshold = st.slider(
        "Similarity Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.9,
        step=0.05,
    )

    st.subheader("Extractor Selection")
    use_docling = st.checkbox("Docling", value=True)
    use_mineru = st.checkbox("MinerU", value=False, disabled=True, help="Install MinerU to enable")

    st.divider()

    st.subheader("About")
    st.info(
        "**PDF-to-Markdown Extractor**\n\n"
        "Human arbitration interface for resolving extraction divergences."
    )

# Main area
st.title("📄 PDF-to-Markdown Extractor")
st.subheader("Arbitration Interface")

# Tabs for different sections
tab1, tab2, tab3 = st.tabs(["📤 Upload", "🔍 Review Divergences", "📊 Results"])

with tab1:
    st.header("Upload PDF Document")

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload a PDF document for extraction"
    )

    if uploaded_file:
        st.success(f"✅ File uploaded: {uploaded_file.name}")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")

        with col2:
            if st.button("🚀 Start Extraction", type="primary"):
                st.info("Extraction feature will be implemented in Phase 4")

with tab2:
    st.header("Review Extraction Divergences")

    st.info("🚧 Divergence review interface - Implementation pending")

    st.write("**Features:**")
    st.write("- Side-by-side comparison of extraction results")
    st.write("- Highlight divergences with similarity scores")
    st.write("- Manual selection of preferred content")
    st.write("- Real-time preview of merged document")

with tab3:
    st.header("Extraction Results")

    st.info("🚧 Results display - Implementation pending")

    st.write("**Will display:**")
    st.write("- Final merged markdown")
    st.write("- Extraction metadata (time, pages, confidence)")
    st.write("- Per-extractor statistics")
    st.write("- Download options (markdown, metadata.json)")

# Footer
st.divider()
st.caption("PDF-to-Markdown Extractor v1.0.0 | Built with Streamlit")
