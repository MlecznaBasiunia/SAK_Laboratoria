# Lab 08 – Asteroids: FSM, Podział i Domknięcie

Finalna wersja projektu. Trzypoziomowy podział asteroid, maszyna stanów (MENU / GAME / GAME_OVER), system punktów z zapisem do pliku, fale, refaktoryzacja.

## Struktura

```
lab08/
├── main.py         ← inicjalizacja + pętla + cleanup (~30 linii)
├── game.py         ← klasa Game: FSM, kolizje, HUD
├── ship.py         ← klasa Ship
├── asteroid.py     ← klasa Asteroid + split() + spawn_wave()
├── bullet.py       ← klasa Bullet
├── explosion.py    ← klasa Explosion
├── resources.py    ← ładowanie/zwalnianie dźwięków i tekstur
├── scoring.py      ← persystencja best score (load/save)
├── utils.py        ← funkcje pomocnicze (rotate, wrap, ghost, kolizje, prune)
├── config.py       ← wszystkie stałe
├── README.md
├── scores.txt      ← (auto) najlepszy wynik
└── assets/
    ├── shoot.wav
    ├── explode.wav
    └── stars.png
```

## Wymagania

- Python 3.12+
- raylib (`pip install raylib`)

## Uruchomienie

```powershell
.\lab\Scripts\Activate.ps1
cd lab08
python main.py
```

## Sterowanie

| Klawisz       | Akcja                       |
|---------------|-----------------------------|
| ENTER / SPACE | Start gry (z menu)          |
| ← →           | Obrót statku                |
| ↑             | Ciąg + płomień              |
| Z             | Hamulec awaryjny            |
| SPACE         | Strzał (max 5 na ekranie)   |
| R / ENTER     | Powrót do menu (game over)  |
| ESC           | Wyjście z gry               |

## Mechanika

**Trzy poziomy asteroid** – każda trafiona dzieli się na dwie mniejsze:

| Level | Rozmiar | Prędkość  | Punkty |
|-------|---------|-----------|--------|
| 3     | duża    | 30–70     | 20     |
| 2     | średnia | 60–130    | 50     |
| 1     | mała    | 100–200   | 100    |

Mniejsza asteroida = szybsza, więcej punktów. Mała znika bezpowrotnie po trafieniu.

**Fale** – po wyczyszczeniu wszystkich asteroid, po `WAVE_DELAY` sekundach pojawia się nowa fala z większą liczbą asteroid. Numer fali widoczny w HUD.

**Punktacja** – aktualny wynik i `best` zapisywane do `scores.txt` po każdym pobiciu rekordu. Plik tworzony automatycznie przy pierwszym uruchomieniu.

## Zaimplementowane zadania

- **Zad. 1** – Klasa `Asteroid` z parametrem `level`, parametry z `ASTEROID_LEVELS`, metoda `split()`
- **Zad. 2** – `score`, `best`, `_draw_hud()` w klasie `Game`
- **Zad. 3** – Pełna FSM przez `enum.Enum` (`State.MENU/GAME/GAME_OVER`), pary `update_*` / `draw_*`, dispatcher
- **Zad. 4** – Refaktoryzacja:
  - **Magic numbers** → `config.py` (klawisze, czcionki, marginesy, parametry fal)
  - **Długie funkcje** → `Ship.update` rozbity na `_apply_friction` / `_clamp_speed`; `update_game` wydziela `_check_*_collisions`
  - **Powtórzony kod** → `prune()` w `utils.py` zamiast trzykrotnego list comprehension; `random_velocity()` zamiast inline `cos/sin/uniform`
  - **Importy w środku funkcji** → wszystkie na górze plików
  - **Zasoby** → wydzielone do klasy `Resources` (`load`/`unload`/`play_*`/`draw_background`)
  - **Niejasne nazwy** → `b`, `a`, `e` zamienione na `bullet`, `asteroid`, `explosion`
- **Zad. 5** – Oba warunki końca: kolizja statek-asteroida (GAME_OVER czerwony), pusta lista asteroid → kontynuacja przez fale (zwycięstwo nieosiągalne w tym wariancie, flaga `victory` zostawiona w API)
- **Zad. \*** – System fal z timerem między falami i licznikiem `wave` na HUD
- **Zad. \*\*** – `scoring.py` z `load_best`/`save_best`, `try/except` na `FileNotFoundError`/`ValueError`, plik `scores.txt`

## Uwagi do refaktoryzacji

`main.py` z lab07 miał ~140 linii i robił wszystko (init, audio, kolizje, czyszczenie, render). Po podziale: `main.py` ~30 linii (tylko pętla), cała logika gry w `Game`, zasoby w `Resources`, persistence w `scoring`. Dodanie nowego stanu (np. PAUSE) to teraz dopisanie `update_pause`/`draw_pause` i jednej gałęzi w dispatcherze.

Enum zamiast stringów: literówka `State.GAEM` daje `AttributeError` od razu, `if state == "gaem"` cicho wraca False i przejście nigdy się nie odpala. PyCharm autocompleteuje atrybuty enum.

`split()` jako metoda asteroidy zamiast logiki w `main` – asteroida sama wie jak się dzieli. `main` tylko zbiera wynik i dorzuca do listy. Spójne z enkapsulacją.
