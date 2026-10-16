"""
export_engine.py
Moteur d'extraction PDF et de génération de rapports.
Packing Lists / Bons de Livraison → données structurées → rapport PDF paysage.
"""

from __future__ import annotations

import os
import re
import tempfile
from collections import defaultdict, OrderedDict
from datetime import datetime
from typing import Any

import pdfplumber
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ─────────────────────────────────────────────────────────────
#  COULEURS
# ─────────────────────────────────────────────────────────────
C_PRIMARY        = colors.HexColor("#1a3a5c")
C_SECONDARY      = colors.HexColor("#2e6da4")
C_ACCENT         = colors.HexColor("#e67e22")
C_ALT_ROW        = colors.HexColor("#eaf3fb")
C_TOTAL_CLIENT   = colors.HexColor("#d4e6f1")
C_GRAND_BG       = colors.HexColor("#fff3cd")
C_GRAND_BORDER   = colors.HexColor("#f39c12")
C_BORDER         = colors.HexColor("#a0b8d0")
C_WHITE          = colors.white
C_ERROR          = colors.HexColor("#e74c3c")
C_OK             = colors.HexColor("#27ae60")


# ─────────────────────────────────────────────────────────────
#  HELPERS NUMÉRIQUES
# ─────────────────────────────────────────────────────────────

def clean_number(text: Any) -> float:
    """Convertit texte → float (formats FR et EN)."""
    if text is None:
        return 0.0
    s = str(text).strip()
    s = re.sub(r"[€$£¥\s]", "", s)
    # 1.234,56  →  1234.56
    if re.match(r"^[\d.]+,\d{1,3}$", s):
        s = s.replace(".", "").replace(",", ".")
    # 1,234.56  →  1234.56
    elif re.match(r"^[\d,]+\.\d+$", s):
        s = s.replace(",", "")
    # 1234,56  →  1234.56
    elif "," in s and "." not in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def fmt_num(value: float, decimals: int = 2) -> str:
    """Formate un nombre pour affichage (séparateur FR)."""
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")


# ─────────────────────────────────────────────────────────────
#  EXTRACTION — CHAMPS TEXTUELS
# ─────────────────────────────────────────────────────────────

def extract_client_name(text: str) -> str:
    # GOA format: "P A C K I N G - L I S T  DDOOUUBBLLEEDD NNAAMMEE  DD/MM/YYYY"
    m = re.search(
        r"P\s*A\s*C\s*K\s*I\s*N\s*G\s*-\s*L\s*I\s*S\s*T\s+"
        r"([A-Z]{2}[A-Z\s'',.\-]+?)\s+\d{2}/\d{2}/\d{4}",
        text[:2000],
    )
    if m:
        doubled = m.group(1).strip()
        name = re.sub(r"(.)\1", r"\1", doubled).strip()
        name = re.sub(r"\s{2,}", " ", name)
        if len(name) > 3:
            return name

    # Standard patterns
    patterns = [
        r"(?:Consign[eé]e?|Destinataire|Livr[eé]\s*[aà])[:\s]+([^\n]{5,90})",
        r"(?:Customer|Client|Ship\s*to|Sold\s*to|Deliver(?:y)?\s*to)[:\s]+([^\n]{5,90})",
        r"(?:CONSIGNEE|BUYER|IMPORTER|RECEIVER)[:\s]+([^\n]{5,80})",
        r"(?:Pour|À|For)[:\s]+([A-Z][^\n]{5,70})",
        r"(?:TO\s*:)\s+([A-Z][^\n]{5,70})",
    ]
    for pat in patterns:
        m = re.search(pat, text[:5000], re.IGNORECASE)
        if m:
            name = m.group(1).strip().split("\n")[0].strip()
            name = re.sub(r"\s{2,}", " ", name)
            if len(name) > 3:
                return name
    return "CLIENT NON IDENTIFIÉ"


def extract_bl_number(text: str) -> str:
    patterns = [
        # GOA format: "P A C K I N G - L I S T" on line 1, PL number on line 2
        r"P\s*A\s*C\s*K\s*I\s*N\s*G\s*-\s*L\s*I\s*S\s*T[^\n]*\n[^\n]*?\s(\d{2,3}\.\d{3})\b",
        r"(?:Packing\s+List\s+N[o°#]?\.?\s*[:\-]?\s*)([A-Z0-9\-/_.]{4,30})",
        r"(?:P\.?L\.?\s*N[o°#]?\.?\s*[:\-]?\s*)([A-Z0-9\-/_.]{4,30})",
        r"(?:B\.?L\.?\s*N[o°#]?\.?\s*[:\-]?\s*)([A-Z0-9\-/_.]{4,30})",
        r"(?:Bon\s+de\s+Livraison\s*N[o°#]?\.?\s*[:\-]?\s*)([A-Z0-9\-/_.]{4,30})",
        r"(?:BL\s*Number|BL\s*No)[:\s]+([A-Z0-9\-/_.]{4,30})",
        r"(?:Invoice\s+(?:No|N°|#|Number)[:\s.]*)([A-Z0-9\-/_.]{4,30})",
        r"(?:Ref(?:erence)?[:\s.]+)([A-Z0-9\-/_.]{5,30})",
        r"N[°o\.]\s*[:\-]?\s*([A-Z0-9\-/_.]{5,30})",
    ]
    for pat in patterns:
        m = re.search(pat, text[:4000], re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return "N/A"


def extract_date(text: str) -> str:
    patterns = [
        r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})",
        r"(\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})",
        r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})",
        r"(\d{1,2}\s+(?:Janvier|Février|Mars|Avril|Mai|Juin|Juillet|Août|Septembre|Octobre|Novembre|Décembre)\s+\d{4})",
    ]
    for pat in patterns:
        m = re.search(pat, text[:2000], re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return datetime.now().strftime("%d/%m/%Y")


def extract_currency(text: str) -> str:
    if re.search(r"\bEUR\b|€", text):
        return "EUR"
    if re.search(r"\bUSD\b|\$", text):
        return "USD"
    if re.search(r"\bMAD\b|\bDH\b|Dirham", text, re.IGNORECASE):
        return "MAD"
    if re.search(r"\bGBP\b|£", text):
        return "GBP"
    return "EUR"


# ─────────────────────────────────────────────────────────────
#  EXTRACTION — POIDS / COLIS / MONTANT
# ─────────────────────────────────────────────────────────────

def _find_value(text: str, *kw_groups: list[str]) -> float:
    """Cherche un nombre après un mot-clé, retourne le premier trouvé > 0."""
    for kws in kw_groups:
        escaped = [re.escape(k) for k in kws]
        pat = r"(?:" + "|".join(escaped) + r")[^\d\n]{0,30}([\d\s.,]{1,18})"
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = clean_number(m.group(1).replace(" ", ""))
            if val > 0:
                return val
    return 0.0


def extract_totals_from_tables(tables: list) -> dict:
    """Extraction depuis les tableaux PDF."""
    result: dict = {"peso_bruto": 0.0, "peso_neto": 0.0, "bultos": 0, "importe": 0.0}

    for table in tables:
        if not table:
            continue
        headers: list[str] = []
        for row in table:
            if not row:
                continue
            row_s = [str(c).strip() if c else "" for c in row]
            row_lower = " ".join(row_s).lower()

            # Détection ligne d'entête
            if any(k in row_lower for k in
                   ["gross", "net", "poids", "package", "colis", "amount", "montant", "valeur", "qty", "quantity"]):
                headers = row_s
                continue

            # Ligne total
            if any(k in row_lower for k in ["total", "totaux", "grand total", "sous-total"]):
                nums = [(i, clean_number(v)) for i, v in enumerate(row_s) if clean_number(v) > 0]
                if headers:
                    for idx, val in nums:
                        if idx < len(headers):
                            h = headers[idx].lower()
                            if ("gross" in h or "brut" in h) and result["peso_bruto"] == 0:
                                result["peso_bruto"] = val
                            elif ("net" in h and "gross" not in h and "brut" not in h) and result["peso_neto"] == 0:
                                result["peso_neto"] = val
                            elif any(k in h for k in ["pack", "colis", "ctn", "carton", "bulto", "case", "box"]):
                                if result["bultos"] == 0 and 0 < val < 1_000_000:
                                    result["bultos"] = int(val)
                            elif any(k in h for k in ["amount", "montant", "value", "valeur"]):
                                if result["importe"] == 0:
                                    result["importe"] = val
    return result


def extract_weights_packages_amount(text: str, tables: list) -> dict:
    result: dict = {
        "peso_bruto": 0.0,
        "peso_neto": 0.0,
        "bultos": 0,
        "importe": 0.0,
        "unidades": 0.0,
        "currency": extract_currency(text),
    }

    # ── GOA format: asterisk-prefixed totals ──────────────────
    # "* TOTAL BULTOS..........  75"
    m = re.search(r"\*+\s*TOTAL BULTOS[\s.]+([0-9.,]+)", text, re.IGNORECASE)
    if m:
        result["bultos"] = int(clean_number(m.group(1)))

    # "** TOTAL PESO BRUTO.....  1.087,51"
    m = re.search(r"\*+\s*TOTAL PESO BRUTO[\s.]+([0-9.,]+)", text, re.IGNORECASE)
    if m:
        result["peso_bruto"] = clean_number(m.group(1))

    # "*** TOTAL PESO NETO.....  1.050,01"
    m = re.search(r"\*+\s*TOTAL PESO NETO[\s.]+([0-9.,]+)", text, re.IGNORECASE)
    if m:
        result["peso_neto"] = clean_number(m.group(1))

    # "**** TOTAL UNIDADES.....  31.144,10"
    m = re.search(r"\*+\s*TOTAL UNIDADES[\s.]+([0-9.,]+)", text, re.IGNORECASE)
    if m:
        result["unidades"] = clean_number(m.group(1))

    # "IMPORTE TOTAL FACTURAS   25.902,50"
    if result["importe"] == 0:
        m = re.search(r"IMPORTE\s+TOTAL\s+FACTURAS\s+([0-9.,]+)", text, re.IGNORECASE)
        if m:
            result["importe"] = clean_number(m.group(1))

    # ── Generic keyword-based extraction (fallback) ───────────
    if result["peso_bruto"] == 0:
        result["peso_bruto"] = _find_value(
            text,
            ["Total Gross Weight", "Gross Weight Total", "Poids Brut Total", "Total G.W", "Total Gross"],
            ["Gross Weight", "Poids Brut", "G.W.", "GW"],
        )
    if result["peso_neto"] == 0:
        result["peso_neto"] = _find_value(
            text,
            ["Total Net Weight", "Net Weight Total", "Poids Net Total", "Total N.W", "Total Net"],
            ["Net Weight", "Poids Net", "N.W.", "NW"],
        )
    if result["bultos"] == 0:
        bultos_raw = _find_value(
            text,
            ["Total Packages", "Total Colis", "Total Cartons", "Total Cases", "Total Bultos",
             "No. of Packages", "Nombre de Colis", "Number of Packages"],
            ["Packages", "Colis", "Cartons", "Cases", "CTN", "CTNS", "PKG", "PKGS"],
        )
        if bultos_raw > 0:
            result["bultos"] = int(bultos_raw)

    if result["importe"] == 0:
        result["importe"] = _find_value(
            text,
            ["Grand Total", "Total Amount", "Montant Total", "Total Valeur", "Total HT",
             "Total Invoice", "INVOICE TOTAL", "NET AMOUNT"],
            ["Total", "Amount Due", "Net à payer", "TOTAL"],
        )

    # ── Compléter avec les tables si nécessaire ───────────────
    tbl_vals = extract_totals_from_tables(tables)
    for key in ("peso_bruto", "peso_neto", "bultos", "importe"):
        if result[key] == 0 and tbl_vals.get(key, 0):
            result[key] = tbl_vals[key]

    return result


# ─────────────────────────────────────────────────────────────
#  PARSING COMPLET D'UN PDF
# ─────────────────────────────────────────────────────────────

def parse_pdf(pdf_path: str, filename: str | None = None) -> dict:
    """
    Analyse un PDF Packing List et retourne un dict structuré.
    """
    record: dict = {
        "filename":   filename or os.path.basename(pdf_path),
        "bl_number":  "N/A",
        "client":     "CLIENT NON IDENTIFIÉ",
        "date":       datetime.now().strftime("%d/%m/%Y"),
        "bultos":     0,
        "peso_bruto": 0.0,
        "peso_neto":  0.0,
        "importe":    0.0,
        "unidades":   0.0,
        "currency":   "EUR",
        "pages":      0,
        "error":      None,
        "warnings":   [],
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            record["pages"] = len(pdf.pages)
            all_text = ""
            all_tables: list = []

            for page in pdf.pages:
                page_text = page.extract_text() or ""
                all_text += page_text + "\n"
                # Tables via lignes
                for strategy in [
                    {},
                    {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
                    {"vertical_strategy": "text",  "horizontal_strategy": "text"},
                ]:
                    try:
                        t = page.extract_tables(strategy)
                        if t:
                            all_tables.extend(t)
                    except Exception:
                        pass

            record["client"]    = extract_client_name(all_text)
            record["bl_number"] = extract_bl_number(all_text)
            record["date"]      = extract_date(all_text)

            totals = extract_weights_packages_amount(all_text, all_tables)
            record.update(totals)

            # Avertissements si données manquantes
            if record["bultos"] == 0:
                record["warnings"].append("Nombre de colis non trouvé")
            if record["peso_bruto"] == 0:
                record["warnings"].append("Poids brut non trouvé")
            if record["peso_neto"] == 0:
                record["warnings"].append("Poids net non trouvé")
            if record["importe"] == 0:
                record["warnings"].append("Montant non trouvé")
            if record["client"] == "CLIENT NON IDENTIFIÉ":
                record["warnings"].append("Client non identifié")

    except Exception as exc:
        record["error"] = str(exc)

    return record


def parse_pdf_pages(pdf_path: str, filename: str | None = None) -> list[dict]:
    """
    Parse un PDF multi-pages où chaque page est un Packing List distinct.
    Retourne une liste de records (un par page PL détectée).
    Si aucune page n'est détectée comme PL individuel, retourne parse_pdf().
    """
    fname = filename or os.path.basename(pdf_path)
    records: list[dict] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            n_pages = len(pdf.pages)
            if n_pages <= 1:
                return [parse_pdf(pdf_path, filename=fname)]

            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                # Detect a self-contained PL page (has totals)
                has_totals = bool(re.search(
                    r"\*+\s*TOTAL\s+(?:BULTOS|PESO\s+BRUTO|PESO\s+NETO|UNIDADES)",
                    text, re.IGNORECASE,
                ) or re.search(r"IMPORTE\s+TOTAL\s+FACTURAS", text, re.IGNORECASE))

                if not has_totals:
                    continue

                tables: list = []
                for strategy in [{}, {"vertical_strategy": "lines", "horizontal_strategy": "lines"}]:
                    try:
                        t = page.extract_tables(strategy)
                        if t:
                            tables.extend(t)
                    except Exception:
                        pass

                rec: dict = {
                    "filename":   f"{fname} (p.{i + 1})",
                    "bl_number":  "N/A",
                    "client":     "CLIENT NON IDENTIFIÉ",
                    "date":       datetime.now().strftime("%d/%m/%Y"),
                    "bultos":     0,
                    "peso_bruto": 0.0,
                    "peso_neto":  0.0,
                    "importe":    0.0,
                    "unidades":   0.0,
                    "currency":   "EUR",
                    "pages":      1,
                    "error":      None,
                    "warnings":   [],
                }
                rec["client"]    = extract_client_name(text)
                rec["bl_number"] = extract_bl_number(text)
                rec["date"]      = extract_date(text)
                totals = extract_weights_packages_amount(text, tables)
                rec.update(totals)

                if rec["client"] == "CLIENT NON IDENTIFIÉ":
                    rec["warnings"].append("Client non identifié")
                if rec["bultos"] == 0:
                    rec["warnings"].append("Bultos non trouvés")

                records.append(rec)

    except Exception as exc:
        return [{"filename": fname, "bl_number": "N/A", "client": "CLIENT NON IDENTIFIÉ",
                 "date": "", "bultos": 0, "peso_bruto": 0.0, "peso_neto": 0.0,
                 "importe": 0.0, "unidades": 0.0, "currency": "EUR",
                 "pages": 0, "error": str(exc), "warnings": []}]

    return records if records else [parse_pdf(pdf_path, filename=fname)]


# ─────────────────────────────────────────────────────────────
#  REGROUPEMENT & SYNTHÈSE
# ─────────────────────────────────────────────────────────────

def group_by_client(results: list[dict]) -> OrderedDict:
    grouped: OrderedDict = OrderedDict()
    for r in results:
        client = r.get("client") or "CLIENT NON IDENTIFIÉ"
        grouped.setdefault(client, []).append(r)
    return grouped


def calculate_summary(grouped: dict) -> dict:
    total_bultos   = 0
    total_pb       = 0.0
    total_pn       = 0.0
    total_importe: dict = defaultdict(float)
    total_unidades = 0.0
    total_pls      = 0

    for items in grouped.values():
        for it in items:
            total_bultos   += it.get("bultos", 0)
            total_pb       += it.get("peso_bruto", 0.0)
            total_pn       += it.get("peso_neto",  0.0)
            total_unidades += it.get("unidades", 0.0)
            cur = it.get("currency", "EUR")
            total_importe[cur] += it.get("importe", 0.0)
            total_pls += 1

    return {
        "total_bultos":              total_bultos,
        "total_pb":                  total_pb,
        "total_pn":                  total_pn,
        "total_unidades":            total_unidades,
        "total_importe_by_currency": dict(total_importe),
        "total_clients":             len(grouped),
        "total_pls":                 total_pls,
    }


# ─────────────────────────────────────────────────────────────
#  GÉNÉRATION RAPPORT PDF PAYSAGE
# ─────────────────────────────────────────────────────────────

def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(str(text), style)


def generate_pdf_report(grouped: dict, output_path: str) -> None:
    """Génère le rapport PDF paysage — RÉCAPITULATIF DES PACKING-LISTS PAR DESTINATAIRE."""

    page_w, page_h = landscape(A4)
    margin   = 1.5 * cm
    usable_w = page_w - 2 * margin

    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        rightMargin=margin, leftMargin=margin,
        topMargin=2.6 * cm, bottomMargin=2.0 * cm,
    )

    styles = getSampleStyleSheet()

    def _style(name, base="Normal", **kw) -> ParagraphStyle:
        return ParagraphStyle(name, parent=styles[base], **kw)

    sTitle  = _style("sTitle",  fontSize=14, fontName="Helvetica-Bold",
                     textColor=C_PRIMARY, alignment=TA_CENTER, spaceAfter=2)
    sSub    = _style("sSub",    fontSize=9,  fontName="Helvetica",
                     textColor=C_SECONDARY, alignment=TA_CENTER, spaceAfter=2)
    sTH     = _style("sTH",     fontSize=8,  fontName="Helvetica-Bold",
                     textColor=C_WHITE, alignment=TA_CENTER)
    sTD     = _style("sTD",     fontSize=8,  fontName="Helvetica", alignment=TA_LEFT)
    sTDR    = _style("sTDR",    fontSize=8,  fontName="Helvetica", alignment=TA_RIGHT)
    sTDB    = _style("sTDB",    fontSize=8,  fontName="Helvetica-Bold", alignment=TA_LEFT)
    sTDBR   = _style("sTDBR",   fontSize=8,  fontName="Helvetica-Bold", alignment=TA_RIGHT)
    sCliH   = _style("sCliH",   fontSize=10, fontName="Helvetica-Bold",
                     textColor=C_WHITE, alignment=TA_LEFT)
    sGTHdr  = _style("sGTHdr",  fontSize=12, fontName="Helvetica-Bold",
                     textColor=C_PRIMARY, alignment=TA_CENTER, spaceAfter=5)
    sGT     = _style("sGT",     fontSize=9,  fontName="Helvetica-Bold",
                     textColor=colors.HexColor("#7d5a00"), alignment=TA_CENTER)

    # 7 colonnes : N° PL | Fichier | Bultos | Peso Bruto | Peso Neto | Importe | Unidades
    raw_cw = [2.5, 4.5, 2.0, 2.8, 2.8, 3.5, 3.0]
    scale  = usable_w / (sum(raw_cw) * cm)
    cw     = [w * cm * scale for w in raw_cw]

    col_labels = [
        "N° Packing-List",
        "Fichier PDF",
        "Total Bultos",
        "Total Peso Bruto\n(KG)",
        "Total Peso Neto\n(KG)",
        "Importe Total\nFactura",
        "Total\nUnidades",
    ]

    summary   = calculate_summary(grouped)
    n_clients = summary["total_clients"]
    n_pls     = summary["total_pls"]
    now_str   = datetime.now().strftime("%d/%m/%Y à %H:%M")

    story: list = []

    # ── Titre ─────────────────────────────────────────────────
    story.append(_p("RÉCAPITULATIF DES PACKING-LISTS PAR DESTINATAIRE", sTitle))
    story.append(_p(
        f"Généré le {now_str} &nbsp;|&nbsp; "
        f"{n_clients} destinataire(s) &nbsp;|&nbsp; {n_pls} Packing List(s)",
        sSub,
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=C_PRIMARY, spaceAfter=8))

    grand_bultos   = 0
    grand_pb       = 0.0
    grand_pn       = 0.0
    grand_unidades = 0.0
    grand_imp: dict = defaultdict(float)

    for client_name, items in grouped.items():
        # ── Bandeau destinataire ───────────────────────────────
        ch = Table(
            [[_p(f"DESTINATAIRE : {client_name.upper()}  —  {len(items)} Packing List(s)", sCliH)]],
            colWidths=[usable_w], rowHeights=[22],
        )
        ch.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), C_SECONDARY),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("GRID",          (0, 0), (-1, -1), 0.5, C_BORDER),
        ]))
        story.append(ch)

        # ── Tableau lignes PL ──────────────────────────────────
        tdata: list = [[_p(h, sTH) for h in col_labels]]

        c_bultos = 0; c_pb = 0.0; c_pn = 0.0; c_unidades = 0.0
        c_imp: dict = defaultdict(float)

        for it in items:
            cur = it.get("currency", "EUR")
            b   = it.get("bultos",     0)
            pb  = it.get("peso_bruto", 0.0)
            pn  = it.get("peso_neto",  0.0)
            imp = it.get("importe",    0.0)
            uni = it.get("unidades",   0.0)
            c_bultos += b; c_pb += pb; c_pn += pn; c_unidades += uni
            c_imp[cur] += imp

            tdata.append([
                _p(it.get("bl_number", "N/A"), sTD),
                _p(it.get("filename",  ""),    sTD),
                _p(fmt_num(b, 0),               sTDR),
                _p(fmt_num(pb),                 sTDR),
                _p(fmt_num(pn),                 sTDR),
                _p(f"{fmt_num(imp)} {cur}" if imp else "—", sTDR),
                _p(fmt_num(uni, 2) if uni else "—", sTDR),
            ])

        # Ligne total destinataire
        imp_str = " | ".join(f"{fmt_num(v)} {k}" for k, v in c_imp.items()) or "—"
        tdata.append([
            _p("TOTAL DESTINATAIRE", sTDB),
            _p(f"{len(items)} PL(s)", sTDB),
            _p(fmt_num(c_bultos, 0),    sTDBR),
            _p(fmt_num(c_pb),           sTDBR),
            _p(fmt_num(c_pn),           sTDBR),
            _p(imp_str,                 sTDBR),
            _p(fmt_num(c_unidades, 2),  sTDBR),
        ])

        nr = len(tdata)
        tbl = Table(tdata, colWidths=cw, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),       C_PRIMARY),
            ("TEXTCOLOR",     (0, 0), (-1, 0),       C_WHITE),
            ("ALIGN",         (0, 0), (-1, 0),       "CENTER"),
            ("FONTNAME",      (0, 0), (-1, 0),       "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0),       8),
            ("LINEBELOW",     (0, 0), (-1, 0),       1.2, C_BORDER),
            ("VALIGN",        (0, 0), (-1, -1),      "MIDDLE"),
            ("FONTSIZE",      (0, 1), (-1, -1),      8),
            ("LEFTPADDING",   (0, 0), (-1, -1),      5),
            ("RIGHTPADDING",  (0, 0), (-1, -1),      5),
            ("TOPPADDING",    (0, 0), (-1, -1),      3),
            ("BOTTOMPADDING", (0, 0), (-1, -1),      3),
            ("ROWBACKGROUNDS",(0, 1), (-1, nr - 2),  [C_WHITE, C_ALT_ROW]),
            ("BACKGROUND",    (0, nr - 1), (-1, nr - 1), C_TOTAL_CLIENT),
            ("FONTNAME",      (0, nr - 1), (-1, nr - 1), "Helvetica-Bold"),
            ("LINEABOVE",     (0, nr - 1), (-1, nr - 1), 1.2, C_SECONDARY),
            ("GRID",          (0, 0), (-1, -1),      0.4, C_BORDER),
            ("BOX",           (0, 0), (-1, -1),      1,   C_SECONDARY),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 10))

        grand_bultos   += c_bultos
        grand_pb       += c_pb
        grand_pn       += c_pn
        grand_unidades += c_unidades
        for cur, val in c_imp.items():
            grand_imp[cur] += val

    # ── TOTAL GÉNÉRAL ─────────────────────────────────────────
    story.append(HRFlowable(
        width="100%", thickness=2.5, color=C_GRAND_BORDER,
        spaceBefore=6, spaceAfter=8,
    ))
    story.append(_p("TOTAL GÉNÉRAL — TOUS LES PACKING LISTS", sGTHdr))

    gt_cw  = [usable_w / 7] * 7
    gi_str = "  |  ".join(f"{fmt_num(v)} {k}" for k, v in grand_imp.items()) or "—"

    gt_data = [
        [_p(h, sGT) for h in [
            "NB DESTINATAIRES", "NB PACKING LISTS",
            "TOTAL BULTOS", "TOTAL PESO BRUTO",
            "TOTAL PESO NETO", "TOTAL IMPORTE", "TOTAL UNIDADES",
        ]],
        [
            _p(str(n_clients),              sGT),
            _p(str(n_pls),                  sGT),
            _p(fmt_num(grand_bultos, 0),    sGT),
            _p(f"{fmt_num(grand_pb)} KG",   sGT),
            _p(f"{fmt_num(grand_pn)} KG",   sGT),
            _p(gi_str,                      sGT),
            _p(fmt_num(grand_unidades, 2),  sGT),
        ],
    ]
    gt = Table(gt_data, colWidths=gt_cw, rowHeights=[22, 26])
    gt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0),  C_PRIMARY),
        ("TEXTCOLOR",  (0, 0), (-1, 0),  C_WHITE),
        ("BACKGROUND", (0, 1), (-1, 1),  C_GRAND_BG),
        ("FONTNAME",   (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",       (0, 0), (-1, -1), 1,   C_SECONDARY),
        ("BOX",        (0, 0), (-1, -1), 2,   C_GRAND_BORDER),
        ("LINEABOVE",  (0, 1), (-1, 1),  2,   C_GRAND_BORDER),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(gt)

    # ── Décoration de page ─────────────────────────────────────
    def on_page(canv, doc_obj):
        canv.saveState()
        pw, ph = landscape(A4)
        canv.setStrokeColor(C_PRIMARY)
        canv.setLineWidth(2)
        canv.line(margin, ph - 1.4 * cm, pw - margin, ph - 1.4 * cm)
        canv.setFont("Helvetica", 7.5)
        canv.setFillColor(colors.HexColor("#666666"))
        page_no = canv.getPageNumber()
        canv.drawString(margin, 1.1 * cm,
                        f"Récapitulatif Packing Lists  |  {now_str}")
        canv.drawRightString(pw - margin, 1.1 * cm, f"Page {page_no}")
        canv.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)


def generate_pdf_bytes(grouped: dict) -> bytes:
    """Génère le PDF et retourne les bytes (pour st.download_button)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    try:
        generate_pdf_report(grouped, tmp.name)
        with open(tmp.name, "rb") as f:
            return f.read()
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
