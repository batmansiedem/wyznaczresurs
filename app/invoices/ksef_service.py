"""
Mock serwisu KSeF (Krajowy System e-Faktur).
W środowisku sandbox symuluje cykl: pending → sent → accepted.

Na produkcji zastąp funkcję submit() rzeczywistym wywołaniem API KSeF:
  - sesja interaktywna (POST /api/online/Session/AuthorisationChallenge)
  - podpis XAdES-BES / token serwisowy
  - wysyłka faktury FA(2) jako XML
  - polling statusu UPO (UrzędowePotwierdzenie Odbioru)
"""
import uuid
from django.utils import timezone


def submit(invoice) -> None:
    """
    Wysyła fakturę do KSeF i oczekuje na akceptację.
    Po akceptacji doładowuje punkty użytkownika.

    Modyfikuje obiekt invoice in-place i zapisuje zmiany do bazy.
    """
    # Krok 1: Faktura wysłana do KSeF
    invoice.ksef_status = "sent"
    invoice.save(update_fields=["ksef_status"])

    # Krok 2: Akceptacja przez KSeF (w sandbox — natychmiastowa symulacja)
    # W produkcji: polling UPO lub webhook zwrotny od KSeF
    ksef_ref = f"KSEF-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    invoice.ksef_status = "accepted"
    invoice.ksef_reference_number = ksef_ref
    invoice.save(update_fields=["ksef_status", "ksef_reference_number"])

    # Krok 3: Punkty doładowywane dopiero po akceptacji KSeF
    invoice.user.premium += invoice.points_added
    invoice.user.save(update_fields=["premium"])


def submit_correction(correction_invoice) -> None:
    """
    Wysyła fakturę korygującą do KSeF.
    Korekta nie zmienia salda punktów.
    """
    correction_invoice.ksef_status = "sent"
    correction_invoice.save(update_fields=["ksef_status"])

    ksef_ref = f"KSEF-KOR-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    correction_invoice.ksef_status = "accepted"
    correction_invoice.ksef_reference_number = ksef_ref
    correction_invoice.save(update_fields=["ksef_status", "ksef_reference_number"])
