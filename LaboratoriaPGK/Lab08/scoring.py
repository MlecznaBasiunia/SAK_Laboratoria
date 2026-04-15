import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _path(filename):
    return os.path.join(SCRIPT_DIR, filename)


def load_best(filename):
    """Wczytuje najlepszy wynik z pliku. Zwraca 0 gdy plik nie istnieje lub jest uszkodzony."""
    try:
        with open(_path(filename), "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def save_best(filename, value):
    """Zapisuje najlepszy wynik do pliku."""
    try:
        with open(_path(filename), "w") as f:
            f.write(str(value))
    except OSError:
        pass  # nie blokujemy gry gdy zapis się nie uda
