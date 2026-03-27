"""Generowanie dokumentu Dziennik Eksploatacji UTB (Logbook)."""

import os
from io import BytesIO
from datetime import datetime

from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    Spacer, PageBreak,
)
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
USABLE_W = PAGE_W - 2 * MARGIN_H

# ── Kolory ───────────────────────────────────────────────────────────────────
PRIMARY = colors.HexColor('#1565C0')
C_BLACK = colors.HexColor('#1a1a2e')
C_GREY_TXT = colors.HexColor('#555555')
C_GREY_ROW = colors.HexColor('#f7f8fa')
C_GREY_SEP = colors.HexColor('#e0e4ea')

def _alpha(hex_color, alpha):
    r = hex_color.red   + (1 - hex_color.red)   * (1 - alpha)
    g = hex_color.green + (1 - hex_color.green) * (1 - alpha)
    b = hex_color.blue  + (1 - hex_color.blue)  * (1 - alpha)
    return colors.Color(r, g, b)

def _p(text, font='DVS', size=9, color=C_BLACK, align=0, leading=None):
    style = ParagraphStyle(
        '_',
        fontName=font,
        fontSize=size,
        textColor=color,
        alignment=align,
        leading=leading or (size + 3.5),
    )
    return Paragraph(str(text), style)

class _NumberedCanvas(Canvas):
    def __init__(self, *args, theme=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._theme = theme or PRIMARY
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

    def _draw_footer(self, page_num, total):
        self.saveState()
        y = MARGIN_V * 0.55
        self.setStrokeColor(_alpha(self._theme, 0.35))
        self.setLineWidth(0.5)
        self.line(MARGIN_H, y + 8, PAGE_W - MARGIN_H, y + 8)
        self.setFont('DVS', 7.5)
        self.setFillColor(C_GREY_TXT)
        self.drawRightString(PAGE_W - MARGIN_H, y, f'Strona {page_num} / {total}')
        self.setFont('DVS', 7)
        self.setFillColor(_alpha(self._theme, 0.5))
        self.drawString(MARGIN_H, y, 'wyznaczresurs.com')
        self.restoreState()

def _section_header(text, theme=PRIMARY):
    cell = _p(text.upper(), font='DVSB', size=8, color=theme)
    t = Table([[cell]], colWidths=[USABLE_W])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (0, 0), _alpha(theme, 0.08)),
        ('LINEBEFORE',    (0, 0), (0, 0), 4, theme),
        ('LINEBELOW',     (0, 0), (0, 0), 0.5, _alpha(theme, 0.3)),
        ('LINETOP',       (0, 0), (0, 0), 0.5, _alpha(theme, 0.15)),
        ('LEFTPADDING',   (0, 0), (0, 0), 12),
        ('TOPPADDING',    (0, 0), (0, 0), 7),
        ('BOTTOMPADDING', (0, 0), (0, 0), 7),
    ]))
    return t

def generate_logbook_pdf(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=MARGIN_H, leftMargin=MARGIN_H, topMargin=MARGIN_V, bottomMargin=MARGIN_V + 0.6*cm)
    story = []

    # --- STRONA 1: DANE URZĄDZENIA ---
    title = _p("DZIENNIK REJESTRACJI PRZEBIEGU EKSPLOATACJI<br/>URZĄDZENIA TRANSPORTU BLISKIEGO", 
               font='DVSB', size=16, color=PRIMARY, align=1)
    story.append(title)
    story.append(Spacer(1, 1*cm))

    story.append(_section_header("Dane identyfikacyjne urządzenia"))
    story.append(Spacer(1, 0.3*cm))

    device_info = [
        ['Rodzaj urządzenia:', data.get('rodzaj_urzadzenia', '')],
        ['Numer fabryczny:', data.get('nr_fabryczny', '')],
        ['Numer ewidencyjny UDT:', data.get('nr_udt', '')],
        ['Rok budowy:', data.get('rok_budowy', '')],
        ['Rok dopuszczenia / przeglądu spec.:', data.get('rok_dop', '')],
    ]

    t = Table(device_info, colWidths=[USABLE_W * 0.45, USABLE_W * 0.55])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'DVSB'),
        ('FONTNAME', (1,0), (1,-1), 'DVS'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-1), 0.3, C_GREY_SEP),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TEXTCOLOR', (0,0), (0,-1), C_GREY_TXT),
    ]))
    story.append(t)
    story.append(Spacer(1, 1.5*cm))

    # Dane eksploatującego
    story.append(_section_header("Dane eksploatującego"))
    story.append(Spacer(1, 0.3*cm))
    owner_data = [['Od dnia', 'Do dnia', 'Nazwa eksploatującego', 'Lokalizacja urządzenia']]
    for _ in range(6):
        owner_data.append(['', '', '', ''])
    
    owner_table = Table(owner_data, colWidths=[USABLE_W * 0.15, USABLE_W * 0.15, USABLE_W * 0.4, USABLE_W * 0.3])
    owner_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'DVSB'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('GRID', (0,0), (-1,-1), 0.3, C_GREY_SEP),
        ('BACKGROUND', (0,0), (-1,0), _alpha(PRIMARY, 0.05)),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(owner_table)
    story.append(Spacer(1, 1*cm))

    # Uwagi
    story.append(_section_header("Uwagi i adnotacje"))
    story.append(Spacer(1, 0.3*cm))
    notes_table = Table([['']], colWidths=[USABLE_W], rowHeights=[3.5*cm])
    notes_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.3, C_GREY_SEP),
        ('BACKGROUND', (0,0), (-1,-1), C_GREY_ROW),
    ]))
    story.append(notes_table)
    
    story.append(Spacer(1, 1*cm))
    story.append(_p(
        "Przypomina się o konieczności rejestrowania przebiegu eksploatacji urządzenia, "
        "która będzie podstawą do ciągłego monitorowania stopnia wykorzystania resursu "
        "(zgodnie z § 7 ust. 2 Rozporządzenia MPiT z dnia 30 października 2018 r.)",
        size=7.5, color=C_GREY_TXT, align=1
    ))

    # --- STRONA 2: REJESTRACJA PRZEBIEGU ---
    story.append(PageBreak())
    story.append(_p("REJESTRACJA PRZEBIEGU EKSPLOATACJI", font='DVSB', size=14, color=PRIMARY, align=1))
    story.append(Spacer(1, 0.5*cm))
    
    # Stan resursu
    summary_data = [
        ['Aktualny stopień wykorzystania resursu [%]:', '____________________ %'],
        ['Data wykonania ostatnich obliczeń:', '____________________'],
    ]
    st = Table(summary_data, colWidths=[USABLE_W * 0.5, USABLE_W * 0.5])
    st.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'DVSB'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))
    story.append(st)
    story.append(Spacer(1, 0.5*cm))

    # Tabela rejestracji
    reg_header = [
        ['Data / okres', 'Rejestrowane parametry', '', '', 'Obciążenie (ciężar / % cykli)', '', '', '', ''],
        ['', 'Dni pracy', 'Liczba cykli', 'Motogodziny', 'i1', 'i2', 'i3', 'i4', 'i5']
    ]
    for _ in range(18):
        reg_header.append(['' for _ in range(9)])

    cw = USABLE_W / 10.5
    reg_table = Table(reg_header, colWidths=[cw*1.5, cw, cw, cw, cw, cw, cw, cw, cw])
    reg_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,1), 'DVSB'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('GRID', (0,0), (-1,-1), 0.3, C_GREY_SEP),
        ('SPAN', (1,0), (3,0)),
        ('SPAN', (4,0), (8,0)),
        ('SPAN', (0,0), (0,1)),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,1), _alpha(PRIMARY, 0.05)),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(reg_table)

    doc.build(story, canvasmaker=lambda *a, **kw: _NumberedCanvas(*a, theme=PRIMARY, **kw))
    return buffer.getvalue()
