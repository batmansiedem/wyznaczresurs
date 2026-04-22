from decimal import Decimal
from django.core.exceptions import ValidationError
from .utils import convert_unit
from datetime import date, timedelta
from abc import ABC, abstractmethod

# Helper function (defined here as it's used by DzwignikCalculator and was not in Get-Content output)
def calculate_wsp_kdr(ilosc_cykli, q_max, q_vals, c_vals):
    if q_max == 0:
        return Decimal(0)
    
    k_d_components_sum = Decimal(0)
    total_c = sum(c_vals)
    
    if total_c == 0:
        return Decimal(0)

    for i in range(len(q_vals)):
        q_i = q_vals[i]
        c_i = c_vals[i]
        if c_i != 0:
            k_d_components_sum += (c_i / Decimal(100)) * (q_i / q_max) ** 3
            
    return k_d_components_sum # This is a simplification; adjust as per actual formula if more details are known


# Mapowanie wartości tekstowych na numeryczne
_YES_NO_MAP = {'Tak': Decimal(1), 'Nie': Decimal(0), 'tak': Decimal(1), 'nie': Decimal(0)}

# Stringi oznaczające problem z komponentem (pola select stanu komponentów)
_PROBLEM_STRINGS = frozenset({
    'Uszkodzenia', 'Niezgodne', 'Nieszczelny', 'Niesprawna', 'Niesprawne',
    'Nieprawidłowy', 'Niezgodne z instrukcją',
    'uszkodzenia', 'niezgodne', 'nieszczelny', 'niesprawna', 'niesprawne',
    'nieprawidłowy', 'niezgodne z instrukcją'
})

# Współczynnik niepewności rejestracji — wersja standardowa (żurawie, suwnicy, wciągarki itp.)
_FX_STANDARD = {
    'Rejestrowanie przyrządami': Decimal('1.0'),
    'Rejestrowanie w dzienniku, łącznie ze stosowaniem licznika': Decimal('1.0'),
    'Rejestrowanie na podstawie procesu technologicznego': Decimal('1.1'),
    'Rejestrowanie na podstawie informacji o produkcji': Decimal('1.2'),
    'Informacja o warunkach eksploatacji jest niekompletna': Decimal('1.3'),
    'Brak informacji o historii urządzenia': Decimal('1.5'),
}

# Współczynnik niepewności rejestracji — wersja rozszerzona (żuraw przeł., podest, układnica itp.)
_FX_EXTENDED = {
    'Rejestrowanie przyrządami': Decimal('1.0'),
    'Rejestrowanie w dzienniku, łącznie ze stosowaniem licznika': Decimal('1.0'),
    'Rejestrowanie na podstawie procesu technologicznego': Decimal('1.2'),
    'Rejestrowanie na podstawie informacji o produkcji': Decimal('1.4'),
    'Informacja o warunkach eksploatacji jest niekompletna': Decimal('1.5'),
    'Brak informacji o historii urządzenia': Decimal('1.8'),
}

# Komunikaty o stanie komponentów (wspólne dla większości urządzeń)
_COMPONENT_MESSAGES = {
    'konstrukcja': 'Ze względu na stan konstrukcji, zaleca się niezwłoczne zaprzestanie eksploatacji oraz przeprowadzenie badań nieniszczących i/lub pomiarów w celu ustalenia zakresu naprawy. Naprawę należy przeprowadzić w zakładzie uprawnionym w myśl przepisów o dozorze technicznym',
    'automatyka': 'Zaleca się niezwłoczne podjęcie działań mających na celu włączenia automatyki sterującej i/lub zabezpieczającej',
    'sworznie': 'Zaleca się niezwłoczną wymianę uszkodzonych sworzni i połączeń skręcanych.',
    'ciegna': 'Ze względu na stan cięgien, zaleca się niezwłoczne zaprzestanie eksploatacji oraz wymianę uszkodzonych elementów.',
    'eksploatacja': 'Zaleca się niezwłoczne dostosowanie warunków eksploatacji do przeznaczenia oraz instrukcji eksploatacji urządzenia.',
    'szczelnosc': 'Niezwłocznie dokonać niezbędnych napraw układu hydraulicznego. W przypadku gdy platforma (z obciążeniem lub bez obciążenia) opada więcej niż 100mm zaleca się zaprzestać eksploatacji i dokonać niezbędnych napraw.',
    'hamulce': 'Niezwłocznie dokonać niezbędnych napraw. W przypadku gdy platforma (z obciążeniem lub bez obciążenia) opada więcej niż 100mm zaleca się zaprzestać eksploatacji i dokonać niezbędnych napraw.',
    'nakretka': 'Zaleca się niezwłoczne doprowadzić do zgodności z dokumentacją techniczną.',
}

# Macierz współczynników LDR (5x5) używana przez PodestRuchomy, WozekSpecjalizowany, ZurawPrzeladunkowy
_LDR_COEFFS = [
    Decimal('0.6'), Decimal('0.7'), Decimal('0.85'), Decimal('0.95'), Decimal('1'),
    Decimal('0.5'), Decimal('0.6'), Decimal('0.7'), Decimal('0.85'), Decimal('0.95'),
    Decimal('0.4'), Decimal('0.5'), Decimal('0.6'), Decimal('0.75'), Decimal('0.85'),
    Decimal('0.3'), Decimal('0.4'), Decimal('0.5'), Decimal('0.6'), Decimal('0.75'),
    Decimal('0.2'), Decimal('0.35'), Decimal('0.45'), Decimal('0.55'), Decimal('0.65'),
]

# Macierz U_WSK (zdolność cyklowa) dla żurawi/suwnic wg stanu obciążenia Q1-Q4 i grupy GNP A1-A8
_U_WSK_MATRIX = {
    'Q1-lekki':         {'A1': 6.3e4, 'A2': 1.25e5, 'A3': 2.5e5,  'A4': 5e5,    'A5': 1e6,   'A6': 2e6,   'A7': 4e6, 'A8': 4e6},
    'Q2-przeciętny':    {'A1': 3.2e4, 'A2': 6.3e4,  'A3': 1.25e5, 'A4': 2.5e5,  'A5': 5e5,   'A6': 1e6,   'A7': 2e6, 'A8': 4e6},
    'Q3-ciężki':        {'A1': 1.6e4, 'A2': 3.2e4,  'A3': 6.3e4,  'A4': 1.25e5, 'A5': 2.5e5, 'A6': 5e5,   'A7': 2e6, 'A8': 4e6},
    'Q4-bardzo ciężki': {'A1': 1.6e4, 'A2': 1.6e4,  'A3': 3.2e4,  'A4': 6.3e4,  'A5': 1.25e5,'A6': 2.5e5, 'A7': 5e5, 'A8': 1e6},
}

# Bazowe współczynniki klasy widma obciążeń S0-S7 (bez 'nieznana' — default per kalkulator)
_SS_FACTOR_BASE = {'S02': 0.002, 'S01': 0.004, 'S0': 0.008, 'S1': 0.016, 'S2': 0.032, 'S3': 0.063, 'S4': 0.125, 'S5': 0.25, 'S6': 0.5, 'S7': 1}

# Tabela progów U_DOW → klasa GNP A1-A8 (żuraw, ponowny resurs)
_GNP_U_DOW_THRESHOLDS = {
    'Q1-lekki':         [(6.4e4, 'A1'), (1.25e5, 'A2'), (2.5e5, 'A3'), (5e5, 'A4'), (1e6, 'A5'), (2e6, 'A6'), (4e6, 'A7')],
    'Q2-przeciętny':    [(3.2e4, 'A1'), (6.4e4, 'A2'), (1.25e5, 'A3'), (2.5e5, 'A4'), (5e5, 'A5'), (1e6, 'A6'), (2e6, 'A7')],
    'Q3-ciężki':        [(1.6e4, 'A1'), (3.2e4, 'A2'), (6.4e4, 'A3'), (1.25e5, 'A4'), (2.5e5, 'A5'), (5e5, 'A6'), (1e6, 'A7')],
    'Q4-bardzo ciężki': [(1.6e4, 'A2'), (3.2e4, 'A3'), (6.4e4, 'A4'), (1.25e5, 'A5'), (2.5e5, 'A6'), (5e5, 'A7')],
}

# Tabela (max_cykli, max_czasu) dla WozekJezdniowy wg napędu i planu serwisowego
_WOZEK_MAX_TABLE = {
    'spalinowy': {
        'plan serwisowy zgodny z wymogami instrukcji ekploatacji':                    (500000, 50000),
        'rozszerzony plan serwisowy przekraczający wymogi instrukcji ekploatacji':    (600000, 50000),
    },
    'elektryczny': {
        'plan serwisowy zgodny z wymogami instrukcji ekploatacji':                    (250000, 40000),
        'rozszerzony plan serwisowy przekraczający wymogi instrukcji ekploatacji':    (350000, 50000),
    },
    'elektryczny prowadzony': {
        'plan serwisowy zgodny z wymogami instrukcji ekploatacji':                    (250000, 35000),
        'rozszerzony plan serwisowy przekraczający wymogi instrukcji ekploatacji':    (350000, 40000),
    },
    'hydrauliczny': {
        'plan serwisowy zgodny z wymogami instrukcji ekploatacji':                    (250000, 50000),
        'rozszerzony plan serwisowy przekraczający wymogi instrukcji ekploatacji':    (400000, 60000),
    },
    'hybrydowy': {
        'plan serwisowy zgodny z wymogami instrukcji ekploatacji':                    (250000, 50000),
        'rozszerzony plan serwisowy przekraczający wymogi instrukcji ekploatacji':    (400000, 60000),
    },
}

# Współczynniki konwersji do jednostek bazowych kalkulatora:
# masa → tony (t), czas → lata, długość → metry (m), prędkość → m/min
_UNIT_CONVERSION = {
    # masa — baza: tony (t)
    'kg':    Decimal('0.001'),    # 1 kg = 0.001 t
    't':     Decimal('1.0'),
    'ton':   Decimal('1.0'),      # alias (z migracji 0003)
    # czas — baza: lata
    'h':     Decimal('0.000114155'),   # 1 h ≈ 1/8766 roku
    'hour':  Decimal('0.000114155'),   # alias (z migracji 0003)
    'mth':   Decimal('1.0'),           # motogodziny — wartość surowa (bez konwersji)
    'lata':  Decimal('1.0'),
    'miesiące': Decimal('0.08333333'), # 1 miesiąc = 1/12 roku
    'year':  Decimal('1.0'),      # alias (z migracji 0003)
    'day':   Decimal('0.00273973'),    # 1 dzień = 1/365 roku
    # długość — baza: m
    'cm':    Decimal('0.01'),
    'mm':    Decimal('0.001'),
    'm':     Decimal('1.0'),
    # prędkość — baza: m/min
    'm/s':   Decimal('60.0'),
    'm/min': Decimal('1.0'),
    'm/h':   Decimal('0.01666667'),   # 1 m/h = 1/60 m/min
    # bezjednostkowe
    'cycle': Decimal('1.0'),
    'cycle_per_shift': Decimal('1.0'),
}


# Utility to safely get Decimal values from input_data, handling units
def get_val_from_input(input_data, field_name, default_value=0):
    raw = input_data.get(field_name)
    unit = None
    if isinstance(raw, dict):
        unit = raw.get('unit')
        raw = raw.get('value')
    if raw is None or raw == '':
        return Decimal(default_value)
    # Obsługa "Tak"/"Nie" → 1/0
    if isinstance(raw, str) and raw in _YES_NO_MAP:
        return _YES_NO_MAP[raw]
    try:
        value = Decimal(raw)
    except Exception:
        return Decimal(default_value)
    # Konwersja jednostek do bazy kalkulatora
    if unit and unit in _UNIT_CONVERSION:
        value = value * _UNIT_CONVERSION[unit]
    return value


class BaseCalculator(ABC):
    """
    Abstract Base Class for all device calculators.
    Enforces a common interface for calculation.
    """
    slug = None # To be defined by subclasses

    def __init__(self, input_data):
        self.input_data = input_data
        self.output_data = {}

    @abstractmethod
    def calculate(self):
        """
        Performs the specific calculation for the device.
        Must return a dictionary of results.
        """
        pass

    def _get_val(self, field_name, default_value=0):
        """Helper to get and convert values from input_data."""
        return get_val_from_input(self.input_data, field_name, default_value)
    
    def _get_kg_val(self, field_name):
        """Pobiera wartość pola masowego zawsze w kg (obsługuje unit_options kg/t)."""
        raw = self.input_data.get(field_name)
        if isinstance(raw, dict):
            val = Decimal(str(raw.get('value') or 0))
            return val * 1000 if raw.get('unit') == 't' else val
        return Decimal(str(raw or 0))

    def get_kss(self):
        """Zwraca współczynnik kss (0.5 jeśli wybrano resurs po przeglądzie specjalnym, inaczej 1.0)."""
        spec = self.input_data.get('spec')
        if spec == 'Tak':
            return Decimal('0.5')
        return Decimal('1.0')

    def _calculate_wsp_kdr(self, ilosc_cykli):
        """Oblicza współczynnik widma obciążeń na podstawie q_max, q_1..q_5, c_1..c_5."""
        q_max = self._get_kg_val('q_max')   # zawsze w kg
        q_vals = [self._get_kg_val(f'q_{i}') for i in range(1, 6)]  # zawsze w kg (jak q_max)
        c_vals = [self._get_val(f'c_{i}') for i in range(1, 6)]
        return calculate_wsp_kdr(ilosc_cykli, q_max, q_vals, c_vals)

    def _get_str(self, field_name, default_value=''):
        """Helper to get string values from input_data (obsługuje też dict z value)."""
        raw = self.input_data.get(field_name, default_value)
        if isinstance(raw, dict):
            raw = raw.get('value', default_value)
        return str(raw) if raw is not None else default_value

    def _apply_technical_state_logic(self, component_fields, resurs_message, resurs_wykorzystanie):
        """
        Applies the logic: if any technical checklist field contains a problem string,
        force resurs to 100% and update the message.
        """
        has_technical_problems = False
        resurs_wykorzystanie_dec = Decimal(str(resurs_wykorzystanie))
        
        for field in component_fields:
            if self._get_str(field) in _PROBLEM_STRINGS:
                if not has_technical_problems:
                    resurs_message = "Resurs został osiągnięty ze względu na stan techniczny urządzenia. Zaleca się wykonanie przeglądu specjalnego."
                    resurs_wykorzystanie_dec = Decimal('100.00')
                    has_technical_problems = True
                resurs_message += f" {_COMPONENT_MESSAGES.get(field, '')}"
        
        return resurs_message.strip(), resurs_wykorzystanie_dec, has_technical_problems

    def _extract_and_process_common_inputs(self):
        """Extracts and processes common inputs for resurs calculations."""
        ponowny_resurs_str = self._get_str('ponowny_resurs', 'Nie')
        ponowny_resurs = 1 if ponowny_resurs_str == 'Tak' else 0
        return {
            'lata_pracy': self._get_val('lata_pracy'),
            'ilosc_cykli': self._get_val('ilosc_cykli'),
            'ponowny_resurs': ponowny_resurs,
            'ostatni_resurs': self._get_val('ostatni_resurs') if ponowny_resurs else Decimal(0),
            'sposob_rejestracji': self._get_str('sposob_rejestracji'),
        }

    def _get_kss(self):
        """Zwraca współczynnik kss (0.5 po badaniu specjalnym, 1.0 przed)."""
        return Decimal('0.5') if self._get_val('spec') == 1 else Decimal('1.0')

    @staticmethod
    def _get_stan_obciazenia(wsp_kdr):
        """Zwraca klasę stanu obciążenia Q1-Q4 na podstawie współczynnika widma."""
        if wsp_kdr <= Decimal('0.125'): return 'Q1-lekki'
        if wsp_kdr <= Decimal('0.25'): return 'Q2-przeciętny'
        if wsp_kdr <= Decimal('0.5'): return 'Q3-ciężki'
        return 'Q4-bardzo ciężki'

    def _calculate_resurs_prognosis(self, U_WSK, F_X, ilosc_cykli, lata_pracy, ponowny_resurs, ostatni_resurs):
        """Calculates resurs utilization and prognosis."""
        ilosc_cykli_rok = (ilosc_cykli * F_X) / lata_pracy if lata_pracy > 0 else Decimal(0)

        if U_WSK <= 0:
            raise ValidationError("Nie można obliczyć resursu — U<sub>WSK</sub> wynosi 0. Sprawdź dane wejściowe.")

        resurs_wykorzystanie = round(((ilosc_cykli * F_X) / U_WSK) * 100, 2)
        if ponowny_resurs == 1:
            resurs_wykorzystanie += ostatni_resurs

        resurs_prognoza_dni = 0
        if resurs_wykorzystanie < 100 and ilosc_cykli_rok > 0:
            correction = ostatni_resurs / 100 if ponowny_resurs == 1 else Decimal(0)
            remaining_cycles = U_WSK * (1 - correction) - (ilosc_cykli * F_X)
            resurs_prognoza_dni = min((remaining_cycles / ilosc_cykli_rok) * 365, Decimal(3650)).to_integral_value(rounding='ROUND_FLOOR')
            
        data_prognoza = date.today() + timedelta(days=int(resurs_prognoza_dni))
        
        resurs_message = "Resurs został osiągnięty. Zaleca się wykonanie przeglądu specjalnego." if resurs_wykorzystanie >= 100 else "Resurs nie został osiągnięty."

        return {
            'resurs_wykorzystanie': resurs_wykorzystanie,
            'resurs_message': resurs_message,
            'data_prognoza': data_prognoza.isoformat(),
            'resurs_prognoza_dni': resurs_prognoza_dni,
            'ilosc_cykli_rok': ilosc_cykli_rok,
            'U_WSK': U_WSK,
            'F_X': F_X,
            'ilosc_cykli': ilosc_cykli,
        }


class DzwignikCalculator(BaseCalculator):
    slug = 'dzwignik'

    def calculate(self):
        # Original logic from calculate_dzwignik refactored into a class method
        common_inputs = self._extract_and_process_common_inputs()
        lata_pracy = common_inputs['lata_pracy']
        ilosc_cykli = common_inputs['ilosc_cykli']
        sposob_rejestracji = common_inputs['sposob_rejestracji']
        ponowny_resurs = common_inputs['ponowny_resurs']
        ostatni_resurs = common_inputs['ostatni_resurs']

        typ = self._get_str('typ')
        max_cykle_prod = self._get_val('max_cykle_prod')
        h_max = self._get_val('h_max')

        # --- HDR Calculation ---
        cc_vals = [self._get_val(f'cc_{i}') for i in range(1, 6)]
        h_vals = [self._get_val(f'h_{i}') for i in range(1, 6)]
        cc_sum = sum(cc_vals)
        if cc_sum > 0:
            if abs(cc_sum - Decimal('100')) > Decimal('0.5'):
                raise ValidationError(
                    f"Widmo HDR: suma udziałów czasu musi wynosić 100% (aktualnie {float(cc_sum):.1f}%).")
            for i in range(5):
                if cc_vals[i] > 0 and h_vals[i] <= 0:
                    raise ValidationError(
                        f"Widmo HDR: przy strefie T{i+1} > 0 należy podać wysokość h{i+1}.")
        hdr = Decimal(0)
        if h_max > 0:
            for i in range(5):
                if cc_vals[i] > 0:
                    hdr += (cc_vals[i] * Decimal('0.01')) * (h_vals[i] / h_max) ** 3
        
        # --- WSP_KDR Calculation ---
        wsp_kdr = self._calculate_wsp_kdr(ilosc_cykli)

        F_X = _FX_EXTENDED.get(sposob_rejestracji, Decimal('1.0'))
        
        # --- KSS factor ---
        kss = self._get_kss()

        # --- U_WSK Calculation ---
        U_WSK = Decimal(0)
        if max_cykle_prod > 0:
            U_WSK = max_cykle_prod * kss
        else:
            max_c_map = {"zębatkowy": Decimal(150000), "śrubowy": Decimal(150000), 
                         "tłokowy-hydrauliczny": Decimal(150000), "dźwigniowy": Decimal(150000)}
            max_c = max_c_map.get(typ, Decimal(0))
            if max_c == 0: raise ValidationError("Nieznany typ mechanizmu dźwignika.")
            
            U_WSK = (max_c - Decimal(20000) * wsp_kdr ** 2 + ((Decimal(1) - hdr) * Decimal(8000))) * kss
            U_WSK = U_WSK.to_integral_value(rounding='ROUND_CEILING')

        resurs_prognosis_data = self._calculate_resurs_prognosis(U_WSK, F_X, ilosc_cykli, lata_pracy, ponowny_resurs, ostatni_resurs)

        resurs_message = resurs_prognosis_data['resurs_message']
        resurs_wykorzystanie = resurs_prognosis_data['resurs_wykorzystanie']
        
        # --- Component checks ---
        component_fields = ['konstrukcja', 'automatyka', 'sworznie', 'ciegna', 'eksploatacja', 'szczelnosc', 'hamulce']
        resurs_message, resurs_wykorzystanie, has_technical_problems = self._apply_technical_state_logic(
            component_fields, resurs_message, resurs_wykorzystanie
        )

        self.output_data.update({
            **resurs_prognosis_data,
            'resurs_wykorzystanie': resurs_wykorzystanie,
            'hdr': hdr,
            'wsp_kdr': wsp_kdr,
            'stan_obciazenia': self._get_stan_obciazenia(wsp_kdr),
            'resurs_message': resurs_message,
            'technical_state_reached': has_technical_problems
        })
        return self.output_data

class ZurawCalculator(BaseCalculator):
    slug = 'zuraw'

    def calculate(self):
        common_inputs = self._extract_and_process_common_inputs()
        lata_pracy = common_inputs['lata_pracy']
        ilosc_cykli = common_inputs['ilosc_cykli']
        sposob_rejestracji = common_inputs['sposob_rejestracji']
        ponowny_resurs = common_inputs['ponowny_resurs']
        ostatni_resurs = common_inputs['ostatni_resurs']

        gnp = self._get_str('gnp')
        kss = self._get_kss()

        # Żuraw: Kd uwzględnia masę osprzętu Q_o → Kd = Σ[ci/100 * ((Qi + Q_o) / Qmax)^3]
        q_max = self._get_kg_val('q_max')     # zawsze w kg
        q_o = self._get_kg_val('q_o')         # zawsze w kg
        q_vals = [self._get_kg_val(f'q_{i}') for i in range(1, 6)]  # zawsze w kg
        c_vals = [self._get_val(f'c_{i}') for i in range(1, 6)]
        if q_o > 0:
            q_vals = [q + q_o for q in q_vals]
        wsp_kdr = calculate_wsp_kdr(ilosc_cykli, q_max, q_vals, c_vals)

        stan_obciazenia = self._get_stan_obciazenia(wsp_kdr)

        # --- Opcjonalne przeliczenie GNP na podstawie czasu do kolejnego badania ---
        gnp_check = self._get_str('gnp_check')
        U_DOW = Decimal(0)
        if gnp_check and gnp_check != 'Nie':
            gnp_czas = self._get_val('gnp_czas')
            if lata_pracy > 0:
                U_DOW = (ilosc_cykli / lata_pracy) * (lata_pracy + gnp_czas)
                for threshold, gnp_val in _GNP_U_DOW_THRESHOLDS.get(stan_obciazenia, []):
                    if U_DOW <= threshold:
                        gnp = gnp_val
                        break
                else:
                    gnp = 'A8'

        F_X = _FX_STANDARD.get(sposob_rejestracji, Decimal('1.0'))

        U_WSK = Decimal(_U_WSK_MATRIX.get(stan_obciazenia, {}).get(gnp, 0))
        
        U_WSK *= kss

        resurs_prognosis_data = self._calculate_resurs_prognosis(U_WSK, F_X, ilosc_cykli, lata_pracy, ponowny_resurs, ostatni_resurs)

        resurs_message = resurs_prognosis_data['resurs_message']
        resurs_wykorzystanie = resurs_prognosis_data['resurs_wykorzystanie']

        # --- Component checks ---
        component_fields = ['konstrukcja', 'automatyka', 'sworznie', 'ciegna', 'eksploatacja']
        resurs_message, resurs_wykorzystanie, has_technical_problems = self._apply_technical_state_logic(
            component_fields, resurs_message, resurs_wykorzystanie
        )

        self.output_data.update({
            **resurs_prognosis_data,
            'resurs_wykorzystanie': resurs_wykorzystanie,
            'wsp_kdr': wsp_kdr,
            'stan_obciazenia': stan_obciazenia,
            'resurs_message': resurs_message,
            'technical_state_reached': has_technical_problems,
            'recalculated_gnp': gnp if gnp_check else None,
            'U_DOW': U_DOW,
        })
        return self.output_data

class DzwigCalculator(BaseCalculator):
    slug = 'dzwig'
    def calculate(self):
        common_inputs = self._extract_and_process_common_inputs()
        lata_pracy = common_inputs['lata_pracy']

        rok_budowy = self._get_val('rok_budowy')
        cykle_dzwig = self._get_val('cykle_dzwig')
        pyt_motogodzin_input = self._get_str('pyt_motogodzin')
        licznik_pracy = self._get_val('licznik_pracy')
        dni_robocze = self._get_val('dni_robocze')

        zakres_godzin = sum([self._get_val(f'zakres_godzin_{i}') for i in range(1, 7)])

        if pyt_motogodzin_input == '1':
            licznik_godzin = licznik_pracy
        else:
            licznik_godzin = zakres_godzin * lata_pracy * dni_robocze
            
        # ilosc_cykli
        if cykle_dzwig > 0:
            ilosc_cykli = cykle_dzwig
        else:
            # v_jaz: odczyt z obsługą unit_options [m/s, m/min, m/h], normalizacja do m/s
            v_jaz_raw = self.input_data.get('v_jaz')
            if isinstance(v_jaz_raw, dict):
                v_jaz_val = Decimal(str(v_jaz_raw.get('value') or 0))
                v_jaz_unit = v_jaz_raw.get('unit', 'm/s')
                if v_jaz_unit == 'm/min':
                    v_jaz = v_jaz_val / Decimal('60')
                elif v_jaz_unit == 'm/h':
                    v_jaz = v_jaz_val / Decimal('3600')
                else:  # m/s
                    v_jaz = v_jaz_val
            else:
                v_jaz = Decimal(str(v_jaz_raw or 0))  # dane sprzed unit_options: przyjmowane jako m/s

            h_pod = self._get_val('h_pod')
            przystanki = self._get_val('przystanki')
            budynek = self._get_str('budynek')
            operator = self._get_str('operator')
            przeznaczenie = self._get_str('przeznaczenie')
            liczba_dzwigow = self._get_val('liczba_dzwigow')

            # Wzór: (60 * v_m_s * 0.5) * L_h * 0.5 / h_m (jak w PHP)
            ilosc_cykli = (((Decimal('60') * v_jaz * Decimal('0.5')) * licznik_godzin * Decimal('0.5')) / h_pod)
            ilosc_cykli *= (1 + 1 / (przystanki + 1))
            
            k_bud_map = {"budowa": Decimal('0.95'), "magazyn": Decimal('0.85'), "budynek mieszkalny": Decimal('1.0'), "budynek firmowy": Decimal('0.75'), "budynek administracji publicznej": Decimal('0.6'), "budynek użyteczności publicznej": Decimal('0.55'), "pojazd": Decimal('0.15')}
            ilosc_cykli *= k_bud_map.get(budynek, Decimal('1.0'))
            
            k_op_map = {"bez prawa jazdy w kabinie": Decimal('0.45'), "jazda z operatorem": Decimal('0.5'), "jazda bez operatora": Decimal('1.0')}
            ilosc_cykli *= k_op_map.get(operator, Decimal('1.0'))
            
            k_prz_map = {"dźwig osobowy": Decimal('1.0'), "dźwig towarowy": Decimal('0.5'), "dźwig osobowo-towarowy": Decimal('0.75'), "transport osób niepełnosprawnych": Decimal('0.75')}
            ilosc_cykli *= k_prz_map.get(przeznaczenie, Decimal('1.0'))
            
            if liczba_dzwigow > 0:
                ilosc_cykli /= liczba_dzwigow
            ilosc_cykli = ilosc_cykli.to_integral_value(rounding='ROUND_FLOOR')

        # Resurs calculation
        wiek_dzwigu = date.today().year - int(rok_budowy)
        wsp_kdr = self._calculate_wsp_kdr(ilosc_cykli)

        resurs = Decimal(0)
        if wiek_dzwigu <= 5: resurs = 3 * wiek_dzwigu * wsp_kdr
        elif 5 < wiek_dzwigu <= 10: resurs = (5 * wiek_dzwigu - 10)
        elif 10 < wiek_dzwigu <= 15: resurs = (4 * wiek_dzwigu)
        elif 15 < wiek_dzwigu <= 20: resurs = (3 * wiek_dzwigu + 15)
        elif 20 < wiek_dzwigu <= 25: resurs = (2 * wiek_dzwigu + 35)
        else: resurs = Decimal(90)

        # Adjustments based on lata_pracy (PHP L166-L172)
        if wiek_dzwigu > 25:
            if lata_pracy <= 5: resurs -= 40
            elif 5 < lata_pracy <= 10: resurs -= 30
            elif 10 < lata_pracy <= 15: resurs -= 20
        elif 15 < wiek_dzwigu <= 25:
            if lata_pracy <= 5: resurs -= 45
            elif 5 < lata_pracy <= 10: resurs -= 35
            elif 10 < lata_pracy <= 15: resurs -= 25

        # Adjustment for daily operating hours (PHP L184)
        ilosc_motogodzin_dzien = licznik_godzin / (lata_pracy * dni_robocze) if lata_pracy > 0 and dni_robocze > 0 else Decimal(0)
        resurs = resurs * ((Decimal('1')/Decimal('120')) * Decimal(str(ilosc_motogodzin_dzien)) + Decimal('0.8'))

        # Min caps for resurs based on wiek_dzwigu (PHP L187-L192)
        if wiek_dzwigu <= 5: resurs = min(resurs, Decimal(15))
        elif 5 < wiek_dzwigu <= 10: resurs = min(resurs, Decimal(40))
        elif 10 < wiek_dzwigu <= 15: resurs = min(resurs, Decimal(60))
        elif 15 < wiek_dzwigu <= 20: resurs = min(resurs, Decimal(75))
        elif 20 < wiek_dzwigu <= 25: resurs = min(resurs, Decimal(85))
        else: resurs = min(resurs, Decimal(90))

        # Component checks - resurs additions (PHP L194-L215)
        component_resurs_add = {            'liny_nosne': 3, 'wciagarka': 3, 'konstrukcja_nosna': 3, 'mocowanie_lin': 3,
            'ogranicznik_predkosci': 3, 'chwytacze_kabiny': 3, 'kola_kabiny': 3,
            'kola_przeciwwagi': 3, 'prowadnice_kabiny': 3, 'prowadnice_przeciwwagi': 3,
            'zderzak_kabiny': 3, 'zderzak_przeciwwagi': 3, 'automatyka': 3, 'drzwi': 3,
            'silownik': 3, 'zawor_blokowy': 3, 'zawor_zwrotny': 3, 'przewody_hydrauliczne': 3,
            'mocowanie_napedu': 3, 'mechanizm_zebatkowy': 3, 'mechanizm_srubowy': 3,
            'przekladnia': 3
        }
        for field, add_val in component_resurs_add.items():
            state = self._get_val(field)
            if state == 1: # Bez zastrzeżeń
                resurs += Decimal(add_val)
            elif state == 0.5: # Wymagający remontu/wymiany w ciągu 5 lat
                resurs += Decimal(add_val) * Decimal('0.75')
            elif state == 0: # Wymagający remontu/wymiany w ciągu 1-2 lat
                 resurs += Decimal('1.5')

        resurs = round(resurs, 2)

        # Prognoza
        prognoza = Decimal(0)
        component_prognoza_penalty = {
            'liny_nosne': 5, 'wciagarka': 5, 'konstrukcja_nosna': 5, 'mocowanie_lin': 5,
            'ogranicznik_predkosci': 5, 'chwytacze_kabiny': 5, 'kola_kabiny': 5,
            'kola_przeciwwagi': 5, 'prowadnice_kabiny': 5, 'prowadnice_przeciwwagi': 5,
            'zderzak_kabiny': 5, 'zderzak_przeciwwagi': 5, 'automatyka': 5, 'drzwi': 5,
            'silownik': 5, 'zawor_blokowy': 5, 'zawor_zwrotny': 5, 'przewody_hydrauliczne': 5,
            'mocowanie_napedu': 5, 'mechanizm_zebatkowy': 5, 'mechanizm_srubowy': 5,
            'przekladnia': 5
        }
        for field, penalty in component_prognoza_penalty.items():
            state = self._get_val(field)
            if state == 0: # Wymagający remontu/wymiany w ciągu 1-2 lat
                prognoza += Decimal(penalty)
            elif state == 0.5: # Wymagający remontu/wymiany w ciągu 5 lat
                prognoza += (Decimal(penalty) + Decimal('2')) / 2
            elif state == 1: # Bez zastrzeżeń
                prognoza += Decimal('2')

        if prognoza == 0:
            prognoza = Decimal('-0.25') * resurs + Decimal('25')
        prognoza = prognoza.to_integral_value(rounding='ROUND_FLOOR')

        data_prognoza = (date.today() + timedelta(days=int(prognoza * 365))).isoformat()

        zalecenia = "Resurs nie został osiągnięty"
        if resurs >= 100:
            zalecenia = "Resurs został osiągnięty. Zaleca się wykonanie przeglądu specjalnego"
            data_prognoza = date.today().isoformat()

        self.output_data.update({
            'resurs': resurs,
            'resurs_wykorzystanie': resurs,  # alias dla spójności z pozostałymi kalkulatorami
            'ilosc_cykli': ilosc_cykli,
            'wiek_dzwigu': wiek_dzwigu,
            'ilosc_cykli_rok': (ilosc_cykli / lata_pracy).to_integral_value(rounding='ROUND_FLOOR') if lata_pracy > 0 else Decimal(0),
            'ilosc_motogodzin_rok': round(licznik_godzin / lata_pracy, 1) if lata_pracy > 0 else Decimal(0),
            'ilosc_motogodzin_dzien': round(ilosc_motogodzin_dzien, 1),
            'licznik_godzin': round(licznik_godzin, 1),
            'prognoza': prognoza,
            'data_prognoza': data_prognoza,
            'wsp_kdr': wsp_kdr,
            'stan_obciazenia': 'N/A',
            'zalecenia': zalecenia,
        })
        return self.output_data


class GenericDeviceCalculator(BaseCalculator):
    slug = 'generic_device_placeholder' # Use a unique slug not to conflict with views.py mapping

    def calculate(self):
        common_inputs = self._extract_and_process_common_inputs()
        
        # Placeholder logic for generic devices like Suwnica and Wciagarka
        U_WSK = Decimal(80000)
        F_X = Decimal(1.0)

        resurs_prognosis_data = self._calculate_resurs_prognosis(
            U_WSK, F_X, common_inputs['ilosc_cykli'], common_inputs['lata_pracy'], 
            common_inputs['ponowny_resurs'], common_inputs['ostatni_resurs']
        )
        self.output_data.update(resurs_prognosis_data)
        return self.output_data


# --- Placeholder classes for all other identified devices ---
class AutotransporterCalculator(BaseCalculator):
    slug = 'autotransporter'
    def calculate(self):
        common_inputs = self._extract_and_process_common_inputs()
        lata_pracy = common_inputs['lata_pracy']
        ilosc_cykli = common_inputs['ilosc_cykli']
        sposob_rejestracji = common_inputs['sposob_rejestracji']
        ponowny_resurs = common_inputs['ponowny_resurs']
        ostatni_resurs = common_inputs['ostatni_resurs']

        max_cykle_prod = self._get_val('max_cykle_prod')

        # --- WSP_KDR Calculation ---
        wsp_kdr = self._calculate_wsp_kdr(ilosc_cykli)

        F_X = _FX_EXTENDED.get(sposob_rejestracji, Decimal('1.0'))
        
        # --- KSS factor ---
        kss = self.get_kss()

        # --- U_WSK Calculation ---
        if max_cykle_prod > 0:
            U_WSK = max_cykle_prod * kss
        else:
            U_WSK = (-5000 * wsp_kdr + Decimal('25000')) * kss
        U_WSK = U_WSK.to_integral_value(rounding='ROUND_CEILING')

        # --- Stan obciazenia (load state) ---
        stan_obciazenia = self._get_stan_obciazenia(wsp_kdr)
        
        resurs_prognosis_data = self._calculate_resurs_prognosis(U_WSK, F_X, ilosc_cykli, lata_pracy, ponowny_resurs, ostatni_resurs)

        resurs_message = resurs_prognosis_data['resurs_message']
        resurs_wykorzystanie = resurs_prognosis_data['resurs_wykorzystanie']
        # --- Component checks ---
        component_fields = ['konstrukcja', 'automatyka', 'sworznie', 'ciegna', 'eksploatacja', 'szczelnosc', 'nakretka']
        resurs_message, resurs_wykorzystanie, has_technical_problems = self._apply_technical_state_logic(
            component_fields, resurs_message, resurs_wykorzystanie
        )

        self.output_data.update({
            **resurs_prognosis_data,
            'resurs_wykorzystanie': resurs_wykorzystanie,
            'wsp_kdr': wsp_kdr,
            'stan_obciazenia': stan_obciazenia,
            'resurs_message': resurs_message,
            'technical_state_reached': has_technical_problems,
        })
        return self.output_data

class HakowiecCalculator(BaseCalculator):
    slug = 'hakowiec'
    def calculate(self):
        common_inputs = self._extract_and_process_common_inputs()
        lata_pracy = common_inputs['lata_pracy']
        ilosc_cykli = common_inputs['ilosc_cykli']
        sposob_rejestracji = common_inputs['sposob_rejestracji']
        ponowny_resurs = common_inputs['ponowny_resurs']
        ostatni_resurs = common_inputs['ostatni_resurs']

        max_cykle_prod = self._get_val('max_cykle_prod')

        # --- WSP_KDR Calculation ---
        wsp_kdr = self._calculate_wsp_kdr(ilosc_cykli)

        F_X = _FX_EXTENDED.get(sposob_rejestracji, Decimal('1.0'))

        # --- KSS factor ---
        kss = self._get_kss()

        # --- U_WSK Calculation ---
        if max_cykle_prod > 0:
            U_WSK = max_cykle_prod * kss
        else:
            U_WSK = (-2000 * wsp_kdr + 50000) * kss
        U_WSK = U_WSK.to_integral_value(rounding='ROUND_CEILING')

        # --- Stan obciazenia (load state) ---
        stan_obciazenia = self._get_stan_obciazenia(wsp_kdr)
        
        resurs_prognosis_data = self._calculate_resurs_prognosis(U_WSK, F_X, ilosc_cykli, lata_pracy, ponowny_resurs, ostatni_resurs)

        resurs_message = resurs_prognosis_data['resurs_message']
        resurs_wykorzystanie = resurs_prognosis_data['resurs_wykorzystanie']
        # --- Component checks ---
        component_fields = ['konstrukcja', 'automatyka', 'sworznie', 'ciegna', 'eksploatacja', 'szczelnosc']
        resurs_message, resurs_wykorzystanie, has_technical_problems = self._apply_technical_state_logic(
            component_fields, resurs_message, resurs_wykorzystanie
        )

        self.output_data.update({
            **resurs_prognosis_data,
            'resurs_wykorzystanie': resurs_wykorzystanie,
            'wsp_kdr': wsp_kdr,
            'stan_obciazenia': stan_obciazenia,
            'resurs_message': resurs_message,
            'technical_state_reached': has_technical_problems,
        })
        return self.output_data

class TimeBasedCalculator(BaseCalculator):
    """
    Abstract Base Class for time-based device calculators.
    """
    def _calculate_time_based_prognosis(self, T_WSK, czas_uzytkowania_mech, lata_pracy, ponowny_resurs, ostatni_resurs):
        """Calculates time-based resurs utilization and prognosis."""
        
        czas_uzytkowania_mech_rok = czas_uzytkowania_mech / lata_pracy if lata_pracy > 0 else Decimal(0)

        resurs_wykorzystanie = round((czas_uzytkowania_mech / T_WSK) * 100, 2)
        if ponowny_resurs == 1:
            resurs_wykorzystanie += ostatni_resurs

        resurs_prognoza_dni = 0
        if resurs_wykorzystanie < 100 and czas_uzytkowania_mech_rok > 0:
            correction = ostatni_resurs / 100 if ponowny_resurs == 1 else Decimal(0)
            remaining_time = T_WSK * (1 - correction) - czas_uzytkowania_mech
            resurs_prognoza_dni = min((remaining_time / czas_uzytkowania_mech_rok) * 365, Decimal(3650)).to_integral_value(rounding='ROUND_FLOOR')

        data_prognoza = (date.today() + timedelta(days=int(resurs_prognoza_dni))).isoformat()
        resurs_message = "Resurs został osiągnięty. Zaleca się wykonanie przeglądu specjalnego." if resurs_wykorzystanie >= 100 else "Resurs nie został osiągnięty."

        return {
            'resurs_wykorzystanie': resurs_wykorzystanie,
            'resurs_message': resurs_message,
            'data_prognoza': data_prognoza,
            'resurs_prognoza_dni': resurs_prognoza_dni,
            'czas_uzytkowania_mech_rok': czas_uzytkowania_mech_rok,
            'T_WSK': T_WSK,
        }

class MechJazdySuwnicyCalculator(TimeBasedCalculator):
    slug = 'mech_jazdy_suwnicy'
    def calculate(self):
        common_inputs = self._extract_and_process_common_inputs()
        lata_pracy = common_inputs['lata_pracy']
        ilosc_cykli = common_inputs['ilosc_cykli']
        sposob_rejestracji = common_inputs['sposob_rejestracji']
        ponowny_resurs = common_inputs['ponowny_resurs']
        ostatni_resurs = common_inputs['ostatni_resurs']

        kss = self._get_kss()

        wsp_km = self._calculate_wsp_kdr(ilosc_cykli)

        # Klasy obciążenia L1-L4 (norma ISO dla mechanizmów, analogicznie do Q1-Q4)
        if wsp_km <= Decimal('0.125'): stan_obciazenia = 'L1-lekki'
        elif wsp_km <= Decimal('0.25'): stan_obciazenia = 'L2-przeciętny'
        elif wsp_km <= Decimal('0.5'): stan_obciazenia = 'L3-ciężki'
        else: stan_obciazenia = 'L4-bardzo ciężki'
        
        gnp = self._get_str('gnp') # Should be M1-M8

        T_WSK_matrix = {
            'L1-lekki': {'M1': 800, 'M2': 1600, 'M3': 3200, 'M4': 6300, 'M5': 12500, 'M6': 25000, 'M7': 50000, 'M8': 100000},
            'L2-przeciętny': {'M1': 400, 'M2': 800, 'M3': 1600, 'M4': 3200, 'M5': 6300, 'M6': 12500, 'M7': 25000, 'M8': 50000},
            'L3-ciężki': {'M1': 200, 'M2': 400, 'M3': 800, 'M4': 1600, 'M5': 3200, 'M6': 6300, 'M7': 12500, 'M8': 25000},
            'L4-bardzo ciężki': {'M1': 200, 'M2': 200, 'M3': 400, 'M4': 800, 'M5': 1600, 'M6': 3200, 'M7': 6300, 'M8': 12500}
        }
        T_WSK = Decimal(T_WSK_matrix.get(stan_obciazenia, {}).get(gnp, 0))
        if T_WSK <= 0:
            raise ValidationError("Nie można obliczyć resursu — T_WSK = 0. Sprawdź grupę natężenia pracy (GNP M1-M8).")
        T_WSK *= kss

        F_X = _FX_STANDARD.get(sposob_rejestracji, Decimal('1.0'))

        # Kd / stan obciążenia — ostrzeżenie jeśli widmo puste
        if wsp_km == 0:
            self.output_data['warning_kd'] = 'Widmo obciążeń Kd nie zostało wypełnione — przyjęto L1-lekki (może być nieprawidłowe).'

        # Czy podano motogodziny bezpośrednio?
        ilosc_mth_raw = self.input_data.get('ilosc_mth')
        if isinstance(ilosc_mth_raw, dict):
            ilosc_mth = Decimal(str(ilosc_mth_raw.get('value') or 0))
        else:
            ilosc_mth = Decimal(str(ilosc_mth_raw or 0))

        if ilosc_mth > 0:
            # Motogodziny jako bezpośrednie wejście (mth = godziny)
            czas_uzytkowania_mech = ilosc_mth * F_X
        else:
            # Oblicz z cykli × czas cyklu
            czas_cykle_raw = self.input_data.get('czas_cykle')
            if isinstance(czas_cykle_raw, dict):
                czas_cykle = Decimal(str(czas_cykle_raw.get('value') or 0))
                jednostka = czas_cykle_raw.get('unit', 's')
            else:
                czas_cykle = self._get_val('czas_cykle')
                jednostka = self._get_str('jednostka', 's')  # kompatybilność wsteczna

            if jednostka == 's':
                czas_cykle_h = czas_cykle / 3600
            elif jednostka == 'min':
                czas_cykle_h = czas_cykle / 60
            else:  # 'h'
                czas_cykle_h = czas_cykle

            czas_uzytkowania_mech = ilosc_cykli * czas_cykle_h * F_X

        # ostatni_resurs podany jest w mth — przelicz na % zużycia resursu
        if ponowny_resurs == 1 and ostatni_resurs > 0:
            ostatni_resurs = (ostatni_resurs / T_WSK) * 100

        prognosis_data = self._calculate_time_based_prognosis(T_WSK, czas_uzytkowania_mech, lata_pracy, ponowny_resurs, ostatni_resurs)

        self.output_data.update({
            **prognosis_data,
            'wsp_km': wsp_km,
            'stan_obciazenia': stan_obciazenia,
            'F_X': F_X,
            'czas_uzytkowania_mech': czas_uzytkowania_mech
        })
        return self.output_data

class MechJazdyWciagarkiCalculator(MechJazdySuwnicyCalculator):
    slug = 'mech_jazdy_wciagarki'

class MechJazdyWciagnikaCalculator(MechJazdySuwnicyCalculator):
    slug = 'mech_jazdy_wciagnika'

class MechJazdyZurawiaCalculator(MechJazdySuwnicyCalculator):
    slug = 'mech_jazdy_zurawia'

class MechPodnoszeniaCalculator(MechJazdySuwnicyCalculator):
    slug = 'mech_podnoszenia'

class MechZmianyObrotuCalculator(MechJazdySuwnicyCalculator):
    slug = 'mech_zmiany_obrotu'

class MechZmianyWysieguCalculator(MechJazdySuwnicyCalculator):
    slug = 'mech_zmiany_wysiegu'

class PodestRuchomyCalculator(BaseCalculator):
    slug = 'podest_ruchomy'

    def _calculate_ldr_type(self, common_inputs, kss):
        """Calculates resurs for LDR-based platform types."""
        ilosc_cykli = common_inputs['ilosc_cykli']
        ponowny_resurs = self._get_val('ponowny_resurs')
        ostatni_resurs = common_inputs['ostatni_resurs']

        s_factor = self._get_str('s_factor', 'nieznana')
        ss_factor = Decimal(str(_SS_FACTOR_BASE.get(s_factor, 0.008)))

        p_vals = [self._get_val(f'p_{i}') for i in range(1, 26)]
        p_sum = sum(p_vals)
        if p_sum > 0 and abs(p_sum - Decimal('100')) > Decimal('0.5'):
            raise ValidationError(
                f"Widmo LDR: suma udziałów p musi wynosić 100% (aktualnie {float(p_sum):.1f}%).")
        ldr = sum((p_vals[i] * Decimal('0.01')) * _LDR_COEFFS[i] ** 3 for i in range(25))

        wsp_kdr = self._calculate_wsp_kdr(ilosc_cykli)

        U_WSK = Decimal(0)
        max_cykle_prod = self._get_val('max_cykle_prod')
        if max_cykle_prod > 0:
            U_WSK = max_cykle_prod
        else:
            if wsp_kdr > 0:
                U_WSK1 = (Decimal('2e6') * ss_factor) / wsp_kdr
                U_WSK = U_WSK1 + Decimal('0.15') * U_WSK1 * (Decimal('1') - ldr)
        
        if ponowny_resurs == 1:
            U_WSK *= (Decimal('1') - ostatni_resurs * Decimal('0.01'))
            
        U_WSK = U_WSK.to_integral_value(rounding='ROUND_CEILING')
        
        return U_WSK, {'ldr': ldr, 'wsp_kdr': wsp_kdr}

    def _calculate_hdr_type(self, common_inputs, kss):
        """Calculates resurs for HDR-based platform types."""
        ilosc_cykli = common_inputs['ilosc_cykli']
        ponowny_resurs = self._get_val('ponowny_resurs')
        ostatni_resurs = common_inputs['ostatni_resurs']

        s_factor = self._get_str('s_factor', 'nieznana')
        ss_factor = Decimal(str(_SS_FACTOR_BASE.get(s_factor, 0.008)))

        h_max = self._get_val('h_max')
        cc_vals = [self._get_val(f'cc_{i}') for i in range(1, 6)]
        h_vals = [self._get_val(f'h_{i}') for i in range(1, 6)]
        cc_sum = sum(cc_vals)
        if cc_sum > 0:
            if abs(cc_sum - Decimal('100')) > Decimal('0.5'):
                raise ValidationError(
                    f"Widmo HDR: suma udziałów czasu musi wynosić 100% (aktualnie {float(cc_sum):.1f}%).")
            for i in range(5):
                if cc_vals[i] > 0 and h_vals[i] <= 0:
                    raise ValidationError(
                        f"Widmo HDR: przy strefie T{i+1} > 0 należy podać wysokość h{i+1}.")

        hdr = Decimal(0)
        if h_max > 0 and cc_sum > 0:
            hdr = sum(((cc_vals[i] / 100) * (h_vals[i] / h_max) ** 3) for i in range(5))

        wsp_kdr = self._calculate_wsp_kdr(ilosc_cykli)

        U_WSK = Decimal(0)
        max_cykle_prod = self._get_val('max_cykle_prod')
        if max_cykle_prod > 0:
            U_WSK = max_cykle_prod
        else:
            if wsp_kdr > 0:
                U_WSK1 = (Decimal('2e6') * ss_factor) / wsp_kdr
                U_WSK = U_WSK1 + Decimal('0.15') * U_WSK1 * (Decimal('1') - hdr)
        
        if ponowny_resurs == 1:
            U_WSK *= (Decimal('1') - ostatni_resurs * Decimal('0.01'))

        U_WSK = U_WSK.to_integral_value(rounding='ROUND_CEILING')

        return U_WSK, {'hdr': hdr, 'wsp_kdr': wsp_kdr}

    def _calculate_bumar_type(self, common_inputs, kss):
        """Calculates resurs for BUMAR type platforms."""
        max_moto_prod = self._get_val('max_moto_prod')
        # For this type, U_WSK is simply the max motor hours provided by manufacturer.
        return max_moto_prod, {}

    def calculate(self):
        common_inputs = self._extract_and_process_common_inputs()
        typ = self._get_str('typ')
        kss = self._get_kss()

        U_WSK = Decimal(0)
        extra_data = {}

        if typ == 'składany na pojeździe BUMAR':
            U_WSK, extra_data = self._calculate_bumar_type(common_inputs, kss)
            # BUMAR: U_WSK to motogodziny wg producenta — kss nie skaluje U_WSK
        elif typ in ['nożycowy samobieżny', 'masztowy samobieżny', 'masztowy stacjonarny']:
            U_WSK, extra_data = self._calculate_hdr_type(common_inputs, kss)
            U_WSK *= kss
        else: # Default to LDR type for all others
            U_WSK, extra_data = self._calculate_ldr_type(common_inputs, kss)
            U_WSK *= kss

        # Common final calculation
        sposob_rejestracji = common_inputs['sposob_rejestracji']
        F_X = _FX_EXTENDED.get(sposob_rejestracji, Decimal('1.0'))

        # Prognosis logic varies based on type
        if typ == 'składany na pojeździe BUMAR':
            moto_podest_ruchomy = self._get_val('moto_podest_ruchomy')
            procent_bumar = self._get_val('procent_bumar', 100)
            effective_usage = moto_podest_ruchomy * (procent_bumar / 100)
            
            ostatni_licznik = self._get_val('ostatni_licznik') if common_inputs['ponowny_resurs'] == 1 else Decimal(0)
            effective_delta = effective_usage - (ostatni_licznik * (procent_bumar / 100)) if common_inputs['ponowny_resurs'] == 1 else effective_usage
            
            resurs_wykorzystanie = round((effective_delta / U_WSK) * 100, 2) if U_WSK > 0 else Decimal(0)
            if common_inputs['ponowny_resurs'] == 1:
                resurs_wykorzystanie += common_inputs['ostatni_resurs']
            
            usage_per_year = effective_usage / common_inputs['lata_pracy'] if common_inputs['lata_pracy'] > 0 else 0
            
            resurs_prognoza_dni = 0
            if resurs_wykorzystanie < 100 and usage_per_year > 0:
                remaining_usage = U_WSK * (Decimal('1') - (common_inputs['ostatni_resurs'] / 100 if common_inputs['ponowny_resurs'] == 1 else 0)) - effective_delta
                resurs_prognoza_dni = min((remaining_usage / (usage_per_year * (procent_bumar / 100))) * 365, Decimal(3650)) if procent_bumar > 0 else 0
                resurs_prognoza_dni = Decimal(str(resurs_prognoza_dni)).to_integral_value(rounding='ROUND_FLOOR')

            prognosis_data = {
                'resurs_wykorzystanie': resurs_wykorzystanie,
                'resurs_prognoza_dni': resurs_prognoza_dni,
                'data_prognoza': (date.today() + timedelta(days=int(resurs_prognoza_dni))).isoformat(),
                'T_WSK': {'value': U_WSK, 'unit': 'mth'},
                'moto_efektywne': round(effective_usage, 2),
                'moto_rok': round(usage_per_year, 2) if usage_per_year else None,
                'ilosc_cykli_rok': (common_inputs['ilosc_cykli'] * F_X / common_inputs['lata_pracy']).to_integral_value(rounding='ROUND_CEILING') if common_inputs['lata_pracy'] > 0 else Decimal(0),
            }
        else:
            prognosis_data = self._calculate_resurs_prognosis(
                U_WSK, F_X, common_inputs['ilosc_cykli'], common_inputs['lata_pracy'], 
                common_inputs['ponowny_resurs'], common_inputs['ostatni_resurs']
            )

        resurs_message = prognosis_data.get('resurs_message', "Resurs został osiągnięty. Zaleca się wykonanie przeglądu specjalnego." if prognosis_data['resurs_wykorzystanie'] >= 100 else "Resurs nie został osiągnięty.")
        resurs_wykorzystanie = prognosis_data['resurs_wykorzystanie']
        
        # --- Component checks ---
        component_fields = ['konstrukcja', 'automatyka', 'sworznie', 'ciegna', 'eksploatacja', 'szczelnosc', 'hamulce']
        resurs_message, resurs_wykorzystanie, has_technical_problems = self._apply_technical_state_logic(
            component_fields, resurs_message, resurs_wykorzystanie
        )

        if 'wsp_kdr' in extra_data:
            extra_data['stan_obciazenia'] = self._get_stan_obciazenia(extra_data['wsp_kdr'])
        self.output_data.update({
            **prognosis_data,
            **extra_data,
            'resurs_wykorzystanie': resurs_wykorzystanie,
            'resurs_message': resurs_message,
            'technical_state_reached': has_technical_problems,
        })
        return self.output_data

class PodestZaladowczyCalculator(BaseCalculator):
    slug = 'podest_zaladowczy'
    def calculate(self):
        common_inputs = self._extract_and_process_common_inputs()
        lata_pracy = common_inputs['lata_pracy']
        ilosc_cykli = common_inputs['ilosc_cykli']
        sposob_rejestracji = common_inputs['sposob_rejestracji']
        ponowny_resurs = common_inputs['ponowny_resurs']
        ostatni_resurs = common_inputs['ostatni_resurs']

        wsp_kdr = self._calculate_wsp_kdr(ilosc_cykli)
        kss = self._get_kss()

        max_cykle_prod = self._get_val('max_cykle_prod')
        if max_cykle_prod > 0:
            U_WSK = max_cykle_prod * kss
        else:
            U_WSK = (-2000 * wsp_kdr + Decimal('65000')) * kss
        U_WSK = U_WSK.to_integral_value(rounding='ROUND_CEILING')

        F_X = _FX_EXTENDED.get(sposob_rejestracji, Decimal('1.0'))
        
        prognosis_data = self._calculate_resurs_prognosis(U_WSK, F_X, ilosc_cykli, lata_pracy, ponowny_resurs, ostatni_resurs)
        
        resurs_message = prognosis_data['resurs_message']
        resurs_wykorzystanie = prognosis_data['resurs_wykorzystanie']
        # --- Component checks ---
        component_fields = ['konstrukcja', 'automatyka', 'sworznie', 'ciegna', 'eksploatacja', 'szczelnosc', 'hamulce']
        resurs_message, resurs_wykorzystanie, has_technical_problems = self._apply_technical_state_logic(
            component_fields, resurs_message, resurs_wykorzystanie
        )

        self.output_data.update({
            **prognosis_data,
            'resurs_wykorzystanie': resurs_wykorzystanie,
            'wsp_kdr': wsp_kdr,
            'stan_obciazenia': self._get_stan_obciazenia(wsp_kdr),
            'resurs_message': resurs_message,
            'technical_state_reached': has_technical_problems,
        })
        return self.output_data

class PodnosnikSamochodowyCalculator(BaseCalculator):
    slug = 'podnosnik_samochodowy'
    def calculate(self):
        common_inputs = self._extract_and_process_common_inputs()
        lata_pracy = common_inputs['lata_pracy']
        ilosc_cykli = common_inputs['ilosc_cykli']
        sposob_rejestracji = common_inputs['sposob_rejestracji']
        ponowny_resurs = self._get_val('ponowny_resurs')
        ostatni_resurs = common_inputs['ostatni_resurs']

        wsp_kdr = self._calculate_wsp_kdr(ilosc_cykli)
        
        max_cykle_prod = self._get_val('max_cykle_prod')
        if max_cykle_prod > 0:
            U_WSK = max_cykle_prod
        else:
            U_WSK = -5000 * wsp_kdr + Decimal('15000')
        U_WSK = U_WSK.to_integral_value(rounding='ROUND_CEILING')

        F_X = _FX_EXTENDED.get(sposob_rejestracji, Decimal('1.0'))
        
        prognosis_data = self._calculate_resurs_prognosis(U_WSK, F_X, ilosc_cykli, lata_pracy, ponowny_resurs, ostatni_resurs)
        
        resurs_message = prognosis_data['resurs_message']
        resurs_wykorzystanie = prognosis_data['resurs_wykorzystanie']
        # --- Component checks ---
        component_fields = ['konstrukcja', 'automatyka', 'sworznie', 'ciegna', 'eksploatacja', 'szczelnosc', 'nakretka']
        resurs_message, resurs_wykorzystanie, has_technical_problems = self._apply_technical_state_logic(
            component_fields, resurs_message, resurs_wykorzystanie
        )

        self.output_data.update({
            **prognosis_data,
            'resurs_wykorzystanie': resurs_wykorzystanie,
            'wsp_kdr': wsp_kdr,
            'stan_obciazenia': self._get_stan_obciazenia(wsp_kdr),
            'resurs_message': resurs_message,
            'technical_state_reached': has_technical_problems,
        })
        return self.output_data

class SuwnicaCalculator(BaseCalculator):
    slug = 'suwnica'
    def calculate(self):
        common_inputs = self._extract_and_process_common_inputs()
        lata_pracy = common_inputs['lata_pracy']
        ilosc_cykli = common_inputs['ilosc_cykli']
        sposob_rejestracji = common_inputs['sposob_rejestracji']
        ponowny_resurs = common_inputs['ponowny_resurs']
        ostatni_resurs = common_inputs['ostatni_resurs']

        gnp = self._get_str('gnp')
        kss = self._get_kss()

        wsp_kdr = self._calculate_wsp_kdr(ilosc_cykli)
        stan_obciazenia = self._get_stan_obciazenia(wsp_kdr)

        F_X = _FX_STANDARD.get(sposob_rejestracji, Decimal('1.0'))

        U_WSK = Decimal(_U_WSK_MATRIX.get(stan_obciazenia, {}).get(gnp, 0))
        U_WSK *= kss

        resurs_prognosis_data = self._calculate_resurs_prognosis(U_WSK, F_X, ilosc_cykli, lata_pracy, ponowny_resurs, ostatni_resurs)

        resurs_message = resurs_prognosis_data['resurs_message']
        resurs_wykorzystanie = resurs_prognosis_data['resurs_wykorzystanie']
        # --- Component checks ---
        component_fields = ['konstrukcja', 'automatyka', 'sworznie', 'ciegna', 'eksploatacja']
        resurs_message, resurs_wykorzystanie, has_technical_problems = self._apply_technical_state_logic(
            component_fields, resurs_message, resurs_wykorzystanie
        )

        self.output_data.update({
            **resurs_prognosis_data,
            'resurs_wykorzystanie': resurs_wykorzystanie,
            'wsp_kdr': wsp_kdr,
            'stan_obciazenia': stan_obciazenia,
            'resurs_message': resurs_message,
            'technical_state_reached': has_technical_problems,
        })
        return self.output_data

class UkladnicaMagazynowaCalculator(BaseCalculator):
# ... (rest of UkladnicaMagazynowaCalculator)

    slug = 'ukladnica_magazynowa'

    def _calculate_pod_mechanism(self, lata_pracy, F_X, max_t, EDS_factor):
        v_pod = self._get_val('v_pod')
        h_max = self._get_val('h_max')
        k_pod_2 = Decimal('1.2')
        k_v_pod = ((v_pod ** 2) / 50000) - (v_pod / 250) + 1 if v_pod <= 100 else Decimal('0.7')
        t_max_pod = (Decimal('0.62') * max_t * k_v_pod * EDS_factor).to_integral_value(rounding='ROUND_FLOOR')

        licznik_pracy_pod = self._get_val('licznik_pracy_pod')
        if licznik_pracy_pod > 0:
            t_sum_pod = licznik_pracy_pod
        else:
            t_sum_pod = (self._get_val('ilosc_cykli') * F_X * k_pod_2 * (h_max / v_pod) / 60).to_integral_value(rounding='ROUND_FLOOR')

        resurs_wyk_pod = round((t_sum_pod / t_max_pod) * 100, 2) if t_max_pod > 0 else Decimal(0)
        
        resurs_prog_pod = Decimal(0)
        if resurs_wyk_pod < 100 and t_sum_pod > 0 and lata_pracy > 0:
            resurs_prog_pod = min((((t_max_pod - t_sum_pod) / (t_sum_pod / lata_pracy)) * 365), Decimal(3650))
        
        data_prog_pod = (date.today() + timedelta(days=int(resurs_prog_pod.to_integral_value(rounding='ROUND_FLOOR')))).isoformat()

        return {'t_max_pod': t_max_pod, 't_sum_pod': t_sum_pod, 'resurs_wyk_pod': resurs_wyk_pod, 'resurs_prog_pod': resurs_prog_pod, 'data_prog_pod': data_prog_pod}

    def _calculate_jaz_mechanism(self, lata_pracy, F_X, max_t, EDS_factor):
        v_jaz = self._get_val('v_jaz')
        s_sz = self._get_val('s_sz')
        k_jaz_2 = Decimal('1.2')
        k_v_jaz = ((v_jaz ** 2) / 72000) - (v_jaz / 300) + 1 if v_jaz <= 180 else Decimal('0.7')
        t_max_jaz = (k_v_jaz * max_t * Decimal('0.6') * EDS_factor).to_integral_value(rounding='ROUND_FLOOR')

        licznik_pracy_jaz = self._get_val('licznik_pracy_jaz')
        if licznik_pracy_jaz > 0:
            t_sum_jaz = licznik_pracy_jaz
        else:
            t_sum_jaz = (self._get_val('ilosc_cykli') * k_jaz_2 * F_X * (s_sz / v_jaz) / 60).to_integral_value(rounding='ROUND_FLOOR')
            
        resurs_wyk_jaz = round((t_sum_jaz / t_max_jaz) * 100, 2) if t_max_jaz > 0 else Decimal(0)

        resurs_prog_jaz = Decimal(0)
        if resurs_wyk_jaz < 100 and t_sum_jaz > 0 and lata_pracy > 0:
            resurs_prog_jaz = min((((t_max_jaz - t_sum_jaz) / (t_sum_jaz / lata_pracy)) * 365), Decimal(3650))
            
        data_prog_jaz = (date.today() + timedelta(days=int(resurs_prog_jaz.to_integral_value(rounding='ROUND_FLOOR')))).isoformat()

        return {'t_max_jaz': t_max_jaz, 't_sum_jaz': t_sum_jaz, 'resurs_wyk_jaz': resurs_wyk_jaz, 'resurs_prog_jaz': resurs_prog_jaz, 'data_prog_jaz': data_prog_jaz}

    def _calculate_prz_mechanism(self, lata_pracy, F_X, max_t):
        v_prz = self._get_val('v_prz')
        s_max = Decimal('1.2') * Decimal('1.8')
        k_s_2 = Decimal('1.2')
        t_max_prz = (max_t * Decimal('0.12')).to_integral_value(rounding='ROUND_FLOOR')

        licznik_pracy_prz = self._get_val('licznik_pracy_prz')
        if licznik_pracy_prz > 0:
            t_sum_prz = licznik_pracy_prz
        elif v_prz > 0:
            t_sum_prz = (self._get_val('ilosc_cykli') * k_s_2 * F_X * (s_max / v_prz) / 60).to_integral_value(rounding='ROUND_FLOOR')
        else:
            t_sum_prz = Decimal(0)

        resurs_wyk_prz = round((t_sum_prz / t_max_prz) * 100, 2) if t_max_prz > 0 else Decimal(0)
        
        resurs_prog_prz = Decimal(0)
        if resurs_wyk_prz < 100 and t_sum_prz > 0 and lata_pracy > 0:
            resurs_prog_prz = min((((t_max_prz - t_sum_prz) / (t_sum_prz / lata_pracy)) * 365), Decimal(3650))

        data_prog_prz = (date.today() + timedelta(days=int(resurs_prog_prz.to_integral_value(rounding='ROUND_FLOOR')))).isoformat()
        
        return {'t_max_prz': t_max_prz, 't_sum_prz': t_sum_prz, 'resurs_wyk_prz': resurs_wyk_prz, 'resurs_prog_prz': resurs_prog_prz, 'data_prog_prz': data_prog_prz}

    def calculate(self):
        common_inputs = self._extract_and_process_common_inputs()
        
        wsp_kdr = self._calculate_wsp_kdr(common_inputs['ilosc_cykli'])
        
        EDS_factor = (Decimal('0.1') * wsp_kdr ** 2) - (Decimal('0.2') * wsp_kdr) + 1
        k_ster = Decimal('1.0') if self._get_str('ster') == 'Układnica magazynowa sterowana autmatycznie' else Decimal('0.95')
        
        U_WSK = (Decimal('1500000') * EDS_factor * k_ster).to_integral_value(rounding='ROUND_CEILING')

        F_X = _FX_EXTENDED.get(common_inputs['sposob_rejestracji'], Decimal('1.0'))

        overall_prognosis = self._calculate_resurs_prognosis(
            U_WSK, F_X, common_inputs['ilosc_cykli'], common_inputs['lata_pracy'],
            common_inputs['ponowny_resurs'], common_inputs['ostatni_resurs']
        )
        
        max_t = Decimal('60000')
        pod_results = self._calculate_pod_mechanism(common_inputs['lata_pracy'], F_X, max_t, EDS_factor)
        jaz_results = self._calculate_jaz_mechanism(common_inputs['lata_pracy'], F_X, max_t, EDS_factor)
        prz_results = self._calculate_prz_mechanism(common_inputs['lata_pracy'], F_X, max_t)

        resurs_message = overall_prognosis['resurs_message']
        resurs_wykorzystanie = overall_prognosis['resurs_wykorzystanie']
        # --- Component checks ---
        component_fields = ['konstrukcja', 'automatyka', 'sworznie', 'ciegna', 'eksploatacja']
        resurs_message, resurs_wykorzystanie, has_technical_problems = self._apply_technical_state_logic(
            component_fields, resurs_message, resurs_wykorzystanie
        )

        self.output_data.update({
            **overall_prognosis,
            **pod_results,
            **jaz_results,
            **prz_results,
            'resurs_wykorzystanie': resurs_wykorzystanie,
            'wsp_kdr': wsp_kdr,
            'stan_obciazenia': self._get_stan_obciazenia(wsp_kdr),
            'EDS_factor': EDS_factor,
            'resurs_message': resurs_message,
            'technical_state_reached': has_technical_problems,
        })
        return self.output_data

class WciagarkaCalculator(SuwnicaCalculator):
    slug = 'wciagarka'

class WciagnikCalculator(SuwnicaCalculator):
    slug = 'wciagnik'

class WindaDekarskaCalculator(BaseCalculator):
    slug = 'winda_dekarska'
    def calculate(self):
        common_inputs = self._extract_and_process_common_inputs()
        lata_pracy = common_inputs['lata_pracy']
        ilosc_cykli = common_inputs['ilosc_cykli']
        sposob_rejestracji = common_inputs['sposob_rejestracji']
        ponowny_resurs = common_inputs['ponowny_resurs']
        ostatni_resurs = common_inputs['ostatni_resurs']
        ostatni_resurs_mech_pod = self._get_val('ostatni_resurs_mech_pod') if ponowny_resurs == 1 else Decimal(0)
        ostatni_licznik = self._get_val('ostatni_licznik') if ponowny_resurs == 1 else Decimal(0)
        
        # --- Coefficients from a_1, a_2, a_3 ---
        a_1 = self._get_val('a_1')
        a_2 = self._get_val('a_2')
        a_3 = self._get_val('a_3')
        
        k_k = (a_1 * Decimal('0.01') * 1) + (a_2 * Decimal('0.01') * Decimal('1.1')) + (a_3 * Decimal('0.01') * Decimal('1.2'))
        k_w = (a_1 * Decimal('0.01') * Decimal('1.2')) + (a_2 * Decimal('0.01') * Decimal('1.1')) + (a_3 * Decimal('0.01') * 1)

        F_X = _FX_EXTENDED.get(sposob_rejestracji, Decimal('1.0'))

        # --- Part 1: Hoisting Mechanism (Time-based) ---
        t_max = Decimal('3000') # Base value for both "elektryczny" and "hydrauliczny"
        t_max_pod = t_max * k_w
        
        h_max = self._get_val('h_max')
        # v_pod as dict (unit_options: m/s / m/min / m/h) → convert to m/h
        v_pod_raw = self.input_data.get('v_pod')
        if isinstance(v_pod_raw, dict):
            v_pod_val = Decimal(str(v_pod_raw.get('value') or 0))
            v_pod_unit = v_pod_raw.get('unit', 'm/min')
            if v_pod_unit == 'm/s':
                v_pod_j = v_pod_val * 3600
            elif v_pod_unit == 'm/min':
                v_pod_j = v_pod_val * 60
            else:  # m/h
                v_pod_j = v_pod_val
        else:
            # stare dane: plain number zakładamy m/min (domyślna jednostka)
            v_pod_j = Decimal(str(v_pod_raw or 0)) * 60
            
        ilosc_cykli_delta = ilosc_cykli - ostatni_licznik if ponowny_resurs == 1 else ilosc_cykli
        t_sum_pod = (h_max / v_pod_j) * F_X * ilosc_cykli_delta if v_pod_j > 0 else Decimal(0)
        t_sum_pod = t_sum_pod.to_integral_value(rounding='ROUND_FLOOR')

        resurs_wyk_pod = round((t_sum_pod / t_max_pod) * 100, 2) if t_max_pod > 0 else Decimal(0)
        if ponowny_resurs == 1:
            resurs_wyk_pod += ostatni_resurs_mech_pod
        
        resurs_prog_pod = Decimal(0)
        if resurs_wyk_pod < 100 and t_sum_pod > 0 and lata_pracy > 0:
            resurs_prog_pod = min(((t_max_pod - t_sum_pod) / (t_sum_pod / lata_pracy)) * 365, Decimal(3650))
        data_prog_pod = (date.today() + timedelta(days=int(resurs_prog_pod.to_integral_value(rounding='ROUND_FLOOR')))).isoformat()

        # --- Part 2: Structure (Cycle-based) ---
        max_cykle = self._get_val('max_cykle')
        max_c = max_cykle if max_cykle > 0 else Decimal('120000')
        U_WSK = max_c * k_k
        
        prognosis_data = self._calculate_resurs_prognosis(U_WSK, F_X, ilosc_cykli, lata_pracy, ponowny_resurs, ostatni_resurs)

        resurs_message = prognosis_data['resurs_message']
        resurs_wykorzystanie = prognosis_data['resurs_wykorzystanie']
        
        # --- Component checks ---
        component_fields = ['konstrukcja', 'automatyka', 'sworznie', 'eksploatacja', 'szczelnosc', 'hamulce']
        resurs_message, resurs_wykorzystanie, has_technical_problems = self._apply_technical_state_logic(
            component_fields, resurs_message, resurs_wykorzystanie
        )

        self.output_data.update({
            **prognosis_data,
            'resurs_wykorzystanie': resurs_wykorzystanie,
            'resurs_message': resurs_message,
            'technical_state_reached': has_technical_problems,
            'k_k': k_k,
            'k_w': k_w,
            't_max_pod': t_max_pod,
            't_sum_pod': t_sum_pod,
            'resurs_wyk_pod': resurs_wyk_pod,
            'resurs_prog_pod': int(resurs_prog_pod),
            'data_prog_pod': data_prog_pod,
            'ilosc_cykli_rok': (ilosc_cykli * F_X / lata_pracy).to_integral_value(rounding='ROUND_CEILING') if lata_pracy > 0 else Decimal(0),
        })
        return self.output_data
        return self.output_data

class WozekJezdniowyCalculator(BaseCalculator):
    slug = 'wozek_jezdniowy'

    def _calculate_wsp_kdr(self, ilosc_cykli):
        """Nadpisanie Kd dla wózka: uwzględnia masę osprzętu Q_o (zgodnie z PHP)."""
        q_max = self._get_kg_val('q_max')
        q_o = self._get_kg_val('q_o')
        q_vals = [self._get_kg_val(f'q_{i}') for i in range(1, 6)]  # zawsze w kg
        c_vals = [self._get_val(f'c_{i}') for i in range(1, 6)]
        if q_o > 0:
            q_vals = [q + q_o for q in q_vals]
        return calculate_wsp_kdr(ilosc_cykli, q_max, q_vals, c_vals)

    def calculate(self):
        common_inputs = self._extract_and_process_common_inputs()
        lata_pracy = common_inputs['lata_pracy']
        ilosc_cykli = common_inputs['ilosc_cykli']
        sposob_rejestracji = common_inputs['sposob_rejestracji']
        ponowny_resurs = common_inputs['ponowny_resurs']
        ostatni_resurs = common_inputs['ostatni_resurs']

        naped = self._get_str('naped')
        serwis = self._get_str('serwis')
        operator = self._get_str('operator')
        temperatura = self._get_str('temperatura')
        srodowisko = self._get_str('srodowisko')
        kss = self.get_kss()

        licznik_pracy = self._get_val('licznik_pracy')
        h_max = self._get_val('h_max')
        v_pod = self._get_val('v_pod')
        powierzchnia = self._get_str('powierzchnia')
        widly_check = self._get_val('widly_check')
        dlugosc_widel = self._get_val('dlugosc_widel')
        alfa = self._get_val('alfa')
        beta = self._get_val('beta')
        q_o = self._get_val('q_o')
        max_czas = self._get_val('max_czas')

        # --- WSP_KDR Calculation ---
        wsp_kdr = self._calculate_wsp_kdr(ilosc_cykli)

        F_X = _FX_EXTENDED.get(sposob_rejestracji, Decimal('1.0'))

        # --- KSS factor is already calculated above

        # --- k_wid factor ---
        k_wid = Decimal('1.0') if widly_check == 1 else Decimal('0.95')

        # --- k_oper factor ---
        k_oper_map = {
            '1 operator': Decimal('1.0'), '2 operatorów': Decimal('0.99'),
            '3 operatorów': Decimal('0.98'), '4 operatorów': Decimal('0.97'),
            '5 i więcej operatorów': Decimal('0.96')
        }
        k_oper = k_oper_map.get(operator, Decimal('1.0'))

        # --- max_c i t_max wg napędu i planu serwisowego ---
        max_c_raw, t_max_raw = _WOZEK_MAX_TABLE.get(naped, {}).get(serwis, (0, 0))
        max_c = Decimal(max_c_raw) * kss
        t_max = Decimal(t_max_raw) * kss
        
        # Współczynnik wsp_kdr na max_c (zgodnie z PHP: wsp_kdr<0.05 → 2.5x; wsp_kdr<0.02 → nadpisane 1x)
        if wsp_kdr < Decimal('0.05') and wsp_kdr >= Decimal('0.02'):
            max_c *= Decimal('2.5')

        if temperatura == "praca w zmiennych temperaturach (praca na zewnątrz, chłodnie)":
            max_c *= Decimal('0.95')
            t_max *= Decimal('0.95')
        
        k_sro = Decimal('1.0')
        if srodowisko == "TAK":
            max_c *= Decimal('0.5')
            t_max *= Decimal('0.5')
            k_sro = Decimal('0.5')
        
        EDS_factor = (Decimal('0.1') * wsp_kdr ** 2) - (Decimal('0.2') * wsp_kdr) + Decimal('1.0')
        U_WSK_overall = max_c * EDS_factor * k_oper * k_wid
        
        stan_obciazenia = self._get_stan_obciazenia(wsp_kdr)
        
        ilosc_cykli_rok = (ilosc_cykli * F_X) / lata_pracy if lata_pracy > 0 else Decimal(0)

        # Overall Resurs and Prognosis
        resurs_prognosis_data_overall = self._calculate_resurs_prognosis(U_WSK_overall, F_X, ilosc_cykli, lata_pracy, ponowny_resurs, ostatni_resurs)
        resurs_message_overall = resurs_prognosis_data_overall['resurs_message']
        resurs_wykorzystanie_overall = resurs_prognosis_data_overall['resurs_wykorzystanie']
        
        # Component checks - for overall resurs
        component_fields = ['konstrukcja', 'automatyka', 'sworznie', 'ciegna', 'eksploatacja']
        resurs_message_overall, resurs_wykorzystanie_overall, has_technical_problems_initial = self._apply_technical_state_logic(
            component_fields, resurs_message_overall, resurs_wykorzystanie_overall
        )

        # --- Calculations for individual mechanisms ---
        # 1. Mech podnoszenia (lifting mechanism)
        k_pod_1 = Decimal('0.62')
        wskaznik_cykle = "mały" if (ilosc_cykli / lata_pracy if lata_pracy > 0 else 0) <= 40000 else "duży"
        k_pod_2 = Decimal('0.10') if wskaznik_cykle == "duży" else Decimal('0')
        k_v_pod = (Decimal('19')/Decimal('20')) + ((v_pod ** 2)/Decimal('98000')) if v_pod <= 70 else Decimal('1')
        k_h_pod = (Decimal('19')/Decimal('20')) + ((h_max ** 2)/Decimal('72000')) if h_max <= 100 else Decimal('1')
        
        t_max_pod = Decimal(0)
        if max_czas > 0:
            t_max_pod = max_czas * k_sro
        else:
            t_max_pod = k_pod_1 * t_max * k_v_pod * k_h_pod * EDS_factor
        t_max_pod = t_max_pod.to_integral_value(rounding='ROUND_FLOOR')

        t_sum_pod = (k_pod_1 + k_pod_2) * (licznik_pracy * F_X) # PHP code uses $licznik_roznica which is $licznik_pracy - $ostatni_licznik. Need $ostatni_licznik
        t_sum_pod = t_sum_pod.to_integral_value(rounding='ROUND_FLOOR')

        resurs_wyk_pod = Decimal(0)
        resurs_prog_pod = Decimal(0)
        data_prog_pod = date.today().isoformat()
        
        if ponowny_resurs == 1:
            ostatni_licznik = self._get_val('ostatni_licznik') # Need to get this from input
            ostatni_resurs_mech_pod = self._get_val('ostatni_resurs_mech_pod') # Need to get this from input
            licznik_roznica = max(Decimal(0), licznik_pracy - ostatni_licznik)
            t_sum_pod = (k_pod_1 + k_pod_2) * (licznik_roznica * F_X)
            t_sum_pod = t_sum_pod.to_integral_value(rounding='ROUND_FLOOR')
            resurs_wyk_pod = ostatni_resurs_mech_pod + (round(((t_sum_pod) / t_max_pod) * 100, 2) if t_max_pod > 0 else Decimal(0))
            if resurs_wyk_pod < 100 and t_sum_pod > 0 and lata_pracy > 0:
                resurs_prog_pod = min((((Decimal('1') - resurs_wyk_pod / Decimal('100')) * (t_max_pod - t_sum_pod) / (t_sum_pod / lata_pracy)) * 365), Decimal(3650))
            resurs_prog_pod = resurs_prog_pod.to_integral_value(rounding='ROUND_FLOOR')
            data_prog_pod = (date.today() + timedelta(days=int(resurs_prog_pod))).isoformat()
        else:
            resurs_wyk_pod = round(((t_sum_pod) / t_max_pod) * 100, 2) if t_max_pod > 0 else Decimal(0)
            if resurs_wyk_pod < 100 and t_sum_pod > 0 and lata_pracy > 0:
                resurs_prog_pod = min((((t_max_pod - t_sum_pod) / (t_sum_pod / lata_pracy)) * 365), Decimal(3650))
            resurs_prog_pod = resurs_prog_pod.to_integral_value(rounding='ROUND_FLOOR')
            data_prog_pod = (date.today() + timedelta(days=int(resurs_prog_pod))).isoformat()

        # 2. Mech jazdy (driving mechanism)
        k_mag_map = {
            'równa, gładka bez ubytków': Decimal('1'),
            'równa chropowata z małą ilością ubytków': Decimal('0.98'),
            'różnorodna z dużą ilością ubytków': Decimal('0.97')
        }
        k_mag = k_mag_map.get(powierzchnia, Decimal('1'))

        k_jaz_1 = Decimal('0.71')
        wskaznik_motogodzin = "mały" if (licznik_pracy / lata_pracy if lata_pracy > 0 else 0) <= 1000 else "duży"
        k_jaz_2 = Decimal('0.10') if wskaznik_motogodzin == "duży" else Decimal('0')

        t_max_jaz = Decimal(0)
        if max_czas > 0:
            t_max_jaz = max_czas * k_sro
        else:
            t_max_jaz = t_max * k_jaz_1 * EDS_factor * k_mag * Decimal('1.2')
        t_max_jaz = t_max_jaz.to_integral_value(rounding='ROUND_FLOOR')
        
        resurs_wyk_jaz = Decimal(0)
        resurs_prog_jaz = Decimal(0)
        data_prog_jaz = date.today().isoformat()

        if ponowny_resurs == 1:
            ostatni_licznik = self._get_val('ostatni_licznik')
            ostatni_resurs_mech_jaz = self._get_val('ostatni_resurs_mech_jaz')
            licznik_roznica = max(Decimal(0), licznik_pracy - ostatni_licznik)
            t_sum_jaz = (k_jaz_1 + k_jaz_2) * (licznik_roznica * F_X)
            t_sum_jaz = t_sum_jaz.to_integral_value(rounding='ROUND_FLOOR')
            resurs_wyk_jaz = ostatni_resurs_mech_jaz + (round(((t_sum_jaz) / t_max_jaz) * 100, 2) if t_max_jaz > 0 else Decimal(0))
            if resurs_wyk_jaz < 100 and t_sum_jaz > 0 and lata_pracy > 0:
                resurs_prog_jaz = min((((Decimal('1') - resurs_wyk_jaz / Decimal('100')) * (t_max_jaz - t_sum_jaz) / (t_sum_jaz / lata_pracy)) * 365), Decimal(3650))
            resurs_prog_jaz = resurs_prog_jaz.to_integral_value(rounding='ROUND_FLOOR')
            data_prog_jaz = (date.today() + timedelta(days=int(resurs_prog_jaz))).isoformat()
        else:
            t_sum_jaz = (k_jaz_1 + k_jaz_2) * (licznik_pracy * F_X)
            t_sum_jaz = t_sum_jaz.to_integral_value(rounding='ROUND_FLOOR')
            resurs_wyk_jaz = round(((t_sum_jaz) / t_max_jaz) * 100, 2) if t_max_jaz > 0 else Decimal(0)
            if resurs_wyk_jaz < 100 and t_sum_jaz > 0 and lata_pracy > 0:
                resurs_prog_jaz = min((((t_max_jaz - t_sum_jaz) / (t_sum_jaz / lata_pracy)) * 365), Decimal(3650))
            resurs_prog_jaz = resurs_prog_jaz.to_integral_value(rounding='ROUND_FLOOR')
            data_prog_jaz = (date.today() + timedelta(days=int(resurs_prog_jaz))).isoformat()

        # 3. Mech przesuwu platformy (platform shifting mechanism)
        k_s_1 = Decimal('0.16')
        t_max_prz = Decimal(0)
        if max_czas > 0:
            t_max_prz = max_czas * k_sro
        else:
            t_max_prz = k_s_1 * t_max * EDS_factor
        t_max_prz = t_max_prz.to_integral_value(rounding='ROUND_FLOOR')

        resurs_wyk_prz = Decimal(0)
        resurs_prog_prz = Decimal(0)
        data_prog_prz = date.today().isoformat()
        
        if ponowny_resurs == 1:
            ostatni_licznik = self._get_val('ostatni_licznik') # Need to get this from input
            ostatni_resurs_mech_prz = self._get_val('ostatni_resurs_mech_prz') # Need to get this from input
            licznik_roznica = max(Decimal(0), licznik_pracy - ostatni_licznik)
            t_sum_prz = licznik_roznica * k_s_1 * F_X
            t_sum_prz = t_sum_prz.to_integral_value(rounding='ROUND_FLOOR')
            resurs_wyk_prz = ostatni_resurs_mech_prz + (round(((t_sum_prz) / t_max_prz) * 100, 2) if t_max_prz > 0 else Decimal(0))
            if resurs_wyk_prz < 100 and t_sum_prz > 0 and lata_pracy > 0:
                resurs_prog_prz = min((((Decimal('1') - resurs_wyk_prz / Decimal('100')) * (t_max_prz - t_sum_prz) / (t_sum_prz / lata_pracy)) * 365), Decimal(3650))
            resurs_prog_prz = resurs_prog_prz.to_integral_value(rounding='ROUND_FLOOR')
            data_prog_prz = (date.today() + timedelta(days=int(resurs_prog_prz))).isoformat()
        else:
            t_sum_prz = licznik_pracy * k_s_1 * F_X
            t_sum_prz = t_sum_prz.to_integral_value(rounding='ROUND_FLOOR')
            resurs_wyk_prz = round(((t_sum_prz) / t_max_prz) * 100, 2) if t_max_prz > 0 else Decimal(0)
            if resurs_wyk_prz < 100 and t_sum_prz > 0 and lata_pracy > 0:
                resurs_prog_prz = min((((t_max_prz - t_sum_prz) / (t_sum_prz / lata_pracy)) * 365), Decimal(3650))
            resurs_prog_prz = resurs_prog_prz.to_integral_value(rounding='ROUND_FLOOR')
            data_prog_prz = (date.today() + timedelta(days=int(resurs_prog_prz))).isoformat()
        
        # 4. Mech odchylenia masztu (mast tilting mechanism)
        k_m_1 = Decimal('0.12')
        t_max_mas = Decimal(0)
        if max_czas > 0:
            t_max_mas = max_czas * k_sro
        else:
            t_max_mas = k_m_1 * t_max * EDS_factor
        t_max_mas = t_max_mas.to_integral_value(rounding='ROUND_FLOOR')

        resurs_wyk_mas = Decimal(0)
        resurs_prog_mas = Decimal(0)
        data_prog_mas = date.today().isoformat()
        
        if ponowny_resurs == 1:
            ostatni_licznik = self._get_val('ostatni_licznik') # Need to get this from input
            ostatni_resurs_mech_mas = self._get_val('ostatni_resurs_mech_mas') # Need to get this from input
            licznik_roznica = max(Decimal(0), licznik_pracy - ostatni_licznik)
            t_sum_mas = k_m_1 * licznik_roznica * F_X
            t_sum_mas = t_sum_mas.to_integral_value(rounding='ROUND_FLOOR')
            resurs_wyk_mas = ostatni_resurs_mech_mas + (round(((t_sum_mas) / t_max_mas) * 100, 2) if t_max_mas > 0 else Decimal(0))
            if resurs_wyk_mas < 100 and t_sum_mas > 0 and lata_pracy > 0:
                resurs_prog_mas = min((((Decimal('1') - resurs_wyk_mas / Decimal('100')) * (t_max_mas - t_sum_mas) / (t_sum_mas / lata_pracy)) * 365), Decimal(3650))
            resurs_prog_mas = resurs_prog_mas.to_integral_value(rounding='ROUND_FLOOR')
            data_prog_mas = (date.today() + timedelta(days=int(resurs_prog_mas))).isoformat()
        else:
            t_sum_mas = k_m_1 * licznik_pracy * F_X
            t_sum_mas = t_sum_mas.to_integral_value(rounding='ROUND_FLOOR')
            resurs_wyk_mas = round(((t_sum_mas) / t_max_mas) * 100, 2) if t_max_mas > 0 else Decimal(0)
            if resurs_wyk_mas < 100 and t_sum_mas > 0 and lata_pracy > 0:
                resurs_prog_mas = min((((t_max_mas - t_sum_mas) / (t_sum_mas / lata_pracy)) * 365), Decimal(3650))
            resurs_prog_mas = resurs_prog_mas.to_integral_value(rounding='ROUND_FLOOR')
            data_prog_mas = (date.today() + timedelta(days=int(resurs_prog_mas))).isoformat()

        # Zerowy condition
        if lata_pracy == 0 and max_czas > 0:
            tryb_pracy_input = self._get_str('tryb_pracy')
            tryb_pracy_liczba = 0
            if tryb_pracy_input == 'jednozmianowy':
                tryb_pracy_liczba = 1
            elif tryb_pracy_input == 'dwuzmianowy':
                tryb_pracy_liczba = 2
            elif tryb_pracy_input == 'trzyzmianowy':
                tryb_pracy_liczba = 3

            ilosc_cykli_zmiana = self._get_val('ilosc_cykli_zmiana')
            ilosc_dni_roboczych = self._get_val('ilosc_dni_roboczych')

            czas_prognoza_stos = max_czas / Decimal('60000')
            U_WSK_overall = (U_WSK_overall * czas_prognoza_stos).to_integral_value(rounding='ROUND_FLOOR')

            denominator = ilosc_cykli_zmiana * ilosc_dni_roboczych * tryb_pracy_liczba
            ilosc_cykli_rok_sym = min((U_WSK_overall / denominator) * 365, Decimal(3650)) if denominator > 0 else Decimal(3650)
            
            resurs_prognoza_overall = ilosc_cykli_rok_sym.to_integral_value(rounding='ROUND_FLOOR')
            data_prognoza_overall = (date.today() + timedelta(days=int(resurs_prognoza_overall))).isoformat()
            
            t_sum_pod, t_sum_jaz, t_sum_prz, t_sum_mas = Decimal(0), Decimal(0), Decimal(0), Decimal(0)
            resurs_wyk_pod, resurs_wyk_jaz, resurs_wyk_prz, resurs_wyk_mas = Decimal(0), Decimal(0), Decimal(0), Decimal(0)
            
            resurs_prog_pod = resurs_prognoza_overall
            resurs_prog_jaz = resurs_prognoza_overall
            resurs_prog_prz = resurs_prognoza_overall
            resurs_prog_mas = resurs_prognoza_overall
            
            data_prog_pod = data_prognoza_overall
            data_prog_jaz = data_prognoza_overall
            data_prog_prz = data_prognoza_overall
            data_prog_mas = data_prognoza_overall
            
            # Since this is a special case, we update the main prognosis data as well
            resurs_prognosis_data_overall['resurs_prognoza_dni'] = resurs_prognoza_overall
            resurs_prognosis_data_overall['data_prognoza'] = data_prognoza_overall

        else:
            # This block is for when lata_pracy > 0, so we just assign the already calculated values
            resurs_prognoza_overall = resurs_prognosis_data_overall['resurs_prognoza_dni']
            data_prognoza_overall = resurs_prognosis_data_overall['data_prognoza']

        # Component checks - for overall resurs
        resurs_message_overall, resurs_wykorzystanie_overall, has_technical_problems = self._apply_technical_state_logic(
            component_fields, resurs_message_overall, resurs_wykorzystanie_overall
        )

        self.output_data.update({
            **resurs_prognosis_data_overall,
            'resurs_wykorzystanie': resurs_wykorzystanie_overall,
            'wsp_kdr': wsp_kdr,
            'stan_obciazenia': stan_obciazenia,
            'resurs_message': resurs_message_overall,
            'technical_state_reached': has_technical_problems or has_technical_problems_initial,
            'k_wid': k_wid,
            'k_oper': k_oper,
            'kss': kss,
            'EDS_factor': EDS_factor,
            't_max_pod': t_max_pod,
            't_sum_pod': t_sum_pod,
            'resurs_wyk_pod': resurs_wyk_pod,
            'resurs_prog_pod': resurs_prog_pod,
            'data_prog_pod': data_prog_pod,
            't_max_jaz': t_max_jaz,
            't_sum_jaz': t_sum_jaz,
            'resurs_wyk_jaz': resurs_wyk_jaz,
            'resurs_prog_jaz': resurs_prog_jaz,
            'data_prog_jaz': data_prog_jaz,
            't_max_prz': t_max_prz,
            't_sum_prz': t_sum_prz,
            'resurs_wyk_prz': resurs_wyk_prz,
            'resurs_prog_prz': resurs_prog_prz,
            'data_prog_prz': data_prog_prz,
            't_max_mas': t_max_mas,
            't_sum_mas': t_sum_mas,
            'resurs_wyk_mas': resurs_wyk_mas,
            'resurs_prog_mas': resurs_prog_mas,
            'data_prog_mas': data_prog_mas,
            'max_c': max_c,
            't_max': t_max,
            'k_sro': k_sro,
            'wskaznik_cykle': wskaznik_cykle,
            'wskaznik_motogodzin': wskaznik_motogodzin,
            'ilosc_cykli_rok': resurs_prognosis_data_overall['ilosc_cykli_rok'],
            'resurs_prognoza': resurs_prognoza_overall,
            'data_prognoza': data_prognoza_overall,
        })
        return self.output_data

class WozekSpecjalizowanyCalculator(BaseCalculator):
    slug = 'wozek_specjalizowany'
    def calculate(self):
        common_inputs = self._extract_and_process_common_inputs()
        lata_pracy = common_inputs['lata_pracy']
        ilosc_cykli = common_inputs['ilosc_cykli']
        sposob_rejestracji = common_inputs['sposob_rejestracji']
        ponowny_resurs = common_inputs['ponowny_resurs']
        ostatni_resurs = common_inputs['ostatni_resurs']
        ostatni_licznik = self._get_val('ostatni_licznik') if ponowny_resurs == 1 else Decimal(0)

        sposob_pracy = self._get_str('sposob_pracy')
        operator = self._get_str('operator')

        F_X = _FX_EXTENDED.get(sposob_rejestracji, Decimal('1.0'))

        p_vals = [self._get_val(f'p_{i}') for i in range(1, 26)]
        p_sum = sum(p_vals)
        if p_sum > 0 and abs(p_sum - Decimal('100')) > Decimal('0.5'):
            raise ValidationError(
                f"Widmo LDR: suma udziałów p musi wynosić 100% (aktualnie {float(p_sum):.1f}%).")
        ldr_coeffs = _LDR_COEFFS
        ldr = sum((p_vals[i] * Decimal('0.01')) * ldr_coeffs[i] ** 3 for i in range(25))

        k_oper_map = {'1 operator': 1, '2 operatorów': 0.99, '3 operatorów': 0.98, '4 operatorów': 0.97, '5 i więcej operatorów': 0.96}
        k_oper = Decimal(str(k_oper_map.get(operator, 1.0)))

        wsp_kdr = self._calculate_wsp_kdr(ilosc_cykli)

        final_data = {}

        if sposob_pracy == "wózek widłowy/ładowarka":
            max_moto_prod = self._get_val('max_moto_prod')
            T_WSK_base = max_moto_prod if max_moto_prod > 0 else Decimal('15000')

            T_WSK1 = Decimal('0.01') * (Decimal('-10') * ldr + Decimal('10')) * T_WSK_base

            T_WSK2 = Decimal(0)
            if wsp_kdr <= Decimal('0.2'): T_WSK2 = Decimal('0.05') * T_WSK_base
            elif wsp_kdr <= Decimal('0.4'): T_WSK2 = Decimal('0.02') * T_WSK_base

            T_WSK = (T_WSK_base + T_WSK1 + T_WSK2) * k_oper
            T_WSK = T_WSK.to_integral_value(rounding='ROUND_CEILING')

            ilosc_moto = self._get_val('ilosc_moto')
            procent_jazda = self._get_val('procent_jazda')

            ilosc_moto_cal = ilosc_moto - (ilosc_moto * Decimal('0.01') * procent_jazda)

            ostatni_moto_cal = ostatni_licznik - (ostatni_licznik * Decimal('0.01') * procent_jazda) if ponowny_resurs == 1 else Decimal(0)
            moto_delta = (ilosc_moto_cal - ostatni_moto_cal) if ponowny_resurs == 1 else ilosc_moto_cal

            resurs_wykorzystanie = round((moto_delta * F_X / T_WSK) * 100, 2) if T_WSK > 0 else 0
            if ponowny_resurs == 1:
                resurs_wykorzystanie += ostatni_resurs

            ilosc_moto_rok = (ilosc_moto_cal * F_X) / lata_pracy if lata_pracy > 0 else 0

            resurs_prognoza = Decimal(0)
            if resurs_wykorzystanie < 100 and ilosc_moto_rok > 0:
                correction = ostatni_resurs / 100 if ponowny_resurs == 1 else Decimal(0)
                remaining_time = T_WSK * (1 - correction) - (moto_delta * F_X)
                resurs_prognoza = min((remaining_time / ilosc_moto_rok) * 365, Decimal(3650))

            data_prognoza = (date.today() + timedelta(days=int(resurs_prognoza.to_integral_value(rounding='ROUND_FLOOR')))).isoformat()
            resurs_msg = 'Resurs został osiągnięty. Zaleca się wykonanie przeglądu specjalnego.' if resurs_wykorzystanie >= 100 else 'Resurs nie został osiągnięty.'

            final_data = {
                'T_WSK': T_WSK, 
                'moto_rok': round(ilosc_moto_rok, 2), 
                'resurs_wykorzystanie': resurs_wykorzystanie, 
                'resurs_prognoza_dni': int(resurs_prognoza), 
                'data_prognoza': data_prognoza, 
                'resurs_message': resurs_msg,
                'ilosc_moto_cal': round(ilosc_moto_cal, 2)
            }

        else: # "podnośnik koszowy/wózek widłowy/ładowarka"
            U_WSK_base = (Decimal('2e6') * Decimal('0.008')) / wsp_kdr if wsp_kdr > 0 else Decimal(0)
            U_WSK1 = Decimal('0.01') * (Decimal('-10') * ldr + Decimal('10')) * U_WSK_base

            procent_podnosnik = self._get_val('procent_podnosnik')
            U_WSK2 = Decimal(0)
            if procent_podnosnik < 15: U_WSK2 = Decimal('0.10') * U_WSK_base
            elif procent_podnosnik < 25: U_WSK2 = Decimal('0.75') * U_WSK_base # Matching PHP
            elif procent_podnosnik < 50: U_WSK2 = Decimal('0.35') * U_WSK_base

            U_WSK = (U_WSK_base + U_WSK1 + U_WSK2) * k_oper
            U_WSK = U_WSK.to_integral_value(rounding='ROUND_CEILING')

            prognosis_data = self._calculate_resurs_prognosis(U_WSK, F_X, ilosc_cykli, lata_pracy, ponowny_resurs, ostatni_resurs)
            final_data = {**prognosis_data}

        # Common component checks
        resurs_message = final_data.get('resurs_message', '')
        resurs_wykorzystanie = final_data.get('resurs_wykorzystanie', 0)
        component_fields = ['konstrukcja', 'automatyka', 'sworznie', 'ciegna', 'eksploatacja', 'szczelnosc']
        resurs_message, resurs_wykorzystanie, has_technical_problems = self._apply_technical_state_logic(
            component_fields, resurs_message, resurs_wykorzystanie
        )
        final_data['resurs_message'] = resurs_message
        final_data['resurs_wykorzystanie'] = resurs_wykorzystanie

        self.output_data.update({
            **final_data,
            'wsp_kdr': wsp_kdr,
            'stan_obciazenia': self._get_stan_obciazenia(wsp_kdr),
            'ldr': ldr,
            'technical_state_reached': has_technical_problems,
            'ilosc_cykli_rok': (ilosc_cykli * F_X / lata_pracy).to_integral_value(rounding='ROUND_CEILING') if lata_pracy > 0 else Decimal(0),
        })
        return self.output_data
class ZurawPrzeladunkowyCalculator(BaseCalculator):
    slug = 'zuraw_przeladunkowy'
    def calculate(self):
        common_inputs = self._extract_and_process_common_inputs()
        lata_pracy = common_inputs['lata_pracy']
        ilosc_cykli = common_inputs['ilosc_cykli']
        sposob_rejestracji = common_inputs['sposob_rejestracji']
        ponowny_resurs = common_inputs['ponowny_resurs']
        ostatni_resurs = common_inputs['ostatni_resurs']

        s_factor = self._get_str('s_factor')

        F_X = _FX_EXTENDED.get(sposob_rejestracji, Decimal('1.0'))

        ss_factor = Decimal(str(_SS_FACTOR_BASE.get(s_factor, 0.002)))

        p_vals = [self._get_val(f'p_{i}') for i in range(1, 26)]
        p_sum = sum(p_vals)
        if p_sum > 0 and abs(p_sum - Decimal('100')) > Decimal('0.5'):
            raise ValidationError(
                f"Widmo LDR: suma udziałów p musi wynosić 100% (aktualnie {float(p_sum):.1f}%).")
        ldr_coeffs = _LDR_COEFFS
        ldr = Decimal(0)
        for i in range(25):
            ldr += (p_vals[i] * Decimal('0.01')) * (ldr_coeffs[i] ** 3)

        max_cykle_prod = self._get_val('max_cykle_prod')
        wsp_kdr = self._calculate_wsp_kdr(ilosc_cykli)

        U_WSK = Decimal(0)
        if max_cykle_prod > 0:
            U_WSK = max_cykle_prod
            if ponowny_resurs == 1:
                U_WSK *= (Decimal('1') - ostatni_resurs * Decimal('0.01'))
        else:
            U_WSK1 = (2 * Decimal('1e6') * ss_factor) / wsp_kdr if wsp_kdr > 0 else Decimal(0)
            U_WSK = U_WSK1 + Decimal('0.15') * U_WSK1 * (Decimal('1') - ldr)
            if ponowny_resurs == 1:
                 U_WSK *= (Decimal('1') - ostatni_resurs * Decimal('0.01'))
        U_WSK = U_WSK.to_integral_value(rounding='ROUND_CEILING')

        kss = self._get_kss()
        U_WSK *= kss

        stan_obciazenia = self._get_stan_obciazenia(wsp_kdr)

        resurs_prognosis_data = self._calculate_resurs_prognosis(U_WSK, F_X, ilosc_cykli, lata_pracy, ponowny_resurs, ostatni_resurs)

        resurs_message = resurs_prognosis_data['resurs_message']
        resurs_wykorzystanie = resurs_prognosis_data['resurs_wykorzystanie']
        # --- Component checks ---
        component_fields = ['konstrukcja', 'automatyka', 'sworznie', 'ciegna', 'eksploatacja', 'szczelnosc', 'hamulce']
        resurs_message, resurs_wykorzystanie, has_technical_problems = self._apply_technical_state_logic(
            component_fields, resurs_message, resurs_wykorzystanie
        )

        self.output_data.update({
            **resurs_prognosis_data,
            'resurs_wykorzystanie': resurs_wykorzystanie,
            'wsp_kdr': wsp_kdr,
            'stan_obciazenia': stan_obciazenia,
            'ldr': ldr,
            'ss_factor': ss_factor,
            'resurs_message': resurs_message,
            'technical_state_reached': has_technical_problems,
        })
        return self.output_data


class CalculatorFactory:
    _calculators = {}

    @classmethod
    def register_calculator(cls, calculator_class):
        if not issubclass(calculator_class, BaseCalculator):
            raise ValueError("Calculator class must inherit from BaseCalculator")
        if not calculator_class.slug:
            raise ValueError("Calculator class must define a 'slug' attribute")
        cls._calculators[calculator_class.slug] = calculator_class

    @classmethod
    def get_calculator(cls, slug, input_data):
        calculator_class = cls._calculators.get(slug)
        if not calculator_class:
            raise ValidationError(f"No calculator registered for slug: {slug}")
        return calculator_class(input_data)

# Register all calculator classes
CalculatorFactory.register_calculator(DzwignikCalculator)
CalculatorFactory.register_calculator(ZurawCalculator)
CalculatorFactory.register_calculator(DzwigCalculator)
CalculatorFactory.register_calculator(GenericDeviceCalculator) 
CalculatorFactory.register_calculator(AutotransporterCalculator)
CalculatorFactory.register_calculator(HakowiecCalculator)
CalculatorFactory.register_calculator(MechJazdySuwnicyCalculator)
CalculatorFactory.register_calculator(MechJazdyWciagarkiCalculator)
CalculatorFactory.register_calculator(MechJazdyWciagnikaCalculator)
CalculatorFactory.register_calculator(MechJazdyZurawiaCalculator)
CalculatorFactory.register_calculator(MechPodnoszeniaCalculator)
CalculatorFactory.register_calculator(MechZmianyObrotuCalculator)
CalculatorFactory.register_calculator(MechZmianyWysieguCalculator)
CalculatorFactory.register_calculator(PodestRuchomyCalculator)
CalculatorFactory.register_calculator(PodestZaladowczyCalculator)
CalculatorFactory.register_calculator(PodnosnikSamochodowyCalculator)
CalculatorFactory.register_calculator(SuwnicaCalculator)
CalculatorFactory.register_calculator(UkladnicaMagazynowaCalculator)
CalculatorFactory.register_calculator(WciagarkaCalculator)
CalculatorFactory.register_calculator(WciagnikCalculator)
CalculatorFactory.register_calculator(WindaDekarskaCalculator)
CalculatorFactory.register_calculator(WozekJezdniowyCalculator)
CalculatorFactory.register_calculator(WozekSpecjalizowanyCalculator)
CalculatorFactory.register_calculator(ZurawPrzeladunkowyCalculator)
