from django.test import TestCase
from decimal import Decimal
from .calculation_logic import ZurawCalculator, calculate_wsp_kdr

class CalculationLogicTest(TestCase):
    def test_calculate_wsp_kdr(self):
        # q_max = 10, q_1 = 5 (50%), c_1 = 100%
        # Kd = (100/100) * (5/10)**3 = 0.5**3 = 0.125
        kd = calculate_wsp_kdr(0, Decimal('10'), [Decimal('5')], [Decimal('100')])
        self.assertEqual(kd, Decimal('0.125'))

    def test_zuraw_calculator_units(self):
        # Test if ZurawCalculator handles tons correctly in diagram
        input_data = {
            'q_max': {'value': 10, 'unit': 't'}, # 10000 kg
            'q_o': 0,
            'q_1': {'value': 5, 'unit': 't'},    # 5000 kg
            'c_1': 100,
            'lata_pracy': 10,
            'ilosc_cykli': 1000,
            'sposob_rejestracji': 'Rejestrowanie przyrządami',
            'gnp': 'A1',
            'ponowny_resurs': 'Nie'
        }
        calc = ZurawCalculator(input_data)
        result = calc.calculate()
        # q_i / q_max should be 5000 / 10000 = 0.5
        # wsp_kdr = 1.0 * (0.5**3) = 0.125
        self.assertEqual(result['wsp_kdr'], Decimal('0.125'))
