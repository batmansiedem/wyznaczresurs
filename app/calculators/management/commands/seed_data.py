from django.core.management.base import BaseCommand
from decimal import Decimal
from calculators.models import Unit, CalculatorDefinition


UNITS = [
    # Masa — baza: t (tona)
    {"name": "tona", "symbol": "t", "unit_type": "mass", "conversion_factor": Decimal("1.0")},
    {"name": "kilogram", "symbol": "kg", "unit_type": "mass", "conversion_factor": Decimal("0.001")},
    # Czas — baza: lata
    {"name": "lata", "symbol": "lata", "unit_type": "time", "conversion_factor": Decimal("1.0")},
    {"name": "godziny", "symbol": "h", "unit_type": "time", "conversion_factor": Decimal("0.000114155")},
    # Długość — baza: m
    {"name": "metr", "symbol": "m", "unit_type": "length", "conversion_factor": Decimal("1.0")},
    {"name": "centymetr", "symbol": "cm", "unit_type": "length", "conversion_factor": Decimal("0.01")},
    # Prędkość — baza: m/min
    {"name": "metry na minutę", "symbol": "m/min", "unit_type": "velocity", "conversion_factor": Decimal("1.0")},
    {"name": "metry na sekundę", "symbol": "m/s", "unit_type": "velocity", "conversion_factor": Decimal("60.0")},
    # Bezjednostkowe
    {"name": "cykle", "symbol": "cykl", "unit_type": "dimensionless", "conversion_factor": Decimal("1.0")},
]


CALCULATOR_DEFINITIONS = [
    {"slug": "wciagarka",            "name": "Wciągarka",                 "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "wciagnik",             "name": "Wciągnik",                  "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "suwnica",              "name": "Suwnica",                   "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "zuraw",                "name": "Żuraw",                     "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "zuraw_przeladunkowy",  "name": "Żuraw przeładunkowy",       "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "ukladnica_magazynowa", "name": "Układnica magazynowa",      "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "dzwignik",             "name": "Dźwignik",                  "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "hakowiec",             "name": "Hakowiec",                  "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "podnosnik_samochodowy","name": "Podnośnik samochodowy",     "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "autotransporter",      "name": "Autotransporter",           "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "podest_ruchomy",       "name": "Podest ruchomy",            "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "podest_zaladowczy",    "name": "Podest załadowczy",         "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "wozek_jezdniowy",      "name": "Wózek jezdniowy",           "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "wozek_specjalizowany", "name": "Wózek specjalizowany",      "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "dzwig",                "name": "Dźwig",                     "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "winda_dekarska",       "name": "Winda dekarska",            "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "mech_podnoszenia",     "name": "Mechanizm podnoszenia",     "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "mech_jazdy_suwnicy",   "name": "Mechanizm jazdy suwnicy",   "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "mech_jazdy_wciagarki", "name": "Mechanizm jazdy wciągarki", "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "mech_jazdy_zurawia",   "name": "Mechanizm jazdy żurawia",   "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "mech_zmiany_wysiegu",  "name": "Mechanizm zmiany wysięgu",  "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
    {"slug": "mech_zmiany_obrotu",   "name": "Mechanizm zmiany obrotu",   "premium_cost": Decimal("100.00"), "premium_cost_recurring": Decimal("80.00")},
]


class Command(BaseCommand):
    help = "Seeduje jednostki miar i definicje kalkulatorów"

    def handle(self, *args, **options):
        self._seed_units()
        self._seed_calculators()

    def _seed_units(self):
        # Usuń stary angielski symbol 'cycle' zastąpiony przez 'cykl'
        deleted, _ = Unit.objects.filter(symbol='cycle').delete()
        if deleted:
            self.stdout.write(f"Usunięto stary symbol 'cycle' ({deleted} rekordów).")

        created = updated = 0
        for data in UNITS:
            _, was_created = Unit.objects.update_or_create(
                symbol=data["symbol"],
                defaults=data,
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(self.style.SUCCESS(
            f"Jednostki: {created} dodanych, {updated} zaktualizowanych."
        ))

    def _seed_calculators(self):
        created = updated = 0
        for data in CALCULATOR_DEFINITIONS:
            _, was_created = CalculatorDefinition.objects.update_or_create(
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "premium_cost": data["premium_cost"],
                    "premium_cost_recurring": data["premium_cost_recurring"],
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(self.style.SUCCESS(
            f"Kalkulatory: {created} dodanych, {updated} zaktualizowanych."
        ))
