# Laboratorium 05 – Generator Lasu z Typami Roślin i Biomami

**Przedmiot:** Systemy Animacji Komputerowej  
**Technologia:** Blender 5.1 + Python API (`bpy`)  
**Plik skryptu:** `las05.py`  
**Plik renderowy:** `las_05.png` (1200×800, Eevee)

## Opis

Skrypt proceduralnie generuje scenę leśną w Blenderze. Na podstawie systemu biomów (centrum → drzewa, strefa środkowa → mix, peryferia → kwiaty i kamienie) rozmieszcza obiekty po całej mapie 35×35 jednostek. Każde uruchomienie z tym samym seedem daje identyczny las (odtwarzalność).

## Typy roślin i obiektów

Wszystkie parametry zdefiniowane w słowniku `TYPY_ROSLIN`:

| Typ | Opis | Elementy |
|-----|------|----------|
| **drzewo** | Pień + gałęzie + gęsta korona z kul UV | 4–7 kul, 3–5 korzeni |
| **stokrotka** | Biały kwiat z żółtym środkiem | 8–14 płatków |
| **chaber** | Niebieski kwiat z fioletowym środkiem | 6–10 płatków |
| **grzyb** | Jasna nóżka + czerwony kapelusz | spawnuje pod drzewami |
| **trawa/mech** | Kępki stożków (trawa) lub kuleczek (mech) | 5–12 źdźbeł na kępkę |
| **kamień** | Spłaszczona szara sfera | losowa wariacja koloru |
| **pniak** | Krótki cylinder + dysk słojów | na peryferiach |
| **krzew jagodowy** | 2–3 zielone kule + czerwone jagody | 4–10 jagód |
| **motyl** | Ciało + 2 trójkątne skrzydła | unosi się nad kwiatami |
| **opadłe liście** | Płaskie dyski w ciepłych kolorach | pod drzewami |

## Elementy dodatkowe

- **Źródełko** — 3 nakładające się elipsy z emisją + 20 kamyków wokół brzegu
- **Oświetlenie nastrojowe** — ciepłe point lights między drzewami
- **Podłoże** — zielona płaszczyzna 35×35
- **Tło** — jasne niebo (World Background)

## System biomów

Funkcja `wybierz_typ_biomu(x, z)` dzieli mapę na trzy strefy na podstawie znormalizowanej odległości od centrum:

- **Centrum (<35%)** — dominują drzewa (55%) i krzewy jagodowe (15%)
- **Strefa środkowa (35–70%)** — mieszanka: drzewa, kwiaty, krzewy, kamienie, pniaki
- **Peryferia (>70%)** — kwiaty, kamienie, pniaki, pojedyncze drzewa (20%)

## Fazy generowania

1. **Faza 1** — 80 głównych roślin z logiki biomów rozrzuconych po całej mapie
2. **Faza 2** — grzyby (1–3), trawa (3–5 kępek) i opadłe liście pod każdym drzewem
3. **Faza 3** — 120 kępek trawy losowo po całej mapie
4. **Faza 4** — 30 gęstych kępek trawy w pierścieniu wokół źródełka
5. **Faza 5** — motyle nad ~40% kwiatów

## Kolekcje w Outlinerze

```
Las/
├── Drzewa/
├── Stokrotki/
├── Chabry/
├── Grzyby/
├── Trawa_Mech/
├── Kamienie/
├── Pniaki/
├── Krzewy_Jagodowe/
├── Motyle/
├── Opadle_Liscie/
└── Zrodelko/
```

## Uruchomienie

1. Otwórz Blender 5.1
2. Przejdź do zakładki **Scripting** (lub otwórz Text Editor)
3. Wczytaj plik `las05.py`
4. Uruchom skryptem **Alt+P**
5. Render zapisze się automatycznie jako `las_05.png` obok skryptu

## Parametry do modyfikacji

```python
generuj_las(liczba_roslin=80, seed=42)
```

- `liczba_roslin` — ilość obiektów w fazie 1 (domyślnie 80)
- `seed` — ziarno generatora losowego (identyczny seed = identyczny las)
- `ROZMIAR_MAPY` — stała globalna, rozmiar podłoża i strefy spawnu (domyślnie 35)

## Wymagania

- Blender 5.1+
- Python 3.x (wbudowany w Blender)
- Silnik renderujący: Eevee (domyślnie) lub Workbench
