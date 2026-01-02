"""
PDF-to-Markdown Extractor - Streamlit Arbitration Interface (Features #88-96).

Human arbitration interface for resolving extraction divergences.
"""

import streamlit as st
from pathlib import Path
import json
import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
USE_REAL_API = os.getenv("USE_REAL_API", "false").lower() == "true"
IS_MOCK_MODE = not USE_REAL_API

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
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0
if 'user_jobs' not in st.session_state:
    st.session_state.user_jobs = []
if 'show_job_created_banner' not in st.session_state:
    st.session_state.show_job_created_banner = False
if 'latest_job_id' not in st.session_state:
    st.session_state.latest_job_id = None
if 'extraction_completed' not in st.session_state:
    st.session_state.extraction_completed = False
if 'uploaded_filename' not in st.session_state:
    st.session_state.uploaded_filename = None
if 'uploaded_size' not in st.session_state:
    st.session_state.uploaded_size = None
if 'uploaded_pdf_path' not in st.session_state:
    st.session_state.uploaded_pdf_path = None
if 'extraction_results' not in st.session_state:
    st.session_state.extraction_results = None
if 'job_pdf_paths' not in st.session_state:
    st.session_state.job_pdf_paths = {}  # Map job_id -> pdf_path
if 'job_extraction_results' not in st.session_state:
    st.session_state.job_extraction_results = {}  # Map job_id -> extraction_results

# Strategy descriptions with Mistral integration
STRATEGY_INFO = {
    "fallback": {
        "name": "Fallback (Sequential)",
        "extractors": ["Docling 🟢", "MinerU 🟢", "Mistral 🔵"],
        "mode": "Sequential (on failure)",
        "cost": "Free → ~$0.002/page si Mistral nécessaire",
        "best_for": "Documents simples, économique"
    },
    "parallel_local": {
        "name": "Parallel Local (Free)",
        "extractors": ["Docling 🟢", "MinerU 🟢"],
        "mode": "Parallèle (2 extracteurs)",
        "cost": "Gratuit",
        "best_for": "Complexité moyenne, validation qualité"
    },
    "parallel_all": {
        "name": "Parallel All (Max Accuracy)",
        "extractors": ["Docling 🟢", "MinerU 🟢", "Mistral 🔵"],
        "mode": "Parallèle (3 extracteurs)",
        "cost": "~$0.002/page",
        "best_for": "Documents complexes, précision maximale"
    },
    "hybrid": {
        "name": "Hybrid (Smart)",
        "extractors": ["Docling 🟢", "MinerU 🟢", "Mistral 🔵 (conditionnel)"],
        "mode": "Local first, Mistral si divergences",
        "cost": "Variable (généralement gratuit)",
        "best_for": "Workflows qualité-sensibles"
    }
}


def render_pdf_page_with_highlight(
    pdf_path: Path,
    page_num: int,
    divergence: Optional[Dict] = None,
    dpi: int = 150
) -> Optional[Any]:
    """
    Render PDF page avec highlighting optionnel des divergences.

    Args:
        pdf_path: Chemin vers le PDF
        page_num: Numéro de page (1-indexed pour affichage)
        divergence: Dict de divergence optionnel pour highlighting
        dpi: Résolution de rendu (150 = bon compromis)

    Returns:
        PIL Image ou None si échec
    """
    try:
        import fitz  # PyMuPDF
        from PIL import Image, ImageDraw

        doc = fitz.open(str(pdf_path))
        page_idx = page_num - 1  # fitz utilise 0-indexed

        if page_idx < 0 or page_idx >= len(doc):
            logger.warning(f"Page invalide: {page_num}")
            return None

        page = doc[page_idx]

        # Render en pixmap
        pix = page.get_pixmap(dpi=dpi)

        # Conversion PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Highlighting si divergence fournie
        if divergence:
            draw = ImageDraw.Draw(img, 'RGBA')

            # Recherche du texte divergent dans le PDF
            # Support both old format (content_a) and new format (contents dict)
            if 'contents' in divergence:
                # New format: get first extractor's content
                first_content = list(divergence['contents'].values())[0] if divergence['contents'] else ''
                search_text = first_content[:50]
            else:
                # Old format: use content_a
                search_text = divergence.get('content_a', '')[:50]

            if search_text:
                rects = page.search_for(search_text)

                if rects:
                    # Facteur d'échelle PDF → Image
                    scale = pix.width / page.rect.width

                    # Rectangles semi-transparents rouges
                    for rect in rects:
                        x0, y0, x1, y1 = rect
                        draw.rectangle(
                            [(x0*scale, y0*scale), (x1*scale, y1*scale)],
                            outline=(255, 0, 0, 255),  # Bordure rouge
                            fill=(255, 0, 0, 50),      # Remplissage rouge léger
                            width=3
                        )

        doc.close()
        return img

    except Exception as e:
        logger.error(f"Échec rendu PDF: {e}")
        return None


@st.cache_data
def _cached_pdf_render(pdf_path_str: str, page_num: int, dpi: int):
    """Cache des pages rendues pour éviter re-rendu."""
    return render_pdf_page_with_highlight(Path(pdf_path_str), page_num, None, dpi)


def adapt_divergences_to_ui(result_data):
    """
    Convertit les divergences backend en format UI pour affichage multi-extracteur.

    Args:
        result_data: Résultat de l'API avec divergences et all_results

    Returns:
        Liste de divergences au format UI
    """
    # Récupérer résultats par extracteur
    all_results = result_data.get('all_results', {})
    divergences_backend = result_data.get('divergences', [])

    if not all_results or not divergences_backend:
        return []

    ui_divergences = []

    # Convertir chaque divergence
    for div in divergences_backend:
        # Construire contents dict pour tous les extracteurs
        contents = {}
        confidences = {}

        # Extraire noms extracteurs depuis all_results
        extractor_names = list(all_results.keys())

        # Aligner les contenus
        # Note: Le backend compare par paires, on doit reconstruire pour N extracteurs
        # Simplification: utiliser content_a/b et mapper aux extracteurs
        if len(extractor_names) >= 2:
            contents[extractor_names[0]] = div.get('content_a', '')
            contents[extractor_names[1]] = div.get('content_b', '')

            # Si 3+ extracteurs, on a besoin du contenu du 3e
            # Dans le cas réel, il faudrait comparer 3 extractions
            if len(extractor_names) > 2:
                # Placeholder pour 3e extracteur
                contents[extractor_names[2]] = div.get('content_a', '')  # Temporary

        # Confidences depuis all_results
        for extractor_name, result in all_results.items():
            if isinstance(result, dict):
                confidences[extractor_name] = result.get('confidence_score', 0.5)
            else:
                confidences[extractor_name] = result.confidence_score if hasattr(result, 'confidence_score') else 0.5

        # Extracteur recommandé = plus haute confiance
        recommended = max(confidences, key=confidences.get) if confidences else extractor_names[0]

        # Format UI
        ui_div = {
            "id": div.get('id', f"div-{len(ui_divergences)}"),
            "type": div.get('type', 'text_mismatch'),
            "page": div.get('page', 1),
            "block_id": div.get('block_id', 'unknown'),
            "num_extractors": len(all_results),
            "contents": contents,
            "confidences": confidences,
            "recommended": recommended,
            "avg_similarity": div.get('similarity', 0.0),
            # Backward compatibility
            "content_a": div.get('content_a', ''),
            "content_b": div.get('content_b', ''),
            "similarity": div.get('similarity', 0.0),
        }

        ui_divergences.append(ui_div)

    return ui_divergences


# Sidebar
with st.sidebar:
    st.title("⚙️ Configuration")

    st.subheader("Extraction Settings")
    strategy = st.selectbox(
        "Extraction Strategy",
        list(STRATEGY_INFO.keys()),
        index=1,
        format_func=lambda x: STRATEGY_INFO[x]["name"]
    )

    with st.expander("📋 Détails de la stratégie", expanded=False):
        info = STRATEGY_INFO[strategy]
        st.write(f"**Extracteurs**: {', '.join(info['extractors'])}")
        st.write(f"**Mode**: {info['mode']}")
        st.write(f"**Coût**: {info['cost']}")
        st.write(f"**Idéal pour**: {info['best_for']}")

    similarity_threshold = st.slider(
        "Similarity Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.9,
        step=0.05,
    )

    # Check Mistral API key availability
    has_mistral_key = os.getenv("MISTRAL_API_KEY") is not None

    st.subheader("Extractor Selection")
    use_docling = st.checkbox("Docling", value=True)
    use_mineru = st.checkbox("MinerU", value=False, help="Install MinerU to enable")
    use_mistral = st.checkbox(
        "Mistral OCR API",
        value=False,
        disabled=not has_mistral_key,
        help=(
            "🔵 OCR basé sur vision models Mistral\n"
            f"Status: {'🟢 Disponible' if has_mistral_key else '🔴 Indisponible (définir MISTRAL_API_KEY)'}\n"
            "Coût: ~$0.002/page (~$2 pour 1000 pages)"
        )
    )

    # Validation stratégie vs sélection
    if use_mistral and strategy == "parallel_local":
        st.warning(
            "⚠️ Mistral est API-based mais 'parallel_local' n'utilise que les extracteurs locaux. "
            "Considérez 'parallel_all' pour inclure Mistral."
        )

    st.divider()

    st.subheader("About")
    st.info(
        "**PDF-to-Markdown Extractor**\n\n"
        "Human arbitration interface for resolving extraction divergences."
    )

# Main area
st.title("📄 PDF-to-Markdown Extractor")
st.subheader("Arbitration Interface")

# Banner global pour mode mock
if IS_MOCK_MODE:
    st.warning(
        "⚠️ **MODE DÉMONSTRATION** - Données fictives affichées. "
        "Définissez `USE_REAL_API=true` dans .env et démarrez les services pour l'extraction réelle.",
        icon="🎭"
    )

# Show job created banner if flag is set
if st.session_state.show_job_created_banner and st.session_state.latest_job_id:
    st.success(f"✅ **Nouveau job créé**: `{st.session_state.latest_job_id}` - Cliquez sur l'onglet **🔍 Review** pour commencer!")

    if st.button("❌ Fermer cette notification"):
        st.session_state.show_job_created_banner = False
        st.rerun()

# Feature #89: Jobs list page
tab1, tab2, tab3, tab4 = st.tabs(["📋 Jobs", "📤 Upload", "🔍 Review", "📊 Results"])

with tab1:
    st.header("Jobs Awaiting Arbitration")

    # Mock mode signaling
    if IS_MOCK_MODE:
        st.info("🎭 **Jobs de démonstration** - Liste de jobs fictifs pour tests UI", icon="ℹ️")

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

    # Merge with user-created jobs
    all_jobs = st.session_state.user_jobs + mock_jobs

    for job in all_jobs:
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
                    # Get PDF path from mapping (for user jobs) or use default (for mock jobs)
                    if job['job_id'] in st.session_state.job_pdf_paths:
                        st.session_state.current_pdf_path = st.session_state.job_pdf_paths[job['job_id']]
                    else:
                        st.session_state.current_pdf_path = f"/data/uploads/{job['filename']}"
                    st.success(f"✅ Job **{job['job_id']}** sélectionné!")
                    st.info("👆 Cliquez sur l'onglet **🔍 Review** en haut pour commencer l'arbitrage")

            st.divider()

with tab2:
    st.header("Upload PDF Document")

    # Mock mode signaling
    if IS_MOCK_MODE:
        st.warning(
            "⚠️ **Extraction simulée** - La progression est fictive. "
            "Pour extraction réelle, définissez `USE_REAL_API=true` et démarrez les services.",
            icon="🎭"
        )

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload a PDF document for extraction"
    )

    if uploaded_file:
        # Save file physically to temp directory
        import tempfile
        temp_dir = Path(tempfile.gettempdir()) / "pdf-extractor-uploads"
        temp_dir.mkdir(exist_ok=True)

        temp_pdf_path = temp_dir / uploaded_file.name

        # Write uploaded file to disk
        with open(temp_pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Save file info to session state for persistence
        st.session_state.uploaded_filename = uploaded_file.name
        st.session_state.uploaded_size = uploaded_file.size
        st.session_state.uploaded_pdf_path = str(temp_pdf_path)

        st.success(f"✅ File uploaded: {uploaded_file.name}")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")

        with col2:
            if st.button("🚀 Start Extraction", type="primary"):
                # Show extraction progress
                st.divider()

                # Get selected extractors from sidebar
                selected_extractors = []
                if use_docling:
                    selected_extractors.append("Docling")
                if use_mineru:
                    selected_extractors.append("MinerU")
                if use_mistral:
                    selected_extractors.append("Mistral")

                if not selected_extractors:
                    st.error("⚠️ Veuillez sélectionner au moins un extracteur dans la sidebar!")
                else:
                    st.info(f"**Stratégie**: {STRATEGY_INFO[strategy]['name']}")
                    st.info(f"**Extracteurs actifs**: {', '.join(selected_extractors)}")

                    # === EXTRACTION RÉELLE OU MOCK ===
                    if USE_REAL_API:
                        # Vraie extraction via API
                        try:
                            import httpx
                            from io import BytesIO

                            # Préparer le fichier - convertir en BytesIO
                            pdf_bytes = uploaded_file.getvalue()  # Get bytes directly
                            pdf_file = BytesIO(pdf_bytes)
                            pdf_file.name = uploaded_file.name

                            # Appel API réel
                            with st.spinner("📤 Upload vers l'API..."):
                                files = {"file": (uploaded_file.name, pdf_file, "application/pdf")}
                                data = {"strategy": strategy}

                                response = httpx.post(
                                    f"{API_BASE_URL}/api/v1/extract",
                                    files=files,
                                    data=data,
                                    timeout=30.0
                                )
                                response.raise_for_status()
                                job_data = response.json()
                                job_id = job_data["job_id"]

                            st.success(f"✅ Job créé: `{job_id}`")

                            # Polling pour progression
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            # Attendre un instant pour que le job soit enregistré
                            time.sleep(0.5)

                            max_wait = 300  # 5 minutes max
                            elapsed = 0

                            while elapsed < max_wait:
                                try:
                                    status_response = httpx.get(
                                        f"{API_BASE_URL}/api/v1/status/{job_id}",
                                        timeout=10.0
                                    )
                                    status_response.raise_for_status()
                                    status_data = status_response.json()
                                except httpx.HTTPStatusError as e:
                                    if e.response.status_code == 404:
                                        # Job pas encore dans le tracker, réessayer
                                        st.warning(f"⏳ Job en cours d'enregistrement... (tentative {elapsed//2 + 1})")
                                        time.sleep(2)
                                        elapsed += 2
                                        continue
                                    else:
                                        raise

                                job_status = status_data.get("status", "unknown")
                                progress = status_data.get("progress_percentage")

                                # Handle None or null progress
                                if progress is None:
                                    if job_status == "completed":
                                        progress = 100
                                    elif job_status == "extracting":
                                        progress = 50
                                    else:
                                        progress = 25

                                progress_bar.progress(int(progress))
                                status_text.text(f"📊 Status: {job_status} ({progress:.0f}%)")

                                if job_status == "completed":
                                    break
                                elif job_status == "failed":
                                    error_msg = status_data.get("metadata", {}).get("error", "Unknown error")
                                    st.error(f"❌ Extraction échouée: {error_msg}")
                                    st.stop()

                                time.sleep(2)
                                elapsed += 2

                            if elapsed >= max_wait:
                                st.error("⏱️ Timeout: L'extraction a pris trop de temps")
                                st.stop()

                            # Récupérer résultat final
                            result_response = httpx.get(f"{API_BASE_URL}/api/v1/result/{job_id}")
                            result_data = result_response.json()

                            # Stocker dans session state
                            st.session_state.extraction_completed = True
                            st.session_state.extraction_results = {
                                'job_id': job_id,
                                'strategy': strategy,
                                'extractors': selected_extractors,
                                'pages': result_data['result']['page_count'],
                                'divergences': len(result_data.get('divergences', [])),
                                'time': result_data['result']['extraction_time'],
                                'all_results': result_data.get('all_results', {}),
                            }

                            st.success("✅ **Extraction réelle terminée!**")

                        except httpx.HTTPError as e:
                            st.error(f"❌ Erreur API: {e}")
                            st.error("💡 Vérifiez que les services sont démarrés: FastAPI (port 8000), Redis, Celery")
                        except Exception as e:
                            st.error(f"❌ Erreur: {e}")

                    else:
                        # Mode mock: simulation
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        steps = [
                            ("📤 Upload du fichier vers le serveur...", 10),
                            ("📄 Analyse de la complexité du document...", 20),
                            ("🔍 Lancement de l'extraction...", 30),
                        ]

                        progress_per_extractor = 60 // len(selected_extractors)
                        current_progress = 30

                        for extractor in selected_extractors:
                            emoji = "🟢" if extractor != "Mistral" else "🔵"
                            steps.append((f"{emoji} Extraction avec {extractor}...", current_progress + progress_per_extractor))
                            current_progress += progress_per_extractor

                        steps.extend([
                            ("⚖️ Comparaison des résultats...", 95),
                            ("✅ Extraction terminée!", 100),
                        ])

                        for step_text, progress in steps:
                            status_text.text(step_text)
                            progress_bar.progress(progress)
                            time.sleep(0.8)

                        # Save mock results
                        st.session_state.extraction_completed = True
                        st.session_state.extraction_results = {
                            'strategy': STRATEGY_INFO[strategy]['name'],
                            'extractors': selected_extractors,
                            'pages': 7,
                            'divergences': 3,
                            'time': len(selected_extractors) * 2.5
                        }

    # Show extraction results if completed (persists after rerun)
    if st.session_state.extraction_completed and st.session_state.uploaded_filename:
        st.divider()
        st.success("✅ **Extraction terminée avec succès!**")

        # Show results summary
        results = st.session_state.extraction_results
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Pages extraites", results['pages'])
        with col_b:
            st.metric("Divergences détectées", results['divergences'])
        with col_c:
            st.metric("Temps d'extraction", f"{results['time']:.1f}s")

        # Action button (persists after rerun!)
        st.info("💡 **Étape suivante**: Créez le job et allez dans **🔍 Review**")

        if st.button("🔍 Créer Job & Aller à la Review", type="primary", use_container_width=True, key="create_job_btn"):
            # Create new job
            now = datetime.now()
            new_job = {
                "job_id": f"job-{now.strftime('%Y%m%d-%H%M%S')}",
                "filename": st.session_state.uploaded_filename,
                "status": "needs_review",
                "divergence_count": results['divergences'],
                "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }

            # Add to user jobs list
            st.session_state.user_jobs.insert(0, new_job)

            # Set as current job
            st.session_state.current_job_id = new_job["job_id"]
            st.session_state.current_pdf_path = st.session_state.uploaded_pdf_path

            # Save PDF path for this job
            st.session_state.job_pdf_paths[new_job["job_id"]] = st.session_state.uploaded_pdf_path

            # Map this job to its extraction results for Review tab
            if st.session_state.extraction_results and 'job_id' in st.session_state.extraction_results:
                st.session_state.job_extraction_results = st.session_state.job_extraction_results or {}
                st.session_state.job_extraction_results[new_job["job_id"]] = st.session_state.extraction_results

            # Reset upload state (but keep extraction results for Review)
            st.session_state.extraction_completed = False
            # Don't reset extraction_results yet - Review needs it!

            # Set banner flags
            st.session_state.show_job_created_banner = True
            st.session_state.latest_job_id = new_job["job_id"]

            # Refresh page to show banner
            st.rerun()

with tab3:
    st.header("Review Extraction Divergences")

    # Mock mode signaling
    if IS_MOCK_MODE:
        st.error(
            "🎭 **DONNÉES MOCKÉES** - Ces divergences sont fictives! "
            "Uploadez un PDF réel en mode production (`USE_REAL_API=true`) pour voir vos vraies divergences.",
            icon="⚠️"
        )

    # Feature #90: Comparison view
    if st.session_state.current_job_id:
        # Find job details
        job_info = None
        for job in st.session_state.user_jobs:
            if job['job_id'] == st.session_state.current_job_id:
                job_info = job
                break

        if job_info:
            st.success(f"✅ **Job actif**: {st.session_state.current_job_id} - {job_info['filename']}")
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.metric("Divergences à traiter", job_info['divergence_count'])
            with col_info2:
                st.metric("Créé le", job_info['created_at'])
        else:
            st.info(f"📋 **Job actif**: {st.session_state.current_job_id}")

        # === CHARGER DIVERGENCES RÉELLES OU MOCK ===
        divergences_list = []

        # Try to get extraction results for this job
        job_results = None
        if st.session_state.current_job_id in st.session_state.job_extraction_results:
            job_results = st.session_state.job_extraction_results[st.session_state.current_job_id]
        elif st.session_state.extraction_results:
            job_results = st.session_state.extraction_results

        if USE_REAL_API and job_results and 'job_id' in job_results:
            # Charger vraies divergences depuis l'API
            try:
                import httpx
                job_id = job_results['job_id']

                result_response = httpx.get(f"{API_BASE_URL}/api/v1/result/{job_id}")
                result_data = result_response.json()

                # Adapter divergences au format UI
                divergences_list = adapt_divergences_to_ui(result_data)

                if not divergences_list or len(divergences_list) == 0:
                    st.success("✅ **Aucune divergence détectée!** Toutes les extractions sont cohérentes.")
                    st.info("Les extracteurs sont d'accord sur tout le contenu. Pas besoin d'arbitrage!")
                    st.balloons()
                    # Force None pour ne pas afficher les mock
                    divergences_list = None

            except Exception as e:
                st.error(f"❌ Erreur chargement divergences: {e}")
                divergences_list = None

        else:
            # Mode mock: données fictives avec variations visibles
            divergences_list = [
                {
                    "id": "div-1",
                    "type": "text_mismatch",
                    "page": 1,
                    "block_id": "para-2",
                    "num_extractors": 3,
                    "contents": {
                        "mistral": "This is a simple text-only PDF document created for testing PDF extraction functionality.",
                        "docling": "This is a simple text-only PDF document created for testing extraction capabilities.",
                        "mineru": "This is a simple PDF document created for testing extraction functionality."
                    },
                    "confidences": {"docling": 0.89, "mineru": 0.75, "mistral": 0.92},
                    "recommended": "mistral",
                    "avg_similarity": 0.85,
                    "content_a": "This is a simple text-only PDF document created for testing PDF extraction functionality.",
                    "content_b": "This is a simple PDF document created for testing extraction functionality.",
                    "similarity": 0.75,
                },
                {
                    "id": "div-2",
                    "type": "text_mismatch",
                    "page": 1,
                    "block_id": "para-3",
                    "num_extractors": 3,
                    "contents": {
                        "mistral": "It contains multiple paragraphs with standard formatting and no complex elements.",
                        "docling": "It contains multiple paragraphs with standard formatting and no complex elements.",
                        "mineru": "Contains multiple paragraphs with standard formatting."
                    },
                    "confidences": {"docling": 0.93, "mineru": 0.71, "mistral": 0.94},
                    "recommended": "mistral",
                    "avg_similarity": 0.91,
                    "content_a": "It contains multiple paragraphs with standard formatting and no complex elements.",
                    "content_b": "Contains multiple paragraphs with standard formatting.",
                    "similarity": 0.88,
                },
                {
                    "id": "div-3",
                    "type": "text_mismatch",
                    "page": 1,
                    "block_id": "para-4",
                    "num_extractors": 3,
                    "contents": {
                        "mistral": "The purpose of this document is to verify that basic text extraction works correctly.",
                        "docling": "The purpose is to verify that basic text extraction works correctly.",
                        "mineru": "Purpose: verify text extraction works correctly."
                    },
                    "confidences": {"docling": 0.90, "mineru": 0.68, "mistral": 0.93},
                    "recommended": "mistral",
                    "avg_similarity": 0.80,
                    "content_a": "The purpose of this document is to verify that basic text extraction works correctly.",
                    "content_b": "Purpose: verify text extraction works correctly.",
                    "similarity": 0.72,
                }
            ]

        # Si divergences disponibles, afficher
        if divergences_list:
            current_index = st.session_state.current_divergence_index
            mock_divergence = divergences_list[current_index % len(divergences_list)]

            # Feature #90: Dynamic comparison with 3+ extractors support
            st.subheader(f"Divergence #{st.session_state.current_divergence_index + 1}")
            st.write(f"**Type:** {mock_divergence['type']}")
            st.write(f"**Page:** {mock_divergence['page']}")

            # Use multi-extractor data if available, fallback to 2-extractor
            if 'num_extractors' in mock_divergence and mock_divergence['num_extractors'] > 2:
                # Multi-extractor layout with confidence scoring
                st.write(f"**Similarité moyenne:** {mock_divergence['avg_similarity']:.1%}")

                # Sort extractors by confidence (descending)
                sorted_extractors = sorted(
                    mock_divergence['confidences'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )

                num_extractors = len(sorted_extractors)
                recommended = mock_divergence['recommended']

                # Show recommendation
                st.success(
                    f"🏆 **Recommandé**: {recommended.title()} "
                    f"(Confiance: {mock_divergence['confidences'][recommended]:.1%})"
                )

                # Dynamic columns for extractors
                cols = st.columns(num_extractors)

                for idx, (extractor_name, confidence) in enumerate(sorted_extractors):
                    with cols[idx]:
                        # Medal for top 3
                        medals = {0: "🥇", 1: "🥈", 2: "🥉"}
                        medal = medals.get(idx, "")

                        is_recommended = (extractor_name == recommended)

                        # Header
                        st.markdown(f"### {medal} {extractor_name.title()}")
                        if is_recommended:
                            st.markdown("⭐ **RECOMMANDÉ**")

                        # Confidence metric
                        st.metric("Confiance", f"{confidence:.1%}")

                        # Content display
                        content = mock_divergence['contents'][extractor_name]
                        st.text_area(
                            "Contenu",
                            value=content,
                            height=120,
                            disabled=True,
                            key=f"content_{extractor_name}_{mock_divergence['id']}"
                        )

                        # Choice button
                        button_type = "primary" if is_recommended else "secondary"
                        button_label = f"✓ Utiliser {extractor_name.title()}"

                        if st.button(
                            button_label,
                            type=button_type,
                            use_container_width=True,
                            key=f"choose_{extractor_name}_{mock_divergence['id']}"
                        ):
                            st.session_state.arbitration_choices[mock_divergence['id']] = {
                                'choice': extractor_name,
                                'content': content,
                                'confidence': confidence
                            }
                            st.success(f"Choix sauvegardé: {extractor_name}")
                            st.rerun()

                # Manual edit button
                st.divider()
                if st.button("✏️ Éditer Manuellement", use_container_width=True):
                    st.session_state.show_editor = True

            else:
                # Backward compatibility: 2-extractor layout
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

                # Choice buttons
                st.subheader("Choose Content")

                choice_col1, choice_col2, choice_col3 = st.columns(3)

                with choice_col1:
                    if st.button("✅ Use A (Docling)", type="primary", use_container_width=True):
                        st.session_state.arbitration_choices[mock_divergence['id']] = {
                            'choice': 'A',
                            'content': mock_divergence['content_a']
                        }
                        st.success("Choice saved: Using extraction A")

                with choice_col2:
                    if st.button("✅ Use B (MinerU)", type="primary", use_container_width=True):
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
                    value=mock_divergence.get('content_a', list(mock_divergence['contents'].values())[0] if mock_divergence.get('contents') else ''),
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

            # Feature #93: PDF preview with highlighting
            st.divider()
            st.subheader("📄 Référence PDF")

            # Get PDF path from session state
            pdf_path = st.session_state.get('current_pdf_path')

            if pdf_path and Path(pdf_path).exists():
                st.info(f"**PDF Original - Page {mock_divergence['page']}**")

                # Render PDF page with highlighting
                img = render_pdf_page_with_highlight(
                    Path(pdf_path),
                    page_num=mock_divergence['page'],
                    divergence=mock_divergence
                )

                if img:
                    st.image(img, caption=f"Page {mock_divergence['page']}")
                else:
                    st.error("Échec rendu PDF")
            else:
                st.warning("Aperçu PDF indisponible (fichier non chargé)")
                st.write(f"Afficherait: Page {mock_divergence['page']} avec highlighting")

            # Navigation
            st.divider()
            nav_col1, nav_col2, nav_col3 = st.columns(3)

            with nav_col1:
                if st.button("⬅️ Previous Divergence"):
                    st.session_state.current_divergence_index = max(0, st.session_state.current_divergence_index - 1)

            with nav_col2:
                st.write(f"Divergence {st.session_state.current_divergence_index + 1} / {len(divergences_list)}")

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

    # Mock mode signaling
    if IS_MOCK_MODE:
        st.info("🎭 **Résultats de démonstration** - Exemple de format de sortie", icon="ℹ️")

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
