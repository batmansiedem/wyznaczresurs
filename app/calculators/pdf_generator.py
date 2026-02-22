"""Generowanie raportów PDF dla wyników obliczeń resursu UTB."""

import os
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.units import cm
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime

PRIMARY = colors.HexColor('#1565C0')

# Rejestracja czcionek wspierających polskie znaki
FONT_PATH = os.path.join(settings.BASE_DIR, '..', 'public_html', 'fpdf', 'font', 'unifont')
pdfmetrics.registerFont(TTFont('DejaVuSans', os.path.join(FONT_PATH, 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', os.path.join(FONT_PATH, 'DejaVuSans-Bold.ttf')))

# Etykiety pól wyjściowych
OUTPUT_LABELS = {
    'resurs_wykorzystanie': ('Wykorzystanie resursu', '%'),
    'resurs_message': ('Status resursu', ''),
    'U_WSK': ('Zdolność cyklowa U_WSK', 'cykli'),
    'T_WSK': ('Zdolność czasowa T_WSK', 'h'),
    'F_X': ('Współczynnik niepewności F_X', ''),
    'ilosc_cykli': ('Ilość odbytych cykli', 'cykli'),
    'ilosc_cykli_rok': ('Cykli na rok', 'cykli/rok'),
    'czas_uzytkowania_mech': ('Czas użytkowania mechanizmu', 'h'),
    'czas_uzytkowania_mech_rok': ('Czas użytkowania/rok', 'h/rok'),
    'wsp_kdr': ('Współczynnik widma obciążeń Kdr', ''),
    'wsp_km': ('Współczynnik widma km', ''),
    'stan_obciazenia': ('Klasa obciążenia', ''),
    'data_prognoza': ('Data prognozy resursu', ''),
    'resurs_prognoza_dni': ('Prognoza resursu', 'dni'),
}


def _make_pie_chart(utilization: float) -> Drawing:
    """Tworzy kołowy wykres wykorzystania resursu (ReportLab Drawing)."""
    used = max(0.0, min(100.0, float(utilization)))
    remaining = max(0.0, 100.0 - used)
    d = Drawing(160, 130)
    pie = Pie()
    pie.x = 30
    pie.y = 15
    pie.width = 100
    pie.height = 100
    pie.data = [used, remaining]
    pie.labels = [f'{used:.1f}%', f'{remaining:.1f}%']
    pie.slices[0].fillColor = PRIMARY
    pie.slices[1].fillColor = colors.HexColor('#B0BEC5')
    pie.slices[0].strokeColor = colors.white
    pie.slices[1].strokeColor = colors.white
    pie.sideLabels = 0
    # Ustawienie czcionki dla etykiet wykresu (ReportLab Pie chart)
    pie.labels[0].fontName = 'DejaVuSans'
    pie.labels[1].fontName = 'DejaVuSans'
    d.add(pie)
    return d


def _format_input_value(val):
    """Formatuje wartość wejściową (obsługa {value, unit})."""
    if isinstance(val, dict):
        v = val.get('value', '')
        u = val.get('unit', '')
        return f"{v} {u}".strip() if v not in (None, '') else '-'
    return str(val) if val is not None else '-'


def generate_result_pdf(result, calculator_name: str) -> bytes:
    """Generuje raport PDF dla wyniku obliczeń resursu."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
        textColor=PRIMARY, fontSize=16, spaceAfter=6, fontName='DejaVuSans-Bold')
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'],
        textColor=colors.grey, fontSize=9, spaceAfter=12, fontName='DejaVuSans')
    section_style = ParagraphStyle('Section', parent=styles['Heading3'],
        textColor=PRIMARY, spaceBefore=8, spaceAfter=4, fontName='DejaVuSans-Bold')
    note_style = ParagraphStyle('Note', parent=styles['Normal'],
        fontSize=9, textColor=colors.grey, fontName='DejaVuSans')
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
        fontSize=7, textColor=colors.grey, fontName='DejaVuSans')

    # Nagłówek
    story.append(Paragraph("Raport wyznaczenia resursu UTB", title_style))
    story.append(Paragraph(
        f"Kalkulator: <b>{calculator_name}</b> &nbsp;|&nbsp; "
        f"Data: {result.created_at.strftime('%d.%m.%Y %H:%M')} &nbsp;|&nbsp; "
        f"Użytkownik: {result.user.email}", sub_style))

    # Niebieski pasek separatora
    story.append(Table([['']], colWidths=[17*cm],
        style=TableStyle([('LINEABOVE', (0,0),(0,0), 3, PRIMARY),
                          ('LINEBELOW', (0,0),(0,0), 0.5, colors.lightgrey)])))
    story.append(Spacer(1, 0.4*cm))

    # Dane wejściowe
    story.append(Paragraph("Dane wejściowe", section_style))

    input_rows = [['Parametr', 'Wartość']]
    for key, val in result.input_data.items():
        formatted = _format_input_value(val)
        if formatted and formatted != '-':
            label = key.replace('_', ' ').capitalize()
            input_rows.append([label, formatted])

    input_table = Table(input_rows, colWidths=[9*cm, 8*cm])
    input_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'DejaVuSans-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'DejaVuSans'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F5F5F5')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(input_table)
    story.append(Spacer(1, 0.5*cm))

    # Wyniki obliczeń
    story.append(Paragraph("Wyniki obliczeń", section_style))

    result_rows = [['Wskaźnik', 'Wartość']]
    resurs_val = result.output_data.get('resurs_wykorzystanie')
    for key, (label, unit) in OUTPUT_LABELS.items():
        val = result.output_data.get(key)
        if val is None:
            continue
        if key == 'resurs_message':
            continue  # wyświetlany oddzielnie
        display = f"{val}{'%' if key == 'resurs_wykorzystanie' else (' ' + unit if unit else '')}"
        result_rows.append([label, display])

    result_table = Table(result_rows, colWidths=[11*cm, 6*cm])

    table_style = [
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'DejaVuSans-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'DejaVuSans'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F5F5F5')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]

    # Kolorowanie i pogrubienie wiersza z % wykorzystania resursu
    if resurs_val is not None:
        try:
            rv = float(resurs_val)
            row_color = (colors.HexColor('#E8F5E9') if rv < 80
                         else colors.HexColor('#FFF8E1') if rv < 100
                         else colors.HexColor('#FFEBEE'))
            row_idx = next(
                (i for i, r in enumerate(result_rows)
                 if i > 0 and 'resursu' in r[0].lower() and r[1].endswith('%')),
                None
            )
            if row_idx:
                table_style.append(('BACKGROUND', (0,row_idx),(-1,row_idx), row_color))
                table_style.append(('FONTNAME', (0,row_idx),(-1,row_idx), 'DejaVuSans-Bold'))
                table_style.append(('FONTSIZE', (0,row_idx),(-1,row_idx), 11))
        except (ValueError, TypeError):
            pass

    result_table.setStyle(TableStyle(table_style))

    # Wykres kołowy obok tabeli wyników
    if resurs_val is not None:
        try:
            pie = _make_pie_chart(float(resurs_val))
            layout = Table([[result_table, pie]], colWidths=[11*cm, 5.5*cm])
            layout.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            story.append(layout)
        except Exception:
            story.append(result_table)
    else:
        story.append(result_table)

    # Komunikat statusu
    msg = result.output_data.get('resurs_message', '')
    if msg:
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f"<i>{msg}</i>", note_style))

    # Stopka
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        f"Raport wygenerowany: {datetime.now().strftime('%d.%m.%Y %H:%M')} "
        f"| System wyznaczania resursu UTB",
        footer_style))

    doc.build(story)
    return buffer.getvalue()
