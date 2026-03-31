"""Ładowanie konfiguracji urządzeń z plików JSON."""
import json
import re
from pathlib import Path
from functools import lru_cache

CONFIG_DIR = Path(__file__).parent / 'device_configs'


@lru_cache(maxsize=None)
def load_config(slug: str) -> dict:
    """Zwraca konfigurację urządzenia (pola wejściowe + sekcje + pola wyjściowe)."""
    path = CONFIG_DIR / f'{slug}.json'
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    return {}


def get_all_configs() -> dict:
    """Zwraca słownik {slug: config} dla wszystkich urządzeń."""
    configs = {}
    for path in sorted(CONFIG_DIR.glob('*.json')):
        configs[path.stem] = load_config(path.stem)
    return configs


def get_field_label(slug: str, field_key: str) -> str:
    """Zwraca etykietę pola wejściowego dla danego urządzenia i klucza."""
    config = load_config(slug)
    field = config.get('fields', {}).get(field_key, {})
    label = field.get('label', field_key.replace('_', ' ').capitalize())
    # Usuń tagi HTML z etykiety
    return re.sub(r'<[^>]*>', '', label)
