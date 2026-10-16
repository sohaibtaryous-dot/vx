"""
ui.py
Interface Streamlit professionnelle — animations 3D, glassmorphism, effets visuels premium.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

import streamlit as st

from export_engine import calculate_summary, fmt_num


# ─────────────────────────────────────────────────────────────
#  CSS GLOBAL + ANIMATIONS 3D
# ─────────────────────────────────────────────────────────────

def inject_css() -> None:
    st.markdown(
        """
<style>
/* ══════════════════════════════════════════════════════════
   VARIABLES & RESET
══════════════════════════════════════════════════════════ */
:root {
  --pri:    #0d2137;
  --sec:    #1a5fa8;
  --acc:    #f0a500;
  --acc2:   #e74c3c;
  --ok:     #00c896;
  --bg:     #070e1a;
  --card:   rgba(255,255,255,0.05);
  --glass:  rgba(255,255,255,0.08);
  --bdr:    rgba(255,255,255,0.12);
  --txt:    #e8f0fe;
  --txt2:   #8faabe;
  --gt-bg:  rgba(240,165,0,0.12);
  --gt-b:   #f0a500;
  --shadow: 0 8px 32px rgba(0,0,0,0.5);
  --glow:   0 0 30px rgba(26,95,168,0.4);
}

/* ── Layout ── */
.stApp { background: var(--bg) !important; }
.block-container {
  max-width: 1500px !important;
  padding: 1.5rem 2rem !important;
}
header[data-testid="stHeader"] {
  background: rgba(7,14,26,0.95) !important;
  backdrop-filter: blur(20px) !important;
  border-bottom: 1px solid var(--bdr) !important;
}

/* ══════════════════════════════════════════════════════════
   KEYFRAMES
══════════════════════════════════════════════════════════ */
@keyframes fadeInUp {
  from { opacity:0; transform: translateY(30px); }
  to   { opacity:1; transform: translateY(0);    }
}
@keyframes fadeInLeft {
  from { opacity:0; transform: translateX(-40px); }
  to   { opacity:1; transform: translateX(0);     }
}
@keyframes slideInRight {
  from { opacity:0; transform: translateX(40px); }
  to   { opacity:1; transform: translateX(0);    }
}
@keyframes gradientShift {
  0%   { background-position: 0%   50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0%   50%; }
}
@keyframes float {
  0%,100% { transform: translateY(0px) rotate(0deg);   }
  33%     { transform: translateY(-12px) rotate(2deg);  }
  66%     { transform: translateY(-6px) rotate(-1deg);  }
}
@keyframes pulse3d {
  0%,100% { box-shadow: 0 0 0 0 rgba(26,95,168,0); transform: translateZ(0); }
  50%     { box-shadow: 0 0 25px 6px rgba(26,95,168,0.35); transform: translateZ(8px); }
}
@keyframes shimmer {
  0%   { background-position: -200% center; }
  100% { background-position:  200% center; }
}
@keyframes countUp {
  from { opacity:0; transform:scale(0.7) translateY(10px); }
  to   { opacity:1; transform:scale(1)   translateY(0);    }
}
@keyframes glowPulse {
  0%,100% { filter: drop-shadow(0 0 6px rgba(240,165,0,0.3)); }
  50%     { filter: drop-shadow(0 0 18px rgba(240,165,0,0.8)); }
}
@keyframes rotateBorder {
  0%   { --angle: 0deg; }
  100% { --angle: 360deg; }
}
@keyframes particleFloat {
  0%,100% { transform: translateY(0)   translateX(0)   opacity:0.6; }
  50%     { transform: translateY(-25px) translateX(8px) opacity:1; }
}
@keyframes scanLine {
  0%   { top: -2px; }
  100% { top: 100%; }
}
@keyframes spinGlow {
  0%   { transform: rotate(0deg);   box-shadow: 0 0 15px var(--sec); }
  100% { transform: rotate(360deg); box-shadow: 0 0 35px var(--acc); }
}

/* ══════════════════════════════════════════════════════════
   HERO BANNER — 3D + PARTICULES
══════════════════════════════════════════════════════════ */
.hero-wrap {
  position: relative;
  overflow: hidden;
  border-radius: 20px;
  margin-bottom: 2rem;
}
.hero-banner {
  position: relative;
  background: linear-gradient(135deg,
    #0d1b2a 0%, #1a3a5c 30%, #1a5fa8 60%, #0d2137 100%);
  background-size: 300% 300%;
  animation: gradientShift 8s ease infinite;
  border-radius: 20px;
  padding: 2.5rem 3rem;
  overflow: hidden;
  border: 1px solid rgba(26,95,168,0.4);
  box-shadow: 0 20px 60px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.1);
}
.hero-banner::before {
  content: '';
  position: absolute;
  top: -50%; left: -50%;
  width: 200%; height: 200%;
  background: radial-gradient(ellipse at center,
    rgba(26,95,168,0.15) 0%, transparent 70%);
  animation: float 6s ease-in-out infinite;
  pointer-events: none;
}
/* Scan line effect */
.hero-banner::after {
  content: '';
  position: absolute;
  left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(26,95,168,0.6), transparent);
  animation: scanLine 4s linear infinite;
  pointer-events: none;
}
/* Floating orbs */
.hero-orb {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  filter: blur(40px);
}
.hero-orb-1 {
  width: 200px; height: 200px;
  background: rgba(26,95,168,0.25);
  top: -60px; right: 80px;
  animation: float 7s ease-in-out infinite;
}
.hero-orb-2 {
  width: 120px; height: 120px;
  background: rgba(240,165,0,0.15);
  bottom: -30px; right: 300px;
  animation: float 5s ease-in-out infinite reverse;
}
.hero-orb-3 {
  width: 80px; height: 80px;
  background: rgba(0,200,150,0.12);
  top: 20px; left: 40%;
  animation: float 9s ease-in-out infinite 2s;
}
.hero-content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 2rem;
  animation: fadeInLeft 0.8s cubic-bezier(.22,1,.36,1) both;
}
.hero-icon-wrap {
  position: relative;
  width: 72px; height: 72px;
  flex-shrink: 0;
}
.hero-icon-wrap::before {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, var(--acc), var(--sec), var(--acc));
  animation: spinGlow 3s linear infinite;
}
.hero-icon {
  position: relative;
  width: 72px; height: 72px;
  background: rgba(13,33,55,0.9);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  z-index: 1;
}
.hero-title {
  font-size: 1.9rem;
  font-weight: 800;
  color: #fff;
  letter-spacing: -0.02em;
  background: linear-gradient(90deg, #fff 0%, #7eb8f7 50%, var(--acc) 100%);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shimmer 4s linear infinite;
  margin-bottom: 0.4rem;
}
.hero-sub {
  font-size: 0.92rem;
  color: rgba(255,255,255,0.6);
  max-width: 600px;
  line-height: 1.6;
}
.hero-badges {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.8rem;
  flex-wrap: wrap;
}
.hero-badge {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  color: rgba(255,255,255,0.75);
  padding: 0.2rem 0.7rem;
  border-radius: 20px;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

/* ══════════════════════════════════════════════════════════
   STAT CARDS — GLASSMORPHISM 3D
══════════════════════════════════════════════════════════ */
.stats-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 1rem;
  margin: 1.5rem 0;
  perspective: 1200px;
}
.stat-card {
  background: var(--glass);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: 16px;
  padding: 1.4rem 1rem;
  text-align: center;
  border: 1px solid var(--bdr);
  box-shadow: var(--shadow), inset 0 1px 0 rgba(255,255,255,0.08);
  cursor: default;
  transition: transform 0.35s cubic-bezier(.22,1,.36,1),
              box-shadow 0.35s ease,
              border-color 0.3s ease;
  transform-style: preserve-3d;
  animation: fadeInUp 0.6s ease both;
  position: relative;
  overflow: hidden;
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 100%; height: 100%;
  background: linear-gradient(90deg,
    transparent, rgba(255,255,255,0.06), transparent);
  transition: left 0.5s ease;
}
.stat-card:hover::before { left: 100%; }
.stat-card:hover {
  transform: translateY(-8px) rotateX(6deg) rotateY(-2deg) translateZ(10px);
  box-shadow: 0 24px 60px rgba(0,0,0,0.6),
              0 0 30px rgba(26,95,168,0.3),
              inset 0 1px 0 rgba(255,255,255,0.15);
  border-color: rgba(26,95,168,0.6);
}
.stat-card:nth-child(1) { animation-delay: 0.05s; }
.stat-card:nth-child(2) { animation-delay: 0.10s; }
.stat-card:nth-child(3) { animation-delay: 0.15s; }
.stat-card:nth-child(4) { animation-delay: 0.20s; }
.stat-card:nth-child(5) { animation-delay: 0.25s; }
.stat-card:nth-child(6) { animation-delay: 0.30s; }

.stat-icon {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  animation: float 4s ease-in-out infinite;
}
.stat-v {
  font-size: 1.7rem;
  font-weight: 800;
  color: #fff;
  display: block;
  letter-spacing: -0.02em;
  animation: countUp 0.8s cubic-bezier(.22,1,.36,1) both;
  text-shadow: 0 0 20px rgba(26,95,168,0.5);
}
.stat-l {
  font-size: 0.68rem;
  color: var(--txt2);
  text-transform: uppercase;
  letter-spacing: .08em;
  margin-top: 0.2rem;
  display: block;
}
.stat-card.accent .stat-v { color: var(--acc); text-shadow: 0 0 20px rgba(240,165,0,0.4); }
.stat-card.ok    .stat-v { color: var(--ok);  text-shadow: 0 0 20px rgba(0,200,150,0.4); }

/* ══════════════════════════════════════════════════════════
   SECTION DIVIDER
══════════════════════════════════════════════════════════ */
.section-title {
  color: var(--txt2);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .12em;
  margin: 2rem 0 1rem;
  display: flex;
  align-items: center;
  gap: 0.6rem;
}
.section-title::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, var(--bdr), transparent);
}
.section-divider {
  border: none;
  border-top: 1px solid var(--bdr);
  margin: 1.5rem 0;
}

/* ══════════════════════════════════════════════════════════
   CLIENT SECTION — 3D CARD
══════════════════════════════════════════════════════════ */
.client-section {
  margin-bottom: 2rem;
  animation: fadeInLeft 0.7s cubic-bezier(.22,1,.36,1) both;
  transform-style: preserve-3d;
}
.client-section:nth-child(even) {
  animation-name: slideInRight;
}
.client-header {
  background: linear-gradient(135deg, var(--sec) 0%, #0d3a6e 100%);
  color: white;
  padding: 0.9rem 1.4rem;
  border-radius: 14px 14px 0 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 700;
  font-size: 0.92rem;
  border: 1px solid rgba(26,95,168,0.5);
  border-bottom: none;
  position: relative;
  overflow: hidden;
}
.client-header::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(90deg,
    transparent 0%, rgba(255,255,255,0.05) 50%, transparent 100%);
  background-size: 200% 100%;
  animation: shimmer 3s linear infinite;
}
.client-header-text {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 0.6rem;
}
.client-icon {
  width: 32px; height: 32px;
  background: rgba(255,255,255,0.15);
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}
.client-badge {
  position: relative;
  z-index: 1;
  background: rgba(255,255,255,0.15);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.72rem;
  font-weight: 700;
  border: 1px solid rgba(255,255,255,0.2);
  backdrop-filter: blur(4px);
}

/* ── Tableau ── */
.rt-wrap {
  background: var(--glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 0 0 14px 14px;
  overflow: hidden;
  box-shadow: var(--shadow);
  border: 1px solid var(--bdr);
  border-top: none;
  overflow-x: auto;
}
table.rt {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
}
table.rt thead th {
  background: rgba(13,33,55,0.8);
  padding: 0.75rem 1rem;
  text-align: left;
  font-size: 0.71rem;
  font-weight: 700;
  color: var(--txt2);
  border-bottom: 1px solid var(--bdr);
  text-transform: uppercase;
  letter-spacing: .06em;
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 10;
}
table.rt thead th.r { text-align: right; }
table.rt tbody td {
  padding: 0.65rem 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  vertical-align: middle;
  color: var(--txt);
  transition: background 0.2s ease;
}
table.rt tbody td.r {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
}
table.rt tbody tr {
  transition: all 0.2s ease;
  transform-style: preserve-3d;
}
table.rt tbody tr:hover td {
  background: rgba(26,95,168,0.12) !important;
}
table.rt tbody tr:hover {
  transform: translateX(3px);
  box-shadow: inset 3px 0 0 var(--sec);
}
table.rt tbody tr:nth-child(even) td { background: rgba(255,255,255,0.02); }

/* ── Total destinataire ── */
table.rt .tr-total td {
  background: rgba(26,95,168,0.18) !important;
  font-weight: 700;
  border-top: 1px solid rgba(26,95,168,0.4);
  border-bottom: 1px solid rgba(26,95,168,0.2);
  color: #7eb8f7;
}
table.rt .tr-total:hover td {
  background: rgba(26,95,168,0.28) !important;
}

/* ══════════════════════════════════════════════════════════
   TOTAL GÉNÉRAL — GLOW
══════════════════════════════════════════════════════════ */
.grand-total-section {
  margin-top: 1rem;
  animation: fadeInUp 0.9s ease both;
  animation-delay: 0.3s;
}
.grand-total-header {
  background: linear-gradient(135deg,
    rgba(240,165,0,0.2) 0%, rgba(240,80,0,0.15) 100%);
  border: 1px solid rgba(240,165,0,0.4);
  color: var(--acc);
  padding: 0.9rem 1.4rem;
  border-radius: 14px 14px 0 0;
  font-weight: 800;
  font-size: 0.95rem;
  letter-spacing: 0.02em;
  position: relative;
  overflow: hidden;
  animation: glowPulse 3s ease-in-out infinite;
}
.grand-total-header::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(90deg,
    transparent, rgba(240,165,0,0.08), transparent);
  background-size: 200% 100%;
  animation: shimmer 2.5s linear infinite;
}
table.rt .tr-grand td {
  background: rgba(240,165,0,0.08) !important;
  font-weight: 800;
  border-top: 1px solid rgba(240,165,0,0.3);
  color: var(--acc);
  font-size: 0.88rem;
}
table.rt .tr-grand:hover td {
  background: rgba(240,165,0,0.14) !important;
}

/* ══════════════════════════════════════════════════════════
   BADGES & CHIPS
══════════════════════════════════════════════════════════ */
.cbadge {
  display: inline-block;
  padding: 0.1rem 0.45rem;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
  background: rgba(26,95,168,0.2);
  color: #7eb8f7;
  border: 1px solid rgba(26,95,168,0.3);
  margin-left: 4px;
  letter-spacing: 0.04em;
}
.warn-chip {
  display: inline-block;
  background: rgba(240,165,0,0.12);
  color: var(--acc);
  border: 1px solid rgba(240,165,0,0.3);
  border-radius: 6px;
  padding: 0.1rem 0.5rem;
  font-size: 0.7rem;
  font-weight: 600;
  margin: 1px 2px;
}
.err-chip {
  background: rgba(231,76,60,0.12);
  color: #ff7675;
  border-color: rgba(231,76,60,0.3);
}

/* ══════════════════════════════════════════════════════════
   BOUTONS STREAMLIT
══════════════════════════════════════════════════════════ */
div[data-testid="stDownloadButton"] button,
div[data-testid="stButton"] > button[kind="primary"] {
  border-radius: 10px !important;
  font-weight: 700 !important;
  background: linear-gradient(135deg, var(--sec), #0d3a6e) !important;
  border: 1px solid rgba(26,95,168,0.5) !important;
  box-shadow: 0 4px 20px rgba(26,95,168,0.3) !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}
div[data-testid="stDownloadButton"] button:hover,
div[data-testid="stButton"] > button[kind="primary"]:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 30px rgba(26,95,168,0.5) !important;
}

/* ══════════════════════════════════════════════════════════
   INSTRUCTIONS
══════════════════════════════════════════════════════════ */
.instructions-box {
  background: var(--glass);
  backdrop-filter: blur(12px);
  border-radius: 14px;
  padding: 1.4rem 1.8rem;
  border: 1px solid var(--bdr);
  border-left: 3px solid var(--sec);
  margin-bottom: 1.2rem;
  animation: fadeInLeft 0.7s ease both;
}
.instructions-box strong { color: #7eb8f7; }
.instructions-box ol {
  margin: 0.6rem 0 0 1.2rem;
  color: var(--txt2);
  font-size: 0.88rem;
  line-height: 2;
}
.instructions-box li::marker { color: var(--sec); }

/* ══════════════════════════════════════════════════════════
   SCROLLBAR CUSTOM
══════════════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
::-webkit-scrollbar-thumb {
  background: rgba(26,95,168,0.4);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(26,95,168,0.7); }

/* ══════════════════════════════════════════════════════════
   UPLOADER STREAMLIT
══════════════════════════════════════════════════════════ */
[data-testid="stFileUploader"] {
  border: 1px solid var(--bdr) !important;
  border-radius: 14px !important;
  background: var(--glass) !important;
  backdrop-filter: blur(8px) !important;
  transition: border-color 0.3s ease !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: rgba(26,95,168,0.5) !important;
  box-shadow: 0 0 20px rgba(26,95,168,0.15) !important;
}
[data-testid="stFileUploader"] * { color: var(--txt) !important; }

/* Sidebar */
[data-testid="stSidebar"] {
  background: rgba(7,14,26,0.95) !important;
  border-right: 1px solid var(--bdr) !important;
}
[data-testid="stSidebar"] * { color: var(--txt) !important; }
</style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
#  ENTÊTE HERO
# ─────────────────────────────────────────────────────────────

def render_header() -> None:
    st.markdown(
        """
<div class="hero-wrap">
  <div class="hero-banner">
    <div class="hero-orb hero-orb-1"></div>
    <div class="hero-orb hero-orb-2"></div>
    <div class="hero-orb hero-orb-3"></div>
    <div class="hero-content">
      <div class="hero-icon-wrap">
        <div class="hero-icon">📦</div>
      </div>
      <div>
        <div class="hero-title">Packing List Extractor Pro</div>
        <div class="hero-sub">
          Importez vos PDF Packing Lists — extraction automatique, regroupement par destinataire,
          rapport bordereau PDF paysage avec total unidades.
        </div>
        <div class="hero-badges">
          <span class="hero-badge">⚡ Multi-PDF</span>
          <span class="hero-badge">🎯 Extraction IA</span>
          <span class="hero-badge">📊 Rapport PDF A4</span>
          <span class="hero-badge">🌍 Format GOA</span>
        </div>
      </div>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
#  CARTES DE STATISTIQUES
# ─────────────────────────────────────────────────────────────

def render_stat_cards(summary: dict) -> None:
    imp_str = " / ".join(
        f"{fmt_num(v)} {k}"
        for k, v in summary.get("total_importe_by_currency", {}).items()
    ) or "—"

    n_pls     = summary.get("total_files", summary.get("total_pls", 0))
    n_clients = summary.get("total_clients", 0)
    bultos    = summary.get("total_bultos", 0)
    pb        = summary.get("total_pb", 0.0)
    pn        = summary.get("total_pn", 0.0)
    unidades  = summary.get("total_unidades", 0.0)

    st.markdown(
        f"""
<div class="stats-row">
  <div class="stat-card">
    <div class="stat-icon">📂</div>
    <span class="stat-v">{n_pls}</span>
    <span class="stat-l">PDF traités</span>
  </div>
  <div class="stat-card">
    <div class="stat-icon">👤</div>
    <span class="stat-v">{n_clients}</span>
    <span class="stat-l">Destinataires</span>
  </div>
  <div class="stat-card accent">
    <div class="stat-icon">📦</div>
    <span class="stat-v">{fmt_num(bultos, 0)}</span>
    <span class="stat-l">Total Bultos</span>
  </div>
  <div class="stat-card">
    <div class="stat-icon">⚖️</div>
    <span class="stat-v">{fmt_num(pb)}</span>
    <span class="stat-l">Peso Bruto (KG)</span>
  </div>
  <div class="stat-card">
    <div class="stat-icon">🏷️</div>
    <span class="stat-v">{fmt_num(pn)}</span>
    <span class="stat-l">Peso Neto (KG)</span>
  </div>
  <div class="stat-card ok">
    <div class="stat-icon">🧮</div>
    <span class="stat-v">{fmt_num(unidades, 0)}</span>
    <span class="stat-l">Total Unidades</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
#  TABLEAU PAR DESTINATAIRE
# ─────────────────────────────────────────────────────────────

def _badges(warnings: list[str]) -> str:
    if not warnings:
        return ""
    return "".join(f'<span class="warn-chip">⚠ {w}</span>' for w in warnings)


def render_client_table(client_name: str, items: list[dict]) -> None:
    rows_html  = ""
    c_bultos   = 0
    c_pb       = 0.0
    c_pn       = 0.0
    c_unidades = 0.0
    c_imp: dict = defaultdict(float)

    for it in items:
        cur   = it.get("currency", "EUR")
        b     = it.get("bultos",     0)
        pb    = it.get("peso_bruto", 0.0)
        pn    = it.get("peso_neto",  0.0)
        imp   = it.get("importe",    0.0)
        uni   = it.get("unidades",   0.0)
        warns = it.get("warnings", [])

        c_bultos   += b
        c_pb       += pb
        c_pn       += pn
        c_unidades += uni
        c_imp[cur] += imp

        imp_cell = (
            f'{fmt_num(imp)} <span class="cbadge">{cur}</span>' if imp else "—"
        )
        uni_cell  = fmt_num(uni, 2) if uni else "—"
        warn_html = _badges(warns)
        err = it.get("error")
        if err:
            warn_html += f'<span class="warn-chip err-chip">❌ {err[:50]}</span>'

        rows_html += f"""
<tr>
  <td><strong style="color:#7eb8f7">{it.get('bl_number', 'N/A')}</strong></td>
  <td style="color:var(--txt2);font-size:0.78rem">{it.get('filename', '')}<br>{warn_html}</td>
  <td class="r">{fmt_num(b, 0)}</td>
  <td class="r">{fmt_num(pb)} KG</td>
  <td class="r">{fmt_num(pn)} KG</td>
  <td class="r">{imp_cell}</td>
  <td class="r">{uni_cell}</td>
</tr>
"""

    imp_total = " | ".join(
        f'{fmt_num(v)} <span class="cbadge">{k}</span>'
        for k, v in c_imp.items()
    ) or "—"

    rows_html += f"""
<tr class="tr-total">
  <td colspan="2">🏁 <strong>TOTAL DESTINATAIRE : {client_name.upper()}</strong></td>
  <td class="r"><strong>{fmt_num(c_bultos, 0)}</strong></td>
  <td class="r"><strong>{fmt_num(c_pb)} KG</strong></td>
  <td class="r"><strong>{fmt_num(c_pn)} KG</strong></td>
  <td class="r"><strong>{imp_total}</strong></td>
  <td class="r"><strong>{fmt_num(c_unidades, 2)}</strong></td>
</tr>
"""

    html = f"""
<div class="client-section">
  <div class="client-header">
    <div class="client-header-text">
      <span class="client-icon">👤</span>
      <span>{client_name}</span>
    </div>
    <span class="client-badge">{len(items)} Packing List{'s' if len(items) > 1 else ''}</span>
  </div>
  <div class="rt-wrap">
    <table class="rt">
      <thead>
        <tr>
          <th>N° Packing-List</th>
          <th>Fichier PDF</th>
          <th class="r">Total Bultos</th>
          <th class="r">Total Peso Bruto</th>
          <th class="r">Total Peso Neto</th>
          <th class="r">Importe Total Factura</th>
          <th class="r">Total Unidades</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
  </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  TOTAL GÉNÉRAL
# ─────────────────────────────────────────────────────────────

def render_grand_total(summary: dict) -> None:
    n_clients  = summary.get("total_clients", 0)
    n_pls      = summary.get("total_pls", 0)
    bultos     = summary.get("total_bultos", 0)
    pb         = summary.get("total_pb", 0.0)
    pn         = summary.get("total_pn", 0.0)
    unidades   = summary.get("total_unidades", 0.0)
    imp_dict   = summary.get("total_importe_by_currency", {})

    imp_str = " | ".join(
        f'{fmt_num(v)} <span class="cbadge" style="background:rgba(240,165,0,0.15);'
        f'color:var(--acc);border-color:rgba(240,165,0,0.3)">{k}</span>'
        for k, v in imp_dict.items()
    ) or "—"

    html = f"""
<div class="grand-total-section">
  <div class="grand-total-header">
    🏆 TOTAL GÉNÉRAL — RÉCAPITULATIF TOUTES PACKING LISTS
  </div>
  <div class="rt-wrap">
    <table class="rt">
      <thead>
        <tr>
          <th>—</th>
          <th class="r">DESTINATAIRES</th>
          <th class="r">PACKING LISTS</th>
          <th class="r">TOTAL BULTOS</th>
          <th class="r">TOTAL PESO BRUTO</th>
          <th class="r">TOTAL PESO NETO</th>
          <th class="r">IMPORTE TOTAL</th>
          <th class="r">TOTAL UNIDADES</th>
        </tr>
      </thead>
      <tbody>
        <tr class="tr-grand">
          <td><strong>🏆 TOTAUX GÉNÉRAUX</strong></td>
          <td class="r"><strong>{n_clients}</strong></td>
          <td class="r"><strong>{n_pls}</strong></td>
          <td class="r"><strong>{fmt_num(bultos, 0)}</strong></td>
          <td class="r"><strong>{fmt_num(pb)} KG</strong></td>
          <td class="r"><strong>{fmt_num(pn)} KG</strong></td>
          <td class="r"><strong>{imp_str}</strong></td>
          <td class="r"><strong>{fmt_num(unidades, 2)}</strong></td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  PAGE RÉSULTATS
# ─────────────────────────────────────────────────────────────

def render_results(results: list[dict], grouped: dict) -> None:
    summary = calculate_summary(grouped)
    summary["total_files"] = len(results)

    all_warns = [
        f"{r['filename']}: {', '.join(r['warnings'])}"
        for r in results
        if r.get("warnings")
    ]
    if all_warns:
        with st.expander(f"⚠️ {len(all_warns)} avertissement(s) — données partiellement extraites"):
            for w in all_warns:
                st.caption(w)

    render_stat_cards(summary)

    st.markdown('<div class="section-title">📋 Détail par destinataire</div>', unsafe_allow_html=True)

    for client_name, items in grouped.items():
        render_client_table(client_name, items)

    render_grand_total(summary)


# ─────────────────────────────────────────────────────────────
#  INSTRUCTIONS
# ─────────────────────────────────────────────────────────────

def render_instructions() -> None:
    st.markdown(
        """
<div class="instructions-box">
  <strong>📋 Comment utiliser :</strong>
  <ol>
    <li>Importez un ou plusieurs fichiers PDF Packing List (format GOA ou standard)</li>
    <li>Cliquez sur <strong>« Extraire &amp; Analyser »</strong></li>
    <li>Vérifiez les données extraites par destinataire</li>
    <li>Téléchargez le rapport PDF paysage « Récapitulatif par Destinataire »</li>
  </ol>
  <p style="margin-top:0.6rem;font-size:0.8rem;color:rgba(255,255,255,0.4);">
    ⚡ Détection automatique du format CONFECCIONES GOA — extraction Bultos, Poids, Importe, Unidades.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )
