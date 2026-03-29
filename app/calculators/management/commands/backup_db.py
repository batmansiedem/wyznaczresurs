"""
Komenda zarządzania: tworzy kopię zapasową bazy SQLite.

Użycie:
    python manage.py backup_db               # backup z domyślnymi ustawieniami
    python manage.py backup_db --keep 7      # zachowaj tylko 7 ostatnich kopii

Zalecane ustawienie cron (co noc o 2:00):
    0 2 * * * /ścieżka/do/venv/bin/python /ścieżka/do/app/manage.py backup_db >> /var/log/backup_db.log 2>&1

Konfiguracja w .env:
    BACKUP_DIR=/var/backups/wyznaczresurs    # katalog na kopie zapasowe
    BACKUP_KEEP_LAST=30                      # ile ostatnich kopii zachować
"""
import sqlite3
import os
import stat
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Tworzy kopię zapasową bazy SQLite i usuwa stare kopie (rotacja)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep', type=int, default=None,
            help='Ile ostatnich kopii zachować (domyślnie: BACKUP_KEEP_LAST z ustawień, fallback: 30)'
        )
        parser.add_argument(
            '--secure', action='store_true',
            help='Ustaw uprawnienia chmod 600 na pliku bazy danych (tylko właściciel może czytać)'
        )

    def handle(self, *args, **options):
        db_cfg = settings.DATABASES.get('default', {})
        db_path = Path(str(db_cfg.get('NAME', '')))

        if db_cfg.get('ENGINE', '').endswith('sqlite3'):
            self._backup_sqlite(db_path, options)
        else:
            self.stdout.write(self.style.WARNING(
                "Backup automatyczny obsługuje tylko SQLite. "
                "Dla MySQL/PostgreSQL użyj mysqldump / pg_dump."
            ))
            return

        # Opcjonalne: ustaw uprawnienia na pliku bazy
        if options['secure']:
            self._secure_db_file(db_path)

    def _backup_sqlite(self, db_path, options):
        if not db_path.exists():
            self.stderr.write(self.style.ERROR(f"Baza danych nie istnieje: {db_path}"))
            return

        # Katalog na backupy — z .env lub domyślnie podfolder 'backups' obok bazy
        backup_dir = Path(getattr(settings, 'BACKUP_DIR', db_path.parent / 'backups'))
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Ogranicz dostęp do katalogu backupów (tylko właściciel procesu)
        try:
            backup_dir.chmod(0o700)
        except OSError:
            pass  # Może nie mieć uprawnień na Windows

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f"db_backup_{timestamp}.sqlite3"

        # SQLite hot backup — bezpieczne nawet gdy baza jest używana
        try:
            src = sqlite3.connect(str(db_path))
            dst = sqlite3.connect(str(backup_path))
            with dst:
                src.backup(dst)
            dst.close()
            src.close()
        except sqlite3.Error as e:
            self.stderr.write(self.style.ERROR(f"Błąd tworzenia backupu: {e}"))
            return

        # Ogranicz dostęp do pliku backupu
        try:
            backup_path.chmod(0o600)
        except OSError:
            pass

        size_kb = backup_path.stat().st_size // 1024
        self.stdout.write(self.style.SUCCESS(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"Backup: {backup_path.name} ({size_kb} KB)"
        ))

        # Rotacja — usuń nadmiarowe stare kopie
        keep = options.get('keep') or getattr(settings, 'BACKUP_KEEP_LAST', 30)
        backups = sorted(backup_dir.glob('db_backup_*.sqlite3'))
        to_delete = backups[:-keep] if len(backups) > keep else []
        for old in to_delete:
            old.unlink()
            self.stdout.write(f"  Usunięto stary backup: {old.name}")

        remaining = len(backups) - len(to_delete)
        self.stdout.write(f"  Kopie zapasowe w {backup_dir}: {remaining}/{keep}")

    def _secure_db_file(self, db_path):
        """Ustawia chmod 600 na pliku bazy — dostęp tylko dla właściciela procesu Django."""
        try:
            db_path.chmod(0o600)
            self.stdout.write(self.style.SUCCESS(
                f"Uprawnienia pliku bazy ustawione na 600: {db_path}"
            ))
        except OSError as e:
            self.stderr.write(self.style.WARNING(
                f"Nie udało się ustawić uprawnień na {db_path}: {e}"
            ))
