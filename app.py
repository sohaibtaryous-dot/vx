"""
app.py — Packing List Extractor Pro
Application Streamlit : upload PDF → extraction → rapport par client → export PDF paysage.

Lancement :
    streamlit run app.py
    ou double-cliquer sur lancer_windows.bat
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime

import streamlit as st

from export_engine import (
    calculate_summary,
    generate_pdf_bytes,
    group_by_client,
    parse_pdf,
    parse_pdf_pages,
)
from ui import (
    inject_css,
    render_header,
    render_instructions,
    render_results,
)

# ─────────────────────────────────────────────────────────────
#  CONFIGURATION PAGE
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Packing List Extractor Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "Packing List Extractor Pro — Extraction automatique PDF",
    },
)

inject_css()

# ─────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────

if "results"      not in st.session_state:
    st.session_state.results = []
if "grouped"      not in st.session_state:
    st.session_state.grouped = {}
if "pdf_bytes"    not in st.session_state:
    st.session_state.pdf_bytes = None
if "processed"    not in st.session_state:
    st.session_state.processed = False

# ─────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────

render_header()

# ─────────────────────────────────────────────────────────────
#  SIDEBAR — OPTIONS
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Options")

    st.markdown("### Client par défaut")
    default_client = st.text_input(
        "Nom si non détecté",
        value="CLIENT NON IDENTIFIÉ",
        help="Utilisé si le nom du client ne peut pas être extrait du PDF.",
    )

    st.markdown("---")
    st.markdown("### À propos")
    st.caption(
        "**Packing List Extractor Pro**\n\n"
        "Extrait automatiquement :\n"
        "- N° BL / PKL\n"
        "- Client / Destinataire\n"
        "- Date\n"
        "- Bultos (colis)\n"
        "- Poids Brut (KG)\n"
        "- Poids Net (KG)\n"
        "- Importe HT\n"
        "- Devise\n\n"
        "Génère un rapport PDF paysage avec totaux par client et total général."
    )

    if st.session_state.processed:
        st.markdown("---")
        if st.button("🗑 Nouveau rapport", use_container_width=True):
            st.session_state.results   = []
            st.session_state.grouped   = {}
            st.session_state.pdf_bytes = None
            st.session_state.processed = False
            st.rerun()

# ─────────────────────────────────────────────────────────────
#  ZONE D'UPLOAD
# ─────────────────────────────────────────────────────────────

if not st.session_state.processed:
    render_instructions()

    uploaded = st.file_uploader(
        "📂 Déposer vos PDF Packing Lists ici (ou cliquer pour sélectionner)",
        type=["pdf"],
        accept_multiple_files=True,
        help="Formats acceptés : PDF uniquement. Taille max : 100 MB.",
        label_visibility="visible",
    )

    col1, col2, col3 = st.columns([2, 1, 3])

    with col1:
        extract_btn = st.button(
            "🔍 Extraire & Analyser",
            type="primary",
            disabled=not bool(uploaded),
            use_container_width=True,
        )

    if uploaded:
        st.caption(f"📄 {len(uploaded)} fichier(s) sélectionné(s) — "
                   f"{sum(f.size for f in uploaded) / 1024:.0f} KB total")

    # ── TRAITEMENT ─────────────────────────────────────────
    if extract_btn and uploaded:
        results: list[dict] = []
        progress_bar = st.progress(0, text="Initialisation…")

        tmp_dir = tempfile.mkdtemp()

        for i, f in enumerate(uploaded):
            progress_bar.progress(
                (i + 1) / len(uploaded),
                text=f"Extraction : {f.name}",
            )
            tmp_path = os.path.join(tmp_dir, f.name)
            with open(tmp_path, "wb") as fh:
                fh.write(f.read())

            page_records = parse_pdf_pages(tmp_path, filename=f.name)

            for record in page_records:
                # Appliquer le client par défaut si non détecté
                if record["client"] == "CLIENT NON IDENTIFIÉ" and default_client.strip():
                    record["client"] = default_client.strip()
                results.append(record)

        # Nettoyage temp
        for fname in os.listdir(tmp_dir):
            try:
                os.unlink(os.path.join(tmp_dir, fname))
            except OSError:
                pass
        try:
            os.rmdir(tmp_dir)
        except OSError:
            pass

        progress_bar.progress(1.0, text="✅ Extraction terminée !")

        # Stocker en session
        st.session_state.results   = results
        st.session_state.grouped   = dict(group_by_client(results))
        st.session_state.pdf_bytes = None
        st.session_state.processed = True

        st.rerun()

# ─────────────────────────────────────────────────────────────
#  AFFICHAGE RÉSULTATS
# ─────────────────────────────────────────────────────────────

if st.session_state.processed and st.session_state.results:
    results = st.session_state.results
    grouped = st.session_state.grouped

    # ── Résultats ──────────────────────────────────────────
    render_results(results, grouped)

    st.markdown("---")

    # ── Bouton export PDF ──────────────────────────────────
    col_dl, col_new, _ = st.columns([2, 1.5, 3])

    with col_dl:
        # Générer le PDF si pas encore fait
        if st.session_state.pdf_bytes is None:
            with st.spinner("Génération du rapport PDF…"):
                try:
                    st.session_state.pdf_bytes = generate_pdf_bytes(grouped)
                except Exception as exc:
                    st.error(f"❌ Erreur génération PDF : {exc}")

        if st.session_state.pdf_bytes:
            filename = f"Rapport_PL_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            st.download_button(
                label="📄 Télécharger le Rapport PDF (Paysage)",
                data=st.session_state.pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )

    with col_new:
        if st.button("↩ Nouveau rapport", use_container_width=True):
            st.session_state.results   = []
            st.session_state.grouped   = {}
            st.session_state.pdf_bytes = None
            st.session_state.processed = False
            st.rerun()
