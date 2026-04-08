# Lab 07 – Asteroids: Pociski, Zasoby i Kolizje

Rozszerzenie Lab 06 o pociski, dźwięki, kolizje, eksplozje i tło.

## Struktura

```
lab07/
├── main.py         ← pętla gry, audio, kolizje
├── ship.py         ← klasa Ship (+ reset, nose_position)
├── asteroid.py     ← klasa Asteroid
├── bullet.py       ← klasa Bullet (TTL + alive)
├── explosion.py    ← animacja eksplozji
├── utils.py        ← ghost_positions, rotate, wrap, circles_collide
├── config.py       ← wszystkie stałe
├── README.md
└── assets/
    ├── shoot.wav     (opcjonalne)
    ├── explode.wav   (opcjonalne)
    └── stars.png     (opcjonalne)
```

## Wymagania

- Python 3.12+
- raylib (`pip install raylib`)

## Uruchomienie

```powershell
.\lab\Scripts\Activate.ps1
cd lab07
python main.py
```

Gra **uruchomi się bez plików w `assets/`** – brakujące dźwięki będą po prostu pominięte, a tło zostanie wygenerowane proceduralnie (gwiazdki). Wrzuć pliki do `assets/` żeby je włączyć:

- **shoot.wav, explode.wav** – wygeneruj na https://sfxr.me i wyeksportuj jako WAV
- **stars.png** – obraz 800×600 px z gwiazdkami (lub zostaw fallback proceduralny)

## Sterowanie

| Klawisz | Akcja                   |
|---------|-------------------------|
| ← →     | Obrót statku            |
| ↑       | Ciąg + płomień          |
| Z       | Hamulec awaryjny        |
| Spacja  | Strzał                  |
| ESC     | Zamknięcie okna         |

## Zaimplementowane zadania

- **Zad. 1** – Klasa `Bullet` z TTL, flagą `alive`, wrappingiem
- **Zad. 2** – Strzelanie spacją, `IsKeyPressed` (jednorazowo), czyszczenie list comprehension
- **Zad. 3** – `InitAudioDevice`, `LoadSound`, `PlaySound`, `UnloadSound`, `CloseAudioDevice` w prawidłowej kolejności
- **Zad. 4** – Tekstura tła z fallbackiem proceduralnym (gwiazdki rysowane przed obiektami gry)
- **Zad. 5** – Kolizja kołowa w `utils.circles_collide()`, kolejność: zaznacz → wyczyść (nie usuwamy w trakcie iteracji)
- **Zad. 6** – Klasa `Explosion` z timerem, rosnący promień, malejąca alpha
- **Zad. \*** – Kolizja statek–asteroida: eksplozja + reset statku do środka z zerową prędkością
- **Zad. \*\*** – Limit pocisków na ekranie (`BULLET_LIMIT = 5` w `config.py`)

## Uwagi techniczne

**Cykl życia zasobów:** wszystkie `Load*` przed pętlą, wszystkie `Unload*` po pętli. Audio device zamykany przed oknem. Bez tego raylib zgłasza wycieki w konsoli przy zamknięciu.

**`IsKeyPressed` vs `IsKeyDown`:** strzał używa `IsKeyPressed` – wyzwala się raz przy naciśnięciu klawisza. `IsKeyDown` zwracałby True każdej klatki przez ~60 strzałów na sekundę.

**Kolejność czyszczenia kolizji:** najpierw cały podwójny loop oznacza obiekty jako `alive = False`, dopiero potem list comprehension je usuwa. Modyfikowanie listy w trakcie iteracji łamie iterator.

**Kolizja kołowa vs AABB:** dla obrotowych asteroid i punktowych pocisków koło daje lepsze przybliżenie kształtu niż prostokąt osiowo wyrównany.
