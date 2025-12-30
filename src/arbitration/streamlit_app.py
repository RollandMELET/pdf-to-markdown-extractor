"""
PDF-to-Markdown Extractor - Streamlit Arbitration Interface.

This is a minimal stub to enable docker-compose testing.
Full implementation in later features.
"""

import streamlit as st

st.set_page_config(
    page_title="PDF Extractor - Arbitration",
    page_icon="📄",
    layout="wide"
)

st.title("📄 PDF-to-Markdown Extractor")
st.subheader("Arbitration Interface")

st.info("🚧 Interface in development - Full implementation pending")

st.write("This interface will allow you to:")
st.write("- Review extraction divergences")
st.write("- Compare results from multiple extractors")
st.write("- Make manual corrections")
st.write("- Approve final markdown output")
