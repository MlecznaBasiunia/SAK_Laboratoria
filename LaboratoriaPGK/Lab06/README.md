# Lab 06 – Asteroids: Topologia Świata i Asteroidy

Rozszerzenie Lab 05 o przestrzeń toroidalną (wrapping), ghost rendering i proceduralne asteroidy.

## Struktura

```
lab06/
├── main.py       ← pętla gry
├── ship.py       ← klasa Ship
├── asteroid.py   ← klasa Asteroid + spawn_asteroids()
├── utils.py      ← ghost_positions(), rotate(), wrap(), vec2()
├── config.py     ← wszystkie stałe fizyczne i konfiguracja
└── README.md
```

## Wymagania

- Python 3.12+
- raylib (`pip install raylib`)

## Uruchomienie (opcja z pycharm na starej wersji)

```powershell
.\lab\Scripts\Activate.ps1
cd lab06
python main.py
```

## Sterowanie

| Klawisz | Akcja                   |
|---------|-------------------------|
| ← →     | Obrót statku            |
| ↑       | Ciąg (thrust) + płomień |
| Z       | Hamulec awaryjny        |
| ESC     | Zamknięcie okna         |

## Zaimplementowane zadania

- **Zad. 1** – Wrapping statku przez modulo (działa dla obu kierunków)
- **Zad. 2** – Klasa Asteroid z ruchem, delta time, losowym wektorem prędkości
- **Zad. 3** – Ghost rendering asteroid (widoczność po obu stronach krawędzi)
- **Zad. 4** – Ghost rendering statku, wspólna funkcja `ghost_positions()` w `utils.py`
- **Zad. 5** – Proceduralne wielokąty z własną rotacją
- **Zad. \*** – Separacja konfiguracji do `config.py`
- **Zad. \*\*** – Trzy klasy rozmiarów asteroid (large/medium/small) z automatycznymi parametrami
