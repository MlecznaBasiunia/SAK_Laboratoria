# Lab 05 – Asteroids: Statek

Statek kosmiczny z rotacją wierzchołków 2D, modelem kinematycznym (bezwładność + tarcie) i fizyką niezależną od FPS. Raylib-Python (cffi).

## Struktura

```
lab05/
├── main.py   ← pętla gry, okno, wejście
├── ship.py   ← klasa Ship: geometria, fizyka, rysowanie
└── README.md
```

## Wymagania

- Python 3.12+
- raylib (`pip install raylib`)

## Uruchomienie

```powershell
# 1. Aktywuj venv (jeśli używasz)
.\lab\Scripts\Activate.ps1

# 2. Zainstaluj raylib (jeśli jeszcze nie)
pip install raylib

# 3. Odpal grę
cd lab5
python main.py
```

## Sterowanie

| Klawisz       | Akcja                        |
|---------------|------------------------------|
| ←  →          | Obrót statku                 |
| ↑             | Ciąg (thrust) + płomień      |
| Z             | Hamulec awaryjny             |
| ESC           | Zamknięcie okna              |

## Zaimplementowane funkcje

- **Rotacja wierzchołków** – macierz obrotu 2D, wierzchołki przeliczane co klatkę z układu lokalnego na ekranowy
- **Bezwładność** – prędkość jako oddzielna wielkość od pozycji, statek dryfuje po puszczeniu klawisza
- **Tarcie addytywne** – stała siła hamująca przeciwna do kierunku ruchu, z zabezpieczeniem przed zmianą znaku
- **Clamp prędkości** – `math.hypot` + skalowanie wektora z zachowaniem kierunku
- **Fizyka niezależna od FPS** – każda wielkość fizyczna mnożona przez `dt` (`GetFrameTime`)
- **Płomień silnika** – drugi trójkąt rysowany za statkiem podczas thrustu
- **Hamulec awaryjny (Z)** – gwałtowne wygaszanie prędkości (~4x silniejsze od tarcia)
- **Odbijanie od krawędzi** – zmiana znaku składowej prędkości przy kontakcie ze ścianą

## Diagnostyka

W `ship.py` zmień `DEBUG = True` aby wyświetlić wektor prędkości (linia z centrum statku) i wartość liczbową na ekranie.

## Stałe fizyczne (`ship.py`)

| Stała       | Wartość | Opis                                           |
|-------------|---------|-------------------------------------------------|
| THRUST      | 300     | Siła ciągu silnika                              |
| FRICTION    | 80      | Tarcie addytywne (zatrzymanie po ~2-3 s)        |
| ROT_SPEED   | 4.0     | Prędkość kątowa (rad/s)                         |
| MAX_SPEED   | 350     | Maksymalna prędkość statku                      |
| BRAKE_FORCE | 600     | Siła hamulca awaryjnego                         |

## Uwagi

Kod korzysta z niskopoziomowego API raylib (`from raylib import ffi, rl, colors`) z PascalCase (`rl.InitWindow`, `rl.IsKeyDown`), ponieważ wrapper `pyray` (snake_case) nie generuje się poprawnie w wersji 5.5.x na Pythonie 3.13.
