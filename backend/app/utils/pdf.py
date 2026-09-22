"""PDF generation for cotizaciones — Comercial Minimalista Premium."""

from __future__ import annotations

import os
from datetime import date
from fpdf import FPDF

_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static')
_FRONTEND_URL = "https://cotizaciones-web.onrender.com"

# Page constants — A4 portrait, 10mm margins
_LM = 10
_RM = 10
_TM = 8
_CW = 190  # 210 - 2×10

# Palette
_NAVY  = (10, 25, 55)
_GREEN = (22, 120, 64)
_GRAY  = (100, 116, 139)
_LGRAY = (226, 232, 240)
_BLACK = (15, 23, 42)
_WHITE = (255, 255, 255)


def _cop(amount) -> str:
    try:
        n = round(float(amount))
        return "$" + f"{n:,}".replace(",", ".")
    except Exception:
        return "$0"


def _safe(text) -> str:
    if not text:
        return ""
    return str(text).encode("latin-1", errors="replace").decode("latin-1")


def _trunc(pdf: FPDF, text: str, max_w: float) -> str:
    while pdf.get_string_width(text) > max_w and len(text) > 3:
        text = text[:-4] + "..."
    return text


def _fmt_date(d) -> str:
    if not d:
        return ""
    if isinstance(d, date):
        return d.strftime("%d/%m/%Y")
    s = str(d)
    if len(s) >= 10 and s[4] == "-":
        return f"{s[8:10]}/{s[5:7]}/{s[0:4]}"
    return s


def _fmt_cant(v: float) -> str:
    if v == int(v):
        return str(int(v))
    return f"{v:g}"


class _PDF(FPDF):
    pass


def generate_cotizacion_pdf(cotizacion) -> bytes:
    # ── Pull data ─────────────────────────────────────────────────────────────
    numero          = _safe(getattr(cotizacion, "numero", "") or "")
    titulo          = _safe(getattr(cotizacion, "titulo", "") or "")
    fecha_emision   = _fmt_date(getattr(cotizacion, "fecha_emision", ""))
    fecha_vto       = _fmt_date(getattr(cotizacion, "fecha_vencimiento", ""))
    subtotal        = float(getattr(cotizacion, "subtotal", 0) or 0)
    descuento_monto = float(getattr(cotizacion, "descuento", 0) or 0)
    total           = float(getattr(cotizacion, "total", 0) or 0)
    condiciones     = _safe(getattr(cotizacion, "condiciones_pago", "") or "")
    observaciones   = _safe(getattr(cotizacion, "observaciones", "") or "")
    terminos        = _safe(getattr(cotizacion, "terminos", "") or "")
    con_aiu         = getattr(cotizacion, "con_aiu", False)
    aiu_adm         = float(getattr(cotizacion, "aiu_administracion", 0) or 0)
    aiu_imp         = float(getattr(cotizacion, "aiu_imprevistos", 0) or 0)
    aiu_uti         = float(getattr(cotizacion, "aiu_utilidad", 0) or 0)
    aiu_iva         = float(getattr(cotizacion, "aiu_iva_monto", 0) or 0)
    impuesto_total  = float(getattr(cotizacion, "impuesto", 0) or 0)
    token_publico   = getattr(cotizacion, "token_publico", None)

    cliente_nombre  = _safe(getattr(cotizacion, "cliente_nombre", "") or "")
    cliente_nit     = _safe(getattr(cotizacion, "cliente_nit", "") or "")
    cliente_ciudad  = _safe(getattr(cotizacion, "cliente_ciudad", "") or "")
    cliente_tel     = _safe(getattr(cotizacion, "cliente_telefono", "") or "")
    contacto_nombre = _safe(getattr(cotizacion, "cliente_contacto_nombre", "") or "")
    contacto_email  = _safe(getattr(cotizacion, "cliente_contacto_email", "") or "")
    validez_dias    = getattr(cotizacion, "validez_dias", None)

    descuento_pct = 0
    if subtotal > 0 and descuento_monto > 0:
        descuento_pct = round(descuento_monto / subtotal * 100)

    items = list(getattr(cotizacion, "items", []) or [])

    # ── PDF setup ─────────────────────────────────────────────────────────────
    pdf = _PDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(_LM, _TM, _RM)
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    def sf(style="", size=10):
        pdf.set_font("Helvetica", style, size)

    def tc(*rgb):
        pdf.set_text_color(*rgb)

    def dc(*rgb):
        pdf.set_draw_color(*rgb)

    def fc(*rgb):
        pdf.set_fill_color(*rgb)

    cur_y = _TM

    # ── TOP ACCENT BAR ────────────────────────────────────────────────────────
    fc(*_NAVY)
    dc(*_NAVY)
    pdf.rect(_LM, cur_y, _CW, 2.5, style="F")
    cur_y += 4

    # ── HEADER ROW ────────────────────────────────────────────────────────────
    # [Logo 38mm | Company center 112mm | Cotización box 40mm]
    logo_w = 38
    mid_w  = 112
    cot_w  = 40
    hdr_h  = 16

    # Logo
    for logo_name in ("logo_pdf.jpg", "logo.png"):
        logo_path = os.path.join(_STATIC_DIR, logo_name)
        if os.path.exists(logo_path):
            pdf.image(logo_path, x=_LM, y=cur_y, w=logo_w - 2, h=hdr_h - 1, keep_aspect_ratio=True)
            break

    # Company name + NIT
    sf("B", 13)
    tc(*_NAVY)
    pdf.set_xy(_LM + logo_w, cur_y + 1)
    pdf.cell(mid_w, 7, "TRIPLE A CONSTRUCCIONES SAS", align="L")
    sf("", 8)
    tc(*_GRAY)
    pdf.set_xy(_LM + logo_w, cur_y + 9)
    pdf.cell(mid_w, 5, "NIT: 901.650.581-4  |  tripleaconstruccionessas@gmail.com  |  314 395 2896", align="L")

    # Cotización box (right)
    fc(*_NAVY)
    dc(*_NAVY)
    pdf.rect(_LM + logo_w + mid_w, cur_y, cot_w, hdr_h, style="F")
    sf("", 7)
    tc(*_WHITE)
    pdf.set_xy(_LM + logo_w + mid_w, cur_y + 2)
    pdf.cell(cot_w, 5, "COTIZACION", align="C")
    sf("B", 14)
    pdf.set_xy(_LM + logo_w + mid_w, cur_y + 7)
    pdf.cell(cot_w, 7, f"N\xba {numero}", align="C")

    cur_y += hdr_h + 2

    # ── OBRA / TITULO STRIP ───────────────────────────────────────────────────
    if titulo:
        fc(244, 247, 252)
        dc(*_LGRAY)
        pdf.rect(_LM, cur_y, _CW, 7, style="FD")
        sf("I", 9)
        tc(*_NAVY)
        pdf.set_xy(_LM + 3, cur_y + 1)
        pdf.cell(_CW - 6, 5, _trunc(pdf, titulo, _CW - 8), align="L")
        cur_y += 9

    # ── CLIENT INFO STRIP ─────────────────────────────────────────────────────
    # 2-row strip: labels row + values row, 6 columns
    info_h = 5.5
    # widths: Cliente | NIT | Ciudad | Contacto | Tel | Fecha
    iw = [40, 30, 30, 40, 30, 20]

    def info_cell(x, y, w, label, value):
        sf("", 6.5)
        tc(*_GRAY)
        pdf.set_xy(x, y)
        pdf.cell(w, info_h, label, border="LTR", align="L")
        sf("B" if label == "Cliente" else "", 7.5)
        tc(*_BLACK)
        pdf.set_xy(x, y + info_h)
        pdf.cell(w, info_h, _trunc(pdf, value, w - 2), border="LBR", align="L")

    dc(*_LGRAY)
    x = _LM
    for i, (lbl, val, w) in enumerate([
        ("Cliente",  cliente_nombre,  iw[0]),
        ("NIT",      cliente_nit,     iw[1]),
        ("Ciudad",   cliente_ciudad,  iw[2]),
        ("Contacto", contacto_nombre, iw[3]),
        ("Telefono", cliente_tel,     iw[4]),
        ("Fecha",    fecha_emision,   iw[5]),
    ]):
        info_cell(x, cur_y, w, lbl, val)
        x += w

    cur_y += info_h * 2 + 2

    # second info row: email | condiciones | validez | | | vence
    x = _LM
    for lbl, val, w in [
        ("Email",       _trunc(pdf, contacto_email, iw[0] - 2), iw[0]),
        ("T. Pago",     _trunc(pdf, condiciones, iw[1] - 2),    iw[1]),
        ("Validez",     f"{validez_dias} dias" if validez_dias else "", iw[2]),
        ("Descuento",   f"{descuento_pct}%" if descuento_pct else "0%", iw[3]),
        ("",            "",                                       iw[4]),
        ("Vence",       fecha_vto,                                iw[5]),
    ]:
        info_cell(x, cur_y, w, lbl, val)
        x += w

    cur_y += info_h * 2 + 3

    # ── ITEMS TABLE ───────────────────────────────────────────────────────────
    # Nº | Descripción | Und. | Cant. | Vr Unitario | Vr Total
    cw = [8, 92, 14, 16, 30, 30]
    hdrs = ["No", "Descripcion", "Und.", "Cant.", "Vr. Unitario", "Vr. Total"]
    alns = ["C", "L", "C", "C", "R", "R"]
    row_h = 6

    # Header row
    fc(*_NAVY)
    dc(*_NAVY)
    sf("B", 7.5)
    tc(*_WHITE)
    x = _LM
    for w, h, a in zip(cw, hdrs, alns):
        pdf.set_xy(x, cur_y)
        pdf.cell(w, row_h, h, border=1, align=a, fill=True)
        x += w
    cur_y += row_h

    # Item rows
    dc(*_LGRAY)
    for idx, item in enumerate(items):
        desc   = _safe(getattr(item, "descripcion", None) or getattr(item, "producto_nombre", "") or "")
        cant   = float(getattr(item, "cantidad", 0) or 0)
        unidad = _safe(getattr(item, "unidad", None) or getattr(item, "producto_unidad", "") or "UN")
        pu     = float(getattr(item, "precio_unitario", 0) or 0)
        tot    = float(getattr(item, "total", 0) or 0)

        if idx % 2 == 0:
            fc(248, 250, 252)
        else:
            fc(*_WHITE)

        sf("", 7.5)
        tc(*_BLACK)
        row_vals = [str(idx + 1), _trunc(pdf, desc, cw[1] - 2), unidad, _fmt_cant(cant), _cop(pu), _cop(tot)]
        x = _LM
        for w, v, a in zip(cw, row_vals, alns):
            pdf.set_xy(x, cur_y)
            pdf.cell(w, row_h, v, border=1, align=a, fill=True)
            x += w
        cur_y += row_h

    # IVA row if applicable (no AIU)
    if impuesto_total > 0 and not con_aiu:
        iva_pct = 19
        for it in items:
            p = float(getattr(it, "impuesto_porcentaje", 0) or 0)
            if p > 0:
                iva_pct = int(p)
                break
        fc(250, 252, 250)
        sf("", 7.5)
        tc(*_BLACK)
        row_vals = ["", f"IVA ({iva_pct}%)", "%", "", "", _cop(impuesto_total)]
        x = _LM
        for w, v, a in zip(cw, row_vals, alns):
            pdf.set_xy(x, cur_y)
            pdf.cell(w, row_h, v, border=1, align=a, fill=True)
            x += w
        cur_y += row_h

    cur_y += 3

    # ── FOOTER BLOCK: Observations (left) + Totals (right) ───────────────────
    notes_w  = 107
    totals_w = _CW - notes_w   # 83
    lbl_w    = 50
    val_w    = totals_w - lbl_w  # 33
    tot_x    = _LM + notes_w
    tot_y    = cur_y
    tot_row_h = 6.5

    def draw_tot_row(label: str, value: str, bold: bool = False, accent: bool = False):
        nonlocal tot_y
        if accent:
            fc(*_NAVY)
            dc(*_NAVY)
            pdf.rect(tot_x, tot_y, totals_w, tot_row_h, style="F")
            sf("B", 9)
            tc(*_WHITE)
        else:
            fc(*_WHITE)
            dc(*_LGRAY)
            pdf.rect(tot_x, tot_y, totals_w, tot_row_h, style="FD")
            sf("B" if bold else "", 8)
            tc(*_BLACK)

        pdf.set_xy(tot_x + 2, tot_y + 1)
        pdf.cell(lbl_w - 2, tot_row_h - 2, label, align="L")
        pdf.set_xy(tot_x + lbl_w, tot_y + 1)
        pdf.cell(val_w - 2, tot_row_h - 2, value, align="R")
        tot_y += tot_row_h

    if con_aiu:
        costos_base = subtotal - descuento_monto
        draw_tot_row("Subtotal Directo", _cop(subtotal))
        if descuento_monto > 0:
            draw_tot_row(f"Descuento ({descuento_pct}%)", f"- {_cop(descuento_monto)}")
        draw_tot_row(f"Administracion ({aiu_adm:g}%)", _cop(costos_base * aiu_adm / 100))
        draw_tot_row(f"Imprevistos ({aiu_imp:g}%)",    _cop(costos_base * aiu_imp / 100))
        draw_tot_row(f"Utilidad ({aiu_uti:g}%)",       _cop(costos_base * aiu_uti / 100))
        if aiu_iva > 0:
            draw_tot_row("IVA AIU (19%)", _cop(aiu_iva))
        draw_tot_row("TOTAL GENERAL", _cop(total), bold=True, accent=True)
    else:
        draw_tot_row("Subtotal", _cop(subtotal))
        if descuento_monto > 0:
            draw_tot_row(f"Descuento ({descuento_pct}%)", f"- {_cop(descuento_monto)}")
        if impuesto_total > 0:
            draw_tot_row("IVA", _cop(impuesto_total))
        draw_tot_row("TOTAL", _cop(total), bold=True, accent=True)

    # Observations (left column, aligned with totals block)
    obs_lines: list[str] = []
    if observaciones:
        for ln in observaciones.split("\n"):
            if ln.strip():
                obs_lines.append(_safe(ln.strip()))
    if condiciones:
        obs_lines.insert(0, f"Pago: {condiciones}")
    if terminos:
        for ln in terminos.split("\n"):
            if ln.strip():
                obs_lines.append(_safe(ln.strip()))
    if token_publico:
        link_text = f"Ver online: {_FRONTEND_URL}/ver/{token_publico}"
        obs_lines.append(link_text)

    obs_y = cur_y
    dc(*_LGRAY)
    fc(248, 250, 252)
    if obs_lines:
        sf("B", 7.5)
        tc(*_NAVY)
        pdf.set_xy(_LM, obs_y)
        pdf.cell(notes_w, 6, "Observaciones", border="LTR", align="L", fill=True)
        obs_y += 6

        sf("", 7)
        tc(*_BLACK)
        for ln in obs_lines:
            pdf.set_xy(_LM, obs_y)
            if ln.startswith("Ver online:"):
                tc(*_GREEN)
                sf("", 7)
                pdf.cell(notes_w, 5.5, _trunc(pdf, ln, notes_w - 4), border="LR", align="L")
                tc(*_BLACK)
            else:
                pdf.cell(notes_w, 5.5, f"- {_trunc(pdf, ln, notes_w - 5)}", border="LR", align="L")
            obs_y += 5.5

        # close bottom
        pdf.set_xy(_LM, obs_y)
        pdf.cell(notes_w, 0, "", border="LBR")

    # ── BOTTOM ACCENT BAR ─────────────────────────────────────────────────────
    bot_y = max(tot_y, obs_y) + 4
    fc(*_NAVY)
    dc(*_NAVY)
    pdf.rect(_LM, bot_y, _CW, 2.5, style="F")

    sf("", 7)
    tc(*_GRAY)
    pdf.set_xy(_LM, bot_y + 4)
    pdf.cell(_CW, 5, "Documento generado digitalmente  |  Triple A Construcciones SAS  |  NIT 901.650.581-4", align="C")

    return bytes(pdf.output())
