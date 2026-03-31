"""
Komenda migracji danych ze starej aplikacji PHP do nowej Django.

Parsuje dwa pliki SQL eksportowane z phpMyAdmin:
  - members.sql         → użytkownicy (CustomUser)
  - u685896714_calculators.sql → wyniki obliczeń (CalculatorResult)

Użycie:
    python manage.py migrate_legacy_data
    python manage.py migrate_legacy_data --members-sql path/do/members.sql
    python manage.py migrate_legacy_data --calcs-sql path/do/calculators.sql
    python manage.py migrate_legacy_data --dry-run   # podgląd bez zapisu

Ważne:
  - Hasła ze starej aplikacji (bcrypt PHP $2y$) są przeliczane na format Django.
    Użytkownicy mogą się logować starymi hasłami po dodaniu PASSWORD_HASHERS w settings.py.
  - Wyniki są importowane jako odblokowane (is_locked=False).
  - Jeśli użytkownik lub wynik już istnieje → pomijany (idempotentna operacja).
"""

import re
import json
from pathlib import Path
from datetime import datetime, date

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from calculators.models import CalculatorDefinition, CalculatorResult
from calculators.calculation_logic import CalculatorFactory
from calculators.utils import decimals_to_float
from rest_framework.exceptions import ValidationError as DRFValidationError

User = get_user_model()

# Ścieżki domyślne (relative do BASE_DIR / app)
DEFAULT_MEMBERS_SQL = Path(__file__).resolve().parents[4] / 'members.sql'
DEFAULT_CALCS_SQL   = Path(__file__).resolve().parents[4] / 'u685896714_calculators.sql'

# Pola inspekcji (inspection_status) — stara baza przechowuje 0/1/-1 (int),
# nowa app używa stringów (np. "Brak uszkodzeń", "Uszkodzenia", "Nie dotyczy").
# Konwersja: 1=OK (options[0]), 0=Problem (options[1]), -1=N/D (options[-1])
INSPECTION_FIELDS = {'konstrukcja', 'automatyka', 'sworznie', 'ciegna',
                     'eksploatacja', 'szczelnosc', 'hamulce', 'nakretka'}

def _build_inspection_map() -> dict:
    """
    Zwraca słownik: {slug: {field_name: {1: ok_str, 0: problem_str, -1: na_str}}}
    Dane brane z device_config (per-device JSON) — per kalkulator, bo opcje mogą się różnić.
    """
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
                    1:  opts[0],                           # OK (pierwsza opcja)
                    0:  opts[1],                           # Problem (druga opcja)
                    -1: opts[2] if len(opts) > 2 else opts[0],  # N/A lub OK gdy brak N/A
                }
        if slug_map:
            result[slug] = slug_map
    return result

_INSPECTION_MAP = _build_inspection_map()

# ---------------------------------------------------------------------------
# Podział pól: output (obliczone) vs input (podane przez użytkownika)
# Wszystko poza OUTPUT i METADATA trafia do input_data.
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
    'resurs_prog_pod', 'resurs_wyk_pod',  # winda_dekarska
    'ilosc_moto_rok',
    'ldr', 'hdr',  # obliczone współczynniki LDR/HDR (nie wejście diagramu)
}

# Dla dzwig — ilosc_cykli jest OBLICZANA, nie podawana
DZWIG_EXTRA_OUTPUT = {'ilosc_cykli', 'prognoza', 'zalecenia'}

METADATA_KEYS = {'id', 'username', 'data_obliczen'}

# Pola numeryczne z masą → opakowujemy w {value, unit: 'kg'}
MASS_KEYS = {'q_max', 'q_1', 'q_2', 'q_3', 'q_4', 'q_5', 'q_o'}
# Pola czasu (lata) → {value, unit: 'lata'}
YEAR_KEYS = {'lata_pracy'}
# Pola cykli → {value, unit: 'cykl'} — oprócz dzwig (tam to output)
CYCLE_KEYS = {'ilosc_cykli'}

# Pola binarne: stara baza trzyma 0/1 (int lub string), nowa app oczekuje 'Nie'/'Tak'
BINARY_TAK_NIE = {'ponowny_resurs', 'gnp_check', 'spec'}

# `tryb_pracy` dla mechanizmów — stare wartości słowne → nowe z godziną
# (urządzenia - wciagarka, suwnica itp. - mają te same wartości, więc nie trzeba mapować)
MECH_TRYB_PRACY_MAP = {
    'jednozmianowy': '1-zmianowy (8h)',
    'dwuzmianowy':   '2-zmianowy (16h)',
    'trzyzmianowy':  '3-zmianowy (24h)',
}
MECH_SLUGS = {
    'mech_jazdy_suwnicy', 'mech_jazdy_wciagarki', 'mech_jazdy_wciagnika',
    'mech_jazdy_zurawia', 'mech_podnoszenia', 'mech_zmiany_obrotu', 'mech_zmiany_wysiegu',
}

# `jednostka` jest pomocniczą kolumną do `czas_cykle` w mechanizmach (unit: 's'/'min')
# Po użyciu trafia do czas_cykle jako {value, unit}, sama jest pomijana
JEDNOSTKA_KEY = 'jednostka'

# Zmiana nazw pól: stara baza → nowa aplikacja (dotyczy wszystkich kalkulatorów)
FIELD_RENAMES = {
    'ilosc_cykli_zmiana': 'cykle_zmiana',
    'ilosc_dni_roboczych': 'dni_robocze',
    'max_cykle': 'max_cykle_prod',
}


# ===========================================================================
# PARSER SQL (obsługuje format phpMyAdmin dump)
# ===========================================================================

def _parse_value(s: str):
    """Konwertuje string z SQL na Python: NULL→None, liczby, stringi."""
    s = s.strip()
    if s.upper() == 'NULL':
        return None
    if s.startswith("'") and s.endswith("'"):
        inner = s[1:-1]
        # Odkoduj escaping MySQL: \' → ', '' → ', \\ → \
        inner = inner.replace("\\'", "'").replace("''", "'").replace('\\\\', '\\')
        inner = inner.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
        return inner if inner != '' else None
    try:
        if '.' in s:
            return float(s)
        return int(s)
    except ValueError:
        return s


def _tokenize_row(row_str: str) -> list:
    """
    Tokenizuje jeden wiersz VALUES (...) na listę wartości.
    Obsługuje zagnieżdżone stringi z przecinkami.
    """
    tokens = []
    buf = ''
    in_str = False
    i = 0
    while i < len(row_str):
        ch = row_str[i]
        if in_str:
            if ch == '\\':
                buf += ch + row_str[i + 1] if i + 1 < len(row_str) else ch
                i += 2
                continue
            elif ch == "'":
                # sprawdź '' (escaped quote)
                if i + 1 < len(row_str) and row_str[i + 1] == "'":
                    buf += "''"
                    i += 2
                    continue
                else:
                    buf += ch
                    in_str = False
            else:
                buf += ch
        else:
            if ch == "'":
                buf += ch
                in_str = True
            elif ch == ',':
                tokens.append(_parse_value(buf.strip()))
                buf = ''
            else:
                buf += ch
        i += 1
    if buf.strip():
        tokens.append(_parse_value(buf.strip()))
    return tokens


def parse_sql_inserts(sql_content: str) -> dict[str, list[dict]]:
    """
    Parsuje plik SQL i zwraca dict: {table_name: [row_dict, ...]}
    """
    result = {}

    # Znajdź wszystkie bloki INSERT INTO `table` (cols) VALUES (...)
    pattern = re.compile(
        r'INSERT INTO `(\w+)` \(([^)]+)\) VALUES\s*(.*?);',
        re.DOTALL | re.IGNORECASE
    )

    for match in pattern.finditer(sql_content):
        table   = match.group(1)
        cols_str = match.group(2)
        vals_str = match.group(3)

        columns = [c.strip().strip('`') for c in cols_str.split(',')]

        # Wyciągnij poszczególne wiersze (każdy w nawiasach)
        rows_raw = re.findall(r'\(([^)]*(?:\([^)]*\)[^)]*)*)\)', vals_str)
        # Lepszy parser nawiasów dla wierszy z wartościami string
        rows_raw = _extract_value_tuples(vals_str)

        rows = []
        for row_str in rows_raw:
            values = _tokenize_row(row_str)
            if len(values) == len(columns):
                rows.append(dict(zip(columns, values)))

        if table not in result:
            result[table] = []
        result[table].extend(rows)

    return result


def _extract_value_tuples(vals_str: str) -> list[str]:
    """
    Wyciąga zawartość każdego (tuple) ze stringiem VALUES.
    Obsługuje string z przecinkami i nawiasami wewnątrz.
    """
    tuples = []
    depth = 0
    in_str = False
    start = None
    i = 0
    while i < len(vals_str):
        ch = vals_str[i]
        if in_str:
            if ch == '\\':
                i += 2
                continue
            elif ch == "'":
                in_str = False
        else:
            if ch == "'":
                in_str = True
            elif ch == '(':
                if depth == 0:
                    start = i + 1
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0 and start is not None:
                    tuples.append(vals_str[start:i])
                    start = None
        i += 1
    return tuples


# ===========================================================================
# MIGRACJA UŻYTKOWNIKÓW
# ===========================================================================

def _convert_password(php_hash: str) -> str:
    """
    Konwertuje PHP bcrypt ($2y$) na format Django BCryptPasswordHasher (bcrypt$$2b$).
    """
    if not php_hash:
        return ''
    if php_hash.startswith('$2y$'):
        django_hash = 'bcrypt$' + '$2b$' + php_hash[4:]
        return django_hash
    if php_hash.startswith('$2b$'):
        return 'bcrypt$' + php_hash
    return ''  # nieznany format → brak hasła


def migrate_users(members_rows: list[dict], dry_run: bool, stdout) -> dict[str, User]:
    """
    Tworzy użytkowników z tabeli members.
    Zwraca mapę: old_username → User (dla późniejszego mapowania wyników).
    """
    username_map = {}
    created = skipped = errors = 0

    for row in members_rows:
        old_username = row.get('username', '') or ''
        email = (row.get('email') or '').strip().lower()

        # Brak emaila — jeśli username wygląda jak NIP/telefon (same cyfry), generujemy email
        if not email or '@' not in email:
            if old_username and old_username.isdigit():
                email = f"{old_username}@nip.pl"
                stdout.write(f"  [NIP] username={old_username!r} => email={email}")
            else:
                stdout.write(f"  [SKIP] brak emaila dla username={old_username!r}")
                skipped += 1
                continue

        # Sprawdź czy już istnieje
        existing = User.objects.filter(email=email).first()
        if existing:
            username_map[old_username] = existing
            skipped += 1
            continue

        # Dane osobowe / firmowe
        is_company = (row.get('user_type') or '').lower() == 'firma'
        name = (row.get('name') or '').strip()
        nip_raw = (row.get('NIP') or '').replace('-', '').replace(' ', '').strip()
        is_admin = str(row.get('admin') or 'NO').upper() == 'YES'
        is_active = str(row.get('active') or 'No') == 'Yes'

        # Premium (float w DB → int)
        try:
            premium = max(0, int(float(row.get('premium') or 0)))
        except (ValueError, TypeError):
            premium = 0

        # Rabat
        try:
            discount = int(float(row.get('discount') or 0))
        except (ValueError, TypeError):
            discount = 0

        # Imię/nazwisko lub firma
        first_name = last_name = company_name = ''
        if is_company:
            company_name = name
        else:
            parts = name.split(' ', 1) if name else []
            first_name = parts[0] if parts else ''
            last_name  = parts[1] if len(parts) > 1 else ''

        password_hash = _convert_password(row.get('password') or '')

        if dry_run:
            stdout.write(f"  [DRY] user: {email} | firma={is_company} | premium={premium}")
            created += 1
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
                    address_line=(row.get('adress_street') or '').strip(),
                    postal_code=(row.get('post_code') or '').strip(),
                    city=(row.get('adress_city') or '').strip(),
                    premium=premium,
                    discount_percent=discount,
                    is_staff=is_admin,
                    is_superuser=is_admin,
                    is_active=is_active,
                )
                if password_hash:
                    user.password = password_hash
                else:
                    user.set_unusable_password()
                user.save()
                username_map[old_username] = user
                created += 1
        except Exception as e:
            stdout.write(f"  [ERR] {email}: {e}")
            errors += 1

    stdout.write(f"Użytkownicy: {created} nowych, {skipped} pominiętych, {errors} błędów.")
    return username_map


# ===========================================================================
# MIGRACJA WYNIKÓW KALKULATORÓW
# ===========================================================================

def _convert_inspection(key: str, val, slug: str):
    """
    Konwertuje pole inspekcji: stara baza: 0/1/-1 → nowa app: string.
    Używa options z calculator_fields.json dla danego kalkulatora.
    """
    try:
        int_val = int(float(val))
    except (ValueError, TypeError):
        return val  # nieznana wartość — zostaw jak jest

    slug_map = _INSPECTION_MAP.get(slug, {})
    field_map = slug_map.get(key)
    if not field_map:
        # Fallback gdy kalkulator nie ma zdefiniowanych opcji — ogólna mapa
        _FALLBACK = {
            'konstrukcja': {1: 'Brak uszkodzen', 0: 'Uszkodzenia',   -1: 'Nie dotyczy'},
            'automatyka':  {1: 'Brak uszkodzen', 0: 'Uszkodzenia',   -1: 'Nie dotyczy'},
            'sworznie':    {1: 'Prawidlowy',      0: 'Nieprawidlowy', -1: 'Prawidlowy'},
            'ciegna':      {1: 'Brak uszkodzen', 0: 'Uszkodzenia',   -1: 'Nie dotyczy'},
            'eksploatacja':{1: 'Zgodne',          0: 'Niezgodne',     -1: 'Nie dotyczy'},
            'szczelnosc':  {1: 'Szczelny',        0: 'Nieszczelny',   -1: 'Nie dotyczy'},
            'hamulce':     {1: 'Sprawne',         0: 'Niesprawne',    -1: 'Nie dotyczy'},
            'nakretka':    {1: 'Sprawna',         0: 'Niesprawna',    -1: 'Nie dotyczy'},
        }
        field_map = _FALLBACK.get(key)
        if not field_map:
            return val

    return field_map.get(int_val, field_map.get(1))  # domyslnie: OK


def _normalize_numeric(val):
    """
    Konwertuje wartość na liczbę jeśli to możliwe.
    Obsługuje polskie separatory dziesiętne (przecinek): '0,5' → 0.5
    Zwraca None dla wartości niekonwertowalnych (np. '-').
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return val
    s = str(val).strip()
    if not s or s == '-' or s.upper() == 'NULL':
        return None
    normalized = s.replace(',', '.')
    try:
        if '.' in normalized:
            return float(normalized)
        return int(normalized)
    except ValueError:
        return val  # nie jest liczbą — zwróć oryginał


def _wrap_value(key: str, val, slug: str, row: dict = None) -> object:
    """Opakowuje wartość numeryczną w {value, unit} jeśli potrzeba, lub konwertuje select/inspekcje."""
    if key in INSPECTION_FIELDS:
        return _convert_inspection(key, val, slug)
    if key in BINARY_TAK_NIE:
        # 0/'0' → 'Nie', cokolwiek innego nie-zerowego → 'Tak'
        try:
            return 'Tak' if int(float(val)) != 0 else 'Nie'
        except (ValueError, TypeError):
            return val  # juz jako tekst (np. 'Tak'/'Nie') — zostaw
    if key == 'tryb_pracy' and slug in MECH_SLUGS:
        return MECH_TRYB_PRACY_MAP.get(str(val), val)
    if key == 'czas_cykle' and slug in MECH_SLUGS and row is not None:
        jednostka = str(row.get(JEDNOSTKA_KEY) or 's').strip() or 's'
        if val is None or val == '':
            return val
        return {'value': _normalize_numeric(val) or val, 'unit': jednostka}
    # Normalizuj przecinkowe separatory dziesiętne dla pól numerycznych
    if key in MASS_KEYS | YEAR_KEYS | CYCLE_KEYS | {
        'zakres_godzin_1', 'zakres_godzin_2', 'zakres_godzin_3',
        'zakres_godzin_4', 'zakres_godzin_5', 'zakres_godzin_6',
        'procent_jazda', 'procent_podnosnik', 'ilosc_moto', 'max_moto_prod',
        'lata_pracy', 'ilosc_cykli', 'cykle_zmiana', 'dni_robocze',
        'h_max', 'v_pod', 'v_jaz', 'h_pod', 'L_b_max', 's_sz', 'v_prz',
        'licznik_pracy', 'ostatni_licznik', 'ldr', 'hdr',
        'ostatni_resurs', 'ostatni_resurs_mech_pod', 'ostatni_resurs_mech_jaz',
        'ostatni_resurs_mech_prz', 'ostatni_resurs_mech_mas',
    }:
        val = _normalize_numeric(val)
    if val is None or val == '':
        return val
    if key in MASS_KEYS:
        return {'value': val, 'unit': 'kg'}
    if key in YEAR_KEYS:
        return {'value': val, 'unit': 'lata'}
    if key in CYCLE_KEYS and slug != 'dzwig':
        return {'value': val, 'unit': 'cykl'}
    return val


def _split_row(row: dict, slug: str) -> tuple[dict, dict]:
    """Dzieli wiersz DB na (input_data, output_data)."""
    extra_output = DZWIG_EXTRA_OUTPUT if slug == 'dzwig' else set()
    all_output = OUTPUT_KEYS | extra_output

    input_data  = {}
    output_data = {}

    # Stary 'resurs' to tekst wiadomości — przepisz jako resurs_message
    if 'resurs' in row and isinstance(row.get('resurs'), str):
        output_data['resurs_message'] = row['resurs']

    for key, val in row.items():
        if key in METADATA_KEYS:
            continue
        if key == 'resurs':
            continue  # już obsłużone wyżej jako resurs_message
        if key == JEDNOSTKA_KEY:
            continue  # scalane z czas_cykle w _wrap_value
        # Zmień nazwę pola jeśli istnieje w mapie
        key = FIELD_RENAMES.get(key, key)
        if key in all_output:
            output_data[key] = val
        else:
            input_data[key] = _wrap_value(key, val, slug, row)

    return input_data, output_data


def migrate_calculators(calcs_data: dict, username_map: dict[str, User],
                        dry_run: bool, stdout) -> None:
    """Tworzy CalculatorResult dla każdej tabeli w calcs_data."""

    # Wczytaj wszystkie definicje kalkulatorów do słownika
    defs = {d.slug: d for d in CalculatorDefinition.objects.all()}
    if not defs:
        stdout.write("  [WARN] Brak definicji kalkulatorów w DB. Uruchom: python manage.py seed_data")
        return

    total_created = total_skipped = total_errors = 0

    for table_name, rows in sorted(calcs_data.items()):
        slug = table_name.replace('_table', '')
        calc_def = defs.get(slug)
        if not calc_def:
            stdout.write(f"  [SKIP] brak definicji dla slug={slug!r} ({len(rows)} wierszy)")
            total_skipped += len(rows)
            continue

        created = skipped = errors = 0

        for row in rows:
            old_username = row.get('username') or ''
            user = username_map.get(old_username)
            if not user:
                # Spróbuj znaleźć po emailu (czasem username = email)
                if '@' in old_username:
                    user = User.objects.filter(email=old_username.lower()).first()
            if not user:
                skipped += 1
                continue

            # Data obliczenia
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

            # Oblicz wyniki nową logiką; jeśli się nie uda — użyj starych wyników z SQL
            try:
                calc_instance = CalculatorFactory.get_calculator(slug, input_data)
                output_data = decimals_to_float(calc_instance.calculate())
            except (DRFValidationError, Exception) as e:
                if old_output_data:
                    stdout.write(f"  [WARN-CALC] {slug} row={row.get('id')}: {e} — używam starych wyników")
                    output_data = old_output_data
                else:
                    stdout.write(f"  [ERR-CALC] {slug} row={row.get('id')}: {e}")
                    errors += 1
                    continue

            if dry_run:
                stdout.write(
                    f"  [DRY] {slug} | user={user.email} | "
                    f"nr={input_data.get('nr_fabryczny', '?')} | "
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
                stdout.write(f"  [ERR] {slug} row={row.get('id')}: {e}")
                errors += 1

        stdout.write(
            f"  {slug:35s} => {created:4d} importowanych, "
            f"{skipped:3d} pominieto (brak usera), {errors:2d} bledow"
        )
        total_created += created
        total_skipped += skipped
        total_errors  += errors

    stdout.write(
        f"\nWyniki kalkulatorów: {total_created} importowanych, "
        f"{total_skipped} pominiętych, {total_errors} błędów."
    )


# ===========================================================================
# KOMENDA
# ===========================================================================

class Command(BaseCommand):
    help = "Migruje dane z legacy PHP (members.sql + calculators.sql) do Django"

    def add_arguments(self, parser):
        parser.add_argument(
            '--members-sql', type=str, default=str(DEFAULT_MEMBERS_SQL),
            help=f'Ścieżka do members.sql (domyślnie: {DEFAULT_MEMBERS_SQL})'
        )
        parser.add_argument(
            '--calcs-sql', type=str, default=str(DEFAULT_CALCS_SQL),
            help=f'Ścieżka do u685896714_calculators.sql (domyślnie: {DEFAULT_CALCS_SQL})'
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Podgląd co zostałoby zaimportowane — bez zapisu do DB'
        )
        parser.add_argument(
            '--skip-users', action='store_true',
            help='Pomiń import użytkowników (tylko wyniki kalkulatorów)'
        )
        parser.add_argument(
            '--skip-calcs', action='store_true',
            help='Pomiń import wyników kalkulatorów (tylko użytkownicy)'
        )

    def handle(self, *args, **options):
        dry_run      = options['dry_run']
        members_path = Path(options['members_sql'])
        calcs_path   = Path(options['calcs_sql'])

        if dry_run:
            self.stdout.write(self.style.WARNING("=== TRYB DRY RUN — żadne dane nie zostaną zapisane ==="))

        # ── Użytkownicy ──────────────────────────────────────────────────────
        username_map = {}

        if not options['skip_users']:
            if not members_path.exists():
                self.stderr.write(self.style.ERROR(f"Nie znaleziono: {members_path}"))
                return

            self.stdout.write(f"\n--- IMPORT UZYTKOWNIKOW ({members_path.name}) ---")
            members_sql = members_path.read_text(encoding='utf-8', errors='replace')
            members_data = parse_sql_inserts(members_sql)

            if 'members' not in members_data:
                self.stderr.write("Nie znaleziono tabeli 'members' w pliku SQL.")
                return

            username_map = migrate_users(members_data['members'], dry_run, self.stdout)
        else:
            # Wczytaj istniejących użytkowników do mapy username→User
            # (na podstawie pola first_name jako heurystyki)
            self.stdout.write("Pomijam import użytkowników — ładuję istniejących...")
            if members_path.exists():
                members_sql = members_path.read_text(encoding='utf-8', errors='replace')
                members_data = parse_sql_inserts(members_sql)
                for row in members_data.get('members', []):
                    old_username = row.get('username', '') or ''
                    email = (row.get('email') or '').strip().lower()
                    if not email or '@' not in email:
                        if old_username and old_username.isdigit():
                            email = f"{old_username}@nip.pl"
                        else:
                            continue
                    user = User.objects.filter(email=email).first()
                    if user:
                        username_map[old_username] = user

        # ── Wyniki kalkulatorów ───────────────────────────────────────────────
        if not options['skip_calcs']:
            if not calcs_path.exists():
                self.stderr.write(self.style.ERROR(f"Nie znaleziono: {calcs_path}"))
                return

            self.stdout.write(f"\n--- IMPORT WYNIKOW KALKULATOROW ({calcs_path.name}) ---")
            calcs_sql  = calcs_path.read_text(encoding='utf-8', errors='replace')
            calcs_data = parse_sql_inserts(calcs_sql)
            migrate_calculators(calcs_data, username_map, dry_run, self.stdout)

        self.stdout.write(self.style.SUCCESS("\nMigracja zakończona."))
        if not dry_run and not options['skip_users']:
            self.stdout.write(self.style.WARNING(
                "\nUWAGA: Aby użytkownicy mogli logować się starymi hasłami, dodaj do settings.py:\n"
                "PASSWORD_HASHERS = [\n"
                "    'django.contrib.auth.hashers.PBKDF2PasswordHasher',\n"
                "    'django.contrib.auth.hashers.BCryptPasswordHasher',\n"
                "]\n"
                "oraz zainstaluj: pip install bcrypt"
            ))
