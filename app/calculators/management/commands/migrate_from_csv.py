"""
Migracja danych z plików CSV (eksport phpMyAdmin) do Django.

Pliki źródłowe:
  members.csv               → użytkownicy (CustomUser)
  u685896714_calculators.csv → wyniki obliczeń (CalculatorResult)

Format pliku CSV:
  - separator: średnik (;)
  - wartości w cudzysłowach (")
  - WIELE tabel w jednym pliku: kolejne tabele oddzielone nowym nagłówkiem
    (linia zaczynająca się od "id";"username")
  - Kolejność 22 sekcji ↔ slugów zdefiniowana w SECTION_SLUGS (potwierdzona analizą kolumn)

Użycie:
    python manage.py migrate_from_csv
    python manage.py migrate_from_csv --dry-run
    python manage.py migrate_from_csv --skip-users
    python manage.py migrate_from_csv --skip-calcs
    python manage.py migrate_from_csv --members-csv path/do/members.csv
    python manage.py migrate_from_csv --calcs-csv  path/do/calculators.csv
"""

import csv
import io
import json
import logging
from pathlib import Path
from datetime import datetime

# Kolejność kodowań do próby — utf-8-sig/utf-8 pierwsze (nowe pliki), potem cp1250/iso dla starszych exportów phpMyAdmin
_ENCODINGS_TO_TRY = ['utf-8-sig', 'utf-8', 'cp1250', 'iso-8859-2']


def _read_text(path: Path, encoding: str = '') -> str:
    """Odczytuje plik tekstowy z auto-detekcją kodowania."""
    if encoding:
        return path.read_text(encoding=encoding, errors='replace')
    for enc in _ENCODINGS_TO_TRY:
        try:
            text = path.read_text(encoding=enc, errors='strict')
            logger_csv = logging.getLogger(__name__)
            logger_csv.info("Plik %s odczytany z kodowaniem %s", path.name, enc)
            return text
        except (UnicodeDecodeError, LookupError):
            continue
    # ostateczny fallback
    return path.read_text(encoding='utf-8', errors='replace')

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import CalculatorDefinition, CalculatorResult
from calculators.calculation_logic import CalculatorFactory
from calculators.utils import decimals_to_float
from rest_framework.exceptions import ValidationError as DRFValidationError

logger = logging.getLogger('calculators')
User = get_user_model()

BASE_DIR = Path(__file__).resolve().parents[4]
DEFAULT_MEMBERS_CSV = BASE_DIR / 'members.csv'
DEFAULT_CALCS_CSV   = BASE_DIR / 'u685896714_calculators.csv'

# ---------------------------------------------------------------------------
# Mapowanie kolejności sekcji w CSV → slug kalkulatora
# Potwierdzone przez analizę unikalnych kolumn i wartości pola typ w każdej sekcji
# ---------------------------------------------------------------------------
SECTION_SLUGS = [
    'autotransporter',        #  1 (19 wierszy, nakretka, typ=tlokowy/mechaniczny, BEZ ponowny_resurs)
    'dzwignik',               #  2 (218, +HDR h_1/cc_1/hdr, typ=śrubowy/tłokowy-hydrauliczny/dźwigniowy)
    'dzwig',                  #  3 (212, +przystanki/liczba_dzwigow)
    'hakowiec',               #  4 (113, typ=Hakowiec)
    'mech_jazdy_suwnicy',     #  5 (350, typ_urzadzenia=Suwnica)
    'mech_jazdy_wciagarki',   #  6 (625, typ_urzadzenia mixed)
    'mech_jazdy_zurawia',     #  7 (42,  typ_urzadzenia=Zuraw)
    'mech_podnoszenia',       #  8 (893, typ_urzadzenia mixed, największa sekcja mech)
    'mech_zmiany_obrotu',     #  9 (193, typ_urzadzenia=Zuraw)
    'mech_zmiany_wysiegu',    # 10 (164, typ_urzadzenia=Zuraw)
    'podest_ruchomy',         # 11 (1185, +p_1..p_25/moto_podest_ruchomy)
    'zuraw_przeladunkowy',    # 12 (474, hamulce=True, typ=hydrauliczny prostowodowy)
    'podnosnik_samochodowy',  # 13 (215, nakretka, ponowny_resurs, typ=mechaniczny/hydrauliczny/mieszany)
    'suwnica',                # 14 (614, gnp=True, typ=Suwnica warsztatowa)
    'ukladnica_magazynowa',   # 15 (143, +ster/licznik_pracy_pod/jaz/prz)
    'wciagarka',              # 16 (41,  gnp=True, typ=Wciagarka warsztatowa)
    'wciagnik',               # 17 (255, gnp=True, typ=Wciagnik warsztatowy)
    'winda_dekarska',         # 18 (16,  +producent/nr_udt/a_1/a_2/a_3)
    'wozek_jezdniowy',        # 19 (1272,+naped/widly_check/dlugosc_widel)
    'wozek_specjalizowany',   # 20 (117, +sposob_pracy/procent_jazda/procent_podnosnik, brak pola typ)
    'podest_zaladowczy',      # 21 (489, +L_b_max/s_factor/ldr/p_1..p_25)
    'zuraw',                  # 22 (506, +gnp_check/gnp_czas/q_o)
]

# ---------------------------------------------------------------------------
# Identyczne transformacje jak w migrate_legacy_data (pola output, masy, itd.)
# ---------------------------------------------------------------------------
OUTPUT_KEYS = {
    'F_X', 'U_WSK', 'T_WSK', 'resurs', 'resurs_message',
    'resurs_wykorzystanie', 'data_prognoza', 'ilosc_cykli_rok',
    'resurs_prognoza', 'wsp_kdr', 'stan_obciazenia',
    'klasa_wykorzystania_txt', 'klasa_wykorzystania',
    'resurs_wyk_pod', 'resurs_prog_pod', 'data_prog_pod',
    'resurs_wyk_jaz', 'resurs_prog_jaz', 'data_prog_jaz',
    'resurs_wyk_prz', 'resurs_prog_prz', 'data_prog_prz',
    'resurs_wyk_mas', 'resurs_prog_mas', 'data_prog_mas',
    't_max_pod', 't_sum_pod', 't_max_jaz', 't_sum_jaz',
    't_max_prz', 't_sum_prz', 't_max_mas', 't_sum_mas',
    'czas_uzytkowania_mech_rok', 'czas_uzytkowania_mech', 'wsp_km',
    'EDS_factor', 's_factor', 'ss_factor',
    'ilosc_motogodzin_rok', 'ilosc_motogodzin_dzien',
    'wiek_dzwigu', 'prognoza', 'zalecenia',
    'ilosc_moto_rok',
    'ldr', 'hdr',
}
DZWIG_EXTRA_OUTPUT = {'ilosc_cykli', 'prognoza', 'zalecenia'}
METADATA_KEYS = {'id', 'username', 'data_obliczen'}

MASS_KEYS  = {'q_max', 'q_1', 'q_2', 'q_3', 'q_4', 'q_5', 'q_o'}
YEAR_KEYS  = {'lata_pracy'}
CYCLE_KEYS = {'ilosc_cykli'}
BINARY_TAK_NIE = {'ponowny_resurs', 'gnp_check', 'spec'}
INSPECTION_FIELDS = {'konstrukcja', 'automatyka', 'sworznie', 'ciegna',
                     'eksploatacja', 'szczelnosc', 'hamulce', 'nakretka'}
MECH_SLUGS = {
    'mech_jazdy_suwnicy', 'mech_jazdy_wciagarki', 'mech_jazdy_zurawia',
    'mech_podnoszenia', 'mech_zmiany_obrotu', 'mech_zmiany_wysiegu',
}
MECH_TRYB_PRACY_MAP = {
    'jednozmianowy':  '1-zmianowy (8h)',
    'dwuzmianowy':    '2-zmianowy (16h)',
    'trzyzmianowy':   '3-zmianowy (24h)',
}
FIELD_RENAMES = {
    'ilosc_cykli_zmiana':   'cykle_zmiana',
    'ilosc_dni_roboczych':  'dni_robocze',
    'max_cykle':            'max_cykle_prod',
}
NUMERIC_NORMALIZE = {
    'zakres_godzin_1', 'zakres_godzin_2', 'zakres_godzin_3',
    'zakres_godzin_4', 'zakres_godzin_5', 'zakres_godzin_6',
    'procent_jazda', 'procent_podnosnik', 'ilosc_moto', 'max_moto_prod',
    'lata_pracy', 'ilosc_cykli', 'cykle_zmiana', 'dni_robocze',
    'h_max', 'v_pod', 'v_jaz', 'h_pod', 'L_b_max', 's_sz', 'v_prz',
    'licznik_pracy', 'ostatni_licznik', 'ostatni_resurs',
    'ostatni_resurs_mech_pod', 'ostatni_resurs_mech_jaz',
    'ostatni_resurs_mech_prz', 'ostatni_resurs_mech_mas',
}

# Fallback gdy device_config nie ma opcji dla danego pola (z polskimi znakami)
INSPECTION_FALLBACK = {
    'konstrukcja':  {1: 'Brak uszkodzeń', 0: 'Uszkodzenia',    -1: 'Nie dotyczy'},
    'automatyka':   {1: 'Brak uszkodzeń', 0: 'Uszkodzenia',    -1: 'Nie dotyczy'},
    'sworznie':     {1: 'Prawidłowy',     0: 'Nieprawidłowy',   -1: 'Prawidłowy'},
    'ciegna':       {1: 'Brak uszkodzeń', 0: 'Uszkodzenia',    -1: 'Nie dotyczy'},
    'eksploatacja': {1: 'Zgodne',         0: 'Niezgodne',      -1: 'Nie dotyczy'},
    'szczelnosc':   {1: 'Szczelny',       0: 'Nieszczelny',    -1: 'Nie dotyczy'},
    'hamulce':      {1: 'Sprawne',        0: 'Niesprawne',     -1: 'Nie dotyczy'},
    'nakretka':     {1: 'Sprawna',        0: 'Niesprawna',     -1: 'Nie dotyczy'},
}

# Mapa per-slug z prawdziwymi opcjami z device_config (ładowana raz przy starcie)
def _build_inspection_map() -> dict:
    try:
        from calculators.device_config import get_all_configs
        all_configs = get_all_configs()
    except Exception:
        return {}
    result = {}
    for slug, config in all_configs.items():
        fields = config.get('fields', {})
        slug_map = {}
        for fname, fdef in fields.items():
            if fname not in INSPECTION_FIELDS:
                continue
            opts = fdef.get('options', [])
            if len(opts) >= 2:
                slug_map[fname] = {
                    1:  opts[0],
                    0:  opts[1],
                    -1: opts[2] if len(opts) > 2 else opts[0],
                }
        if slug_map:
            result[slug] = slug_map
    return result

_INSPECTION_MAP = _build_inspection_map()


# ---------------------------------------------------------------------------
# CSV parser
# ---------------------------------------------------------------------------

def _parse_csv_value(s: str):
    """Konwertuje string CSV na Python-ową wartość."""
    if s is None or s.strip() == '' or s.upper() == 'NULL':
        return None
    s = s.strip()
    try:
        if '.' in s:
            return float(s)
        return int(s)
    except ValueError:
        return s if s else None


def parse_multitable_csv(file_path: Path, encoding: str = '') -> list[tuple[str, list[dict]]]:
    """
    Parsuje plik CSV z wieloma tabelami (phpMyAdmin export).
    Każda tabela zaczyna się nowym wierszem nagłówkowym (id;username;...).

    Zwraca listę krotek (slug, rows_list) w kolejności SECTION_SLUGS.
    """
    content = _read_text(file_path, encoding=encoding)
    lines = content.splitlines()

    sections_raw = []       # lista list wierszy (per sekcja)
    current_header = None
    current_rows_raw = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Nagłówek = linia zaczynająca się od "id";"username" lub id;username
        is_header = (
            stripped.startswith('"id";"username"') or
            stripped.startswith('id;username')
        )
        if is_header:
            if current_header is not None:
                sections_raw.append((current_header, current_rows_raw))
            current_header = stripped
            current_rows_raw = []
        else:
            if current_header is not None:
                current_rows_raw.append(stripped)

    if current_header is not None:
        sections_raw.append((current_header, current_rows_raw))

    result = []
    for idx, (header_line, raw_rows) in enumerate(sections_raw):
        slug = SECTION_SLUGS[idx] if idx < len(SECTION_SLUGS) else f'unknown_{idx}'
        columns = _parse_header(header_line)
        rows = []
        for raw in raw_rows:
            parsed = _parse_csv_row(raw, columns)
            if parsed:
                rows.append(parsed)
        result.append((slug, rows))
        logger.debug("CSV sekcja %d → %s: %d wierszy", idx + 1, slug, len(rows))

    return result


def _parse_header(line: str) -> list[str]:
    """Parsuje linię nagłówkową CSV → lista nazw kolumn."""
    reader = csv.reader(io.StringIO(line), delimiter=';', quotechar='"')
    for row in reader:
        return [c.strip() for c in row]
    return []


def _parse_csv_row(line: str, columns: list[str]) -> dict | None:
    """Parsuje jeden wiersz CSV → słownik {kolumna: wartość}."""
    try:
        reader = csv.reader(io.StringIO(line), delimiter=';', quotechar='"')
        for row in reader:
            if len(row) != len(columns):
                return None  # uszkodzony wiersz
            return {col: _parse_csv_value(val) for col, val in zip(columns, row)}
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Transformacje (identyczne jak w migrate_legacy_data)
# ---------------------------------------------------------------------------

def _normalize_numeric(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return val
    s = str(val).strip()
    if not s or s == '-':
        return None
    normalized = s.replace(',', '.')
    try:
        return float(normalized) if '.' in normalized else int(normalized)
    except ValueError:
        return val


def _convert_inspection(key: str, val, slug: str = '') -> str:
    try:
        int_val = int(float(val))
    except (ValueError, TypeError):
        return val
    # Szukaj w per-slug mapie (z prawdziwymi opcjami z JSON)
    field_map = _INSPECTION_MAP.get(slug, {}).get(key)
    if not field_map:
        field_map = INSPECTION_FALLBACK.get(key)
    if not field_map:
        return val
    return field_map.get(int_val, field_map.get(1))


def _wrap_value(key: str, val, slug: str, row: dict) -> object:
    if key in INSPECTION_FIELDS:
        return _convert_inspection(key, val, slug)
    if key in BINARY_TAK_NIE:
        try:
            return 'Tak' if int(float(val)) != 0 else 'Nie'
        except (ValueError, TypeError):
            return val
    if key == 'tryb_pracy' and slug in MECH_SLUGS:
        return MECH_TRYB_PRACY_MAP.get(str(val), val)
    if key == 'czas_cykle' and slug in MECH_SLUGS:
        jednostka = str(row.get('jednostka') or 's').strip() or 's'
        if val is None:
            return val
        return {'value': _normalize_numeric(val) or val, 'unit': jednostka}
    if key in MASS_KEYS | YEAR_KEYS | CYCLE_KEYS | NUMERIC_NORMALIZE:
        val = _normalize_numeric(val)
    if val is None:
        return val
    if key in MASS_KEYS:
        return {'value': val, 'unit': 'kg'}
    if key in YEAR_KEYS:
        return {'value': val, 'unit': 'lata'}
    if key in CYCLE_KEYS and slug != 'dzwig':
        return {'value': val, 'unit': 'cykl'}
    return val


def _split_row(row: dict, slug: str) -> tuple[dict, dict]:
    extra_output = DZWIG_EXTRA_OUTPUT if slug == 'dzwig' else set()
    all_output = OUTPUT_KEYS | extra_output

    input_data = {}
    output_data = {}

    if 'resurs' in row and isinstance(row.get('resurs'), str):
        output_data['resurs_message'] = row['resurs']

    for key, val in row.items():
        if key in METADATA_KEYS or key == 'resurs' or key == 'jednostka':
            continue
        key = FIELD_RENAMES.get(key, key)
        if key in all_output:
            output_data[key] = val
        else:
            input_data[key] = _wrap_value(key, val, slug, row)

    return input_data, output_data


# ---------------------------------------------------------------------------
# Konwersja hasła PHP bcrypt
# ---------------------------------------------------------------------------

def _convert_password(php_hash: str) -> str:
    if not php_hash:
        return ''
    if php_hash.startswith('$2y$'):
        return 'bcrypt$' + '$2b$' + php_hash[4:]
    if php_hash.startswith('$2b$'):
        return 'bcrypt$' + php_hash
    return ''


# ---------------------------------------------------------------------------
# Import użytkowników
# ---------------------------------------------------------------------------

def migrate_users(rows: list[dict], dry_run: bool, stdout) -> dict[str, object]:
    username_map = {}
    created = skipped = errors = 0

    for row in rows:
        old_username = str(row.get('username') or '').strip()
        email = str(row.get('email') or '').strip().lower()

        if not email or '@' not in email:
            if old_username and old_username.isdigit():
                email = f"{old_username}@nip.pl"
                stdout.write(f"  [NIP] username={old_username!r} => email={email}")
            else:
                stdout.write(f"  [SKIP] brak emaila: username={old_username!r}")
                skipped += 1
                continue

        existing = User.objects.filter(email=email).first()
        if existing:
            username_map[old_username] = existing
            skipped += 1
            continue

        is_company = str(row.get('user_type') or '').lower() == 'firma'
        name = str(row.get('name') or '').strip()
        nip_raw = str(row.get('NIP') or '').replace('-', '').replace(' ', '').strip()
        is_admin = str(row.get('admin') or 'NO').upper() == 'YES'
        is_active = str(row.get('active') or 'No') == 'Yes'

        try:
            premium = max(0, int(float(row.get('premium') or 0)))
        except (ValueError, TypeError):
            premium = 0
        try:
            discount = int(float(row.get('discount') or 0))
        except (ValueError, TypeError):
            discount = 0

        first_name = last_name = company_name = ''
        if is_company:
            company_name = name
        else:
            parts = name.split(' ', 1) if name else []
            first_name = parts[0] if parts else ''
            last_name  = parts[1] if len(parts) > 1 else ''

        password_hash = _convert_password(str(row.get('password') or ''))

        if dry_run:
            stdout.write(f"  [DRY] user: {email} | firma={is_company} | premium={premium}")
            created += 1
            username_map[old_username] = None
            continue

        try:
            with transaction.atomic():
                user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_company=is_company,
                    company_name=company_name,
                    nip=nip_raw,
                    address_line=str(row.get('adress_street') or '').strip(),
                    postal_code=str(row.get('post_code') or '').strip(),
                    city=str(row.get('adress_city') or '').strip(),
                    premium=premium,
                    discount_percent=discount,
                    is_staff=is_admin,
                    is_superuser=is_admin,
                    is_active=is_active,
                )
                user.password = password_hash if password_hash else None
                if not password_hash:
                    user.set_unusable_password()
                user.save()
                username_map[old_username] = user
                created += 1
                logger.info("Dodano użytkownika: %s (premium=%d)", email, premium)
        except Exception as e:
            stdout.write(f"  [ERR] {email}: {e}")
            logger.error("Błąd importu usera %s: %s", email, e)
            errors += 1

    stdout.write(f"Użytkownicy: {created} nowych, {skipped} pominiętych, {errors} błędów.")
    return username_map


# ---------------------------------------------------------------------------
# Import wyników kalkulatorów
# ---------------------------------------------------------------------------

def migrate_calculators(sections: list[tuple[str, list[dict]]],
                        username_map: dict, dry_run: bool, stdout) -> dict:
    defs = {d.slug: d for d in CalculatorDefinition.objects.all()}
    if not defs:
        stdout.write("  [WARN] Brak definicji kalkulatorów. Uruchom: python manage.py seed_data")
        return {}

    summary = {}
    total_created = total_skipped = total_errors = 0

    for slug, rows in sections:
        calc_def = defs.get(slug)
        if not calc_def:
            stdout.write(f"  [SKIP] slug={slug!r} — brak definicji w DB ({len(rows)} wierszy)")
            total_skipped += len(rows)
            summary[slug] = {'created': 0, 'skipped': len(rows), 'errors': 0}
            continue

        created = skipped = errors = 0

        for row in rows:
            old_username = str(row.get('username') or '').strip()
            user = username_map.get(old_username)
            if not user:
                if '@' in old_username:
                    user = User.objects.filter(email=old_username.lower()).first()
            if not user:
                skipped += 1
                continue

            raw_date = row.get('data_obliczen')
            if isinstance(raw_date, str):
                try:
                    created_at = datetime.strptime(raw_date, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    created_at = datetime.now()
            elif isinstance(raw_date, datetime):
                created_at = raw_date
            else:
                created_at = datetime.now()

            input_data, old_output_data = _split_row(row, slug)

            try:
                calc_instance = CalculatorFactory.get_calculator(slug, input_data)
                output_data = decimals_to_float(calc_instance.calculate())
            except (DRFValidationError, Exception) as e:
                if old_output_data:
                    output_data = old_output_data
                    logger.debug("[WARN-CALC] %s row=%s: %s — stare wyniki", slug, row.get('id'), e)
                else:
                    stdout.write(f"  [ERR-CALC] {slug} id={row.get('id')}: {e}")
                    errors += 1
                    continue

            if dry_run:
                nr = str(input_data.get('nr_fabryczny', '?'))
                nr = nr.encode('ascii', 'replace').decode('ascii')
                stdout.write(
                    f"  [DRY] {slug} | {user.email} | "
                    f"nr={nr} | "
                    f"resurs={output_data.get('resurs_wykorzystanie', '?')}%"
                )
                created += 1
                continue

            try:
                with transaction.atomic():
                    result = CalculatorResult(
                        user=user,
                        calculator_definition=calc_def,
                        input_data=input_data,
                        output_data=output_data,
                        is_locked=False,
                    )
                    result.save()
                    CalculatorResult.objects.filter(pk=result.pk).update(created_at=created_at)
                    created += 1
            except Exception as e:
                stdout.write(f"  [ERR] {slug} id={row.get('id')}: {e}")
                logger.error("Błąd importu %s id=%s: %s", slug, row.get('id'), e)
                errors += 1

        total_created += created
        total_skipped += skipped
        total_errors  += errors
        summary[slug] = {'created': created, 'skipped': skipped, 'errors': errors}
        stdout.write(
            f"  {slug:35s} => {created:4d} importowanych, "
            f"{skipped:3d} pominieto (brak usera), {errors:2d} bledow"
        )

    stdout.write(
        f"\nWyniki: {total_created} importowanych, "
        f"{total_skipped} pominiętych, {total_errors} błędów."
    )
    return summary


# ---------------------------------------------------------------------------
# Komenda
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = "Migruje dane z CSV (phpMyAdmin export) do Django"

    def add_arguments(self, parser):
        parser.add_argument('--members-csv', type=str, default=str(DEFAULT_MEMBERS_CSV))
        parser.add_argument('--calcs-csv',   type=str, default=str(DEFAULT_CALCS_CSV))
        parser.add_argument('--dry-run',     action='store_true')
        parser.add_argument('--skip-users',  action='store_true')
        parser.add_argument('--skip-calcs',  action='store_true')
        parser.add_argument('--encoding',    type=str, default='',
                            help='Kodowanie plików CSV (np. cp1250, utf-8). Domyślnie: auto-detekcja.')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        enc = options['encoding']
        if dry_run:
            self.stdout.write(self.style.WARNING("=== DRY RUN — nic nie zapisuję ==="))
        if enc:
            self.stdout.write(f"Kodowanie: {enc} (ręcznie)")
        else:
            self.stdout.write(f"Kodowanie: auto-detekcja (kolejność: {', '.join(_ENCODINGS_TO_TRY)})")

        username_map = {}

        # ── Użytkownicy ──────────────────────────────────────────────────
        if not options['skip_users']:
            members_path = Path(options['members_csv'])
            if not members_path.exists():
                self.stderr.write(self.style.ERROR(f"Nie znaleziono: {members_path}"))
                return
            self.stdout.write(f"\n--- IMPORT UŻYTKOWNIKÓW ({members_path.name}) ---")
            rows = list(csv.DictReader(
                _read_text(members_path, encoding=enc).splitlines(),
                delimiter=';', quotechar='"',
            ))
            # Przekształć wszystkie wartości przez _parse_csv_value
            cleaned = [{k: _parse_csv_value(str(v)) if v else None for k, v in r.items()} for r in rows]
            username_map = migrate_users(cleaned, dry_run, self.stdout)
        else:
            members_path = Path(options['members_csv'])
            if members_path.exists():
                self.stdout.write("Pomijam import — ładuję istniejących użytkowników...")
                rows = list(csv.DictReader(
                    _read_text(members_path, encoding=enc).splitlines(),
                    delimiter=';', quotechar='"',
                ))
                for row in rows:
                    old_username = str(row.get('username') or '').strip()
                    email = str(row.get('email') or '').strip().lower()
                    if not email or '@' not in email:
                        if old_username and old_username.isdigit():
                            email = f"{old_username}@nip.pl"
                        else:
                            continue
                    user = User.objects.filter(email=email).first()
                    if user:
                        username_map[old_username] = user

        # ── Wyniki kalkulatorów ──────────────────────────────────────────
        if not options['skip_calcs']:
            calcs_path = Path(options['calcs_csv'])
            if not calcs_path.exists():
                self.stderr.write(self.style.ERROR(f"Nie znaleziono: {calcs_path}"))
                return
            self.stdout.write(f"\n--- IMPORT WYNIKÓW ({calcs_path.name}) ---")
            sections = parse_multitable_csv(calcs_path, encoding=enc)
            self.stdout.write(f"Znaleziono {len(sections)} sekcji (tabel).")
            for i, (slug, rows) in enumerate(sections):
                self.stdout.write(f"  Sekcja {i+1:2d}: {slug} ({len(rows)} wierszy)")
            self.stdout.write("")
            migrate_calculators(sections, username_map, dry_run, self.stdout)

        self.stdout.write(self.style.SUCCESS("\nMigracja zakończona."))

        # Weryfikacja po imporcie
        if not dry_run:
            user_count = User.objects.count()
            calc_count = CalculatorResult.objects.count()
            self.stdout.write(
                f"\nStan bazy po migracji:\n"
                f"  Użytkownicy:         {user_count}\n"
                f"  Wyniki kalkulatorów: {calc_count}\n"
            )
