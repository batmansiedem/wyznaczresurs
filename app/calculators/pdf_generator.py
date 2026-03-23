"""Generowanie raportów PDF dla wyników obliczeń resursu UTB.

Wzór: public_html/wciagarka/print_wciagarka.php
Layout: dwukolumnowa tabela (zielona etykieta | wartość) + wykresy słupkowe na stronie 2.
"""

import os
from PIL import Image as PILImage
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    Spacer, Image, PageBreak,
)
from reportlab.lib.units import cm, mm
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime

# ── Kolory (wg PHP: SetFillColor) ──────────────────────────────────────────
C_GREEN   = colors.HexColor('#2E8B57')   # (46,139,87)  — tło etykiety
C_GREY    = colors.HexColor('#D8D8D8')   # (216,216,216) — nagłówki sekcji
C_SALMON  = colors.HexColor('#EC7063')   # (236,112,99)  — "Przebieg" header
C_SALMON2 = colors.HexColor('#F1948A')   # (241,148,138) — "Przebieg" label
C_WHITE   = colors.white
C_BLACK   = colors.black
C_BAR1    = colors.HexColor('#CC8400')   # (204,132,0)   — bar resurs
C_BAR2    = colors.HexColor('#6464FF')   # (100,100,255) — bar cykli

# ── Czcionki ────────────────────────────────────────────────────────────────
FONT_PATH = os.path.join(settings.BASE_DIR, 'core', 'fonts')
pdfmetrics.registerFont(TTFont('DVS',  os.path.join(FONT_PATH, 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DVSB', os.path.join(FONT_PATH, 'DejaVuSans-Bold.ttf')))

# ── Etykiety wejściowe (zgodne z PHP public_html) ──────────────────────────
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
    'cykle_zmiana':         'Ilość cykli przypadających na zmianę',
    'dni_robocze':          'Przyjęta ilość dni roboczych',
    'tryb_pracy':           'Tryb pracy',
    'sposob_rejestracji':   'Sposób rejestracji przez eksploatującego warunków eksploatacji urządzenia',
    'q_max':                'Udźwig maksymalny Q_max [kg]',
    'q_o':                  'Masa osprzętu Q_osp [kg]',
    'h_max':                'Maksymalna wysokość podnoszenia h_max [m]',
    'v_pod':                'Prędkość podnoszenia/opuszczania v_pod [m/min]',
    'v_jaz':                'Prędkość jazdy [m/min]',
    'v_prz':                'Prędkość przesuwu [m/min]',
    's_sz':                 'Długość szyny jezdnej s [m]',
    'max_cykle_prod':       'Graniczna ilość cykli wg producenta',
    'spec':                 'Czy chcesz wyznaczyć resurs po pierwszym przeglądzie specjalnym?',
    'ponowny_resurs':       'Czy chcesz wykonać ponowne wyznaczenie resursu?',
    'ostatni_resurs':       'Procent wykorzystania z ostatnich obliczeń resursu [%]',
    'data_resurs':          'Data wyznaczenia ostatniego resursu',
    'ster':                 'Rodzaj sterowania',
    'gnp_check':            'GNP',
    'gnp_czas':             'Przewidywany czas pracy GNP [h]',
    'mechanizm_pomocniczy': 'Mechanizm pomocniczy',
    'czas_pracy_mech':      'Średni czas pracy mechanizmu na cykl [min]',
    'konstrukcja':          'Czy konstrukcja stalowa jest zdeformowana i/lub pojawiły się pęknięcia w złączach spawanych?',
    'automatyka':           'Czy automatyka sterująca i/lub zabezpieczająca jest sprawna i aktywna?',
    'sworznie':             'Czy sworznie oraz połączenia rozłączne są właściwie zmontowane i w dobrym stanie technicznym?',
    'ciegna':               'Czy cięgna (łańcuchy, liny) są w dobrym stanie technicznym?',
    'eksploatacja':         'Czy urządzenie eksploatowane jest zgodnie z przeznaczeniem i instrukcją eksploatacji?',
    'szczelnosc':           'Czy układ hydrauliczny jest szczelny, a zawory zwrotne sprawne?',
    'hamulce':              'Czy układ hamulcowy jest sprawny?',
    'nakretka':             'Czy nakrętka kontrująca oraz bolec zabezpieczający są w dobrym stanie technicznym?',
    'warkocz':              'Warkocz lin (liny nośne)',
    'rok_budowy':           'Rok budowy dźwigu',
    'przeznaczenie':        'Przeznaczenie dźwigu',
    'operator':             'Rodzaj obsługi',
    'budynek':              'Miejsce zabudowy',
    'przystanki':           'Ilość przystanków',
    'liczba_dzwigow':       'Liczba dźwigów obsługujących przystanki',
    'h_pod':                'Wysokość podnoszenia kabiny [m]',
    'pyt_motogodzin':       'Czy dźwig posiada licznik motogodzin?',
    'licznik_pracy':        'Łączna ilość motogodzin [h]',
    'cykle_dzwig':          'Ilość jazd dźwigu',
    'naped':                'Rodzaj napędu',
    'operatorzy':           'Ilość operatorów',
    'powierzchnia':         'Stan powierzchni magazynu',
    'serwis':               'Plan serwisowy',
    'dlugosc_widel':        'Długość wideł [mm]',
    'kat_masztu_alfa':      'Kąt przechyłu masztu alfa [°]',
    'kat_masztu_beta':      'Kąt przechyłu masztu beta [°]',
    'motogodziny':          'Łączna ilość motogodzin [h]',
    'efektywny_czas':       'Efektywny czas pracy [%]',
    'klasa_naprezenia':     'Klasa współczynnika przebiegu naprężeń',
    # Widmo Kd
    'q_1': 'Ciężar dla cykli C(i=1) [kg]',  'c_1': 'Procent cykli C(i=1) [%]',
    'q_2': 'Ciężar dla cykli C(i=2) [kg]',  'c_2': 'Procent cykli C(i=2) [%]',
    'q_3': 'Ciężar dla cykli C(i=3) [kg]',  'c_3': 'Procent cykli C(i=3) [%]',
    'q_4': 'Ciężar dla cykli C(i=4) [kg]',  'c_4': 'Procent cykli C(i=4) [%]',
    'q_5': 'Ciężar dla cykli C(i=5) [kg]',  'c_5': 'Procent cykli C(i=5) [%]',
    # Widmo HDR
    'h_1': 'Wys. podnoszenia H(i=1) [m]',   'cc_1': 'Procent czasu T(i=1) [%]',
    'h_2': 'Wys. podnoszenia H(i=2) [m]',   'cc_2': 'Procent czasu T(i=2) [%]',
    'h_3': 'Wys. podnoszenia H(i=3) [m]',   'cc_3': 'Procent czasu T(i=3) [%]',
    'h_4': 'Wys. podnoszenia H(i=4) [m]',   'cc_4': 'Procent czasu T(i=4) [%]',
    'h_5': 'Wys. podnoszenia H(i=5) [m]',   'cc_5': 'Procent czasu T(i=5) [%]',
}

# ── Etykiety wynikowe ───────────────────────────────────────────────────────
OUTPUT_LABELS = {
    'resurs_wykorzystanie':      ('Resurs wykorzystanie [%]', '%'),
    'U_WSK':                     ('Maksymalna liczba cykli (U_WSK)', 'cykli'),
    'T_WSK':                     ('Projektowa zdolność czasowa T_WSK', 'h'),
    'F_X':                       ('Współczynnik F [-]', ''),
    'ilosc_cykli':               ('Ilość odbytych cykli', 'cykli'),
    'ilosc_cykli_rok':           ('Ilość cykli przypadających na rok [cykle/rok]', 'cykli/rok'),
    'czas_uzytkowania_mech':     ('Czas użytkowania mechanizmu', 'h'),
    'czas_uzytkowania_mech_rok': ('Czas użytkowania mechanizmu/rok', 'h/rok'),
    'wsp_kdr':                   ('Współczynnik Kd [-]', ''),
    'wsp_km':                    ('Współczynnik widma km', ''),
    'stan_obciazenia':           ('Stan obciążenia', ''),
    'data_prognoza':             ('Symulacja daty osiągnięcia resursu przy obecnych parametrach pracy', ''),
    'resurs_prognoza_dni':       ('Ilość dni pozostałych do osiągnięcia resursu przy obecnych parametrach pracy [dni] *', 'dni'),
    'ldr':                       ('Współczynnik widma LDR', ''),
    'hdr':                       ('Współczynnik HDR', ''),
    'ss_factor':                 ('Współczynnik SS', ''),
    'zalecenia':                 ('Zalecenia', ''),
    'prognoza':                  ('Prognoza', 'lata'),
    'wiek_dzwigu':               ('Wiek dźwigu', 'lata'),
}

# Kolejność pól w tabeli parametrów (wg kolejności z PHP)
_PARAM_ORDER = [
    'typ', 'nr_fabryczny', 'nr_ewidencyjny', 'nr_udt', 'producent',
    'wykonawca', 'uwagi',
    'q_max', 'h_max', 'v_pod', 'v_jaz', 'v_prz', 's_sz',
    'ponowny_resurs', 'data_resurs', 'ostatni_resurs',
    'lata_pracy', 'ilosc_cykli', 'cykle_zmiana', 'dni_robocze', 'tryb_pracy',
    'sposob_rejestracji', 'max_cykle_prod',
    'ster', 'gnp_check', 'gnp_czas', 'mechanizm_pomocniczy', 'czas_pracy_mech',
    'q_o', 'spec',
    'q_1', 'c_1', 'q_2', 'c_2', 'q_3', 'c_3', 'q_4', 'c_4', 'q_5', 'c_5',
    'h_1', 'cc_1', 'h_2', 'cc_2', 'h_3', 'cc_3', 'h_4', 'cc_4', 'h_5', 'cc_5',
    'konstrukcja', 'automatyka', 'sworznie', 'ciegna',
    'eksploatacja', 'szczelnosc', 'hamulce', 'nakretka', 'warkocz',
    'rok_budowy', 'przeznaczenie', 'operator', 'budynek', 'przystanki',
    'liczba_dzwigow', 'h_pod', 'pyt_motogodzin', 'licznik_pracy', 'cykle_dzwig',
    'naped', 'operatorzy', 'powierzchnia', 'serwis',
    'dlugosc_widel', 'kat_masztu_alfa', 'kat_masztu_beta',
    'motogodziny', 'efektywny_czas', 'klasa_naprezenia',
]

# Kolejność pól wynikowych (wg PHP — resurs na końcu strony 1)
_RESULT_ORDER = [
    'wsp_kdr', 'wsp_km', 'ldr', 'hdr', 'ss_factor',
    'stan_obciazenia', 'F_X',
    'U_WSK', 'T_WSK', 'ilosc_cykli', 'czas_uzytkowania_mech',
    'ilosc_cykli_rok', 'czas_uzytkowania_mech_rok',
    'resurs_wykorzystanie',
    'resurs_prognoza_dni', 'data_prognoza',
    'prognoza', 'wiek_dzwigu',
]


# ── Pomocnicze ──────────────────────────────────────────────────────────────

def _format_val(val) -> str:
    if isinstance(val, dict):
        v = val.get('value', '')
        u = val.get('unit', '')
        return f"{v} {u}".strip() if v not in (None, '') else '-'
    s = str(val) if val is not None else ''
    return s if s else '-'


def _s(font='DVS', size=9, color=C_BLACK, align=0):
    return ParagraphStyle('_', fontName=font, fontSize=size,
                          textColor=color, alignment=align, leading=size + 3)


def _p(text, **kw):
    return Paragraph(str(text), _s(**kw))




def _two_col_table(rows: list, w1=9.5, w2=8.0, label_color=None) -> Table:
    """
    Buduje dwukolumnową tabelę wg wzoru PHP:
    rows: list of (label_str, value_str) lub (label_str, value_str, label_bg_color)
    """
    lc = label_color or C_GREEN
    table_data = []
    row_colors = []

    for i, row in enumerate(rows):
        lbl, val = row[0], row[1]
        bg = row[2] if len(row) > 2 else lc
        table_data.append([
            _p(lbl, font='DVSB', size=9, color=C_WHITE),
            _p(val, font='DVS',  size=9, color=C_BLACK, align=1),
        ])
        row_colors.append(bg)

    t = Table(table_data, colWidths=[w1 * cm, w2 * cm])
    styles = [
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#AAAAAA')),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]
    for i, bg in enumerate(row_colors):
        styles.append(('BACKGROUND', (0, i), (0, i), bg))
        styles.append(('TEXTCOLOR',  (0, i), (0, i), C_WHITE))
    t.setStyle(TableStyle(styles))
    return t


def _section_header_row(text: str, bg=None) -> Table:
    """Nagłówek sekcji — szary/kolorowy pasek na pełną szerokość."""
    bg = bg or C_GREY
    t = Table(
        [[_p(text, font='DVSB', size=9,
             color=C_WHITE if bg != C_GREY else C_BLACK, align=1)]],
        colWidths=[17.5 * cm],
    )
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (0, 0), bg),
        ('LEFTPADDING',   (0, 0), (0, 0), 5),
        ('TOPPADDING',    (0, 0), (0, 0), 4),
        ('BOTTOMPADDING', (0, 0), (0, 0), 4),
        ('GRID',          (0, 0), (0, 0), 0.5, colors.HexColor('#AAAAAA')),
    ]))
    return t


def _horiz_bar_chart(bars: list, total_w_cm=17.5, bar_h_cm=1.2) -> Drawing:
    """
    Poziomy wykres słupkowy wg wzoru FPDF BarDiagram.
    bars: list of (label_str, value, max_value, bar_color)
    """
    LABEL_W = 8.5 * cm
    BAR_ZONE = (total_w_cm * cm) - LABEL_W - 0.3 * cm
    ROW_H    = bar_h_cm * cm
    BAR_H    = ROW_H * 0.75
    BAR_OFF  = (ROW_H - BAR_H) / 2

    nb       = len(bars)
    TOTAL_H  = ROW_H * nb + 1.2 * cm   # +miejsce na skalę

    d = Drawing(total_w_cm * cm, TOTAL_H)

    # Oś / ramka
    d.add(Rect(LABEL_W, 1.2 * cm, BAR_ZONE, ROW_H * nb,
               fillColor=colors.white, strokeColor=colors.HexColor('#AAAAAA'),
               strokeWidth=0.5))

    # Podziałka (4 działy)
    for n_div in range(5):
        x = LABEL_W + (n_div / 4) * BAR_ZONE
        d.add(Line(x, 0.7 * cm, x, 1.2 * cm + ROW_H * nb,
                   strokeColor=colors.HexColor('#BBBBBB'), strokeWidth=0.4))
        # Label skali pod osią
        val_max = bars[0][2] if bars else 100
        tick_val = (n_div / 4) * val_max
        d.add(String(x, 0.1 * cm, f'{tick_val:.0f}',
                     fontName='DVS', fontSize=6.5,
                     fillColor=colors.HexColor('#555555'), textAnchor='middle'))

    for i, (lbl, val, max_val, bar_color) in enumerate(bars):
        y_row = 1.2 * cm + i * ROW_H

        # Słupek
        fill_w = max(1, (float(val) / max(float(max_val), 0.001)) * BAR_ZONE)
        d.add(Rect(LABEL_W, y_row + BAR_OFF, fill_w, BAR_H,
                   fillColor=bar_color, strokeColor=None))

        # Etykieta po prawej stronie słupka
        d.add(String(LABEL_W + fill_w + 3, y_row + BAR_OFF + BAR_H / 2 - 4,
                     str(val), fontName='DVSB', fontSize=7.5,
                     fillColor=bar_color))

        # Etykieta wiersza (lewa strona)
        d.add(String(LABEL_W - 4, y_row + BAR_OFF + BAR_H / 2 - 4,
                     lbl, fontName='DVS', fontSize=7.5,
                     fillColor=C_BLACK, textAnchor='end'))

    return d


# ── Nagłówek strony (logo + tytuł) ─────────────────────────────────────────

def _build_header(result, calculator_name: str, logo_obj, theme) -> list:
    """Zwraca listę elementów story dla nagłówka dokumentu."""
    story_items = []

    # Logo
    logo_img = None
    show_logo = getattr(result.user, 'show_logo_on_pdf', True)
    logo_pos  = 'right'
    logo_w_cm = 4.5

    if show_logo:
        active_img  = logo_obj.image if logo_obj else getattr(result.user, 'custom_logo', None)
        logo_w_mm   = (logo_obj.width  if logo_obj else getattr(result.user, 'logo_width', 45))
        logo_h_mm   = (logo_obj.height if logo_obj else getattr(result.user, 'logo_height', 20))
        logo_pos    = (logo_obj.position if logo_obj else getattr(result.user, 'logo_position', 'right'))
        logo_w_cm   = logo_w_mm / 10.0

        if active_img:
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

    # Tytuł
    title_para = _p(f'Wyznaczenie resursu — {calculator_name}',
                    font='DVSB', size=11, color=theme)
    date_para  = _p(
        f'Data obliczeń: {result.created_at.strftime("%d.%m.%Y")}    '
        f'Użytkownik: {result.user.email}',
        font='DVS', size=8, color=colors.grey)

    USABLE = 17.5  # cm
    if logo_img:
        lw = logo_w_cm + 0.5
        tw = USABLE - lw
        if logo_pos == 'left':
            hdr = Table([[logo_img,
                          Table([[title_para], [date_para]], colWidths=[tw * cm])]],
                        colWidths=[lw * cm, tw * cm])
        else:
            hdr = Table([[Table([[title_para], [date_para]], colWidths=[tw * cm]),
                          logo_img]],
                        colWidths=[tw * cm, lw * cm])
    else:
        hdr = Table([[Table([[title_para], [date_para]], colWidths=[USABLE * cm])]],
                    colWidths=[USABLE * cm])

    hdr.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LINEBELOW',     (0, 0), (-1, -1), 1.5, theme),
    ]))
    story_items.append(hdr)
    story_items.append(Spacer(1, 0.3 * cm))
    return story_items


# ── Główna funkcja ──────────────────────────────────────────────────────────

def generate_result_pdf(result, calculator_name: str, logo_obj=None, signature_obj=None) -> bytes:
    """Generuje raport PDF dla wyniku obliczeń resursu (wg wzoru PHP)."""

    user_color = getattr(logo_obj, 'theme_color', None) or getattr(result.user, 'theme_color', '#1565C0')
    THEME = colors.HexColor(user_color)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.5 * cm, leftMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    story = []

    # ── Nagłówek ─────────────────────────────────────────────────────────────
    story += _build_header(result, calculator_name, logo_obj, THEME)

    W1 = 9.5   # cm — szerokość kolumny etykiety
    W2 = 8.0   # cm — szerokość kolumny wartości

    # ── Strona 1: Parametry wejściowe ────────────────────────────────────────
    input_data = result.input_data or {}

    # Budujemy wiersze wg ustalonej kolejności + pozostałe nieujęte
    seen = set()
    param_rows = []

    for key in _PARAM_ORDER:
        if key not in input_data:
            continue
        val = _format_val(input_data[key])
        if val and val != '-':
            label = INPUT_LABELS.get(key, key.replace('_', ' ').capitalize())
            param_rows.append((label, val))
            seen.add(key)

    # Pola poza listą (np. dodane w przyszłości)
    for key, raw in input_data.items():
        if key in seen:
            continue
        val = _format_val(raw)
        if val and val != '-':
            label = INPUT_LABELS.get(key, key.replace('_', ' ').capitalize())
            param_rows.append((label, val))

    if param_rows:
        story.append(_two_col_table(param_rows, w1=W1, w2=W2))
        story.append(Spacer(1, 0.3 * cm))

    # ── Wyniki (na końcu strony 1) ────────────────────────────────────────────
    output_data = result.output_data or {}

    result_rows = []
    seen_out = set()
    for key in _RESULT_ORDER:
        val = output_data.get(key)
        if val is None:
            continue
        label, unit = OUTPUT_LABELS.get(key, (key.replace('_', ' ').capitalize(), ''))
        display = f"{val} {unit}".strip() if unit else str(val)
        result_rows.append((label, display))
        seen_out.add(key)

    for key, raw in output_data.items():
        if key in seen_out or key == 'resurs_message':
            continue
        label, unit = OUTPUT_LABELS.get(key, (key.replace('_', ' ').capitalize(), ''))
        display = f"{raw} {unit}".strip() if unit else str(raw)
        result_rows.append((label, display))

    if result_rows:
        story.append(_two_col_table(result_rows, w1=W1, w2=W2))

    # ── Strona 2: Wykresy + zalecenia ────────────────────────────────────────
    story.append(PageBreak())
    story += _build_header(result, calculator_name, logo_obj, THEME)

    # Zalecenia / status
    zalecenia = output_data.get('zalecenia') or output_data.get('resurs_message', '')
    if zalecenia:
        story.append(_two_col_table(
            [('Zalecenia', str(zalecenia), THEME)], w1=W1, w2=W2))
        story.append(Spacer(1, 0.3 * cm))

    # ── Wykres 1: Stopień wykorzystania resursu ──────────────────────────────
    resurs_val = output_data.get('resurs_wykorzystanie')
    if resurs_val is not None:
        try:
            rv = float(resurs_val)
            story.append(_section_header_row('Zestawienie — Stopień wykorzystania resursu'))
            story.append(Spacer(1, 0.2 * cm))
            bars = [('Resurs wykorzystanie [%]', rv, 100.0, C_BAR1)]
            story.append(Table(
                [[_horiz_bar_chart(bars)]],
                colWidths=[17.5 * cm],
            ))
            story.append(Spacer(1, 0.4 * cm))
        except (ValueError, TypeError):
            pass

    # ── Wykres 2: Ilość cykli vs U_WSK ──────────────────────────────────────
    u_wsk = output_data.get('U_WSK')
    ilosc = output_data.get('ilosc_cykli') or input_data.get('ilosc_cykli')
    if u_wsk is not None and ilosc is not None:
        try:
            uv = float(u_wsk)
            iv = float(_format_val(ilosc).split()[0].replace(',', '.'))
            max_v = max(uv, iv) * 1.05
            story.append(_section_header_row('Zestawienie — Ilość cykli'))
            story.append(Spacer(1, 0.2 * cm))
            bars2 = [
                ('Ilość odbytych cykli', iv, max_v, C_BAR2),
                ('Maksymalna ilość cykli (U_WSK)', uv, max_v, C_BAR2),
            ]
            story.append(Table(
                [[_horiz_bar_chart(bars2, bar_h_cm=1.1)]],
                colWidths=[17.5 * cm],
            ))
            story.append(Spacer(1, 0.4 * cm))
        except (ValueError, TypeError, AttributeError):
            pass

    # ── Wykres 3: Czas vs T_WSK (dla mechanizmów czasowych) ─────────────────
    t_wsk = output_data.get('T_WSK')
    czas  = output_data.get('czas_uzytkowania_mech')
    if t_wsk is not None and czas is not None:
        try:
            tv = float(t_wsk)
            cv = float(str(czas).split()[0].replace(',', '.'))
            max_v = max(tv, cv) * 1.05
            story.append(_section_header_row('Zestawienie — Czas użytkowania mechanizmu'))
            story.append(Spacer(1, 0.2 * cm))
            bars3 = [
                ('Czas użytkowania mechanizmu [h]', cv, max_v, C_BAR2),
                ('Projektowa zdolność czasowa T_WSK [h]', tv, max_v, C_BAR2),
            ]
            story.append(Table(
                [[_horiz_bar_chart(bars3, bar_h_cm=1.1)]],
                colWidths=[17.5 * cm],
            ))
            story.append(Spacer(1, 0.4 * cm))
        except (ValueError, TypeError, AttributeError):
            pass

    # ── Przebieg — porównanie (jeśli ponowny resurs) ──────────────────────────
    ponowny = str(input_data.get('ponowny_resurs', '')).lower()
    if ponowny in ('tak', '1', 'true', 'yes'):
        ostatni   = input_data.get('ostatni_resurs', '-')
        data_ost  = _format_val(input_data.get('data_resurs', '-'))
        data_now  = result.created_at.strftime('%d.%m.%Y')
        rv_str    = str(resurs_val) if resurs_val is not None else '-'
        try:
            zmiana = f"{float(rv_str) - float(str(ostatni)):+.2f} %"
        except (ValueError, TypeError):
            zmiana = '-'

        story.append(_section_header_row('Przebieg — Stopień wykorzystania', bg=C_SALMON))
        story.append(Spacer(1, 0.1 * cm))
        story.append(_two_col_table([
            (data_ost,  f"{ostatni} %", C_SALMON2),
            (data_now,  f"{rv_str} %",  C_SALMON2),
            ('Zmiana',  zmiana,          C_SALMON2),
        ], w1=W1, w2=W2))
        story.append(Spacer(1, 0.4 * cm))

    # ── Podpis ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.6 * cm))

    show_sig = getattr(result.user, 'show_signature_on_pdf', True)
    if show_sig:
        if not signature_obj:
            from users.models import UserSignature
            signature_obj = UserSignature.objects.filter(
                user=result.user, is_default=True).first()

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
                sig_t = Table([[sig_img]], colWidths=[17.5 * cm])
                sig_t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), align)]))
                story.append(sig_t)
                if signature_obj.name:
                    al = {'bottom_left': 0, 'bottom_center': 1}.get(
                        signature_obj.position, 2)
                    story.append(_p(signature_obj.name, size=8,
                                    color=colors.grey, align=al))
            except Exception:
                pass

    # Linia podpisu
    sign_row = _two_col_table([
        ('Podpis osoby wykonującej obliczenia',
         '................................................................', THEME),
        ('Podpis eksploatującego',
         '................................................................', THEME),
    ], w1=W1, w2=W2)
    story.append(sign_row)
    story.append(Spacer(1, 0.4 * cm))

    # ── Stopka prawna (wg PHP) ───────────────────────────────────────────────
    legal1 = ('Dane o przebiegu eksploatacji wprowadzono w oparciu o oświadczeniu '
              'eksploatującego urządzenie.')
    legal2 = ('*-symulowana data osiągnięcia resursu może ulec zmianie w zależności '
              'od przyszłych warunków eksploatacji. Przypomina się o konieczności rejestrowania '
              'przebiegu eksploatacji urządzenia, która będzie podstawą do ciągłego monitorowania '
              'stopnia wykorzystania resursu (par. 7.2 RMPiT z dnia 30 października 2018).')
    legal3 = ('W przypadku modernizacji urządzenia w zakresie ww. parametrów pracy przyjętych '
              'do obliczeń resursu urządzenia należy wyznaczyć ponownie resurs.')

    for txt in (legal1, legal2, legal3):
        story.append(_p(txt, size=7, color=colors.grey, align=1))
        story.append(Spacer(1, 0.15 * cm))

    doc.build(story)
    return buffer.getvalue()
