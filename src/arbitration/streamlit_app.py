"""
PDF-to-Markdown Extractor - Streamlit Arbitration Interface (Features #88-96).

Human arbitration interface for resolving extraction divergences.
"""

import streamlit as st
from pathlib import Path
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# Feature #88: Streamlit app skeleton with basic layout
# Feature #89: Jobs list page
# Feature #90: Comparison view for divergences
# Feature #91: Choice buttons (A, B, Edit)
# Feature #92: Manual editor
# Feature #93: PDF preview
# Feature #94: Arbitration persistence
# Feature #95: Apply arbitration choices
# Feature #96: Complete arbitration flow

st.set_page_config(
    page_title="PDF Extractor - Arbitration",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if 'current_job_id' not in st.session_state:
    st.session_state.current_job_id = None
if 'arbitration_choices' not in st.session_state:
    st.session_state.arbitration_choices = {}
if 'current_divergence_index' not in st.session_state:
    st.session_state.current_divergence_index = 0

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
    use_mineru = st.checkbox("MinerU", value=False, help="Install MinerU to enable")

    st.divider()

    st.subheader("About")
    st.info(
        "**PDF-to-Markdown Extractor**\n\n"
        "Human arbitration interface for resolving extraction divergences."
    )

# Main area
st.title("📄 PDF-to-Markdown Extractor")
st.subheader("Arbitration Interface")

# Feature #89: Jobs list page
tab1, tab2, tab3, tab4 = st.tabs(["📋 Jobs", "📤 Upload", "🔍 Review", "📊 Results"])

with tab1:
    st.header("Jobs Awaiting Arbitration")

    # Feature #89: Show jobs list
    st.info("**Jobs requiring human review**")

    # Mock jobs for demonstration
    mock_jobs = [
        {
            "job_id": "job-001",
            "filename": "technical_report.pdf",
            "status": "needs_review",
            "divergence_count": 7,
            "created_at": "2025-12-30 14:30:00"
        },
        {
            "job_id": "job-002",
            "filename": "research_paper.pdf",
            "status": "needs_review",
            "divergence_count": 12,
            "created_at": "2025-12-30 15:45:00"
        },
    ]

    for job in mock_jobs:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

            with col1:
                st.write(f"**{job['filename']}**")

            with col2:
                st.write(f"🔍 {job['divergence_count']} divergences")

            with col3:
                st.write(f"⏰ {job['created_at']}")

            with col4:
                if st.button("Review", key=f"review_{job['job_id']}"):
                    st.session_state.current_job_id = job['job_id']
                    st.rerun()

            st.divider()

with tab2:
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
                st.info("Extraction will be triggered via API (Feature #101)")

with tab3:
    st.header("Review Extraction Divergences")

    # Feature #90: Comparison view
    if st.session_state.current_job_id:
        st.info(f"Reviewing job: **{st.session_state.current_job_id}**")

        # Mock divergence data
        mock_divergence = {
            "id": "div-1",
            "type": "text_mismatch",
            "page": 3,
            "block_id": "para-5",
            "content_a": "Machine learning algorithms require careful tuning of hyperparameters.",
            "content_b": "Machine learning methods need precise hyperparameter optimization.",
            "similarity": 0.75,
        }

        # Feature #90: Side-by-side comparison
        st.subheader(f"Divergence #{st.session_state.current_divergence_index + 1}")
        st.write(f"**Type:** {mock_divergence['type']}")
        st.write(f"**Page:** {mock_divergence['page']}")
        st.write(f"**Similarity:** {mock_divergence['similarity']:.1%}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🅰️ Extraction A (Docling)")
            st.text_area(
                "Content A",
                value=mock_divergence['content_a'],
                height=150,
                key="content_a",
                disabled=True
            )

        with col2:
            st.markdown("### 🅱️ Extraction B (MinerU)")
            st.text_area(
                "Content B",
                value=mock_divergence['content_b'],
                height=150,
                key="content_b",
                disabled=True
            )

        # Feature #91: Choice buttons
        st.subheader("Choose Content")

        choice_col1, choice_col2, choice_col3 = st.columns(3)

        with choice_col1:
            if st.button("✅ Use A (Docling)", type="primary", use_container_width=True):
                # Feature #94: Save choice
                st.session_state.arbitration_choices[mock_divergence['id']] = {
                    'choice': 'A',
                    'content': mock_divergence['content_a']
                }
                st.success("Choice saved: Using extraction A")

        with choice_col2:
            if st.button("✅ Use B (MinerU)", type="primary", use_container_width=True):
                # Feature #94: Save choice
                st.session_state.arbitration_choices[mock_divergence['id']] = {
                    'choice': 'B',
                    'content': mock_divergence['content_b']
                }
                st.success("Choice saved: Using extraction B")

        with choice_col3:
            if st.button("✏️ Edit Manually", use_container_width=True):
                st.session_state.show_editor = True

        # Feature #92: Manual editor
        if st.session_state.get('show_editor', False):
            st.subheader("Manual Edit")
            edited_content = st.text_area(
                "Edit content manually",
                value=mock_divergence['content_a'],
                height=200,
                key="manual_edit"
            )

            if st.button("💾 Save Edited Version"):
                # Feature #94: Save manual edit
                st.session_state.arbitration_choices[mock_divergence['id']] = {
                    'choice': 'manual',
                    'content': edited_content
                }
                st.success("Manual edit saved")
                st.session_state.show_editor = False

        # Feature #93: PDF preview
        st.divider()
        st.subheader("📄 PDF Reference")
        st.info(f"**Original PDF - Page {mock_divergence['page']}**")
        st.write("PDF preview would be displayed here (Feature #93)")
        # PDF preview requires pdf2image or similar library

        # Navigation
        st.divider()
        nav_col1, nav_col2, nav_col3 = st.columns(3)

        with nav_col1:
            if st.button("⬅️ Previous Divergence"):
                st.session_state.current_divergence_index = max(0, st.session_state.current_divergence_index - 1)

        with nav_col2:
            st.write(f"Divergence {st.session_state.current_divergence_index + 1} / 7")

        with nav_col3:
            if st.button("Next Divergence ➡️"):
                st.session_state.current_divergence_index += 1

        # Feature #96: Complete arbitration flow
        st.divider()
        if st.button("✅ Complete Review & Finalize", type="primary", use_container_width=True):
            # Feature #95: Apply arbitration choices
            st.success(f"✅ Arbitration complete! {len(st.session_state.arbitration_choices)} choices saved")
            st.info("Job status updated: needs_review → completed (Feature #96)")
            # In real implementation, would call API to apply choices

    else:
        st.info("Select a job from the **Jobs** tab to begin review")

with tab4:
    st.header("Extraction Results")

    if st.session_state.current_job_id:
        st.subheader(f"Results for {st.session_state.current_job_id}")

        # Mock result display
        st.markdown("### Final Merged Markdown")
        st.code("""
# Technical Report

Machine learning algorithms require careful tuning of hyperparameters.

## Results

Performance metrics:
- Accuracy: 94.7%
- F1-Score: 92.0%
""", language="markdown")

        st.divider()

        # Metadata display
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Extraction Time", "45.2s")

        with col2:
            st.metric("Confidence", "94.5%")

        with col3:
            st.metric("Pages", "25")

        # Download options
        st.subheader("📥 Download")

        download_col1, download_col2 = st.columns(2)

        with download_col1:
            st.download_button(
                "📄 Download Markdown",
                "# Merged content...",
                file_name="result.md",
                mime="text/markdown"
            )

        with download_col2:
            st.download_button(
                "📊 Download Metadata",
                json.dumps({"confidence": 0.945}, indent=2),
                file_name="metadata.json",
                mime="application/json"
            )

    else:
        st.info("Select a job to view results")

# Footer
st.divider()
st.caption("PDF-to-Markdown Extractor v1.0.0 | Built with Streamlit")
