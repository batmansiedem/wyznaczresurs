"""Generowanie dokumentu Dziennik Eksploatacji UTB (Logbook)."""

import os
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime

# Rejestracja czcionek
FONT_PATH = os.path.join(settings.BASE_DIR, 'core', 'fonts')
pdfmetrics.registerFont(TTFont('DejaVuSans', os.path.join(FONT_PATH, 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', os.path.join(FONT_PATH, 'DejaVuSans-Bold.ttf')))

PRIMARY = colors.HexColor('#1565C0')
SECONDARY = colors.HexColor('#0A1929')

def generate_logbook_pdf(data):
    """
    Generuje PDF Dziennika Eksploatacji na podstawie przekazanych danych.
    data: {
        'rodzaj_urzadzenia': str,
        'nr_fabryczny': str,
        'nr_udt': str,
        'rok_budowy': str,
        'rok_dop': str,
    }
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    styles = getSampleStyleSheet()

    # Style
    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
        textColor=PRIMARY, fontSize=18, alignment=1, spaceAfter=20, fontName='DejaVuSans-Bold')
    header_style = ParagraphStyle('Header', parent=styles['Normal'],
        fontSize=12, fontName='DejaVuSans-Bold', spaceAfter=10)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'],
        fontSize=10, fontName='DejaVuSans')
    small_style = ParagraphStyle('Small', parent=styles['Normal'],
        fontSize=8, fontName='DejaVuSans', textColor=colors.grey, alignment=1)

    # --- STRONA 1: DANE URZĄDZENIA ---
    story.append(Paragraph("DZIENNIK REJESTRACJI PRZEBIEGU EKSPLOATACJI<br/>URZĄDZENIA TRANSPORTU BLISKIEGO", title_style))
    story.append(Spacer(1, 1*cm))

    device_info = [
        ['Rodzaj urządzenia:', data.get('rodzaj_urzadzenia', '')],
        ['Numer fabryczny:', data.get('nr_fabryczny', '')],
        ['Numer ewidencyjny UDT:', data.get('nr_udt', '')],
        ['Rok budowy:', data.get('rok_budowy', '')],
        ['Rok dopuszczenia / przeglądu spec.:', data.get('rok_dop', '')],
    ]

    t = Table(device_info, colWidths=[8*cm, 10*cm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'DejaVuSans-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'DejaVuSans'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(Spacer(1, 1.5*cm))

    # Dane eksploatującego (Tabela pusta do uzupełnienia)
    story.append(Paragraph("Dane eksploatującego:", header_style))
    owner_data = [['Od dnia', 'Do dnia', 'Nazwa eksploatującego', 'Lokalizacja']]
    for _ in range(8):
        owner_data.append(['', '', '', ''])
    
    owner_table = Table(owner_data, colWidths=[2.5*cm, 2.5*cm, 7*cm, 6*cm])
    owner_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'DejaVuSans-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(owner_table)
    story.append(Spacer(1, 1*cm))

    # Uwagi
    story.append(Paragraph("Uwagi:", header_style))
    notes_table = Table([['']], colWidths=[18*cm], rowHeights=[3*cm])
    notes_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(notes_table)
    
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        "Przypomina się o konieczności rejestrowania przebiegu eksploatacji urządzenia, "
        "która będzie podstawą do ciągłego monitorowania stopnia wykorzystania resursu "
        "(zgodnie z § 7 ust. 2 Rozporządzenia MPiT z dnia 30 października 2018 r.)",
        small_style
    ))

    # --- STRONA 2: REJESTRACJA PRZEBIEGU ---
    story.append(PageBreak())
    story.append(Paragraph("REJESTRACJA PRZEBIEGU EKSPLOATACJI", title_style))
    
    # Stan resursu na początek dziennika
    summary_data = [
        ['Stopień wykorzystania resursu [%]:', '____________________'],
        ['Data wykonania obliczeń resursu:', '____________________'],
    ]
    st = Table(summary_data, colWidths=[8*cm, 10*cm])
    st.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'DejaVuSans-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(st)
    story.append(Spacer(1, 0.5*cm))

    # Tabela rejestracji (Główna)
    # Nagłówek dwupoziomowy
    reg_header = [
        ['Data / okres', 'Rejestrowane parametry', '', '', 'Obciążenie (ciężar / % cykli)', '', '', '', ''],
        ['', 'Dni pracy', 'Liczba cykli', 'Motogodziny', 'i1', 'i2', 'i3', 'i4', 'i5']
    ]
    
    # Dane puste
    for _ in range(20):
        reg_header.append(['' for _ in range(9)])

    reg_table = Table(reg_header, colWidths=[
        2.2*cm, # Data
        2.0*cm, 2.0*cm, 2.0*cm, # Parametry
        1.56*cm, 1.56*cm, 1.56*cm, 1.56*cm, 1.56*cm # i1-i5
    ])
    
    reg_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,1), 'DejaVuSans-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('SPAN', (1,0), (3,0)), # Rejestrowane parametry
        ('SPAN', (4,0), (8,0)), # Obciążenie
        ('SPAN', (0,0), (0,1)), # Data / okres
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,1), colors.whitesmoke),
    ]))
    story.append(reg_table)

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("wyznaczresurs.com - profesjonalny system zarządzania resursem UTB", small_style))

    doc.build(story)
    return buffer.getvalue()
