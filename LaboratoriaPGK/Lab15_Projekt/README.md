# Asteroids on Steroids

Rozbudowany klon Asteroids napisany w Pythonie z użyciem [raylib](https://github.com/electronstudio/raylib-python-cffi). Obsługuje tryb jednoosobowy, kooperację przez LAN, wiele topologii nieeuklidesowych, walki z bossami, moduły broni, perki i pełną lokalizację.

---

## Funkcjonalności

### Rozgrywka
- **Progresja falowa** — liczba asteroid rośnie z każdą falą; co kilka fal zmienia się topologia świata
- **5 topologii świata** — Torus, Cylinder, Wstęga Möbiusa, Butelka Kleina, Sfera; wszystkie z poprawnym ghost-renderingiem na krawędziach
- **3 rozmiary asteroid** — Duże → Średnie → Małe rozpadają się przy zniszczeniu; kryształowe asteroidy wymagają kilku trafień
- **System frakcji** — asteroidy przyciągające i odpychające z różnym zachowaniem
- **Zarządzanie ciepłem** — ciągły ogień i ciąg budują temperaturę; przegrzanie tymczasowo blokuje broń

### Przeciwnicy
| Przeciwnik | Opis |
|------------|------|
| Asteroida (duża/średnia/mała) | Proceduralny wielokąt z własną rotacją |
| Kryształowa asteroida | 4 HP, mnożnik punktów ×5 |
| UFO (duże/małe) | Cykliczne pojawy, celowany ogień |
| Dron myśliwski | Ściga gracza, 2 HP |
| Przeciwnik lustrzany | Kopiuje wejście gracza |
| Rój | Klaster 12 szybkich jednostek |
| **Boss: Behemot** | 30 HP, promień 80 — co 5. fala |
| **Boss: Królowa Roju** | 20 HP, co 3 s spawnuje drony |
| **Boss: Władca Luster** | 15 HP |

### Broń i moduły
Jednocześnie można mieć zamontowane do 4 modułów broni:

| Moduł | Efekt |
|-------|-------|
| RAPID | Skrócony czas odnowienia strzału |
| PIERCE | Pociski przebijają jedną asteroidę |
| SPLIT | Potrójny strzał |
| HOMING | Lekkie naprowadzanie na cel |
| GRAVITY | Alternatywny ogień: bomba grawitacyjna (obszarowe przyciąganie, `X`) |
| BOUNCE | Pociski odbijają się od krawędzi ekranu |
| HYPER | Strzał torusowy — wraps przez topologię (`C`) |

### Perki
Między falami losowany jest wybór 3 perków:
Przebijające strzały, Rykoszet, Naprowadzanie, Podwójne punkty, Magnes na power-upy, Pole spowolnienia, Dodatkowe życie, Wielka eksplozja, Tarcza ciągu, Bomba grawitacyjna, Strzał hiperprzestrzenny, Pociski prędkości i inne.

### Zagrożenia środowiskowe
- **Portale (wormhole)** — parowane teleportery pojawiające się cyklicznie
- **Studnie grawitacyjne** — przyciągają pobliskie obiekty; promień działania 180 px

### Multiplayer
- Kooperacja przez LAN dla maksymalnie **4 graczy** (1 host + 3 klientów)
- **Rozgłoszenie UDP** (port 5555) do automatycznego wykrywania hosta — bez wpisywania adresu IP
- **TCP** (port 5556) przesyła autorytatywny stan gry przy każdym ticku
- Lobby z systemem gotowości; host może wymusić start
- Wspólna pula żyć z konfigurowalnymi trybami respawnu: fala / punkty / czas

### Pozostałe
- **4 skórki statku** — Classic, Arrow, Diamond, Falcon; własny kolor dla każdego gracza
- **Tryb seedowanego RNG** — powtarzalne rozgrywki do wyzwań
- **Trwałe rekordy** (`highscores.json`) z nazwą gracza, falą, trybem i seedem
- **Lokalizacja** — angielski, polski, rosyjski, hiszpański (`lang.py`)
- **Mnożnik combo** oraz bonusy punktowe za prędkość, dystans i przejścia przez krawędź

---

## Struktura projektu

```
lab6/
├── main.py          # pętla gry, menu, maszyna stanów, orkiestracja renderowania
├── ship.py          # klasa Ship, 4 skórki, system ciepła, sloty modułów
├── asteroid.py      # klasa Asteroid, helpery spawnowania, logika frakcji
├── bullet.py        # warianty pocisków (normalny, odbijający, naprowadzany, grawitacyjny, hyper)
├── boss.py          # Behemoth, SwarmQueen, MirrorLord
├── hunter.py        # HunterDrone, MirrorEnemy
├── ufo.py           # UFO (duże / małe)
├── powerup.py       # power-upy (tarcza, nuke, przyspieszenie, moduł)
├── portal.py        # pary portali wormhole
├── gravity_well.py  # zagrożenie: studnia grawitacyjna
├── wave.py          # system fal i sektorów, pula perków, definicje modułów, eventy
├── particle.py      # efekty cząsteczkowe (eksplozje, ciąg, portale, ślad cieplny…)
├── utils.py         # vec2, wrap, ghost_positions, helpery topologii
├── sound.py         # wrapper systemu dźwięku
├── network.py       # multiplayer LAN — strumień TCP + wykrywanie UDP
├── lang.py          # lokalizacja (en / pl / ru / es)
├── config.py        # wszystkie konfigurowalne stałe (fizyka, wrogowie, punktacja…)
├── settings.json    # ustawienia użytkownika zapisywane między sesjami
└── highscores.json  # tabela 10 najlepszych wyników
```

---

## Wymagania

- Python **3.12+**
- [raylib-python-cffi](https://github.com/electronstudio/raylib-python-cffi)

```powershell
pip install raylib
```

> Tylko Windows: moduł ładowania czcionek Unicode szuka plików `arial.ttf` / `segoeui.ttf` / `tahoma.ttf` w katalogu `C:\Windows\Fonts`. Na innych platformach używana jest wbudowana czcionka raylib.

---

## Uruchomienie

```powershell
# (opcjonalnie) aktywacja środowiska wirtualnego
.\lab\Scripts\Activate.ps1

python main.py
```

Aby rozpocząć sesję multiplayer, jeden gracz uruchamia grę i wybiera **Host**; pozostali wybierają **Dołącz** — host jest wykrywany automatycznie w sieci LAN.

---

## Sterowanie

### Tryb jednoosobowy

| Klawisz | Akcja |
|---------|-------|
| `↑` | Ciąg (thrust) |
| `← →` | Obrót |
| `↓` / `A` / `D` | Strafe (ruch boczny) |
| `Z` | Hamulec awaryjny |
| `Spacja` | Strzał |
| `X` | Bomba grawitacyjna (alternatywny ogień) |
| `C` | Strzał hiperprzestrzenny (alternatywny ogień) |
| `ESC` | Pauza / powrót do menu |

### Multiplayer (drugi gracz lokalny)

| Klawisz | Akcja |
|---------|-------|
| `W` | Ciąg |
| `A` / `D` | Obrót |
| `S` | Hamulec |
| `Tab` | Strzał |

---

## Konfiguracja

Wszystkie stałe rozgrywki znajdują się w pliku [`config.py`](config.py). Kluczowe grupy:

| Sekcja | Główne stałe |
|--------|--------------|
| Ekran | `SCREEN_W`, `SCREEN_H` |
| Fizyka statku | `THRUST`, `FRICTION`, `MAX_SPEED`, `BRAKE_FORCE`, `STRAFE_SPEED` |
| System ciepła | `HEAT_THRUST_RATE`, `HEAT_OVERHEAT`, `HEAT_COOLDOWN_TIME` |
| Pociski | `BULLET_SPEED`, `MAX_BULLETS`, `SHOOT_COOLDOWN` |
| Asteroidy | `ASTEROID_SIZES`, `ASTEROID_COUNT`, `ASTEROID_SPECIAL_CHANCE` |
| Bossy | `BOSS_WAVE_INTERVAL`, `BOSS_BEHEMOTH_HP`, … |
| Topologia | `TOPOLOGY_CHANGE_WAVES` |
| Punktacja | `VELOCITY_SCORE_BONUS`, `COMBO_TIMEOUT`, `WRAP_SCORE_PER_WRAP` |
| Multiplayer | `MP_RESPAWN_SCORE`, `MP_RESPAWN_TIMER`, `MP_RESPAWN_MODES` |

Ustaw `DEBUG = True`, aby włączyć nakładki diagnostyczne.

---

## Stos technologiczny

| Komponent | Technologia |
|-----------|-------------|
| Renderowanie | raylib (via raylib-python-cffi) |
| Sieć | stdlib `socket` — TCP + UDP |
| Serializacja | JSON (stan gry, rekordy, ustawienia) |
| Język | Python 3.12 |
