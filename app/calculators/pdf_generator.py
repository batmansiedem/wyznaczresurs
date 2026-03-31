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
    Spacer, Image, PageBreak, HRFlowable, KeepTogether, CondPageBreak,
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, PolyLine, Polygon
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

# ── Czcionki ────────────────────────────────────────────────────────────────
FONT_PATH = os.path.join(settings.BASE_DIR, 'core', 'fonts')
pdfmetrics.registerFont(TTFont('DVS',  os.path.join(FONT_PATH, 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DVSB', os.path.join(FONT_PATH, 'DejaVuSans-Bold.ttf')))

from .device_config import load_config as _load_device_config


def _is_field_visible_in_pdf(key: str, slug: str, input_data: dict) -> bool:
    """Zwraca True jeśli pole powinno być widoczne wg show_if z konfiguracji urządzenia."""
    slug_fields = _load_device_config(slug).get('fields', {})
    field_def = slug_fields.get(key, {})
    show_if = field_def.get('show_if')
    if not show_if:
        return True
    ctrl_field = show_if.get('field')
    required_val = show_if.get('value')
    cur = input_data.get(ctrl_field)
    if isinstance(cur, dict):
        cur = cur.get('value')
    cur_str = str(cur) if cur is not None else ''
    if isinstance(required_val, list):
        matched = any(str(v) in cur_str for v in required_val)
    else:
        matched = cur_str == str(required_val)
    negate = show_if.get('negate', False)
    return not matched if negate else matched


# ── Stałe layoutu ────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN_H = 1.5 * cm
MARGIN_V = 1.5 * cm
MARGIN_TOP = 2.0 * cm   # górny margines (canvas nagłówek zajmuje ~1.5cm strefy nad treścią)
USABLE_W = PAGE_W - 2 * MARGIN_H   # ~18 cm

# Kolumny tabeli parametrów: etykieta | wartość | jednostka
COL_LABEL = 9.5 * cm
COL_VALUE = 6.0 * cm
COL_UNIT  = USABLE_W - COL_LABEL - COL_VALUE  # ~2.5 cm

# ── Kolory bazowe (szarości) ─────────────────────────────────────────────────
C_WHITE    = colors.white
C_BLACK    = colors.HexColor('#1a1a2e')
C_GREY_TXT = colors.HexColor('#555555')
C_GREY_ROW = colors.white                  # brak przemiennego tła — oszczędność tuszu
C_GREY_SEP = colors.HexColor('#d8dce4')    # linia oddzielająca (delikatna)
C_GREY_HDR = colors.HexColor('#eef0f4')    # tło nagłówka sekcji
C_SECONDARY = colors.HexColor('#1976D2')   # secondary blue (jak na stronie — kolor "resurs")


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


def _fmt_num(s: str) -> str:
    """Formatuje liczbę do wyświetlenia: 2 miejsca po przecinku, spacja jako separator tysięcy,
    bez notacji wykładniczej. Zwraca niezmieniony string jeśli to nie liczba."""
    if s in ('-', '', None):
        return s or '-'
    try:
        f = float(str(s).replace(',', '.').replace(' ', ''))
        if abs(f - round(f)) < 1e-9 and abs(f) < 1e12:
            return f'{int(round(f)):,}'.replace(',', ' ')
        else:
            rounded = round(f, 2)
            parts = f'{rounded:,.2f}'.split('.')
            return parts[0].replace(',', ' ') + ',' + parts[1]
    except (ValueError, TypeError):
        return str(s)


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
        tdata.append([
            _p(lbl,  font='DVS',  size=8.5, color=C_GREY_TXT),
            _p(val,  font='DVSB', size=9,   color=val_color, align=2),
            _p(unit, font='DVS',  size=8,   color=C_GREY_TXT),
        ])

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
        ('LINEBEFORE',    (0, 0), (0, 0), 4, theme),
        ('LINEBELOW',     (0, 0), (0, 0), 0.5, _alpha(theme, 0.3)),
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
    LABEL_W   = 7.5 * cm
    RIGHT_PAD = 1.6 * cm   # margines prawy na etykietę wartości
    BAR_ZONE  = USABLE_W - LABEL_W - RIGHT_PAD
    ROW_H     = 1.2 * cm
    BAR_H     = ROW_H * 0.48
    BAR_OFF   = (ROW_H - BAR_H) / 2
    AXIS_H    = 0.75 * cm
    TOTAL_H   = ROW_H * len(bars) + AXIS_H
    RR        = BAR_H / 2   # promień zaokrąglenia (pill)

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
        val_str = _fmt_num(str(int(round(float(val)))) if isinstance(val, (int, float)) else str(val))

        # Track — kontur bez wypełnienia
        d.add(Rect(LABEL_W, y_row + BAR_OFF, BAR_ZONE, BAR_H,
                   fillColor=None, strokeColor=_alpha(theme, 0.25),
                   strokeWidth=0.7, rx=RR, ry=RR))
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

def _diagram_kd(input_data: dict, theme: colors.Color, is_mech: bool = False) -> list:
    """Diagram Kd: rysunek suwnicy + tabela 5 klas widma obciążeń.
    Zawsze renderuje rysunek SVG. Tabelę qi/ci pokazuje tylko gdy dane są dostępne.
    Dla mechanizmów używa etykiety K_m zamiast K_d."""
    has_any = any(
        _get_num(input_data.get(f'q_{i}')) is not None or
        _get_num(input_data.get(f'c_{i}')) is not None
        for i in range(1, 6)
    )

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
    if has_any:
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
    else:
        # Widmo nie zostało zdefiniowane — pokaż informację zamiast pustej tabeli
        tdata.append([
            _p('—', font='DVS', size=8, color=C_GREY_SEP, align=1),
            _p('Widmo nie zdefiniowane', font='DVS', size=8, color=C_GREY_SEP, align=1),
            _p('—', font='DVS', size=8, color=C_GREY_SEP, align=1),
        ])
    tstyle = [
        ('LINEBEFORE',  (0, 0), (0, -1), 3, theme),
        ('LINEBELOW',   (0, 0), (-1, -1), 0.3, C_GREY_SEP),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ('VALIGN',  (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',   (0, 0), (-1, -1), 'CENTER'),
    ]
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
    section_title = 'Współczynnik K_m i stan obciążenia' if is_mech else 'Współczynnik K_d i stan obciążenia'
    return [_section_header(section_title, theme),
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
        ('LINEBEFORE',  (0, 0), (0, -1), 3, theme),
        ('LINEBELOW',   (0, 0), (-1, -1), 0.3, C_GREY_SEP),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',  (0, 0), (-1, -1), 'CENTER'),
    ]
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
    return [_section_header('Współczynnik wykorzystania wysięgu L_DR', theme),
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
        ('LINEBEFORE',  (0, 0), (0, -1), 3, theme),
        ('LINEBELOW',   (0, 0), (-1, -1), 0.3, C_GREY_SEP),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',  (0, 0), (-1, -1), 'CENTER'),
    ]
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
    return [_section_header('Współczynnik wykorzystania wysięgu H_DR', theme),
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
        ('LINEBEFORE',  (0, 0), (0, -1), 3, theme),
        ('LINEBELOW',   (0, 0), (-1, -1), 0.3, C_GREY_SEP),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',  (0, 0), (-1, -1), 'CENTER'),
    ]
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

    # Logo: pokaż jeśli użytkownik ma włączoną opcję i wykupione logo
    use_logo = getattr(result.user, 'show_logo_on_pdf', True)
    has_purchased = getattr(result.user, 'has_custom_logo', False)
    if use_logo and (logo_obj or has_purchased):
        active_img_obj = logo_obj
        if not active_img_obj:
            try:
                from users.models import UserLogo
                active_img_obj = (
                    UserLogo.objects.filter(user=result.user, is_default=True).first()
                    or UserLogo.objects.filter(user=result.user).order_by('-created_at').first()
                )
            except Exception:
                pass

        if active_img_obj:
            active_img = getattr(active_img_obj, 'image', active_img_obj)
            logo_w_mm  = getattr(active_img_obj, 'width',    getattr(result.user, 'logo_width',    45))
            logo_h_mm  = getattr(active_img_obj, 'height',   getattr(result.user, 'logo_height',   20))
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

    nr_fab = result.input_data.get('nr_fabryczny', '') if result.input_data else ''

    # Blok tekstowy: tytuł + nr fabryczny + data
    row1 = _p(f'Wyznaczenie resursu — {calc_name}',
              font='DVSB', size=14, color=theme)
    detail_parts = []
    if nr_fab:
        detail_parts.append(f'Nr fabryczny: {nr_fab}')
    detail_parts.append(f'Data obliczeń: {result.created_at.strftime("%d.%m.%Y")}')
    row2 = _p('   |   '.join(detail_parts), font='DVS', size=8.5, color=C_GREY_TXT)

    # Obszar logo: 5cm dla niestandardowego loga lub brandingu serwisu
    LOGO_ZONE_W = 5.0 * cm
    txt_w = USABLE_W - LOGO_ZONE_W

    txt_block = Table([[row1], [row2]], colWidths=[txt_w])
    txt_block.setStyle(TableStyle([
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    # Pozycja top_center: logo wyśrodkowane nad blokiem tekstowym
    if logo_pos == 'top_center' and logo_img:
        logo_t = Table([[logo_img]], colWidths=[USABLE_W])
        logo_t.setStyle(TableStyle([
            ('ALIGN',         (0, 0), (0, 0), 'CENTER'),
            ('LEFTPADDING',   (0, 0), (0, 0), 0),
            ('RIGHTPADDING',  (0, 0), (0, 0), 0),
            ('TOPPADDING',    (0, 0), (0, 0), 4),
            ('BOTTOMPADDING', (0, 0), (0, 0), 6),
        ]))
        full_txt = Table([[row1], [row2]], colWidths=[USABLE_W])
        full_txt.setStyle(TableStyle([
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW',     (0, -1), (0, -1), 1.5, theme),
        ]))
        items.append(logo_t)
        items.append(full_txt)
        items.append(Spacer(1, 0.35 * cm))
        return items

    if logo_img:
        logo_cell = logo_img
    else:
        # Brak niestandardowego loga — branding serwisu w kolorach jak na stronie
        # "wyznacz" ciemny + "resurs" secondary blue + ".com" szary (jak w navbar)
        brand_style = ParagraphStyle(
            'brand',
            fontName='DVSB',
            fontSize=11,
            textColor=C_BLACK,
            alignment=2,   # TA_RIGHT
            leading=14,
            wordWrap='LTR',
        )
        brand_line = Paragraph(
            'wyznacz<font color="#1976D2">resurs</font>'
            '<font name="DVS" size="8" color="#666666">.com</font>',
            brand_style,
        )
        logo_cell = Table([[brand_line]], colWidths=[LOGO_ZONE_W])
        logo_cell.setStyle(TableStyle([
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ]))

    row_data = [txt_block, logo_cell] if logo_pos != 'left' else [logo_cell, txt_block]
    widths = [txt_w, LOGO_ZONE_W] if logo_pos != 'left' else [LOGO_ZONE_W, txt_w]
    hdr = Table([row_data], colWidths=widths)

    # Indeks kolumny tekstowej (0 gdy logo prawo/brak, 1 gdy logo lewo)
    txt_col = 0 if logo_pos != 'left' else 1
    hdr.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('LEFTPADDING',   (txt_col, 0), (txt_col, -1), 8),  # odstęp od paska akcentu
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBEFORE',    (txt_col, 0), (txt_col, -1), 4, theme),
        ('LINEBELOW',     (0, 0), (-1, -1), 1.5, theme),
    ]))
    items.append(hdr)
    items.append(Spacer(1, 0.35 * cm))
    return items


# ── Klasa canvas z numerami stron ─────────────────────────────────────────────

class _NumberedCanvas(Canvas):
    """Canvas rysujący nagłówek i stopkę na każdej stronie."""

    def __init__(self, *args, theme=None, header_info=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._theme = theme or colors.HexColor('#1565C0')
        self._header = header_info or {}
        self._pages = []

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pages)
        for i, page in enumerate(self._pages, 1):
            self.__dict__.update(page)
            self._draw_page_header(i)
            self._draw_footer(i, total)
            Canvas.showPage(self)
        Canvas.save(self)

    def _draw_page_header(self, page_num: int):
        """Kompaktowy nagłówek u góry strony (od strony 2 — strona 1 ma pełny nagłówek w treści)."""
        if page_num == 1:
            return
        self.saveState()
        # Lewa kreska kolorowa (pionowa, jak akcent sekcji)
        self.setFillColor(self._theme)
        self.rect(MARGIN_H, PAGE_H - 1.3 * cm, 3, 0.9 * cm, fill=1, stroke=0)
        # Tekst: nazwa kalkulatora + nr fabryczny (lewo)
        y_txt = PAGE_H - 0.75 * cm
        calc_name = self._header.get('calc_name', '')
        nr_fab = self._header.get('nr_fab', '')
        left_txt = f'Wyznaczenie resursu — {calc_name}'
        if nr_fab:
            left_txt += f'  |  Nr fab.: {nr_fab}'
        self.setFont('DVSB', 8)
        self.setFillColor(self._theme)
        self.drawString(MARGIN_H + 8, y_txt, left_txt)
        # Data (prawo)
        date_str = self._header.get('date_str', '')
        self.setFont('DVS', 7.5)
        self.setFillColor(C_GREY_TXT)
        self.drawRightString(PAGE_W - MARGIN_H, y_txt, date_str)
        # Linia oddzielająca nagłówek od treści
        self.setStrokeColor(_alpha(self._theme, 0.25))
        self.setLineWidth(0.5)
        self.line(MARGIN_H, PAGE_H - 1.45 * cm, PAGE_W - MARGIN_H, PAGE_H - 1.45 * cm)
        self.restoreState()

    def _draw_footer(self, page_num: int, total: int):
        self.saveState()
        y = MARGIN_V * 0.55
        # Linia stopki
        self.setStrokeColor(_alpha(self._theme, 0.35))
        self.setLineWidth(0.5)
        self.line(MARGIN_H, y + 8, PAGE_W - MARGIN_H, y + 8)
        # Numer strony
        self.setFont('DVS', 7.5)
        self.setFillColor(C_GREY_TXT)
        self.drawRightString(PAGE_W - MARGIN_H, y, f'Strona {page_num} / {total}')
        # Serwis — tylko dla użytkowników bez własnego brandingu
        if not self._header.get('has_brand'):
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
    'L_b_max':              'Maks. wysięg boczny L_b,max',
    's_factor':             'Współczynnik przebiegu naprężeń S',
    'moto_podest_ruchomy':  'Ilość odbytych motogodzin podestu ruchomego od ostatniego przeglądu specjalnego lub od daty rozpoczęcia eksploatacji',
    'max_moto_prod':        'Graniczna ilość motogodzin określona przez producenta',
    'procent_bumar':        'Efektywny czas pracy podestu ruchomego [%]',
    'v_pod':                'Prędkość podnoszenia v_pod',
    'v_jaz':                'Prędkość jazdy v_jaz',
    'v_prz':                'Prędkość przesuwu v_prz',
    's_sz':                 'Długość szyny jezdnej s',
    'max_cykle_prod':       'Graniczna ilość cykli wg producenta',
    'spec':                 'Wyznaczenie po pierwszym przeglądzie specjalnym',
    'ponowny_resurs':       'Ponowne wyznaczenie resursu',
    'ostatni_resurs':       'Wykorzystanie resursu — poprzednie obliczenia',
    'data_resurs':          'Data poprzednich obliczeń resursu',
    'ster':                 'Rodzaj sterowania',
    'gnp':                  'Grupa natężenia pracy',
    'gnp_check':            'Nie znam grupy natężenia pracy',
    'gnp_czas':             'Przewidywany dalszy czas pracy',
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
    'licznik_pracy_pod':    'Licznik pracy mechanizmu podnoszenia',
    'licznik_pracy_jaz':    'Licznik pracy mechanizmu jazdy',
    'licznik_pracy_prz':    'Licznik pracy mechanizmu przesuwu',
    'cykle_dzwig':          'Ilość jazd dźwigu',
    # Zespoły dźwigu
    'liny_nosne':           'Liny nośne',
    'wciagarka':            'Wciągarka',
    'konstrukcja_nosna':    'Konstrukcja nośna',
    'mocowanie_lin':        'Mocowanie lin',
    'ogranicznik_predkosci': 'Ogranicznik prędkości',
    'chwytacze_kabiny':     'Chwytacze kabiny',
    'kola_kabiny':          'Koła kabiny',
    'kola_przeciwwagi':     'Koła przeciwwagi',
    'prowadnice_kabiny':    'Prowadnice kabiny',
    'prowadnice_przeciwwagi': 'Prowadnice przeciwwagi',
    'zderzak_kabiny':       'Zderzak kabiny',
    'zderzak_przeciwwagi':  'Zderzak przeciwwagi',
    'drzwi':                'Drzwi',
    'silownik':             'Siłownik',
    'zawor_blokowy':        'Zawór blokowy',
    'zawor_zwrotny':        'Zawór zwrotny',
    'przewody_hydrauliczne': 'Przewody hydrauliczne',
    'przekladnia':          'Przekładnia',
    'mechanizm_zebatkowy':  'Mechanizm zębatkowy',
    'mechanizm_srubowy':    'Mechanizm śrubowy',
    'mocowanie_napedu':     'Mocowanie napędu',
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
    # Zakresy godzin pracy dźwigu
    'zakres_godzin_1': 'Ilość godz. pracy dźwigu 5:00–9:00',
    'zakres_godzin_2': 'Ilość godz. pracy dźwigu 9:00–13:00',
    'zakres_godzin_3': 'Ilość godz. pracy dźwigu 13:00–17:00',
    'zakres_godzin_4': 'Ilość godz. pracy dźwigu 17:00–21:00',
    'zakres_godzin_5': 'Ilość godz. pracy dźwigu 21:00–0:00',
    'zakres_godzin_6': 'Ilość godz. pracy dźwigu 0:00–5:00',
}

# Etykiety wynikowe: klucz → (etykieta, jednostka)
OUTPUT_LABELS = {
    'resurs_wykorzystanie':      ('Stopień wykorzystania resursu',          '%'),
    'U_WSK':                     ('Projektowa zdolność U_WSK',             ''),
    'moto_efektywne':            ('Efektywne motogodziny',                  'mth'),
    'moto_rok':                  ('Motogodziny efektywne / rok',            'mth/rok'),
    'T_WSK':                     ('Projektowa zdolność czasowa T_WSK',     'h'),
    'F_X':                       ('Współczynnik F_X',                       '—'),
    'ilosc_cykli':               ('Ilość odbytych cykli',                   'cykli'),
    'ilosc_cykli_rok':           ('Ilość cykli / rok',                     'cykli/rok'),
    'czas_uzytkowania_mech':     ('Czas użytkowania mechanizmu',            'h'),
    'czas_uzytkowania_mech_rok': ('Czas użytkowania mechanizmu / rok',      'h/rok'),
    'wsp_kdr':                   ('Współczynnik widma obciążeń K_d',        '—'),
    'wsp_km':                    ('Współczynnik widma obciążeń K_m',        '—'),
    'stan_obciazenia':           ('Klasa stanu obciążenia',                 ''),
    'data_prognoza':             ('Symulowana data wyczerpania resursu',    ''),
    'resurs_prognoza_dni':       ('Dni do wyczerpania resursu *',           'dni'),
    'ldr':                       ('Współczynnik LDR',                       '—'),
    'hdr':                       ('Współczynnik HDR',                       '—'),
    'ss_factor':                 ('Współczynnik SS',                        '—'),
    'zalecenia':                 ('Zalecenia',                              ''),
    'prognoza':                  ('Prognoza eksploatacji',                  'lat'),
    'wiek_dzwigu':               ('Wiek dźwigu',                            'lat'),
    'resurs_wyk_pod':            ('Wykorzystanie resursu mechanizmu podnoszenia', '%'),
    'resurs_prog_pod':           ('Prognoza mechanizmu podnoszenia',        'dni'),
    'resurs_wyk_jaz':            ('Wykorzystanie resursu mechanizmu jazdy',      '%'),
    'resurs_prog_jaz':           ('Prognoza mechanizmu jazdy',               'dni'),
    'resurs_wyk_prz':            ('Wykorzystanie resursu mechanizmu przesuwu',    '%'),
    'resurs_prog_prz':           ('Prognoza mechanizmu przesuwu',            'dni'),
    'resurs_wyk_mas':           ('Wykorzystanie resursu mechanizmu masztu',     '%'),
    'resurs_prog_mas':          ('Prognoza mechanizmu masztu',              'dni'),
    'resurs_prognoza_dni':      ('Dni do wyczerpania resursu',              'dni'),
    'data_prog_pod':            ('Symulowana data (mech. podnoszenia)',     ''),
    't_max_pod':                ('Zdolność resursowa t_max',                'h'),
    't_sum_pod':                ('Czas pracy t_sum',                        'h'),
    }

_PARAM_SECTIONS = [
    ('Dane urządzenia', [
        'wykonawca', 'nr_fabryczny', 'nr_ewidencyjny', 'nr_udt', 'producent',
        'typ', 'q_max', 'q_o', 'uwagi',
    ]),
    ('Informacje o obliczeniach', [
        'spec', 'ponowny_resurs', 'data_resurs', 'ostatni_resurs',
    ]),
    ('Dane o eksploatacji', [
        'lata_pracy', 'ilosc_cykli', 'cykle_zmiana', 'tryb_pracy', 'dni_robocze',
        'sposob_rejestracji', 'gnp', 'gnp_check', 'gnp_czas',
        'ster', 'mechanizm_pomocniczy', 'czas_pracy_mech', 'max_cykle_prod',
        'h_max', 'L_b_max', 'v_pod', 'v_jaz', 'v_prz', 's_sz',
        'rok_budowy', 'przeznaczenie', 'operator', 'budynek', 'przystanki',
        'liczba_dzwigow', 'h_pod', 'pyt_motogodzin', 'licznik_pracy', 'cykle_dzwig',
        'licznik_pracy_pod', 'licznik_pracy_jaz', 'licznik_pracy_prz',
        'naped', 'operatorzy', 'powierzchnia', 'serwis',
        'dlugosc_widel', 'kat_masztu_alfa', 'kat_masztu_beta',
        'motogodziny', 'efektywny_czas', 'klasa_naprezenia',
        's_factor', 'moto_podest_ruchomy', 'max_moto_prod', 'procent_bumar',
    ]),
    ('Stan techniczny', [
        'konstrukcja', 'automatyka', 'sworznie', 'ciegna',
        'eksploatacja', 'szczelnosc', 'hamulce', 'nakretka', 'warkocz',
        'liny_nosne', 'wciagarka', 'konstrukcja_nosna', 'mocowanie_lin',
        'ogranicznik_predkosci', 'chwytacze_kabiny', 'kola_kabiny', 'kola_przeciwwagi',
        'prowadnice_kabiny', 'prowadnice_przeciwwagi', 'zderzak_kabiny', 'zderzak_przeciwwagi',
        'drzwi', 'silownik', 'zawor_blokowy', 'zawor_zwrotny',
        'przewody_hydrauliczne', 'przekladnia', 'mechanizm_zebatkowy', 'mechanizm_srubowy',
        'mocowanie_napedu',
    ]),
]

# Płaska lista kluczy (do eliminacji duplikatów w catch-all)
_PARAM_ORDER = [k for _, keys in _PARAM_SECTIONS for k in keys]

_RESULT_ORDER = [
    'wsp_kdr', 'wsp_km', 'ss_factor',
    'stan_obciazenia', 'F_X',
    'U_WSK', 'T_WSK', 'moto_efektywne', 'moto_rok',
    'ilosc_cykli', 'czas_uzytkowania_mech',
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
    # Mechanizmy wewnętrzne wózka/układnicy — wyświetlane w osobnych sekcjach
    't_max_pod', 't_sum_pod', 'resurs_wyk_pod', 'resurs_prog_pod', 'data_prog_pod',
    't_max_jaz', 't_sum_jaz', 'resurs_wyk_jaz', 'resurs_prog_jaz', 'data_prog_jaz',
    't_max_prz', 't_sum_prz', 'resurs_wyk_prz', 'resurs_prog_prz', 'data_prog_prz',
    't_max_mas', 't_sum_mas', 'resurs_wyk_mas', 'resurs_prog_mas', 'data_prog_mas',
    # Współczynniki inżynieryjne (wewnętrzne)
    'k_wid', 'k_oper', 'EDS_factor', 'k_sro', 'wskaznik_cykle', 'wskaznik_motogodzin',
    'max_c', 't_max', 'k_w', 'k_k', 'k_v_pod', 'k_h_pod',
    # Pola wewnętrzne kalkulatora żurawia (nie odpowiadają polom w nowej aplikacji)
    'recalculated_gnp', 'U_DOW',
    'max_czas',
    # Pola wewnętrzne wózka specjalizowanego
    'technical_state_reached', 'resurs_prognoza_dni',
}


_MECH_SLUGS = {
    'mech_podnoszenia', 'mech_jazdy_suwnicy', 'mech_jazdy_wciagarki',
    'mech_jazdy_zurawia', 'mech_zmiany_obrotu', 'mech_zmiany_wysiegu',
}


def _internal_mechanisms_section(output_data: dict, slug: str, theme: colors.Color) -> list:
    """Sekcje dla mechanizmów wewnętrznych (wózek widłowy, układnica magazynowa)."""
    if slug not in {'wozek_jezdniowy', 'ukladnica_magazynowa'}:
        return []

    mechs = [
        ('Mechanizm podnoszenia', 't_max_pod', 't_sum_pod', 'resurs_wyk_pod', 'resurs_prog_pod', 'data_prog_pod'),
        ('Mechanizm jazdy', 't_max_jaz', 't_sum_jaz', 'resurs_wyk_jaz', 'resurs_prog_jaz', 'data_prog_jaz'),
        ('Mechanizm przesuwu', 't_max_prz', 't_sum_prz', 'resurs_wyk_prz', 'resurs_prog_prz', 'data_prog_prz'),
    ]
    if slug == 'wozek_jezdniowy':
        mechs.append(('Mechanizm odchylenia masztu', 't_max_mas', 't_sum_mas', 'resurs_wyk_mas', 'resurs_prog_mas', 'data_prog_mas'))

    items = []
    for mech_title, key_max, key_sum, key_wyk, key_prog, key_date in mechs:
        t_max = _get_num(output_data.get(key_max))
        t_sum = _get_num(output_data.get(key_sum))
        resurs_wyk = _get_num(output_data.get(key_wyk))
        if t_max is None and resurs_wyk is None:
            continue
        rows = []
        if t_max is not None:
            rows.append(('Maks. czas pracy T_max', _fmt_num(str(round(t_max))), 'mth'))
        if t_sum is not None:
            rows.append(('Czas pracy T_sum', _fmt_num(str(round(t_sum))), 'mth'))
        if resurs_wyk is not None:
            rows.append(('Stopień wykorzystania resursu', _fmt_num(str(resurs_wyk)), '%'))
        prog = _get_num(output_data.get(key_prog))
        if prog is not None and prog > 0:
            rows.append(('Prognoza wyczerpania', _fmt_num(str(int(prog))), 'dni'))
        data_prog = output_data.get(key_date)
        if data_prog:
            try:
                from datetime import datetime as _dtm
                data_str = _dtm.strptime(str(data_prog), '%Y-%m-%d').strftime('%d.%m.%Y')
            except Exception:
                data_str = str(data_prog)
            rows.append(('Symulowana data wyczerpania', data_str, ''))
        _mech_block = [_section_header(mech_title, theme), Spacer(1, 0.15 * cm)]
        if rows:
            _mech_block.append(_param_table(rows, theme, is_results=True))
        _mech_block.append(Spacer(1, 0.3 * cm))
        items.append(KeepTogether(_mech_block))
        if t_max is not None and t_sum is not None and t_max > 0:
            max_v = max(t_max, t_sum) * 1.1
            items.append(Table(
                [[_bar_chart([
                    ('T_max [mth]', t_max, max_v),
                    ('T_sum [mth]', t_sum, max_v),
                ], theme)]],
                colWidths=[USABLE_W]))
            items.append(Spacer(1, 0.4 * cm))
    return items


def _get_nr_fabryczny(input_data: dict) -> str:
    """Wyciąga wartość nr_fabryczny z input_data (obsługuje dict i str)."""
    raw = input_data.get('nr_fabryczny', '')
    if isinstance(raw, dict):
        return str(raw.get('value', '') or '').strip()
    return str(raw or '').strip()


def _mechanism_summary_section(result, theme: colors.Color) -> list:
    """Zwraca elementy PDF z zestawieniem powiązanych mechanizmów (ten sam nr_fabryczny)."""
    from .models import CalculatorResult

    current_slug = result.calculator_definition.slug
    is_mechanism = current_slug in _MECH_SLUGS

    nr_fab = _get_nr_fabryczny(result.input_data or {})
    if not nr_fab:
        return []

    # Zapytanie: wyniki mechanizmów tego użytkownika z tym samym nr_fabryczny
    candidate_qs = (
        CalculatorResult.objects
        .filter(user=result.user, is_locked=False)
        .select_related('calculator_definition')
        .exclude(id=result.id)
    )

    related = []
    for r in candidate_qs:
        if r.calculator_definition.slug not in _MECH_SLUGS:
            continue
        if _get_nr_fabryczny(r.input_data or {}) == nr_fab:
            related.append(r)

    if is_mechanism:
        # Bieżący mechanizm + powiązane (inne mechanizmy tego samego urządzenia)
        rows = [(result, True)] + [(r, False) for r in related]
    else:
        # Urządzenie: tylko powiązane mechanizmy
        if not related:
            return []
        rows = [(r, False) for r in related]

    story = []
    story.append(CondPageBreak(6 * cm))
    story.append(_section_header(f'Zestawienie mechanizmów — nr fabr. {nr_fab}', theme))
    story.append(Spacer(1, 0.15 * cm))

    # Nagłówek tabeli
    tdata = [[
        _p('Mechanizm',        font='DVSB', size=8, color=C_WHITE),
        _p('Stan obciążenia',  font='DVSB', size=8, color=C_WHITE),
        _p('Czas użytk. [mth]', font='DVSB', size=8, color=C_WHITE),
        _p('T_WSK [mth]',      font='DVSB', size=8, color=C_WHITE),
        _p('Resurs [%]',       font='DVSB', size=8, color=C_WHITE),
        _p('Data obliczenia',  font='DVSB', size=8, color=C_WHITE),
    ]]
    tstyle = [
        ('BACKGROUND',    (0, 0), (-1, 0), theme),
        ('FONTNAME',      (0, 0), (-1, -1), 'DVS'),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN',         (0, 0), (0, -1), 'LEFT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW',     (0, 0), (-1, -1), 0.3, C_GREY_SEP),
        ('LINEBEFORE',    (0, 0), (0, -1), 3, _alpha(theme, 0.6)),
    ]

    for ri, (r, is_curr) in enumerate(rows, start=1):
        out = r.output_data or {}
        name = r.calculator_definition.name
        if is_curr:
            name += ' ★'
        stan = str(out.get('stan_obciazenia', '-'))
        czas_raw = out.get('czas_uzytkowania_mech', '-')
        czas_str, _ = _split_value_unit(czas_raw)
        t_wsk_raw = out.get('T_WSK', '-')
        t_wsk_str, _ = _split_value_unit(t_wsk_raw)
        resurs = str(out.get('resurs_wykorzystanie', '-'))
        data = r.created_at.strftime('%d.%m.%Y') if r.created_at else '-'
        tdata.append([
            _p(name,              font='DVS',  size=8, color=C_BLACK),
            _p(stan,              font='DVS',  size=8, color=C_GREY_TXT),
            _p(_fmt_num(czas_str), font='DVSB', size=8, color=theme),
            _p(_fmt_num(t_wsk_str), font='DVSB', size=8, color=theme),
            _p(_fmt_num(resurs),  font='DVSB', size=8.5, color=theme),
            _p(data,              font='DVS',  size=8, color=C_GREY_TXT),
        ])
        if is_curr:
            tstyle.append(('BACKGROUND', (0, ri), (-1, ri), _alpha(theme, 0.08)))

    CW = [6.5 * cm, 3 * cm, 2.5 * cm, 2.5 * cm, 2.2 * cm, 2.3 * cm]
    t = Table(tdata, colWidths=CW, repeatRows=1)
    t.setStyle(TableStyle(tstyle))
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))

    # Wykres słupkowy zużycia mechanizmów
    chart_items = []
    for r, is_curr in rows:
        out = r.output_data or {}
        resurs_val = out.get('resurs_wykorzystanie')
        if resurs_val is not None:
            try:
                name = r.calculator_definition.name + (' ★' if is_curr else '')
                chart_items.append((name, float(resurs_val)))
            except (ValueError, TypeError):
                pass

    if len(chart_items) > 1:
        global_max = max(max(v for _, v in chart_items) * 1.1, 100)
        chart_rows = [(name, val, global_max) for name, val in chart_items]
        story.append(_section_header('Porównanie — Stopień zużycia mechanizmów [%]', theme))
        story.append(Spacer(1, 0.15 * cm))
        story.append(Table([[_bar_chart(chart_rows, theme)]], colWidths=[USABLE_W]))
        story.append(Spacer(1, 0.4 * cm))

    return story


# ── Główna funkcja ────────────────────────────────────────────────────────────

def generate_result_pdf(result, calculator_name: str,
                        logo_obj=None, signature_obj=None) -> bytes:
    """Generuje nowoczesny raport PDF dla wyniku obliczeń resursu."""

    user_color = (getattr(logo_obj, 'theme_color', None)
                  or getattr(result.user, 'theme_color', '#1565C0'))
    THEME = colors.HexColor(user_color)
    has_brand = bool(logo_obj or (getattr(result.user, 'theme_color', None)
                                   and getattr(result.user, 'theme_color', '') != '#1565C0'))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=MARGIN_H, leftMargin=MARGIN_H,
        topMargin=2.2 * cm, bottomMargin=MARGIN_V + 0.6 * cm,
        title=f'Resurs — {calculator_name}',
        author='wyznaczresurs.com',
    )

    story = []
    input_data  = result.input_data  or {}
    output_data = result.output_data or {}

    # ── Nagłówek strony 1 (pełny — z logo) ─────────────────────────────────
    story += _build_header(result, calculator_name, logo_obj, THEME)

    # Mapa wartości inspekcji → czytelne etykiety
    _INSPECTION_VALS = {
        '1': 'Bez zastrzeżeń',
        '0.5': 'Wymagający remontu w ciągu 5 lat',
        '0': 'Wymagający remontu w ciągu 1–2 lat',
        '-1': 'Nie dotyczy',
    }
    seen = set()
    _pdf_slug = result.calculator_definition.slug

    # ── Sekcje wejściowe ──────────────────────────────────────────────────────
    for section_title, section_keys in _PARAM_SECTIONS:
        section_rows = []
        for key in section_keys:
            if key not in input_data or key in _SKIP_KEYS:
                continue
            if not _is_field_visible_in_pdf(key, _pdf_slug, input_data):
                continue
            # Specjalne traktowanie ostatni_resurs: zawsze % (konwersja z mth)
            raw_input = input_data[key]
            if key == 'ostatni_resurs' and isinstance(raw_input, dict) and raw_input.get('unit') == 'mth':
                T_WSK_val = float(output_data.get('T_WSK', 0) or 0)
                if T_WSK_val > 0:
                    pct = round(float(raw_input.get('value', 0)) / T_WSK_val * 100, 2)
                    val, unit = str(pct), '%'
                else:
                    val, unit = _split_value_unit(raw_input)
            else:
                val, unit = _split_value_unit(raw_input)
            if val == '-':
                continue
            label = INPUT_LABELS.get(key, key.replace('_', ' ').capitalize())
            if not unit:
                unit = _extract_unit(label)
            
            # Mapowanie wartości inspekcji tylko dla pól typu inspection_status
            field_def = _load_device_config(_pdf_slug).get('fields', {}).get(key, {})
            if field_def.get('type') == 'inspection_status':
                val = _INSPECTION_VALS.get(str(val).strip(), val)
            
            section_rows.append((label, val, unit))
            seen.add(key)
        if section_rows:
            story.append(KeepTogether([
                _section_header(section_title, THEME),
                Spacer(1, 0.15 * cm),
                _param_table(section_rows, THEME, is_results=False),
                Spacer(1, 0.4 * cm),
            ]))

    # Pozostałe pola wejściowe (nieprzypisane do żadnej sekcji)
    extra_rows = []
    for key, raw in input_data.items():
        if key in seen or key in _SKIP_KEYS:
            continue
        if not _is_field_visible_in_pdf(key, _pdf_slug, input_data):
            continue
        val, unit = _split_value_unit(raw)
        if val == '-':
            continue
        label = INPUT_LABELS.get(key, key.replace('_', ' ').capitalize())
        if not unit:
            unit = _extract_unit(label)
        val = _INSPECTION_VALS.get(str(val).strip(), val)
        extra_rows.append((label, val, unit))
    if extra_rows:
        story.append(KeepTogether([
            _section_header('Parametry urządzenia', THEME),
            Spacer(1, 0.15 * cm),
            _param_table(extra_rows, THEME, is_results=False),
            Spacer(1, 0.4 * cm),
        ]))

    # ── Diagram αd ────────────────────────────────────────────────────────────
    _ad_items = _diagram_ad(input_data, THEME)
    if _ad_items:
        story.append(KeepTogether(_ad_items))

    # ── Sekcja: Współczynnik Kd i stan obciążenia ─────────────────────────────
    # Dla podestu ruchomego: typ decyduje czy LDR czy HDR (nie oba)
    _slug = result.calculator_definition.slug
    _podest_hdr_types = {'nożycowy samobieżny', 'masztowy samobieżny', 'masztowy stacjonarny'}
    if _slug == 'podest_ruchomy':
        _typ_val = str(_split_value_unit(input_data.get('typ', ''))[0])
        _render_ldr = _typ_val not in _podest_hdr_types and _typ_val != 'składany na pojeździe BUMAR'
        _render_hdr = _typ_val in _podest_hdr_types
    else:
        _render_ldr = True
        _render_hdr = True

    _is_mech = result.calculator_definition.slug in _MECH_SLUGS
    _wsp_raw_kd = output_data.get('wsp_km' if _is_mech else 'wsp_kdr')
    _kd_items = _diagram_kd(input_data, THEME, is_mech=_is_mech) if _wsp_raw_kd is not None else []
    _kd_coeff_items = []
    if _wsp_raw_kd is not None:
        _STAN_OPISY_KD = {
            'Q1': 'Q1-lekki — Ładunek nominalny podnoszony bardzo rzadko, zwykle ładunki znacznie mniejsze od nominalnego',
            'Q2': 'Q2-przeciętny — Ładunek nominalny podnoszony rzadko, zwykle ładunki zbliżone do połowy ładunku nominalnego',
            'Q3': 'Q3-ciężki — Ładunek nominalny podnoszony często, zwykle ładunki większe od połowy ładunku nominalnego',
            'Q4': 'Q4-bardzo ciężki — Ładunek nominalny podnoszony regularnie i ładunki bliskie nominalnemu',
            'L1': 'L1-lekki — Mechanizm rzadko stosowany przy małych obciążeniach',
            'L2': 'L2-przeciętny — Mechanizm stosowany regularnie przy średnich obciążeniach',
            'L3': 'L3-ciężki — Mechanizm często stosowany przy dużych obciążeniach',
            'L4': 'L4-bardzo ciężki — Mechanizm regularnie stosowany przy obciążeniach bliskich maksymalnym',
        }
        _THRESHOLDS_Q = [(0.125, 'Q1-lekki'), (0.25, 'Q2-przeciętny'),
                         (0.5, 'Q3-ciężki'), (10.0, 'Q4-bardzo ciężki')]
        _THRESHOLDS_L = [(0.125, 'L1-lekki'), (0.25, 'L2-przeciętny'),
                         (0.5, 'L3-ciężki'), (10.0, 'L4-bardzo ciężki')]

        _stan_kd = output_data.get('stan_obciazenia', '')
        _wsp_raw = _wsp_raw_kd
        if (not _stan_kd or _stan_kd == 'N/A') and _wsp_raw is not None:
            try:
                _kd_val = float(_wsp_raw)
                _thresh = _THRESHOLDS_L if _is_mech else _THRESHOLDS_Q
                _stan_kd = next(s for t, s in _thresh if _kd_val <= t)
            except Exception:
                _stan_kd = ''

        if _stan_kd and _stan_kd != 'N/A':
            _kd_rows = []
            if _wsp_raw is not None:
                try:
                    _kd_rows.append(('Współczynnik K_d', f'{float(_wsp_raw):.4f}', '—'))
                except (ValueError, TypeError):
                    pass
            _stan_opis_kd = next((v for k, v in _STAN_OPISY_KD.items() if str(_stan_kd).startswith(k)), _stan_kd)
            _kd_rows.append(('Stan obciążenia', _stan_opis_kd, ''))
            _kd_coeff_items = [_param_table(_kd_rows, THEME, is_results=True), Spacer(1, 0.35 * cm)]

    if _kd_items or _kd_coeff_items:
        story.append(KeepTogether(_kd_items + _kd_coeff_items))

    # ── Diagram LDR + współczynnik L_DR (po sekcji Kd) ──────────────────────
    if _render_ldr:
        _ldr_base = _diagram_ldr(input_data, THEME)
        if _ldr_base:
            _ldr_all = list(_ldr_base)
            _ldr_val = output_data.get('ldr')
            if _ldr_val is not None:
                try:
                    _ldr_all.append(_param_table(
                        [('Współczynnik L_DR', _fmt_num(str(_ldr_val)), '—')], THEME, is_results=True))
                    _ldr_all.append(Spacer(1, 0.35 * cm))
                except Exception:
                    pass
            story.append(KeepTogether(_ldr_all))

    # ── Diagram HDR + współczynnik H_DR (po sekcji Kd) ──────────────────────
    if _render_hdr:
        _hdr_base = _diagram_hdr(input_data, THEME)
        if _hdr_base:
            _hdr_all = list(_hdr_base)
            _hdr_val = output_data.get('hdr')
            if _hdr_val is not None:
                try:
                    _hdr_all.append(_param_table(
                        [('Współczynnik H_DR', _fmt_num(str(_hdr_val)), '—')], THEME, is_results=True))
                    _hdr_all.append(Spacer(1, 0.35 * cm))
                except Exception:
                    pass
            story.append(KeepTogether(_hdr_all))

    # ── Sekcja: Wyniki obliczeń resursu ──────────────────────────────────────
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
        result_rows.append((label, _fmt_num(v), u))
        seen_out.add(key)

    for key, raw in output_data.items():
        if key in seen_out or key in _SKIP_KEYS:
            continue
        label, unit_hint = OUTPUT_LABELS.get(key, (key.replace('_', ' ').capitalize(), ''))
        v, u = _split_value_unit(raw, unit_hint)
        if v != '-':
            result_rows.append((label, _fmt_num(v), u))

    if result_rows:
        _res_title = 'Wyniki obliczeń resursu'
        if _is_mech:
            _res_title += f' — {calculator_name}'
        story.append(KeepTogether([
            _section_header(_res_title, THEME),
            Spacer(1, 0.15 * cm),
            _param_table(result_rows, THEME, is_results=True),
            Spacer(1, 0.4 * cm),
        ]))

    # ── Sekcja: Stopień wykorzystania resursu (wykres) ────────────────────────
    resurs_val = output_data.get('resurs_wykorzystanie')
    if resurs_val is not None:
        try:
            rv = float(resurs_val)
            story.append(KeepTogether([
                _section_header('Stopień wykorzystania resursu', THEME),
                Spacer(1, 0.15 * cm),
                Table([[_bar_chart([('Stopień zużycia [%]', rv, max(rv * 1.1, 100))], THEME)]],
                      colWidths=[USABLE_W]),
                Spacer(1, 0.4 * cm),
            ]))
        except (ValueError, TypeError):
            pass

    # ── Sekcja: Zestawienie — cykle vs maks. ilość cykli ─────────────────────
    u_wsk  = output_data.get('U_WSK')
    ilosc  = output_data.get('ilosc_cykli') or input_data.get('ilosc_cykli')
    if u_wsk is not None and ilosc is not None:
        try:
            uv = float(u_wsk)
            iv, _ = _split_value_unit(ilosc)
            iv = float(iv.replace(',', '.').replace('', '').replace(' ', ''))
            fx = float(output_data.get('F_X', 1) or 1)
            iv_fx = round(iv * fx, 2)
            max_v = max(uv, iv, iv_fx) * 1.1
            story.append(KeepTogether([
                _section_header('Zestawienie — Ilość cykli vs maks. ilość cykli', THEME),
                Spacer(1, 0.15 * cm),
                Table([[_bar_chart([
                    ('Maks. ilość cykli U_WSK', uv, max_v),
                    ('Odbyte cykle (bez F\u2093)', iv,    max_v),
                    ('Odbyte cykle (z F\u2093)',   iv_fx, max_v),
                ], THEME)]], colWidths=[USABLE_W]),
                Spacer(1, 0.4 * cm),
            ]))
        except (ValueError, TypeError, AttributeError):
            pass

    # ── Zestawienie — czas vs T_WSK ───────────────────────────────────────────
    t_wsk = output_data.get('T_WSK')
    czas  = output_data.get('czas_uzytkowania_mech')
    if t_wsk is not None and czas is not None:
        try:
            tv = float(t_wsk)
            cv, _ = _split_value_unit(czas)
            cv = float(cv.replace(',', '.').replace(' ', ''))
            fx = float(output_data.get('F_X', 1) or 1)
            cv_fx = round(cv * fx, 2)
            max_v = max(tv, cv, cv_fx) * 1.1
            story.append(KeepTogether([
                _section_header('Zestawienie — Czas użytkowania vs T_WSK', THEME),
                Spacer(1, 0.15 * cm),
                Table([[_bar_chart([
                    ('Limit T_WSK [h]',              tv,    max_v),
                    ('Czas użytkowania (bez F\u2093) [h]', cv,    max_v),
                    ('Czas użytkowania (z F\u2093) [h]',   cv_fx, max_v),
                ], THEME)]], colWidths=[USABLE_W]),
                Spacer(1, 0.4 * cm),
            ]))
        except (ValueError, TypeError, AttributeError):
            pass

    # ── Zestawienie mechanizmów wewnętrznych (wózek jezdniowy, układnica) ────
    story += _internal_mechanisms_section(output_data, result.calculator_definition.slug, THEME)

    # ── Przebieg (ponowny resurs) ─────────────────────────────────────────────
    if str(input_data.get('ponowny_resurs', '')).lower() in ('tak', '1', 'true'):
        ostatni_raw = input_data.get('ostatni_resurs')
        ostatni_str, _ = _split_value_unit(ostatni_raw)
        data_raw = input_data.get('data_resurs', '')
        data_ost_raw, _ = _split_value_unit(data_raw)
        try:
            from datetime import datetime as _dt
            data_ost = _dt.strptime(data_ost_raw, '%Y-%m-%d').strftime('%d.%m.%Y')
        except (ValueError, TypeError):
            data_ost = data_ost_raw or '-'
        data_now = result.created_at.strftime('%d.%m.%Y')
        rv_str   = str(resurs_val) if resurs_val is not None else '-'
        ostatni_unit = ostatni_raw.get('unit', '%') if isinstance(ostatni_raw, dict) else '%'
        if ostatni_unit == 'mth':
            T_WSK = output_data.get('T_WSK')
            try:
                prev_pct_str = f"{(float(ostatni_str) / float(T_WSK)) * 100:.2f}"
            except (ValueError, TypeError, ZeroDivisionError):
                prev_pct_str = '-'
            prev_display = prev_pct_str
        else:
            prev_display = ostatni_str
        try:
            zmiana = f"{float(rv_str) - float(prev_display):+.2f}"
        except (ValueError, TypeError):
            zmiana = '-'
        story.append(_section_header('Przebieg — Stopień wykorzystania resursu', THEME))
        story.append(Spacer(1, 0.15 * cm))
        story.append(_param_table([
            ('Poprzednie obliczenia  (' + data_ost + ')', prev_display, '%'),
            ('Bieżące obliczenia  (' + data_now + ')',    rv_str,       '%'),
            ('Zmiana stopnia wykorzystania',               zmiana,       '%'),
        ], THEME, is_results=True))
        story.append(Spacer(1, 0.4 * cm))

    # ── Status analizy ────────────────────────────────────────────────────────
    msg = output_data.get('resurs_message', '')
    status_items = [CondPageBreak(3 * cm), _section_header('Status analizy', THEME), Spacer(1, 0.15 * cm)]
    if msg:
        msg_cell = _p(msg, font='DVSB', size=9, color=THEME)
        t = Table([[msg_cell]], colWidths=[USABLE_W])
        t.setStyle(TableStyle([
            ('LINEBEFORE',    (0, 0), (0, 0), 3, THEME),
            ('LEFTPADDING',   (0, 0), (0, 0), 12),
            ('TOPPADDING',    (0, 0), (0, 0), 8),
            ('BOTTOMPADDING', (0, 0), (0, 0), 8),
        ]))
        status_items.append(t)
    status_items.append(Spacer(1, 0.4 * cm))
    story += status_items

    # ── Podpis cyfrowy (pieczęć/grafika) ────────────────────────────────────────
    story.append(CondPageBreak(10 * cm))
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

    # ── Blok podpisów (z dużą przestrzenią, nie może być ucięty) ─────────────────
    story.append(KeepTogether(_signature_block(THEME)))

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
    _nr_fab = (result.input_data or {}).get('nr_fabryczny', '')
    _header_info = {
        'calc_name': calculator_name,
        'nr_fab': _nr_fab,
        'date_str': result.created_at.strftime('%d.%m.%Y'),
        'has_brand': has_brand,
    }
    doc.build(story,
              canvasmaker=lambda *a, **kw: _NumberedCanvas(
                  *a, theme=THEME, header_info=_header_info, **kw))
    return buffer.getvalue()
