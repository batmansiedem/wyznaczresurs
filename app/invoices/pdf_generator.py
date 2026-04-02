"""Generowanie faktur PDF w formacie A4."""

import os
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime

PRIMARY = colors.HexColor('#1565C0')

# Rejestracja czcionek wspierających polskie znaki
FONT_PATH = os.path.join(settings.BASE_DIR, 'core', 'fonts')
pdfmetrics.registerFont(TTFont('DejaVuSans', os.path.join(FONT_PATH, 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', os.path.join(FONT_PATH, 'DejaVuSans-Bold.ttf')))

def generate_invoice_pdf(invoice) -> bytes:
    """Generuje dokument PDF dla faktury."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    styles = getSampleStyleSheet()

    # Style korzystające z DejaVuSans
    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
        fontSize=18, spaceAfter=12, textColor=PRIMARY, fontName='DejaVuSans-Bold')
    label_style = ParagraphStyle('Label', parent=styles['Normal'],
        fontSize=9, textColor=colors.grey, spaceAfter=2, fontName='DejaVuSans')
    value_style = ParagraphStyle('Value', parent=styles['Normal'],
        fontSize=10, textColor=colors.black, spaceAfter=8, fontName='DejaVuSans')
    table_header_style = ParagraphStyle('THeader', parent=styles['Normal'],
        fontSize=9, textColor=colors.white, fontName='DejaVuSans-Bold')

    # 1. Nagłówek (Numer faktury i daty)
    title_text = f"FAKTURA PROFORMA NR {invoice.invoice_number}" if invoice.is_proforma else f"FAKTURA NR {invoice.invoice_number}"
    story.append(Paragraph(title_text, title_style))
    
    header_data = [
        [Paragraph("Data wystawienia:", label_style), Paragraph("Miejsce wystawienia:", label_style)],
        [Paragraph(invoice.issue_date.strftime('%d.%m.%Y'), value_style), Paragraph("Łódź", value_style)]
    ]
    header_table = Table(header_data, colWidths=[9*cm, 8*cm])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0)]))
    story.append(header_table)
    story.append(Spacer(1, 0.5*cm))

    # 2. Sprzedawca, Nabywca, Odbiorca (Pionowo)
    sides_data = [
        [Paragraph("SPRZEDAWCA", label_style)],
        [Paragraph("<b>EDS Dariusz Surmacki.</b><br/>ul. Lawinowa 36C, 92-010 Łódź<br/>NIP: 7691427583<br/>e-mail: info@wyznaczresurs.com", value_style)],
        [Spacer(1, 0.3*cm)],
        [Paragraph("NABYWCA", label_style)],
        [Paragraph(f"<b>{invoice.buyer_name}</b><br/>{invoice.buyer_address.replace(',', '<br/>')}<br/>NIP: {invoice.buyer_nip}", value_style)]
    ]
    
    if invoice.recipient_name:
        sides_data.extend([
            [Spacer(1, 0.3*cm)],
            [Paragraph("ODBIORCA", label_style)],
            [Paragraph(f"<b>{invoice.recipient_name}</b><br/>{invoice.recipient_address.replace(',', '<br/>')}", value_style)]
        ])
    
    sides_table = Table(sides_data, colWidths=[17*cm])
    sides_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(sides_table)
    story.append(Spacer(1, 0.5*cm))

    # 3. Pozycje na fakturze
    items_data = [
        [Paragraph("Lp.", table_header_style), Paragraph("Nazwa usługi/towaru", table_header_style), 
         Paragraph("Ilość", table_header_style), Paragraph("Netto", table_header_style), 
         Paragraph("VAT", table_header_style), Paragraph("Brutto", table_header_style)]
    ]
    
    # Pozycja z nazwy usługi w modelu
    items_data.append([
        "1", 
        Paragraph(invoice.service_name, value_style), 
        "1 szt.", 
        f"{invoice.net_amount} PLN", 
        "23%", 
        f"{invoice.gross_amount} PLN"
    ])

    items_table = Table(items_data, colWidths=[1*cm, 6*cm, 2*cm, 2.5*cm, 2*cm, 3.5*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,-1), 'DejaVuSans'),
        ('FONTNAME', (0,0), (-1,0), 'DejaVuSans-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.5*cm))

    # 4. Podsumowanie
    summary_data = [
        ["", "Stawka", "Netto", "VAT", "Brutto"],
        ["RAZEM", "23%", f"{invoice.net_amount} PLN", f"{invoice.vat_amount} PLN", f"{invoice.gross_amount} PLN"]
    ]
    summary_table = Table(summary_data, colWidths=[7*cm, 2*cm, 2.5*cm, 2.5*cm, 3*cm])
    summary_table.setStyle(TableStyle([
        ('GRID', (1,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'DejaVuSans'),
        ('FONTNAME', (0,1), (0,1), 'DejaVuSans-Bold'),
        ('BACKGROUND', (1,0), (-1,0), colors.whitesmoke),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.5*cm))

    # Warunki płatności
    terms_map = dict(invoice.PAYMENT_TERM_CHOICES)
    term_label = terms_map.get(invoice.payment_terms, invoice.payment_terms)
    story.append(Paragraph(f"<b>Sposób i termin płatności:</b> {term_label}", value_style))
    story.append(Spacer(1, 0.5*cm))

    # 5. KSeF info
    if invoice.ksef_reference_number:
        story.append(Paragraph("Informacje dodatkowe", label_style))
        story.append(Paragraph(f"Faktura przesłana do KSeF. Numer referencyjny: {invoice.ksef_reference_number}", value_style))
        
        if getattr(invoice, 'ksef_invoice_hash', None):
            import qrcode
            from reportlab.platypus import Image as RLImage
            
            # KSeF v2 QR format: [BASE_URL]/[NrKSeF]/[HASH] lub [BASE_URL]/[NIP]/[DATA]/[HASH]
            inv_hash = invoice.ksef_invoice_hash.replace('+', '-').replace('/', '_').rstrip('=')
            
            is_sandbox = getattr(settings, 'KSEF_SANDBOX', True)
            host = 'qr-test.ksef.mf.gov.pl' if is_sandbox else 'qr.ksef.mf.gov.pl'
            qr_url = f"https://{host}/{invoice.ksef_reference_number}/{inv_hash}"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=1)
            qr.add_data(qr_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            qr_buffer = BytesIO()
            img.save(qr_buffer, format="PNG")
            qr_buffer.seek(0)
            
            qr_image = RLImage(qr_buffer, width=3*cm, height=3*cm)
            
            qr_table_data = [
                [qr_image],
                [Paragraph(invoice.ksef_reference_number or "OFFLINE", ParagraphStyle('QRLabel', parent=styles['Normal'], fontSize=7, alignment=1, fontName='DejaVuSans'))]
            ]
            qr_table = Table(qr_table_data, colWidths=[4*cm])
            qr_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            story.append(Spacer(1, 0.5*cm))
            story.append(qr_table)
            story.append(Paragraph(f"<font size='7' color='grey'>Link weryfikacyjny KSeF v2</font>", ParagraphStyle('QRHint', parent=styles['Normal'], alignment=1, fontName='DejaVuSans')))

    # 6. Stopka
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("Dziękujemy za skorzystanie z naszych usług!", ParagraphStyle('Footer', parent=styles['Normal'], alignment=1, fontName='DejaVuSans')))

    doc.build(story)
    return buffer.getvalue()
