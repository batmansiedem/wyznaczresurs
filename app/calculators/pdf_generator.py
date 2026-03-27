"""Generowanie raportów PDF dla wyników obliczeń resursu UTB.

Nowoczesny layout inżynierski:
- 3 kolumny: Etykieta | Wartość | Jednostka
- Jednokolorowy motyw (kolor motywu użytkownika)
- Logo firmy (opcjonalne)
- Numery stron w stopce
"""

import os
import re
from io import BytesIO
from datetime import datetime
from math import cos, sin, radians

from PIL import Image as PILImage
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    Spacer, Image, PageBreak, HRFlowable,
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, PolyLine, Polygon
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

# ── Czcionki ────────────────────────────────────────────────────────────────
FONT_PATH = os.path.join(settings.BASE_DIR, 'core', 'fonts')
pdfmetrics.registerFont(TTFont('DVS',  os.path.join(FONT_PATH, 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DVSB', os.path.join(FONT_PATH, 'DejaVuSans-Bold.ttf')))

# ── Stałe layoutu ────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN_H = 1.5 * cm
MARGIN_V = 1.5 * cm
MARGIN_TOP = 2.5 * cm   # górny margines (accommodates canvas page header)
USABLE_W = PAGE_W - 2 * MARGIN_H   # ~18 cm

# Kolumny tabeli parametrów: etykieta | wartość | jednostka
COL_LABEL = 11.5 * cm
COL_VALUE = 4.5 * cm
COL_UNIT  = USABLE_W - COL_LABEL - COL_VALUE  # ~2 cm

# ── Kolory bazowe (szarości) ─────────────────────────────────────────────────
C_WHITE    = colors.white
C_BLACK    = colors.HexColor('#1a1a2e')
C_GREY_TXT = colors.HexColor('#555555')
C_GREY_ROW = colors.HexColor('#f7f8fa')    # przemienne tło wiersza
C_GREY_SEP = colors.HexColor('#e0e4ea')    # linia oddzielająca
C_GREY_HDR = colors.HexColor('#eef0f4')    # tło nagłówka sekcji


# ── Pomocnicze ───────────────────────────────────────────────────────────────

def _alpha(hex_color: colors.HexColor, alpha: float) -> colors.Color:
    """Kolor z przezroczystością (blend na białym)."""
    r = hex_color.red   + (1 - hex_color.red)   * (1 - alpha)
    g = hex_color.green + (1 - hex_color.green) * (1 - alpha)
    b = hex_color.blue  + (1 - hex_color.blue)  * (1 - alpha)
    return colors.Color(r, g, b)


def _strip_html(text: str) -> str:
    return re.sub(r'<[^>]*>', '', str(text))


def _fmt_sub(text: str) -> str:
    """Konwertuje X_ABC → X<sub>ABC</sub> dla Paragraph (indeks dolny)."""
    return re.sub(r'_([A-Za-z0-9]+)', r'<sub>\1</sub>', str(text))


def _extract_unit(label: str) -> str:
    """Wyciąga jednostkę z nawiasów kwadratowych etykiety."""
    m = re.search(r'\[([^\]]+)\]', label)
    return m.group(1) if m else ''


def _get_num(raw):
    """Wyciąga wartość float z {value,unit} lub z liczby/stringa."""
    if raw is None:
        return None
    if isinstance(raw, dict):
        v = raw.get('value')
        if v in (None, ''):
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None
    try:
        return float(str(raw).replace(',', '.').replace(' ', ''))
    except (ValueError, TypeError):
        return None


def _split_value_unit(raw, unit_hint: str = '') -> tuple[str, str]:
    """Rozdziela wartość i jednostkę z surowej wartości."""
    if raw is None:
        return '-', unit_hint
    if isinstance(raw, dict):
        v = raw.get('value')
        u = raw.get('unit') or unit_hint
        return (str(v) if v not in (None, '') else '-'), str(u)
    s = str(raw).strip()
    return (s if s else '-'), unit_hint


def _style(font='DVS', size=8.5, color=None, align=0, leading=None):
    color = color or C_BLACK
    return ParagraphStyle(
        '_',
        fontName=font,
        fontSize=size,
        textColor=color,
        alignment=align,
        leading=leading or (size + 3.5),
        wordWrap='LTR',
    )


def _p(text, **kw):
    return Paragraph(_fmt_sub(_strip_html(str(text))), _style(**kw))


# ── Tabela parametrów (3 kolumny) ─────────────────────────────────────────────

def _param_table(rows: list, theme: colors.Color, is_results: bool = False) -> Table:
    """
    rows: list of (label, value, unit)
    Wiersze przemiennie białe/jasnoszare.
    Wyniki techniczne: wartość w kolorze motywu.
    """
    tdata = []
    tstyle = [
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW',     (0, 0), (-1, -1), 0.3, C_GREY_SEP),
        ('ALIGN',         (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN',         (2, 0), (2, -1), 'LEFT'),
    ]

    val_color = theme if is_results else C_BLACK

    for i, (lbl, val, unit) in enumerate(rows):
        bg = C_GREY_ROW if i % 2 == 1 else C_WHITE
        tdata.append([
            _p(lbl,  font='DVS',  size=8.5, color=C_GREY_TXT),
            _p(val,  font='DVSB', size=9,   color=val_color, align=2),
            _p(unit, font='DVS',  size=8,   color=C_GREY_TXT),
        ])
        tstyle.append(('BACKGROUND', (0, i), (-1, i), bg))

    # Lewa krawędź w kolorze motywu
    tstyle.append(('LINEBEFORE', (0, 0), (0, -1), 3, _alpha(theme, 0.6)))

    t = Table(tdata, colWidths=[COL_LABEL, COL_VALUE, COL_UNIT])
    t.setStyle(TableStyle(tstyle))
    return t


def _section_header(text: str, theme: colors.Color) -> Table:
    """Nagłówek sekcji: jasnoszare tło, kolor motywu po lewej, tekst caps."""
    cell = _p(text.upper(), font='DVSB', size=8, color=theme)
    t = Table([[cell]], colWidths=[USABLE_W])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (0, 0), _alpha(theme, 0.08)),
        ('LINEBEFORE',    (0, 0), (0, 0), 4, theme),
        ('LINEBELOW',     (0, 0), (0, 0), 0.5, _alpha(theme, 0.3)),
        ('LINETOP',       (0, 0), (0, 0), 0.5, _alpha(theme, 0.15)),
        ('LEFTPADDING',   (0, 0), (0, 0), 12),
        ('RIGHTPADDING',  (0, 0), (0, 0), 10),
        ('TOPPADDING',    (0, 0), (0, 0), 7),
        ('BOTTOMPADDING', (0, 0), (0, 0), 7),
    ]))
    return t


# ── Wykres słupkowy (poziomy) ─────────────────────────────────────────────────

def _bar_chart(bars: list, theme: colors.Color) -> Drawing:
    """
    bars: list of (label, value, max_value)
    Poziomy wykres — pill-shaped słupki, subtelna siatka.
    """
    LABEL_W  = 7.5 * cm
    BAR_ZONE = USABLE_W - LABEL_W
    ROW_H    = 1.2 * cm
    BAR_H    = ROW_H * 0.48
    BAR_OFF  = (ROW_H - BAR_H) / 2
    AXIS_H   = 0.75 * cm
    TOTAL_H  = ROW_H * len(bars) + AXIS_H
    RR       = BAR_H / 2   # promień zaokrąglenia (pill)

    d = Drawing(USABLE_W, TOTAL_H)

    val_max = bars[0][2] if bars else 100

    # Subtelna siatka pionowa
    for n in range(5):
        x = LABEL_W + (n / 4) * BAR_ZONE
        d.add(Line(x, AXIS_H * 0.45, x, AXIS_H + ROW_H * len(bars),
                   strokeColor=_alpha(theme, 0.10 if n > 0 else 0.25),
                   strokeWidth=0.7 if n > 0 else 1.0))
        d.add(String(x, AXIS_H * 0.05,
                     f'{(n / 4) * val_max:.0f}',
                     fontName='DVS', fontSize=5.5,
                     fillColor=_alpha(theme, 0.45), textAnchor='middle'))

    for i, (lbl, val, max_val) in enumerate(bars):
        y_row  = AXIS_H + i * ROW_H
        ratio  = float(val) / max(float(max_val), 0.001)
        fill_w = max(RR * 2, ratio * BAR_ZONE)
        bar_c  = colors.HexColor('#C62828') if ratio >= 1.0 else theme
        val_str = f'{float(val):.0f}' if isinstance(val, (int, float)) else str(val)

        # Track — pill tło
        d.add(Rect(LABEL_W, y_row + BAR_OFF, BAR_ZONE, BAR_H,
                   fillColor=_alpha(theme, 0.09), strokeColor=_alpha(theme, 0.12),
                   strokeWidth=0.5, rx=RR, ry=RR))
        # Wypełnienie — pill kolor
        d.add(Rect(LABEL_W, y_row + BAR_OFF, fill_w, BAR_H,
                   fillColor=bar_c, strokeColor=None, rx=RR, ry=RR))
        # Wartość za słupkiem
        d.add(String(LABEL_W + fill_w + 5,
                     y_row + BAR_OFF + BAR_H / 2 - 3.5,
                     val_str,
                     fontName='DVSB', fontSize=7, fillColor=bar_c))
        # Etykieta — od lewej krawędzi
        d.add(String(4,
                     y_row + BAR_OFF + BAR_H / 2 - 3.5,
                     _strip_html(lbl),
                     fontName='DVS', fontSize=7.5,
                     fillColor=C_GREY_TXT, textAnchor='start'))

    return d


# ── Diagramy arkuszów obliczeniowych ─────────────────────────────────────────

def _diagram_kd(input_data: dict, theme: colors.Color) -> list:
    """Diagram Kd: rysunek suwnicy + tabela 5 klas widma obciążeń."""
    has_any = any(
        _get_num(input_data.get(f'q_{i}')) is not None or
        _get_num(input_data.get(f'c_{i}')) is not None
        for i in range(1, 6)
    )
    if not has_any:
        return []

    # ── Rysunek suwnicy (SVG 320×320 → 4.8cm) ───────────────────────
    SVG_W, SVG_H = 320, 320
    DW = 4.8 * cm
    DH = DW
    sc = DW / SVG_W

    def rr(sx, sy, sw, sh, **kw):
        return Rect(sx * sc, DH - (sy + sh) * sc, sw * sc, sh * sc, **kw)

    def rl(x1, y1, x2, y2, **kw):
        return Line(x1 * sc, DH - y1 * sc, x2 * sc, DH - y2 * sc, **kw)

    def rc(cx, cy, r, **kw):
        return Circle(cx * sc, DH - cy * sc, r * sc, **kw)

    def rs(sx, sy, txt, **kw):
        return String(sx * sc, DH - sy * sc, txt, **kw)

    t8  = _alpha(theme, 0.08)
    t15 = _alpha(theme, 0.15)
    t20 = _alpha(theme, 0.20)
    t70 = _alpha(theme, 0.70)
    drw = Drawing(DW, DH)

    # Słupy i podstawy
    drw.add(rr(20, 30, 18, 220, fillColor=t8, strokeColor=theme, strokeWidth=1.5))
    drw.add(rr(282, 30, 18, 220, fillColor=t8, strokeColor=theme, strokeWidth=1.5))
    drw.add(rr(10, 248, 38, 10, fillColor=t70, strokeColor=None))
    drw.add(rr(272, 248, 38, 10, fillColor=t70, strokeColor=None))
    # Ukośne stężenia
    for y1, y2 in [(80, 110), (140, 170), (200, 230)]:
        drw.add(rl(20, y1, 38, y2, strokeColor=_alpha(theme, 0.35), strokeWidth=1.0))
        drw.add(rl(300, y1, 282, y2, strokeColor=_alpha(theme, 0.35), strokeWidth=1.0))
    # Szyny górne
    drw.add(rr(10, 26, 38, 8, fillColor=theme, strokeColor=None))
    drw.add(rr(272, 26, 38, 8, fillColor=theme, strokeColor=None))
    # Most — dwuteownik
    drw.add(rr(38, 34, 244, 10, fillColor=t15, strokeColor=theme, strokeWidth=1.5))
    drw.add(rr(155, 44, 10, 24, fillColor=t20, strokeColor=theme, strokeWidth=1.0))
    drw.add(rr(38, 68, 244, 10, fillColor=t15, strokeColor=theme, strokeWidth=1.5))
    # Wózek
    drw.add(rr(138, 55, 44, 22, fillColor=t20, strokeColor=theme, strokeWidth=1.5))
    drw.add(rc(148, 54, 5, fillColor=C_WHITE, strokeColor=theme, strokeWidth=1.5))
    drw.add(rc(172, 54, 5, fillColor=C_WHITE, strokeColor=theme, strokeWidth=1.5))
    # Lina przerywana
    drw.add(rl(160, 77, 160, 172, strokeColor=theme, strokeWidth=1.5,
               strokeDashArray=[4, 2]))
    # Ładunek
    drw.add(rr(96, 196, 128, 72, fillColor=t8, strokeColor=theme, strokeWidth=2.0))
    for xi in range(108, 226, 16):
        clip_y2 = min(268, 196 + (xi - 96))
        drw.add(rl(xi, 196, 96, clip_y2,
                   strokeColor=_alpha(theme, 0.22), strokeWidth=0.8))
    drw.add(rs(160, 238, 'Q', fontName='DVSB', fontSize=10,
               fillColor=theme, textAnchor='middle'))
    # Strzałka siły ciężkości
    drw.add(rl(160, 270, 160, 294, strokeColor=theme, strokeWidth=1.5))
    drw.add(Polygon([160 * sc, DH - 304 * sc,
                     154 * sc, DH - 292 * sc,
                     166 * sc, DH - 292 * sc],
                    fillColor=theme, strokeColor=None))

    # ── Tabela 5 klas ────────────────────────────────────────────────
    TBL_W = USABLE_W - DW - 0.5 * cm
    C1 = 0.7 * cm              # Nr
    C3 = 1.1 * cm              # ci [%]
    C2 = TBL_W - C1 - C3      # qi — reszta szerokości
    tdata = [[
        _p('Nr', font='DVSB', size=8, color=theme, align=1),
        _p('qi [kg / t]', font='DVSB', size=8, color=theme, align=1),
        _p('ci [%]', font='DVSB', size=8, color=theme, align=1),
    ]]
    for i in range(1, 6):
        qv, qu = _split_value_unit(input_data.get(f'q_{i}'))
        cv, _  = _split_value_unit(input_data.get(f'c_{i}'))
        if qv == '-' and cv == '-':
            continue
        q_str = f'{qv} {qu}'.strip() if qu else qv
        tdata.append([
            _p(str(i), font='DVSB', size=8, color=C_BLACK, align=1),
            _p(q_str,  font='DVS',  size=8, color=C_BLACK, align=1),
            _p(cv,     font='DVS',  size=8, color=C_BLACK, align=1),
        ])
    tstyle = [
        ('BACKGROUND', (0, 0), (-1, 0), _alpha(theme, 0.12)),
        ('LINEBEFORE',  (0, 0), (0, -1), 3, theme),
        ('LINEBELOW',   (0, 0), (-1, -1), 0.3, C_GREY_SEP),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ('VALIGN',  (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',   (0, 0), (-1, -1), 'CENTER'),
    ]
    for ri in range(1, len(tdata)):
        tstyle.append(('BACKGROUND', (0, ri), (-1, ri),
                       C_GREY_ROW if ri % 2 == 0 else C_WHITE))
    CW = TBL_W / 3
    tbl = Table(tdata, colWidths=[CW, CW, CW])
    tbl.setStyle(TableStyle(tstyle))

    combo = Table([[drw, tbl]], colWidths=[DW + 0.5 * cm, TBL_W])
    combo.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return [_section_header('Widmo obciążeń — Kd (widmo klas ładunku)', theme),
            Spacer(1, 0.15 * cm), combo, Spacer(1, 0.35 * cm)]


def _diagram_ldr(input_data: dict, theme: colors.Color) -> list:
    """Diagram LDR: pojazd z wysięgnikiem + siatka 5×5 (wierny SVG z SchemLdr.vue)."""
    active = {}
    for n in range(1, 26):
        v = _get_num(input_data.get(f'p_{n}'))
        if v is not None:
            active[n] = v
    if not active:
        return []

    ROW_LABELS = ['80-100%', '60-80%', '40-60%', '20-40%', '0-20%']
    COL_LABELS = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']

    # SVG viewBox "-10 0 410 490" — treść x∈[-10,385], y∈[80,500]
    SVG_CX0, SVG_CY0 = -10, 78
    SVG_CW, SVG_CH   = 398, 425
    DW = 9.5 * cm
    DH = DW * SVG_CH / SVG_CW
    sc = DW / SVG_CW

    def rX(sx): return (sx - SVG_CX0) * sc
    def rY(sy): return DH - (sy - SVG_CY0) * sc

    def rL(x1, y1, x2, y2, **kw):
        return Line(rX(x1), rY(y1), rX(x2), rY(y2), **kw)

    def rR(sx, sy, sw, sh, **kw):
        return Rect(rX(sx), rY(sy + sh), sw * sc, sh * sc, **kw)

    def rC(cx, cy, r, **kw):
        return Circle(rX(cx), rY(cy), r * sc, **kw)

    def rStr(sx, sy, txt, size=6, **kw):
        return String(rX(sx), rY(sy) - size * 0.35, txt, **kw)

    drw = Drawing(DW, DH)

    GRID_X0, GRID_Y0 = 105, 128
    CELL = 48  # SVG units

    # ── Tło siatki ───────────────────────────────────────────────────
    drw.add(rR(GRID_X0, GRID_Y0, 240, 240,
               fillColor=_alpha(theme, 0.05), strokeColor=None))

    # Linie pomocnicze siatki (dashed)
    for row in range(7):
        gy = GRID_Y0 + row * CELL
        drw.add(rL(109, gy, 347, gy,
                   strokeColor=_alpha(theme, 0.35), strokeWidth=0.5,
                   strokeDashArray=[2, 2]))
    for col in range(7):
        gx = GRID_X0 + col * CELL
        drw.add(rL(gx, 125, gx, 372,
                   strokeColor=_alpha(theme, 0.35), strokeWidth=0.5,
                   strokeDashArray=[2, 2]))

    # ── Osie ─────────────────────────────────────────────────────────
    drw.add(rL(105, 368, 105, 88, strokeColor=theme, strokeWidth=1.5))
    drw.add(Polygon([rX(99), rY(100), rX(105), rY(80), rX(111), rY(100)],
                    fillColor=theme, strokeColor=None))
    drw.add(rL(105, 368, 367, 368, strokeColor=theme, strokeWidth=1.5))
    drw.add(Polygon([rX(356), rY(362), rX(373), rY(368), rX(356), rY(374)],
                    fillColor=theme, strokeColor=None))

    # Y-axis ticks i etykiety
    for gy, lbl in [(368, '0%'), (320, '20%'), (272, '40%'),
                    (224, '60%'), (176, '80%'), (128, '100%')]:
        drw.add(rL(99, gy, 111, gy, strokeColor=theme, strokeWidth=1.0))
        drw.add(rStr(93, gy, lbl, size=5.5,
                     fontName='DVS', fontSize=5.5, fillColor=theme, textAnchor='end'))
    drw.add(rStr(52, 248, 'h / h_max', size=5.5,
                 fontName='DVSB', fontSize=5.5, fillColor=theme, textAnchor='middle'))

    # X-axis ticks i etykiety
    for gx, lbl in [(105, '0%'), (153, '20%'), (201, '40%'),
                    (249, '60%'), (297, '80%'), (345, '100%')]:
        drw.add(rL(gx, 366, gx, 374, strokeColor=theme, strokeWidth=1.0))
        drw.add(rStr(gx, 386, lbl, size=5.5,
                     fontName='DVS', fontSize=5.5, fillColor=theme, textAnchor='middle'))
    drw.add(rStr(225, 398, 'Lb / Lmax', size=5.5,
                 fontName='DVSB', fontSize=5.5, fillColor=theme, textAnchor='middle'))

    # ── Pojazd z wysięgnikiem (z SchemLdr.vue) ───────────────────────
    vk = dict(strokeColor=theme, strokeLineCap=1)
    # Koła
    drw.add(rC(48,  462, 19, fillColor=None, strokeColor=theme, strokeWidth=1.8))
    drw.add(rC(161, 462, 19, fillColor=None, strokeColor=theme, strokeWidth=1.8))
    # Podwozie
    for seg in [(-8, 453, 29, 453), (67, 453, 142, 453), (180, 453, 199, 453)]:
        drw.add(rL(*seg, strokeColor=theme, strokeWidth=1.8, strokeLineCap=1))
    # Kabina
    drw.add(rL(-8, 453, -8, 425, strokeColor=theme, strokeWidth=1.8, strokeLineCap=1))
    drw.add(rL(-8, 425, 20,  396, strokeColor=theme, strokeWidth=1.8, strokeLineCap=1))
    drw.add(rL(20, 396, 67,  396, strokeColor=theme, strokeWidth=1.8, strokeLineCap=1))
    drw.add(rL(67, 396, 67,  453, strokeColor=theme, strokeWidth=1.8, strokeLineCap=1))
    drw.add(rL(-8, 425, 67,  425, strokeColor=theme, strokeWidth=1.8, strokeLineCap=1))
    # Prawa platforma
    drw.add(rL(199, 425, 199, 453, strokeColor=theme, strokeWidth=1.8, strokeLineCap=1))
    drw.add(rL(67,  425, 199, 425, strokeColor=theme, strokeWidth=1.8, strokeLineCap=1))
    # Wysięgnik dolny (do pivot siatki)
    drw.add(rL(142, 425, 105, 368, strokeColor=theme, strokeWidth=2.2, strokeLineCap=1))
    # Wysięgnik górny (przez siatkę)
    drw.add(rL(105, 368, 265, 208, strokeColor=theme, strokeWidth=2.2, strokeLineCap=1))
    # Kosz
    drw.add(rR(254, 197, 22, 13, fillColor=theme, strokeColor=None))

    # ── Komórki siatki 5×5 ───────────────────────────────────────────
    for svgRow in range(1, 6):
        for col in range(1, 6):
            n  = (svgRow - 1) * 5 + col
            cx = GRID_X0 + (col - 1) * CELL + 1
            cy = GRID_Y0 + (svgRow - 1) * CELL + 1
            cw = ch = CELL - 2
            sel  = n in active
            fill = _alpha(theme, 0.55) if sel else _alpha(theme, 0.04)
            drw.add(rR(cx, cy, cw, ch,
                       fillColor=fill,
                       strokeColor=_alpha(theme, 0.5 if sel else 0.18),
                       strokeWidth=0.8))
            if sel:
                drw.add(rStr(cx + cw / 2, cy + ch * 0.36, str(n), size=6.5,
                             fontName='DVSB', fontSize=6.5,
                             fillColor=C_WHITE, textAnchor='middle'))
                drw.add(rStr(cx + cw / 2, cy + ch * 0.64, f'{active[n]:.0f}%', size=5.5,
                             fontName='DVSB', fontSize=5.5,
                             fillColor=C_WHITE, textAnchor='middle'))
            else:
                drw.add(rStr(cx + cw / 2, cy + ch * 0.5, str(n), size=5.5,
                             fontName='DVS', fontSize=5.5,
                             fillColor=_alpha(theme, 0.38), textAnchor='middle'))

    # Obramowanie siatki
    drw.add(rR(GRID_X0, GRID_Y0, 240, 240,
               fillColor=None, strokeColor=theme, strokeWidth=1.2))

    # ── Tabela aktywnych stref (obok diagramu) ────────────────────────
    TBL_W = USABLE_W - DW - 0.3 * cm
    tdata = [[_p('Nr',       font='DVSB', size=7.5, color=theme, align=1),
              _p('H zakres', font='DVSB', size=7.5, color=theme, align=1),
              _p('L zakres', font='DVSB', size=7.5, color=theme, align=1),
              _p('pi [%]',   font='DVSB', size=7.5, color=theme, align=1)]]
    for n in sorted(active.keys()):
        row = (n - 1) // 5 + 1
        col = (n - 1) %  5 + 1
        pi_val = active[n]
        tdata.append([
            _p(str(n),              font='DVSB', size=7.5, color=C_BLACK,    align=1),
            _p(ROW_LABELS[row - 1], font='DVS',  size=7,   color=C_GREY_TXT, align=1),
            _p(COL_LABELS[col - 1], font='DVS',  size=7,   color=C_GREY_TXT, align=1),
            _p(f'{pi_val:.0f}',     font='DVSB', size=8,   color=theme,      align=1),
        ])
    tstyle = [
        ('BACKGROUND',  (0, 0), (-1, 0), _alpha(theme, 0.12)),
        ('LINEBEFORE',  (0, 0), (0, -1), 3, theme),
        ('LINEBELOW',   (0, 0), (-1, -1), 0.3, C_GREY_SEP),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',  (0, 0), (-1, -1), 'CENTER'),
    ]
    for ri in range(1, len(tdata)):
        tstyle.append(('BACKGROUND', (0, ri), (-1, ri),
                       C_GREY_ROW if ri % 2 == 0 else C_WHITE))
    CW = TBL_W / 4
    tbl = Table(tdata, colWidths=[CW, CW, CW, CW])
    tbl.setStyle(TableStyle(tstyle))

    combo = Table([[drw, tbl]], colWidths=[DW + 0.3 * cm, TBL_W])
    combo.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return [_section_header('Widmo LDR — zasieg wysiegnika (siatka 5x5)', theme),
            Spacer(1, 0.15 * cm), combo, Spacer(1, 0.35 * cm)]


def _diagram_hdr(input_data: dict, theme: colors.Color) -> list:
    """Diagram HDR: podest nożycowy + 5 stref wysokości (wierny SVG z SchemHdr.vue)."""
    active = {}
    for i in range(1, 6):
        h  = _get_num(input_data.get(f'h_{i}'))
        cc = _get_num(input_data.get(f'cc_{i}'))
        if h is not None or cc is not None:
            active[i] = (h, cc)
    if not active:
        return []

    # SVG viewBox "0 0 420 550" — treść x∈[0,420], y∈[20,490]
    SVG_CX0, SVG_CY0 = 0, 20
    SVG_CW, SVG_CH   = 420, 475
    DW = 7.5 * cm
    DH = DW * SVG_CH / SVG_CW
    sc = DW / SVG_CW

    def rX(sx): return (sx - SVG_CX0) * sc
    def rY(sy): return DH - (sy - SVG_CY0) * sc

    def rL(x1, y1, x2, y2, **kw):
        return Line(rX(x1), rY(y1), rX(x2), rY(y2), **kw)

    def rR(sx, sy, sw, sh, **kw):
        return Rect(rX(sx), rY(sy + sh), sw * sc, sh * sc, **kw)

    def rC(cx, cy, r, **kw):
        return Circle(rX(cx), rY(cy), r * sc, **kw)

    def rStr(sx, sy, txt, size=6, **kw):
        return String(rX(sx), rY(sy) - size * 0.35, txt, **kw)

    drw = Drawing(DW, DH)

    # ── Pasy stref (zony y: strefa5=55–135, 4=135–215, 3=215–295, 2=295–375, 1=375–455) ──
    ZONES_DEF = [
        (5, '80-100% h_max', 55,  0.28, 0.12),
        (4, '60-80% h_max',  135, 0.23, 0.08),
        (3, '40-60% h_max',  215, 0.18, 0.05),
        (2, '20-40% h_max',  295, 0.14, 0.03),
        (1, '0-20% h_max',   375, 0.10, 0.01),
    ]
    for zone_i, range_lbl, gy_top, a_sel, a_unsel in ZONES_DEF:
        sel = zone_i in active
        drw.add(rR(110, gy_top, 290, 80,
                   fillColor=_alpha(theme, a_sel if sel else a_unsel),
                   strokeColor=_alpha(theme, 0.30 if sel else 0.18),
                   strokeWidth=0.8))
        gy_mid = gy_top + 40
        drw.add(rStr(118, gy_mid - 8, f'Strefa {zone_i}', size=7,
                     fontName='DVSB' if sel else 'DVS', fontSize=7,
                     fillColor=theme if sel else _alpha(theme, 0.5)))
        drw.add(rStr(118, gy_mid + 8, range_lbl, size=5.5,
                     fontName='DVS', fontSize=5.5,
                     fillColor=theme if sel else _alpha(theme, 0.35)))
        if sel:
            h_val, cc_val = active[zone_i]
            parts = []
            if h_val  is not None: parts.append(f'h={h_val:.1f}m')
            if cc_val is not None: parts.append(f'cc={cc_val:.0f}%')
            drw.add(rStr(388, gy_mid, '  '.join(parts), size=6,
                         fontName='DVSB', fontSize=6, fillColor=theme, textAnchor='end'))
            drw.add(rC(400, gy_mid, 7, fillColor=theme, strokeColor=None))
            drw.add(rStr(400, gy_mid + 1, 'v', size=5,
                         fontName='DVSB', fontSize=5, fillColor=C_WHITE, textAnchor='middle'))
        if zone_i > 1:  # linia podziału (poza ostatnią strefą)
            drw.add(rL(110, gy_top + 80, 400, gy_top + 80,
                       strokeColor=_alpha(theme, 0.35), strokeWidth=0.5,
                       strokeDashArray=[4, 2]))

    # ── Oś Y + strzałka ─────────────────────────────────────────────
    drw.add(rL(100, 460, 100, 38, strokeColor=theme, strokeWidth=1.5))
    drw.add(Polygon([rX(94), rY(50), rX(100), rY(26), rX(106), rY(50)],
                    fillColor=theme, strokeColor=None))
    for gy, lbl in [(455, '0%'), (375, '20%'), (295, '40%'),
                    (215, '60%'), (135, '80%'), (55, '100%')]:
        drw.add(rL(94, gy, 106, gy, strokeColor=theme, strokeWidth=1.0))
        drw.add(rStr(88, gy, lbl, size=5.5,
                     fontName='DVS', fontSize=5.5, fillColor=theme, textAnchor='end'))
    drw.add(rStr(28, 258, 'h / h_max [%]', size=5.5,
                 fontName='DVSB', fontSize=5.5, fillColor=theme, textAnchor='middle'))
    # Linia terenu
    drw.add(rL(100, 460, 410, 460, strokeColor=_alpha(theme, 0.4), strokeWidth=1.0,
               strokeDashArray=[4, 3]))
    drw.add(rStr(255, 476, 'poziom terenu', size=5,
                 fontName='DVS', fontSize=5, fillColor=_alpha(theme, 0.45),
                 textAnchor='middle'))

    # ── Podest nożycowy (z SchemHdr.vue) ────────────────────────────
    # Koła
    drw.add(rC(175, 470, 11, fillColor=None, strokeColor=theme, strokeWidth=2.2))
    drw.add(rC(285, 470, 11, fillColor=None, strokeColor=theme, strokeWidth=2.2))
    # Rama dolna
    drw.add(rR(158, 454, 144, 13, fillColor=None, strokeColor=theme, strokeWidth=2.2))
    # Nożyce dolny stopień
    drw.add(rL(168, 454, 290, 268, strokeColor=theme, strokeWidth=2.8, strokeLineCap=1))
    drw.add(rL(292, 454, 170, 268, strokeColor=theme, strokeWidth=2.8, strokeLineCap=1))
    drw.add(rC(230, 361, 4.5, fillColor=theme, strokeColor=None))
    # Rama środkowa
    drw.add(rR(162, 260, 136, 11, fillColor=None,
               strokeColor=_alpha(theme, 0.7), strokeWidth=1.8))
    # Nożyce górny stopień
    drw.add(rL(172, 260, 282, 78, strokeColor=theme, strokeWidth=2.8, strokeLineCap=1))
    drw.add(rL(288, 260, 178, 78, strokeColor=theme, strokeWidth=2.8, strokeLineCap=1))
    drw.add(rC(230, 169, 4.5, fillColor=theme, strokeColor=None))
    # Platforma górna
    drw.add(rR(153, 64, 154, 13, fillColor=_alpha(theme, 0.12),
               strokeColor=theme, strokeWidth=2.2))
    # Barierka
    drw.add(rL(160, 64, 160, 36, strokeColor=theme, strokeWidth=2.0))
    drw.add(rL(300, 64, 300, 36, strokeColor=theme, strokeWidth=2.0))
    drw.add(rL(160, 36, 300, 36, strokeColor=theme, strokeWidth=2.0))
    drw.add(rL(160, 50, 300, 50, strokeColor=_alpha(theme, 0.5), strokeWidth=1.4))
    # Sylwetka osoby
    drw.add(rC(230, 28, 8, fillColor=None, strokeColor=theme, strokeWidth=1.8))
    drw.add(rL(230, 36, 230, 58, strokeColor=theme, strokeWidth=1.8))
    drw.add(rL(215, 46, 245, 46, strokeColor=theme, strokeWidth=1.8))
    drw.add(rL(230, 58, 220, 72, strokeColor=theme, strokeWidth=1.8))
    drw.add(rL(230, 58, 240, 72, strokeColor=theme, strokeWidth=1.8))
    # Strzałka h_max
    drw.add(rL(330, 64, 330, 455, strokeColor=_alpha(theme, 0.4), strokeWidth=1.0,
               strokeDashArray=[3, 3]))
    drw.add(Polygon([rX(324), rY(72), rX(330), rY(54), rX(336), rY(72)],
                    fillColor=_alpha(theme, 0.5), strokeColor=None))
    drw.add(Polygon([rX(324), rY(447), rX(330), rY(465), rX(336), rY(447)],
                    fillColor=_alpha(theme, 0.5), strokeColor=None))
    drw.add(rStr(344, 260, 'h_max', size=6,
                 fontName='DVSB', fontSize=6, fillColor=theme, textAnchor='middle'))

    # ── Tabela danych obok ───────────────────────────────────────────
    TBL_W = USABLE_W - DW - 0.3 * cm
    C_h   = 1.4 * cm
    C_cc  = 1.2 * cm
    C_zon = TBL_W - C_h - C_cc
    ZONE_RANGES = {5: '80-100%', 4: '60-80%', 3: '40-60%',
                   2: '20-40%', 1: '0-20%'}
    tdata = [[_p('Strefa', font='DVSB', size=7.5, color=theme, align=1),
              _p('hi [m]',  font='DVSB', size=7.5, color=theme, align=1),
              _p('cci [%]', font='DVSB', size=7.5, color=theme, align=1)]]
    for zone_i in sorted(active.keys(), reverse=True):
        h_val, cc_val = active[zone_i]
        tdata.append([
            _p(f'{zone_i} ({ZONE_RANGES[zone_i]})', font='DVS', size=7, color=C_BLACK, align=1),
            _p(f'{h_val:.1f}'  if h_val  is not None else '-',
               font='DVSB', size=8, color=theme, align=1),
            _p(f'{cc_val:.0f}' if cc_val is not None else '-',
               font='DVSB', size=8, color=theme, align=1),
        ])
    tstyle = [
        ('BACKGROUND', (0, 0), (-1, 0), _alpha(theme, 0.12)),
        ('LINEBEFORE',  (0, 0), (0, -1), 3, theme),
        ('LINEBELOW',   (0, 0), (-1, -1), 0.3, C_GREY_SEP),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',  (0, 0), (-1, -1), 'CENTER'),
    ]
    for ri in range(1, len(tdata)):
        tstyle.append(('BACKGROUND', (0, ri), (-1, ri),
                       C_GREY_ROW if ri % 2 == 0 else C_WHITE))
    CW = TBL_W / 3
    tbl = Table(tdata, colWidths=[CW, CW, CW])
    tbl.setStyle(TableStyle(tstyle))

    combo = Table([[drw, tbl]], colWidths=[DW + 0.3 * cm, TBL_W])
    combo.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return [_section_header('Widmo HDR — strefy wysokosci podnoszenia', theme),
            Spacer(1, 0.15 * cm), combo, Spacer(1, 0.35 * cm)]


def _diagram_ad(input_data: dict, theme: colors.Color) -> list:
    """Diagram αd: rysunek drabiny + tabela 3 katow (winda dekarska)."""
    a1 = _get_num(input_data.get('a_1'))
    a2 = _get_num(input_data.get('a_2'))
    a3 = _get_num(input_data.get('a_3'))
    if all(v is None for v in (a1, a2, a3)):
        return []

    SVG_W, SVG_H = 215, 235
    DW = 4.5 * cm
    DH = DW * SVG_H / SVG_W
    sc = DW / SVG_W

    def rr(sx, sy, sw, sh, **kw):
        return Rect(sx * sc, DH - (sy + sh) * sc, sw * sc, sh * sc, **kw)

    def rl(x1, y1, x2, y2, **kw):
        return Line(x1 * sc, DH - y1 * sc, x2 * sc, DH - y2 * sc, **kw)

    def rs(sx, sy, txt, **kw):
        return String(sx * sc, DH - sy * sc, txt, **kw)

    t8  = _alpha(theme, 0.08)
    t18 = _alpha(theme, 0.18)
    drw = Drawing(DW, DH)

    # Podłoże
    drw.add(rl(0, 215, 215, 215, strokeColor=_alpha(theme, 0.35), strokeWidth=1.0))
    # Attyka
    drw.add(rr(162, 42, 45, 10, fillColor=t18, strokeColor=theme, strokeWidth=1.2))
    # Ściana budynku + kreskowanie
    drw.add(rr(185, 52, 22, 163, fillColor=t8, strokeColor=theme, strokeWidth=1.2))
    for yoff in range(20, 160, 26):
        drw.add(rl(185, 52 + yoff, 207, 52 + yoff - 20,
                   strokeColor=_alpha(theme, 0.18), strokeWidth=0.8))
    # Okno
    drw.add(rr(190, 100, 11, 16, fillColor=_alpha(theme, 0.15),
               strokeColor=theme, strokeWidth=0.8))
    # Drabina
    drw.add(rl(16, 215, 185, 52, strokeColor=theme, strokeWidth=2.0))
    # Poprzeczki
    for pts in [(141.8, 100.8, 134.8, 93.6),
                (102.6, 139.0,  95.6, 131.8),
                ( 63.4, 177.2,  56.4, 170.0)]:
        drw.add(rl(*pts, strokeColor=_alpha(theme, 0.65), strokeWidth=1.0))
    # Platforma/ładunek
    drw.add(Polygon([103.4 * sc, DH - 138.2 * sc,
                     116.3 * sc, DH - 125.7 * sc,
                     109.4 * sc, DH - 118.5 * sc,
                      96.5 * sc, DH - 131.0 * sc],
                    fillColor=_alpha(theme, 0.20),
                    strokeColor=theme, strokeWidth=1.5))
    # Łuk kąta α — SVG: arc center=(185,52), r=25, od 90° do 136° (CW)
    arc_xy = []
    for theta_deg in range(90, 137, 6):
        theta = radians(theta_deg)
        arc_xy.append((185 + 25 * cos(theta)) * sc)
        arc_xy.append(DH - (52 + 25 * sin(theta)) * sc)
    arc_xy.extend([166.9 * sc, DH - 69.4 * sc])
    drw.add(PolyLine(arc_xy, strokeColor=theme, strokeWidth=1.4, strokeLineCap=1))
    # Etykieta α (wewnątrz łuku)
    drw.add(rs(163, 83, '\u03b1', fontName='DVSB', fontSize=10, fillColor=theme))

    # Tabela kątów
    TBL_W = USABLE_W - DW - 0.5 * cm
    C_ang = 1.6 * cm
    C_ai  = TBL_W - C_ang
    tdata = [[_p('Kąt α', font='DVSB', size=8, color=theme, align=1),
              _p('ai [%]', font='DVSB', size=8, color=theme, align=1)]]
    angle_colors = [colors.HexColor('#2E7D32'), theme, colors.HexColor('#EF6C00')]
    for (lbl, val), ac in zip([('30°', a1), ('60°', a2), ('80°', a3)], angle_colors):
        if val is None:
            continue
        tdata.append([
            _p(lbl,          font='DVSB', size=9, color=ac, align=1),
            _p(f'{val:.0f}', font='DVSB', size=9, color=ac, align=1),
        ])
    tstyle = [
        ('BACKGROUND', (0, 0), (-1, 0), _alpha(theme, 0.12)),
        ('LINEBEFORE',  (0, 0), (0, -1), 3, theme),
        ('LINEBELOW',   (0, 0), (-1, -1), 0.3, C_GREY_SEP),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',  (0, 0), (-1, -1), 'CENTER'),
    ]
    for ri in range(1, len(tdata)):
        tstyle.append(('BACKGROUND', (0, ri), (-1, ri),
                       C_GREY_ROW if ri % 2 == 0 else C_WHITE))
    CW = TBL_W / 2
    tbl = Table(tdata, colWidths=[CW, CW])
    tbl.setStyle(TableStyle(tstyle))

    combo = Table([[drw, tbl]], colWidths=[DW + 0.5 * cm, TBL_W])
    combo.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return [_section_header('Wspolczynnik αd — kat drabiny do sciany (winda dekarska)', theme),
            Spacer(1, 0.15 * cm), combo, Spacer(1, 0.35 * cm)]


def _signature_block(theme: colors.Color) -> list:
    """Blok podpisów z szeroką przestrzenią (~3.5cm) na każdy podpis."""
    items = [_section_header('Podpisy', theme), Spacer(1, 0.4 * cm)]

    for label in ('Osoba wykonująca obliczenia', 'Eksploatujący urządzenie'):
        items.append(_p(label.upper(), font='DVSB', size=7.5,
                        color=_alpha(theme, 0.7)))
        items.append(Spacer(1, 0.2 * cm))

        # Wiersz: Data: _______________
        date_row = Table(
            [[_p('Data:', font='DVS', size=8, color=C_GREY_TXT), '']],
            colWidths=[1.6 * cm, USABLE_W - 1.6 * cm],
        )
        date_row.setStyle(TableStyle([
            ('LINEBELOW',     (1, 0), (1, 0), 0.7, C_GREY_SEP),
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ]))
        items.append(date_row)
        items.append(Spacer(1, 3.5 * cm))   # przestrzeń na podpis

        # Wiersz: Podpis: _______________
        sign_row = Table(
            [[_p('Podpis:', font='DVS', size=8, color=C_GREY_TXT), '']],
            colWidths=[1.6 * cm, USABLE_W - 1.6 * cm],
        )
        sign_row.setStyle(TableStyle([
            ('LINEBELOW',     (1, 0), (1, 0), 0.7, C_GREY_SEP),
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ]))
        items.append(sign_row)
        items.append(Spacer(1, 0.9 * cm))

    return items


# ── Nagłówek strony ──────────────────────────────────────────────────────────

def _build_header(result, calc_name: str, logo_obj, theme: colors.Color) -> list:
    items = []
    logo_img = None
    logo_w_cm = 4.5
    logo_pos = 'right'

    # Logo: pokaż tylko jeśli użytkownik ma włączoną opcję w profilu
    use_logo = getattr(result.user, 'show_logo_on_pdf', True)
    if use_logo:
        # Jeśli przekazano konkretne logo (z dropdownu), użyj go. 
        # W przeciwnym razie użyj domyślnego loga użytkownika.
        active_img_obj = logo_obj
        if not active_img_obj:
            active_img_obj = getattr(result.user, 'custom_logo', None)
            # Jeśli user ma wiele logotypów, pobierz domyślny z modelu UserLogo
            if not active_img_obj:
                try:
                    from users.models import UserLogo
                    active_img_obj = UserLogo.objects.filter(user=result.user, is_default=True).first()
                except Exception:
                    pass

        if active_img_obj:
            # Obsługa zarówno starych logotypów (FileField na User) jak i nowych (UserLogo)
            active_img = getattr(active_img_obj, 'image', active_img_obj)
            logo_w_mm  = getattr(active_img_obj, 'width', getattr(result.user, 'logo_width', 45))
            logo_h_mm  = getattr(active_img_obj, 'height', getattr(result.user, 'logo_height', 20))
            logo_pos   = getattr(active_img_obj, 'position', getattr(result.user, 'logo_position', 'right'))
            
            logo_w_cm  = logo_w_mm / 10.0
            if active_img and hasattr(active_img, 'path'):
                try:
                    with PILImage.open(active_img.path) as pil:
                        ow, oh = pil.size
                    aspect = oh / float(ow)
                    w = logo_w_cm * cm
                    h = w * aspect
                    max_h = (logo_h_mm / 10.0) * cm
                    if h > max_h:
                        h = max_h
                        w = h / aspect
                    logo_img = Image(active_img.path, width=w, height=h)
                except Exception:
                    pass

    title = _p(f'Wyznaczenie resursu — {calc_name}',
               font='DVSB', size=12, color=theme)
    subtitle = _p(
        f'Data obliczeń: {result.created_at.strftime("%d.%m.%Y")}   '
        f'Użytkownik: {result.user.email}',
        font='DVS', size=8, color=C_GREY_TXT)
    txt_block = Table([[title], [subtitle]],
                      colWidths=[USABLE_W - (logo_w_cm + 0.5) * cm if logo_img else USABLE_W])

    if logo_img:
        lw = (logo_w_cm + 0.5) * cm
        tw = USABLE_W - lw
        txt_block = Table([[title], [subtitle]], colWidths=[tw])
        row = [txt_block, logo_img] if logo_pos != 'left' else [logo_img, txt_block]
        widths = [tw, lw] if logo_pos != 'left' else [lw, tw]
        hdr = Table([row], colWidths=widths)
    else:
        hdr = Table([[txt_block]], colWidths=[USABLE_W])

    hdr.setStyle(TableStyle([
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING',   (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 6),
        ('LINEBELOW',    (0, 0), (-1, -1), 2, theme),
    ]))
    items.append(hdr)
    items.append(Spacer(1, 0.4 * cm))
    return items


# ── Klasa canvas z numerami stron ─────────────────────────────────────────────

class _NumberedCanvas(Canvas):
    """Canvas rysujący "Strona X / Y" w stopce każdej strony."""

    def __init__(self, *args, theme=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._theme = theme or colors.HexColor('#1565C0')
        self._pages = []

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pages)
        for i, page in enumerate(self._pages, 1):
            self.__dict__.update(page)
            self._draw_footer(i, total)
            Canvas.showPage(self)
        Canvas.save(self)

    def _draw_footer(self, page_num: int, total: int):
        self.saveState()
        y = MARGIN_V * 0.55
        # Linia stopki
        self.setStrokeColor(_alpha(self._theme, 0.35))
        self.setLineWidth(0.5)
        self.line(MARGIN_H, y + 8, PAGE_W - MARGIN_H, y + 8)
        # Tekst strony
        self.setFont('DVS', 7.5)
        self.setFillColor(C_GREY_TXT)
        self.drawRightString(PAGE_W - MARGIN_H, y,
                             f'Strona {page_num} / {total}')
        # Serwis
        self.setFont('DVS', 7)
        self.setFillColor(_alpha(self._theme, 0.5))
        self.drawString(MARGIN_H, y, 'wyznaczresurs.com')
        self.restoreState()


# ── Etykiety wejściowe ────────────────────────────────────────────────────────

INPUT_LABELS = {
    'wykonawca':            'Wykonawca',
    'uwagi':                'Uwagi',
    'typ':                  'Typ urządzenia',
    'nr_fabryczny':         'Nr fabryczny',
    'nr_ewidencyjny':       'Nr ewidencyjny UDT',
    'producent':            'Producent',
    'nr_udt':               'Nr ewidencyjny UDT',
    'lata_pracy':           'Ilość przepracowanych lat',
    'ilosc_cykli':          'Ilość odbytych cykli',
    'cykle_zmiana':         'Ilość cykli / zmiana',
    'dni_robocze':          'Przyjęta ilość dni roboczych / rok',
    'tryb_pracy':           'Tryb pracy',
    'sposob_rejestracji':   'Sposób rejestracji warunków eksploatacji',
    'q_max':                'Udźwig maksymalny Q_max',
    'q_o':                  'Masa osprzętu Q_osp',
    'h_max':                'Maks. wysokość podnoszenia h_max',
    'v_pod':                'Prędkość podnoszenia v_pod',
    'v_jaz':                'Prędkość jazdy',
    'v_prz':                'Prędkość przesuwu',
    's_sz':                 'Długość szyny jezdnej s',
    'max_cykle_prod':       'Graniczna ilość cykli wg producenta',
    'spec':                 'Wyznaczenie po pierwszym przeglądzie specjalnym',
    'ponowny_resurs':       'Ponowne wyznaczenie resursu',
    'ostatni_resurs':       'Wykorzystanie resursu — poprzednie obliczenia',
    'data_resurs':          'Data poprzednich obliczeń resursu',
    'ster':                 'Rodzaj sterowania',
    'gnp_check':            'GNP',
    'gnp_czas':             'Przewidywany czas pracy GNP',
    'mechanizm_pomocniczy': 'Mechanizm pomocniczy',
    'czas_pracy_mech':      'Średni czas pracy mechanizmu / cykl',
    'konstrukcja':          'Stan konstrukcji stalowej',
    'automatyka':           'Sprawność automatyki sterującej',
    'sworznie':             'Stan sworzni i połączeń rozłącznych',
    'ciegna':               'Stan cięgien (łańcuchy, liny)',
    'eksploatacja':         'Eksploatacja zgodna z przeznaczeniem',
    'szczelnosc':           'Szczelność układu hydraulicznego',
    'hamulce':              'Sprawność układu hamulcowego',
    'nakretka':             'Stan nakrętki kontrującej i bolca',
    'warkocz':              'Warkocz lin nośnych',
    'rok_budowy':           'Rok budowy',
    'przeznaczenie':        'Przeznaczenie',
    'operator':             'Rodzaj obsługi',
    'budynek':              'Miejsce zabudowy',
    'przystanki':           'Ilość przystanków',
    'liczba_dzwigow':       'Liczba dźwigów obsługujących przystanki',
    'h_pod':                'Wysokość podnoszenia kabiny',
    'pyt_motogodzin':       'Licznik motogodzin',
    'licznik_pracy':        'Łączna ilość motogodzin',
    'cykle_dzwig':          'Ilość jazd dźwigu',
    'naped':                'Rodzaj napędu',
    'operatorzy':           'Ilość operatorów',
    'powierzchnia':         'Stan powierzchni magazynu',
    'serwis':               'Plan serwisowy',
    'dlugosc_widel':        'Długość wideł',
    'kat_masztu_alfa':      'Kąt przechyłu masztu α',
    'kat_masztu_beta':      'Kąt przechyłu masztu β',
    'motogodziny':          'Łączna ilość motogodzin',
    'efektywny_czas':       'Efektywny czas pracy',
    'klasa_naprezenia':     'Klasa współczynnika naprężeń',
    # Widmo Kd
    'q_1': 'Ciężar — cykl C₁',   'c_1': 'Udział cykli C₁',
    'q_2': 'Ciężar — cykl C₂',   'c_2': 'Udział cykli C₂',
    'q_3': 'Ciężar — cykl C₃',   'c_3': 'Udział cykli C₃',
    'q_4': 'Ciężar — cykl C₄',   'c_4': 'Udział cykli C₄',
    'q_5': 'Ciężar — cykl C₅',   'c_5': 'Udział cykli C₅',
    # Widmo HDR
    'h_1': 'Wys. podnoszenia H₁',  'cc_1': 'Udział czasu T₁',
    'h_2': 'Wys. podnoszenia H₂',  'cc_2': 'Udział czasu T₂',
    'h_3': 'Wys. podnoszenia H₃',  'cc_3': 'Udział czasu T₃',
    'h_4': 'Wys. podnoszenia H₄',  'cc_4': 'Udział czasu T₄',
    'h_5': 'Wys. podnoszenia H₅',  'cc_5': 'Udział czasu T₅',
}

# Etykiety wynikowe: klucz → (etykieta, jednostka)
OUTPUT_LABELS = {
    'resurs_wykorzystanie':      ('Stopień wykorzystania resursu',          '%'),
    'U_WSK':                     ('Projektowa zdolność cyklowa U_WSK',     'cykli'),
    'T_WSK':                     ('Projektowa zdolność czasowa T_WSK',     'h'),
    'F_X':                       ('Współczynnik niepewności F_X',           '—'),
    'ilosc_cykli':               ('Ilość odbytych cykli',                   'cykli'),
    'ilosc_cykli_rok':           ('Ilość cykli / rok',                     'cykli/rok'),
    'czas_uzytkowania_mech':     ('Czas użytkowania mechanizmu',            'h'),
    'czas_uzytkowania_mech_rok': ('Czas użytkowania mechanizmu / rok',      'h/rok'),
    'wsp_kdr':                   ('Współczynnik widma obciążeń K_d',        '—'),
    'wsp_km':                    ('Współczynnik widma k_m',                 '—'),
    'stan_obciazenia':           ('Klasa stanu obciążenia',                 ''),
    'data_prognoza':             ('Symulowana data wyczerpania resursu',    ''),
    'resurs_prognoza_dni':       ('Dni do wyczerpania resursu *',           'dni'),
    'ldr':                       ('Współczynnik LDR',                       '—'),
    'hdr':                       ('Współczynnik HDR',                       '—'),
    'ss_factor':                 ('Współczynnik SS',                        '—'),
    'zalecenia':                 ('Zalecenia',                              ''),
    'prognoza':                  ('Prognoza eksploatacji',                  'lat'),
    'wiek_dzwigu':               ('Wiek dźwigu',                            'lat'),
}

_PARAM_ORDER = [
    'typ', 'nr_fabryczny', 'nr_ewidencyjny', 'nr_udt', 'producent',
    'wykonawca', 'uwagi',
    'q_max', 'h_max', 'v_pod', 'v_jaz', 'v_prz', 's_sz',
    'ponowny_resurs', 'data_resurs', 'ostatni_resurs',
    'lata_pracy', 'ilosc_cykli', 'cykle_zmiana', 'dni_robocze', 'tryb_pracy',
    'sposob_rejestracji', 'max_cykle_prod',
    'ster', 'gnp_check', 'gnp_czas', 'mechanizm_pomocniczy', 'czas_pracy_mech',
    'q_o', 'spec',
    'konstrukcja', 'automatyka', 'sworznie', 'ciegna',
    'eksploatacja', 'szczelnosc', 'hamulce', 'nakretka', 'warkocz',
    'rok_budowy', 'przeznaczenie', 'operator', 'budynek', 'przystanki',
    'liczba_dzwigow', 'h_pod', 'pyt_motogodzin', 'licznik_pracy', 'cykle_dzwig',
    'naped', 'operatorzy', 'powierzchnia', 'serwis',
    'dlugosc_widel', 'kat_masztu_alfa', 'kat_masztu_beta',
    'motogodziny', 'efektywny_czas', 'klasa_naprezenia',
]

_RESULT_ORDER = [
    'wsp_kdr', 'wsp_km', 'ldr', 'hdr', 'ss_factor',
    'stan_obciazenia', 'F_X',
    'U_WSK', 'T_WSK', 'ilosc_cykli', 'czas_uzytkowania_mech',
    'ilosc_cykli_rok', 'czas_uzytkowania_mech_rok',
    'resurs_wykorzystanie',
    'resurs_prognoza_dni', 'data_prognoza',
    'prognoza', 'wiek_dzwigu',
]

_SKIP_KEYS = {
    'resurs_message', 'technical_state_reached', 'resurs',
    # Pola diagramów — wyświetlane we własnych sekcjach, nie w tabeli parametrów
    'diagram_kd', 'diagram_hdr', 'diagram_ldr', 'diagram_ad',
    'q_1', 'q_2', 'q_3', 'q_4', 'q_5',
    'c_1', 'c_2', 'c_3', 'c_4', 'c_5',
    'h_1', 'h_2', 'h_3', 'h_4', 'h_5',
    'cc_1', 'cc_2', 'cc_3', 'cc_4', 'cc_5',
    'a_1', 'a_2', 'a_3',
    # p_1..p_25 (LDR)
    *[f'p_{i}' for i in range(1, 26)],
    # warning_kd (wewnętrzne)
    'warning_kd',
}


# ── Główna funkcja ────────────────────────────────────────────────────────────

def generate_result_pdf(result, calculator_name: str,
                        logo_obj=None, signature_obj=None) -> bytes:
    """Generuje nowoczesny raport PDF dla wyniku obliczeń resursu."""

    user_color = (getattr(logo_obj, 'theme_color', None)
                  or getattr(result.user, 'theme_color', '#1565C0'))
    THEME = colors.HexColor(user_color)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=MARGIN_H, leftMargin=MARGIN_H,
        topMargin=MARGIN_V, bottomMargin=MARGIN_V + 0.6 * cm,
        title=f'Resurs — {calculator_name}',
        author='wyznaczresurs.com',
    )

    story = []
    input_data  = result.input_data  or {}
    output_data = result.output_data or {}

    # ── Nagłówek ────────────────────────────────────────────────────────────
    story += _build_header(result, calculator_name, logo_obj, THEME)

    # ── Sekcja: Parametry wejściowe ──────────────────────────────────────────
    story.append(_section_header('Parametry wejściowe', THEME))
    story.append(Spacer(1, 0.15 * cm))

    seen = set()
    param_rows = []
    for key in _PARAM_ORDER:
        if key not in input_data or key in _SKIP_KEYS:
            continue
        val, unit = _split_value_unit(input_data[key])
        if val == '-':
            continue
        label = INPUT_LABELS.get(key, key.replace('_', ' ').capitalize())
        if not unit:
            unit = _extract_unit(label)
        param_rows.append((label, val, unit))
        seen.add(key)

    for key, raw in input_data.items():
        if key in seen or key in _SKIP_KEYS:
            continue
        val, unit = _split_value_unit(raw)
        if val == '-':
            continue
        label = INPUT_LABELS.get(key, key.replace('_', ' ').capitalize())
        if not unit:
            unit = _extract_unit(label)
        param_rows.append((label, val, unit))

    if param_rows:
        story.append(_param_table(param_rows, THEME, is_results=False))
    story.append(Spacer(1, 0.4 * cm))

    # ── Sekcja: Wyniki techniczne ────────────────────────────────────────────
    story.append(_section_header('Wyniki obliczeń resursu', THEME))
    story.append(Spacer(1, 0.15 * cm))

    result_rows = []
    seen_out = set()
    for key in _RESULT_ORDER:
        val = output_data.get(key)
        if val is None:
            continue
        label, unit_hint = OUTPUT_LABELS.get(key, (key.replace('_', ' ').capitalize(), ''))
        v, u = _split_value_unit(val, unit_hint)
        if v == '-':
            continue
        result_rows.append((label, v, u))
        seen_out.add(key)

    for key, raw in output_data.items():
        if key in seen_out or key in _SKIP_KEYS:
            continue
        label, unit_hint = OUTPUT_LABELS.get(key, (key.replace('_', ' ').capitalize(), ''))
        v, u = _split_value_unit(raw, unit_hint)
        if v != '-':
            result_rows.append((label, v, u))

    if result_rows:
        story.append(_param_table(result_rows, THEME, is_results=True))
    story.append(Spacer(1, 0.4 * cm))

    # ── Status / komunikat ───────────────────────────────────────────────────
    msg = output_data.get('resurs_message', '')
    if msg:
        story.append(_section_header('Status analizy', THEME))
        story.append(Spacer(1, 0.15 * cm))
        msg_cell = _p(msg, font='DVSB', size=9, color=THEME)
        t = Table([[msg_cell]], colWidths=[USABLE_W])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (0, 0), _alpha(THEME, 0.06)),
            ('LINEBEFORE',    (0, 0), (0, 0), 3, THEME),
            ('LEFTPADDING',   (0, 0), (0, 0), 12),
            ('TOPPADDING',    (0, 0), (0, 0), 8),
            ('BOTTOMPADDING', (0, 0), (0, 0), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4 * cm))

    # ── Strona 2: Wykresy ────────────────────────────────────────────────────
    story.append(PageBreak())
    story += _build_header(result, calculator_name, logo_obj, THEME)

    # Wykres: stopień wykorzystania
    resurs_val = output_data.get('resurs_wykorzystanie')
    if resurs_val is not None:
        try:
            rv = float(resurs_val)
            story.append(_section_header('Stopień wykorzystania resursu', THEME))
            story.append(Spacer(1, 0.15 * cm))
            story.append(Table(
                [[_bar_chart([('Stopień zużycia [%]', rv, max(rv * 1.1, 100))], THEME)]],
                colWidths=[USABLE_W]))
            story.append(Spacer(1, 0.4 * cm))
        except (ValueError, TypeError):
            pass

    # Wykres: cykle vs U_WSK
    u_wsk  = output_data.get('U_WSK')
    ilosc  = output_data.get('ilosc_cykli') or input_data.get('ilosc_cykli')
    if u_wsk is not None and ilosc is not None:
        try:
            uv = float(u_wsk)
            iv, _ = _split_value_unit(ilosc)
            iv = float(iv.replace(',', '.').replace(' ', ''))
            max_v = max(uv, iv) * 1.1
            story.append(_section_header('Zestawienie — Ilość cykli vs U_WSK', THEME))
            story.append(Spacer(1, 0.15 * cm))
            story.append(Table(
                [[_bar_chart([
                    ('Odbyte cykle', iv, max_v),
                    ('Zdolność cyklowa U_WSK', uv, max_v),
                ], THEME)]],
                colWidths=[USABLE_W]))
            story.append(Spacer(1, 0.4 * cm))
        except (ValueError, TypeError, AttributeError):
            pass

    # Wykres: czas vs T_WSK
    t_wsk = output_data.get('T_WSK')
    czas  = output_data.get('czas_uzytkowania_mech')
    if t_wsk is not None and czas is not None:
        try:
            tv = float(t_wsk)
            cv, _ = _split_value_unit(czas)
            cv = float(cv.replace(',', '.').replace(' ', ''))
            max_v = max(tv, cv) * 1.1
            story.append(_section_header('Zestawienie — Czas użytkowania vs T_WSK', THEME))
            story.append(Spacer(1, 0.15 * cm))
            story.append(Table(
                [[_bar_chart([
                    ('Czas użytkowania [h]', cv, max_v),
                    ('Zdolność czasowa T_WSK [h]', tv, max_v),
                ], THEME)]],
                colWidths=[USABLE_W]))
            story.append(Spacer(1, 0.4 * cm))
        except (ValueError, TypeError, AttributeError):
            pass

    # ── Diagramy arkuszów obliczeniowych ────────────────────────────────────────
    story += _diagram_kd(input_data, THEME)
    story += _diagram_ldr(input_data, THEME)
    story += _diagram_hdr(input_data, THEME)
    story += _diagram_ad(input_data, THEME)

    # Przebieg (ponowny resurs)
    if str(input_data.get('ponowny_resurs', '')).lower() in ('tak', '1', 'true'):
        ostatni_raw = input_data.get('ostatni_resurs')
        ostatni_str, _ = _split_value_unit(ostatni_raw)   # wyciąga wartość z dict
        data_raw = input_data.get('data_resurs', '')
        data_ost_raw, _ = _split_value_unit(data_raw)      # plain string lub dict
        # Formatuj datę do polskiego formatu
        try:
            from datetime import datetime as _dt
            data_ost = _dt.strptime(data_ost_raw, '%Y-%m-%d').strftime('%d.%m.%Y')
        except (ValueError, TypeError):
            data_ost = data_ost_raw or '-'
        data_now = result.created_at.strftime('%d.%m.%Y')
        rv_str   = str(resurs_val) if resurs_val is not None else '-'
        try:
            zmiana = f"{float(rv_str) - float(ostatni_str):+.2f}"
        except (ValueError, TypeError):
            zmiana = '-'
        story.append(_section_header('Przebieg — Stopień wykorzystania resursu', THEME))
        story.append(Spacer(1, 0.15 * cm))
        story.append(_param_table([
            ('Poprzednie obliczenia  (' + data_ost + ')', ostatni_str, '%'),
            ('Bieżące obliczenia  (' + data_now + ')',    rv_str,      '%'),
            ('Zmiana stopnia wykorzystania',               zmiana,      '%'),
        ], THEME, is_results=True))
        story.append(Spacer(1, 0.4 * cm))

    # ── Podpis cyfrowy (pieczęć/grafika) ────────────────────────────────────────
    story.append(Spacer(1, 0.2 * cm))
    if getattr(result.user, 'show_signature_on_pdf', True):
        if not signature_obj:
            try:
                from users.models import UserSignature
                signature_obj = UserSignature.objects.filter(
                    user=result.user, is_default=True).first()
            except Exception:
                pass
        if signature_obj:
            try:
                with PILImage.open(signature_obj.image.path) as pil:
                    ow, oh = pil.size
                aspect = oh / float(ow)
                ws = (signature_obj.width  / 10.0) * cm
                hs = ws * aspect
                max_hs = (signature_obj.height / 10.0) * cm
                if hs > max_hs:
                    hs = max_hs
                    ws = hs / aspect
                sig_img = Image(signature_obj.image.path, width=ws, height=hs)
                align = {'bottom_left': 'LEFT', 'bottom_center': 'CENTER'}.get(
                    signature_obj.position, 'RIGHT')
                sig_t = Table([[sig_img]], colWidths=[USABLE_W])
                sig_t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), align)]))
                story.append(sig_t)
                if signature_obj.name:
                    al = {'bottom_left': 0, 'bottom_center': 1}.get(
                        signature_obj.position, 2)
                    story.append(_p(signature_obj.name, size=7.5,
                                    color=C_GREY_TXT, align=al))
                story.append(Spacer(1, 0.3 * cm))
            except Exception:
                pass

    # ── Blok podpisów (z dużą przestrzenią) ─────────────────────────────────────
    story += _signature_block(THEME)

    # ── Stopka prawna ─────────────────────────────────────────────────────────
    legal = [
        'Dane o przebiegu eksploatacji wprowadzono w oparciu o oświadczeniu eksploatującego urządzenie.',
        ('* Symulowana data osiągnięcia resursu może ulec zmianie w zależności od przyszłych warunków eksploatacji. '
         'Przypomina się o konieczności rejestrowania przebiegu eksploatacji urządzenia — podstawa: '
         '§ 7.2 RMPiT z dnia 30 października 2018 r.'),
        'W przypadku modernizacji urządzenia w zakresie parametrów przyjętych do obliczeń należy wyznaczyć resurs ponownie.',
    ]
    for txt in legal:
        story.append(_p(txt, size=7, color=C_GREY_TXT, align=1))
        story.append(Spacer(1, 0.1 * cm))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story,
              canvasmaker=lambda *a, **kw: _NumberedCanvas(*a, theme=THEME, **kw))
    return buffer.getvalue()
