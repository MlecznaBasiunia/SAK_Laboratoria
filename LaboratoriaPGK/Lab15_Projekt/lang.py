"""Localization module for Asteroids on Steroids.

Supports: English (en), Polish (pl), Russian (ru), Spanish (es).
Usage:  from lang import T, set_language
        T("Single Player")  ->  translated string
"""

_current_lang = 'en'

LANGUAGES = ['en', 'pl', 'ru', 'es']
LANGUAGE_NAMES = {
    'en': 'English',
    'pl': 'Polski',
    'ru': '\u0420\u0443\u0441\u0441\u043a\u0438\u0439',  # Русский
    'es': 'Espa\u00f1ol',
}

def set_language(lang):
    global _current_lang
    if lang in LANGUAGES:
        _current_lang = lang

def get_language():
    return _current_lang

def T(key):
    """Return translated string. Key = English text. Falls back to key itself."""
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(_current_lang, key)


# ══════════════════════════════════════════════════════════════
#  Translation table.  Key = English string.
#  Only non-English entries needed (English falls back to key).
# ══════════════════════════════════════════════════════════════

_STRINGS = {

    # ── MAIN MENU ──
    "Single Player": {
        'pl': "Gra jednoosobowa",
        'ru': "\u041e\u0434\u0438\u043d\u043e\u0447\u043d\u0430\u044f \u0438\u0433\u0440\u0430",
        'es': "Un jugador",
    },
    "Multiplayer": {
        'pl': "Wieloosobowa",
        'ru': "\u041c\u0443\u043b\u044c\u0442\u0438\u043f\u043b\u0435\u0435\u0440",
        'es': "Multijugador",
    },
    "High Scores": {
        'pl': "Najlepsze wyniki",
        'ru': "\u0420\u0435\u043a\u043e\u0440\u0434\u044b",
        'es': "Mejores puntuaciones",
    },
    "Options": {
        'pl': "Opcje",
        'ru': "\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438",
        'es': "Opciones",
    },
    "Controls": {
        'pl': "Sterowanie",
        'ru': "\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435",
        'es': "Controles",
    },
    "Quit": {
        'pl': "Wyjd\u017a",
        'ru': "\u0412\u044b\u0445\u043e\u0434",
        'es': "Salir",
    },

    # ── SINGLEPLAYER MENU ──
    "Start Game": {
        'pl': "Nowa gra",
        'ru': "\u041d\u0430\u0447\u0430\u0442\u044c \u0438\u0433\u0440\u0443",
        'es': "Nueva partida",
    },
    "Seeded Run": {
        'pl': "Gra z seedem",
        'ru': "\u0418\u0433\u0440\u0430 \u0441 \u0441\u0438\u0434\u043e\u043c",
        'es': "Partida con semilla",
    },
    "Back": {
        'pl': "Powr\u00f3t",
        'ru': "\u041d\u0430\u0437\u0430\u0434",
        'es': "Volver",
    },

    # ── PAUSE MENU ──
    "Resume": {
        'pl': "Wzn\u00f3w",
        'ru': "\u041f\u0440\u043e\u0434\u043e\u043b\u0436\u0438\u0442\u044c",
        'es': "Reanudar",
    },
    "Restart Wave": {
        'pl': "Restart fali",
        'ru': "\u041f\u0435\u0440\u0435\u0437\u0430\u043f\u0443\u0441\u043a \u0432\u043e\u043b\u043d\u044b",
        'es': "Reiniciar oleada",
    },
    "Main Menu": {
        'pl': "Menu g\u0142\u00f3wne",
        'ru': "\u0413\u043b\u0430\u0432\u043d\u043e\u0435 \u043c\u0435\u043d\u044e",
        'es': "Men\u00fa principal",
    },
    "PAUSED": {
        'pl': "PAUZA",
        'ru': "\u041f\u0410\u0423\u0417\u0410",
        'es': "PAUSA",
    },

    # ── MULTIPLAYER MENU ──
    "Player Name": {
        'pl': "Nazwa gracza",
        'ru': "\u0418\u043c\u044f \u0438\u0433\u0440\u043e\u043a\u0430",
        'es': "Nombre del jugador",
    },
    "Ship Color": {
        'pl': "Kolor statku",
        'ru': "\u0426\u0432\u0435\u0442 \u043a\u043e\u0440\u0430\u0431\u043b\u044f",
        'es': "Color de nave",
    },
    "Ship Skin": {
        'pl': "Sk\u00f3rka statku",
        'ru': "\u0421\u043a\u0438\u043d \u043a\u043e\u0440\u0430\u0431\u043b\u044f",
        'es': "Skin de nave",
    },
    "P1 Ship Skin": {
        'pl': "Sk\u00f3rka statku G1",
        'ru': "\u0421\u043a\u0438\u043d \u043a\u043e\u0440\u0430\u0431\u043b\u044f \u04181",
        'es': "Skin de nave J1",
    },
    "P2 Ship Skin": {
        'pl': "Sk\u00f3rka statku G2",
        'ru': "\u0421\u043a\u0438\u043d \u043a\u043e\u0440\u0430\u0431\u043b\u044f \u04182",
        'es': "Skin de nave J2",
    },
    "Classic": {
        'pl': "Klasyczny",
        'ru': "\u041a\u043b\u0430\u0441\u0441\u0438\u0447\u0435\u0441\u043a\u0438\u0439",
        'es': "Cl\u00e1sico",
    },
    "Arrow": {
        'pl': "Strza\u0142a",
        'ru': "\u0421\u0442\u0440\u0435\u043b\u0430",
        'es': "Flecha",
    },
    "Diamond": {
        'pl': "Diament",
        'ru': "\u0410\u043b\u043c\u0430\u0437",
        'es': "Diamante",
    },
    "Falcon": {
        'pl': "Sok\u00f3\u0142",
        'ru': "\u0421\u043e\u043a\u043e\u043b",
        'es': "Halc\u00f3n",
    },
    "Co-Op (Local)": {
        'pl': "Kooperacja (lokalna)",
        'ru': "\u041a\u043e\u043e\u043f\u0435\u0440\u0430\u0442\u0438\u0432 (\u043b\u043e\u043a\u0430\u043b\u044c\u043d\u043e)",
        'es': "Cooperativo (local)",
    },
    "Host Game": {
        'pl': "Hostuj gr\u0119",
        'ru': "\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0438\u0433\u0440\u0443",
        'es': "Crear partida",
    },
    "Join Game": {
        'pl': "Do\u0142\u0105cz do gry",
        'ru': "\u041f\u0440\u0438\u0441\u043e\u0435\u0434\u0438\u043d\u0438\u0442\u044c\u0441\u044f",
        'es': "Unirse a partida",
    },
    "MULTIPLAYER": {
        'pl': "WIELOOSOBOWA",
        'ru': "\u041c\u0423\u041b\u042c\u0422\u0418\u041f\u041b\u0415\u0415\u0420",
        'es': "MULTIJUGADOR",
    },

    # ── OPTIONS ──
    "OPTIONS": {
        'pl': "OPCJE",
        'ru': "\u041d\u0410\u0421\u0422\u0420\u041e\u0419\u041a\u0418",
        'es': "OPCIONES",
    },
    "Resolution": {
        'pl': "Rozdzielczo\u015b\u0107",
        'ru': "\u0420\u0430\u0437\u0440\u0435\u0448\u0435\u043d\u0438\u0435",
        'es': "Resoluci\u00f3n",
    },
    "Fullscreen": {
        'pl': "Pe\u0142ny ekran",
        'ru': "\u041f\u043e\u043b\u043d\u044b\u0439 \u044d\u043a\u0440\u0430\u043d",
        'es': "Pantalla completa",
    },
    "Borderless Windowed": {
        'pl': "Okno bez ramki",
        'ru': "\u041e\u043a\u043d\u043e \u0431\u0435\u0437 \u0440\u0430\u043c\u043a\u0438",
        'es': "Ventana sin bordes",
    },
    "FPS Limit": {
        'pl': "Limit FPS",
        'ru': "\u041b\u0438\u043c\u0438\u0442 FPS",
        'es': "L\u00edmite de FPS",
    },
    "Show FPS": {
        'pl': "Poka\u017c FPS",
        'ru': "\u041f\u043e\u043a\u0430\u0437\u0430\u0442\u044c FPS",
        'es': "Mostrar FPS",
    },
    "Visual FX": {
        'pl': "Efekty wizualne",
        'ru': "\u0412\u0438\u0437\u0443\u0430\u043b\u044c\u043d\u044b\u0435 \u044d\u0444\u0444\u0435\u043a\u0442\u044b",
        'es': "Efectos visuales",
    },
    "Border Particles": {
        'pl': "Cz\u0105steczki kraw\u0119dzi",
        'ru': "\u0427\u0430\u0441\u0442\u0438\u0446\u044b \u0433\u0440\u0430\u043d\u0438\u0446",
        'es': "Part\u00edculas de borde",
    },
    "Speed Smear": {
        'pl': "Smuga pr\u0119dko\u015bci",
        'ru': "\u0421\u043c\u0430\u0437 \u0441\u043a\u043e\u0440\u043e\u0441\u0442\u0438",
        'es': "Estela de velocidad",
    },
    "Asteroid Speed Color": {
        'pl': "Kolor pr\u0119dko\u015bci asteroid",
        'ru': "\u0426\u0432\u0435\u0442 \u0441\u043a\u043e\u0440\u043e\u0441\u0442\u0438 \u0430\u0441\u0442\u0435\u0440\u043e\u0438\u0434\u043e\u0432",
        'es': "Color de velocidad de asteroides",
    },
    "Bloom Effect": {
        'pl': "Efekt bloom",
        'ru': "\u042d\u0444\u0444\u0435\u043a\u0442 \u0431\u043b\u0443\u043c",
        'es': "Efecto bloom",
    },
    "Audio": {
        'pl': "D\u017awi\u0119k",
        'ru': "\u0417\u0432\u0443\u043a",
        'es': "Sonido",
    },
    "Sound Effects": {
        'pl': "Efekty d\u017awi\u0119kowe",
        'ru': "\u0417\u0432\u0443\u043a\u043e\u0432\u044b\u0435 \u044d\u0444\u0444\u0435\u043a\u0442\u044b",
        'es': "Efectos de sonido",
    },
    "Music": {
        'pl': "Muzyka",
        'ru': "\u041c\u0443\u0437\u044b\u043a\u0430",
        'es': "M\u00fasica",
    },
    "Apply & Back": {
        'pl': "Zastosuj i wr\u00f3\u0107",
        'ru': "\u041f\u0440\u0438\u043c\u0435\u043d\u0438\u0442\u044c \u0438 \u043d\u0430\u0437\u0430\u0434",
        'es': "Aplicar y volver",
    },
    "Language": {
        'pl': "J\u0119zyk",
        'ru': "\u042f\u0437\u044b\u043a",
        'es': "Idioma",
    },
    "ON": {
        'pl': "W\u0141",
        'ru': "\u0412\u041a\u041b",
        'es': "S\u00cd",
    },
    "OFF": {
        'pl': "WY\u0141",
        'ru': "\u0412\u042b\u041a\u041b",
        'es': "NO",
    },
    "LEFT/RIGHT to change": {
        'pl': "LEWO/PRAWO aby zmieni\u0107",
        'ru': "\u041b\u0415\u0412\u041e/\u041f\u0420\u0410\u0412\u041e \u0434\u043b\u044f \u0441\u043c\u0435\u043d\u044b",
        'es': "IZQ/DER para cambiar",
    },
    "ENTER to toggle": {
        'pl': "ENTER aby prze\u0142\u0105czy\u0107",
        'ru': "ENTER \u0434\u043b\u044f \u043f\u0435\u0440\u0435\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u044f",
        'es': "ENTER para cambiar",
    },
    "Changes are applied when you select 'Apply & Back'.": {
        'pl': "Zmiany zostan\u0105 zastosowane po wybraniu 'Zastosuj i wr\u00f3\u0107'.",
        'ru': "\u0418\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f \u043f\u0440\u0438\u043c\u0435\u043d\u044f\u044e\u0442\u0441\u044f \u043f\u043e\u0441\u043b\u0435 '\u041f\u0440\u0438\u043c\u0435\u043d\u0438\u0442\u044c \u0438 \u043d\u0430\u0437\u0430\u0434'.",
        'es': "Los cambios se aplican al seleccionar 'Aplicar y volver'.",
    },
    "Fullscreen and Borderless are mutually exclusive.": {
        'pl': "Pe\u0142ny ekran i okno bez ramki wykluczaj\u0105 si\u0119.",
        'ru': "\u041f\u043e\u043b\u043d\u044b\u0439 \u044d\u043a\u0440\u0430\u043d \u0438 \u043e\u043a\u043d\u043e \u0431\u0435\u0437 \u0440\u0430\u043c\u043a\u0438 \u0432\u0437\u0430\u0438\u043c\u043e\u0438\u0441\u043a\u043b\u044e\u0447\u0430\u044e\u0449\u0438\u0435.",
        'es': "Pantalla completa y sin bordes son mutuamente exclusivos.",
    },
    "VSync syncs to your monitor refresh rate.": {
        'pl': "VSync synchronizuje z cz\u0119stotliwo\u015bci\u0105 monitora.",
        'ru': "VSync \u0441\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0438\u0440\u0443\u0435\u0442 \u0441 \u0447\u0430\u0441\u0442\u043e\u0442\u043e\u0439 \u043c\u043e\u043d\u0438\u0442\u043e\u0440\u0430.",
        'es': "VSync sincroniza con la frecuencia del monitor.",
    },
    "FPS Limit of 0 (Unlimited) removes the frame cap.": {
        'pl': "Limit FPS 0 (Bez limitu) zdejmuje ograniczenie klatek.",
        'ru': "\u041b\u0438\u043c\u0438\u0442 FPS 0 (\u0411\u0435\u0437 \u043b\u0438\u043c\u0438\u0442\u0430) \u0441\u043d\u0438\u043c\u0430\u0435\u0442 \u043e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d\u0438\u0435 \u043a\u0430\u0434\u0440\u043e\u0432.",
        'es': "L\u00edmite FPS 0 (Ilimitado) elimina el l\u00edmite de cuadros.",
    },
    "ESC to go back without applying": {
        'pl': "ESC aby wr\u00f3ci\u0107 bez zastosowania",
        'ru': "ESC \u0447\u0442\u043e\u0431\u044b \u0432\u0435\u0440\u043d\u0443\u0442\u044c\u0441\u044f \u0431\u0435\u0437 \u043f\u0440\u0438\u043c\u0435\u043d\u0435\u043d\u0438\u044f",
        'es': "ESC para volver sin aplicar",
    },

    # ── CONTROLS MENU ──
    "CONTROLS": {
        'pl': "STEROWANIE",
        'ru': "\u0423\u041f\u0420\u0410\u0412\u041b\u0415\u041d\u0418\u0415",
        'es': "CONTROLES",
    },
    "Keyboard P1": {
        'pl': "Klawiatura G1",
        'ru': "\u041a\u043b\u0430\u0432\u0438\u0430\u0442\u0443\u0440\u0430 \u04181",
        'es': "Teclado J1",
    },
    "Keyboard P2 (Co-op)": {
        'pl': "Klawiatura G2 (Co-op)",
        'ru': "\u041a\u043b\u0430\u0432\u0438\u0430\u0442\u0443\u0440\u0430 \u04182 (\u041a\u043e\u043e\u043f)",
        'es': "Teclado J2 (Coop)",
    },
    "Xbox Gamepad": {
        'pl': "Pad Xbox",
        'ru': "\u0413\u0435\u0439\u043c\u043f\u0430\u0434 Xbox",
        'es': "Mando Xbox",
    },
    "ACTION": {
        'pl': "AKCJA",
        'ru': "\u0414\u0415\u0419\u0421\u0422\u0412\u0418\u0415",
        'es': "ACCI\u00d3N",
    },
    "BINDING": {
        'pl': "KLAWISZ",
        'ru': "\u041a\u041b\u0410\u0412\u0418\u0428\u0410",
        'es': "TECLA",
    },
    "Thrust": {
        'pl': "Ci\u0105g",
        'ru': "\u0422\u044f\u0433\u0430",
        'es': "Empuje",
    },
    "Brake / Down": {
        'pl': "Hamulec / D\u00f3\u0142",
        'ru': "\u0422\u043e\u0440\u043c\u043e\u0437 / \u0412\u043d\u0438\u0437",
        'es': "Freno / Abajo",
    },
    "Rotate Left": {
        'pl': "Obr\u00f3t w lewo",
        'ru': "\u041f\u043e\u0432\u043e\u0440\u043e\u0442 \u0432\u043b\u0435\u0432\u043e",
        'es': "Girar izquierda",
    },
    "Rotate Right": {
        'pl': "Obr\u00f3t w prawo",
        'ru': "\u041f\u043e\u0432\u043e\u0440\u043e\u0442 \u0432\u043f\u0440\u0430\u0432\u043e",
        'es': "Girar derecha",
    },
    "Shoot": {
        'pl': "Strza\u0142",
        'ru': "\u0412\u044b\u0441\u0442\u0440\u0435\u043b",
        'es': "Disparar",
    },
    "Alt Brake": {
        'pl': "Alt. hamulec",
        'ru': "\u0410\u043b\u044c\u0442. \u0442\u043e\u0440\u043c\u043e\u0437",
        'es': "Freno alt.",
    },
    "Gravity Bomb": {
        'pl': "Bomba graw.",
        'ru': "\u0413\u0440\u0430\u0432. \u0431\u043e\u043c\u0431\u0430",
        'es': "Bomba grav.",
    },
    "Hyperspace": {
        'pl': "Nadprzestrze\u0144",
        'ru': "\u0413\u0438\u043f\u0435\u0440\u043f\u0440\u043e\u0441\u0442\u0440\u0430\u043d\u0441\u0442\u0432\u043e",
        'es': "Hiperespacio",
    },
    "Strafe Left": {
        'pl': "Unik w lewo",
        'ru': "\u0421\u0442\u0440\u0435\u0439\u0444 \u0432\u043b\u0435\u0432\u043e",
        'es': "Esquivar izq.",
    },
    "Strafe Right": {
        'pl': "Unik w prawo",
        'ru': "\u0421\u0442\u0440\u0435\u0439\u0444 \u0432\u043f\u0440\u0430\u0432\u043e",
        'es': "Esquivar der.",
    },
    "Reset Defaults": {
        'pl': "Przywr\u00f3\u0107 domy\u015blne",
        'ru': "\u0421\u0431\u0440\u043e\u0441\u0438\u0442\u044c",
        'es': "Restablecer",
    },
    "Save & Back": {
        'pl': "Zapisz i wr\u00f3\u0107",
        'ru': "\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c \u0438 \u043d\u0430\u0437\u0430\u0434",
        'es': "Guardar y volver",
    },
    "TAB to switch section": {
        'pl': "TAB aby zmieni\u0107 sekcj\u0119",
        'ru': "TAB \u0434\u043b\u044f \u0441\u043c\u0435\u043d\u044b \u0441\u0435\u043a\u0446\u0438\u0438",
        'es': "TAB para cambiar secci\u00f3n",
    },
    ">> Press a key... <<": {
        'pl': ">> Naci\u015bnij klawisz... <<",
        'ru': ">> \u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u043a\u043b\u0430\u0432\u0438\u0448\u0443... <<",
        'es': ">> Pulsa una tecla... <<",
    },
    ">> Press a button... <<": {
        'pl': ">> Naci\u015bnij przycisk... <<",
        'ru': ">> \u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u043a\u043d\u043e\u043f\u043a\u0443... <<",
        'es': ">> Pulsa un bot\u00f3n... <<",
    },
    "Click an action or press ENTER to rebind. ESC to cancel.": {
        'pl': "Kliknij akcj\u0119 lub ENTER aby zmieni\u0107. ESC anuluje.",
        'ru': "\u041d\u0430\u0436\u043c\u0438\u0442\u0435 ENTER \u0434\u043b\u044f \u0441\u043c\u0435\u043d\u044b. ESC \u0434\u043b\u044f \u043e\u0442\u043c\u0435\u043d\u044b.",
        'es': "Pulsa ENTER para reasignar. ESC para cancelar.",
    },
    "ESC to go back without saving.": {
        'pl': "ESC aby wr\u00f3ci\u0107 bez zapisu.",
        'ru': "ESC \u0447\u0442\u043e\u0431\u044b \u0432\u0435\u0440\u043d\u0443\u0442\u044c\u0441\u044f \u0431\u0435\u0437 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u044f.",
        'es': "ESC para volver sin guardar.",
    },

    # ── HUD ──
    "SCORE: {score}": {
        'pl': "WYNIK: {score}",
        'ru': "\u0421\u0427\u0401\u0422: {score}",
        'es': "PUNTOS: {score}",
    },
    "WAVE {wave}  [{topo}]": {
        'pl': "FALA {wave}  [{topo}]",
        'ru': "\u0412\u041e\u041b\u041d\u0410 {wave}  [{topo}]",
        'es': "OLEADA {wave}  [{topo}]",
    },
    "SECTOR {num}: {name}": {
        'pl': "SEKTOR {num}: {name}",
        'ru': "\u0421\u0415\u041a\u0422\u041e\u0420 {num}: {name}",
        'es': "SECTOR {num}: {name}",
    },
    "HEAT": {
        'pl': "TEMP",
        'ru': "\u041d\u0410\u0413\u0420\u0415\u0412",
        'es': "CALOR",
    },
    "OVERHEAT!": {
        'pl': "PRZEGRZANIE!",
        'ru': "\u041f\u0415\u0420\u0415\u0413\u0420\u0415\u0412!",
        'es': "SOBRECALENT.!",
    },
    "MODULES:": {
        'pl': "MODU\u0141Y:",
        'ru': "\u041c\u041e\u0414\u0423\u041b\u0418:",
        'es': "M\u00d3DULOS:",
    },
    "PERKS:": {
        'pl': "PERKI:",
        'ru': "\u041f\u0415\u0420\u041a\u0418:",
        'es': "MEJORAS:",
    },
    "SHIELD x{n}": {
        'pl': "TARCZA x{n}",
        'ru': "\u0429\u0418\u0422 x{n}",
        'es': "ESCUDO x{n}",
    },
    "[CO-OP] Local": {
        'pl': "[CO-OP] Lokalny",
        'ru': "[\u041a\u041e\u041e\u041f] \u041b\u043e\u043a\u0430\u043b\u044c\u043d\u043e",
        'es': "[COOP] Local",
    },
    "[HOST] Multiplayer": {
        'pl': "[HOST] Wieloosobowa",
        'ru': "[\u0425\u041e\u0421\u0422] \u041c\u0443\u043b\u044c\u0442\u0438\u043f\u043b\u0435\u0435\u0440",
        'es': "[HOST] Multijugador",
    },
    "[CLIENT] Multiplayer": {
        'pl': "[KLIENT] Wieloosobowa",
        'ru': "[\u041a\u041b\u0418\u0415\u041d\u0422] \u041c\u0443\u043b\u044c\u0442\u0438\u043f\u043b\u0435\u0435\u0440",
        'es': "[CLIENTE] Multijugador",
    },
    "DEAD": {
        'pl': "MARTWY",
        'ru': "\u041c\u0401\u0420\u0422\u0412",
        'es': "MUERTO",
    },
    "SPECTATING": {
        'pl': "OBSERWACJA",
        'ru': "\u041d\u0410\u0411\u041b\u042e\u0414\u0415\u041d\u0418\u0415",
        'es': "ESPECTADOR",
    },
    "Respawn at wave clear": {
        'pl': "Odrodzenie po fali",
        'ru': "\u0412\u043e\u0437\u0440\u043e\u0436\u0434\u0435\u043d\u0438\u0435 \u043f\u043e\u0441\u043b\u0435 \u0432\u043e\u043b\u043d\u044b",
        'es': "Reaparici\u00f3n tras oleada",
    },
    "Respawn at {score} pts": {
        'pl': "Odrodzenie przy {score} pkt",
        'ru': "\u0412\u043e\u0437\u0440\u043e\u0436\u0434\u0435\u043d\u0438\u0435 \u043f\u0440\u0438 {score} \u043e\u0447\u043a.",
        'es': "Reaparici\u00f3n a {score} pts",
    },
    "Respawn in {time}s": {
        'pl': "Odrodzenie za {time}s",
        'ru': "\u0412\u043e\u0437\u0440\u043e\u0436\u0434\u0435\u043d\u0438\u0435 \u0447\u0435\u0440\u0435\u0437 {time}\u0441",
        'es': "Reaparici\u00f3n en {time}s",
    },
    "SEED: {seed}": {
        'pl': "SEED: {seed}",
        'ru': "\u0421\u0418\u0414: {seed}",
        'es': "SEMILLA: {seed}",
    },
    "COMBO x{combo}  (x{mult})": {
        'pl': "COMBO x{combo}  (x{mult})",
        'ru': "\u041a\u041e\u041c\u0411\u041e x{combo}  (x{mult})",
        'es': "COMBO x{combo}  (x{mult})",
    },
    "WRAP x{mult}": {
        'pl': "WRAP x{mult}",
        'ru': "WRAP x{mult}",
        'es': "WRAP x{mult}",
    },

    # ── GAME OVER ──
    "GAME OVER": {
        'pl': "KONIEC GRY",
        'ru': "\u041a\u041e\u041d\u0415\u0426 \u0418\u0413\u0420\u042b",
        'es': "FIN DEL JUEGO",
    },
    "Final Score: {score}": {
        'pl': "Wynik ko\u0144cowy: {score}",
        'ru': "\u0418\u0442\u043e\u0433\u043e\u0432\u044b\u0439 \u0441\u0447\u0451\u0442: {score}",
        'es': "Puntuaci\u00f3n final: {score}",
    },
    "Wave: {wave}": {
        'pl': "Fala: {wave}",
        'ru': "\u0412\u043e\u043b\u043d\u0430: {wave}",
        'es': "Oleada: {wave}",
    },
    "Perks: {n}": {
        'pl': "Perki: {n}",
        'ru': "\u041f\u0435\u0440\u043a\u0438: {n}",
        'es': "Mejoras: {n}",
    },
    "Seed: {seed}": {
        'pl': "Seed: {seed}",
        'ru': "\u0421\u0438\u0434: {seed}",
        'es': "Semilla: {seed}",
    },
    "Score: {score}   Wave: {wave}": {
        'pl': "Wynik: {score}   Fala: {wave}",
        'ru': "\u0421\u0447\u0451\u0442: {score}   \u0412\u043e\u043b\u043d\u0430: {wave}",
        'es': "Puntos: {score}   Oleada: {wave}",
    },
    "NEW HIGH SCORE!": {
        'pl': "NOWY REKORD!",
        'ru': "\u041d\u041e\u0412\u042b\u0419 \u0420\u0415\u041a\u041e\u0420\u0414!",
        'es': "\u00a1NUEVA PUNTUACI\u00d3N!",
    },
    "Enter your name:": {
        'pl': "Wpisz swoje imi\u0119:",
        'ru': "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0438\u043c\u044f:",
        'es': "Introduce tu nombre:",
    },
    "ENTER to confirm  |  ESC to skip": {
        'pl': "ENTER potwierd\u017a  |  ESC pomi\u0144",
        'ru': "ENTER \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c  |  ESC \u043f\u0440\u043e\u043f\u0443\u0441\u0442\u0438\u0442\u044c",
        'es': "ENTER confirmar  |  ESC saltar",
    },

    # ── PERK SELECTION ──
    "WAVE CLEARED - CHOOSE A PERK": {
        'pl': "FALA UKO\u0143CZONA - WYBIERZ PERK",
        'ru': "\u0412\u041e\u041b\u041d\u0410 \u041f\u0420\u041e\u0419\u0414\u0415\u041d\u0410 - \u0412\u042b\u0411\u0415\u0420\u0418\u0422\u0415 \u041f\u0415\u0420\u041a",
        'es': "OLEADA SUPERADA - ELIGE UNA MEJORA",
    },
    "MUTATION": {
        'pl': "MUTACJA",
        'ru': "\u041c\u0423\u0422\u0410\u0426\u0418\u042f",
        'es': "MUTACI\u00d3N",
    },
    "(OWNED)": {
        'pl': "(POSIADANY)",
        'ru': "(\u0415\u0421\u0422\u042c)",
        'es': "(ADQUIRIDA)",
    },

    # ── HIGH SCORES ──
    "HIGH SCORES": {
        'pl': "NAJLEPSZE WYNIKI",
        'ru': "\u0420\u0415\u041a\u041e\u0420\u0414\u042b",
        'es': "MEJORES PUNTUACIONES",
    },
    "NAME": {
        'pl': "NAZWA",
        'ru': "\u0418\u041c\u042f",
        'es': "NOMBRE",
    },
    "SCORE": {
        'pl': "WYNIK",
        'ru': "\u0421\u0427\u0401\u0422",
        'es': "PUNTOS",
    },
    "WAVE": {
        'pl': "FALA",
        'ru': "\u0412\u041e\u041b\u041d\u0410",
        'es': "OLEADA",
    },
    "MODE": {
        'pl': "TRYB",
        'ru': "\u0420\u0415\u0416\u0418\u041c",
        'es': "MODO",
    },
    "DATE": {
        'pl': "DATA",
        'ru': "\u0414\u0410\u0422\u0410",
        'es': "FECHA",
    },
    "No scores yet. Play a game!": {
        'pl': "Brak wynik\u00f3w. Zagraj!",
        'ru': "\u041d\u0435\u0442 \u0440\u0435\u043a\u043e\u0440\u0434\u043e\u0432. \u0421\u044b\u0433\u0440\u0430\u0439\u0442\u0435!",
        'es': "\u00a1Sin puntuaciones. Juega una partida!",
    },
    "Press ESC or ENTER to go back": {
        'pl': "ESC lub ENTER aby wr\u00f3ci\u0107",
        'ru': "ESC \u0438\u043b\u0438 ENTER \u0434\u043b\u044f \u0432\u043e\u0437\u0432\u0440\u0430\u0442\u0430",
        'es': "ESC o ENTER para volver",
    },

    # ── SEEDED RUN ──
    "SEEDED RUN": {
        'pl': "GRA Z SEEDEM",
        'ru': "\u0418\u0413\u0420\u0410 \u0421 \u0421\u0418\u0414\u041e\u041c",
        'es': "PARTIDA CON SEMILLA",
    },
    "Enter a seed for a deterministic run.": {
        'pl': "Wpisz seed dla deterministycznej gry.",
        'ru': "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u0438\u0434 \u0434\u043b\u044f \u0434\u0435\u0442\u0435\u0440\u043c\u0438\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u043e\u0439 \u0438\u0433\u0440\u044b.",
        'es': "Introduce una semilla para una partida determinista.",
    },
    "Same seed = same asteroid spawns, events, and layout.": {
        'pl': "Ten sam seed = te same asteroidy, eventy i uk\u0142ad.",
        'ru': "\u041e\u0434\u0438\u043d \u0441\u0438\u0434 = \u0442\u0435 \u0436\u0435 \u0430\u0441\u0442\u0435\u0440\u043e\u0438\u0434\u044b, \u0441\u043e\u0431\u044b\u0442\u0438\u044f \u0438 \u043a\u0430\u0440\u0442\u0430.",
        'es': "Misma semilla = mismos asteroides, eventos y mapa.",
    },
    "ENTER to start  |  R for random seed  |  ESC to go back": {
        'pl': "ENTER start  |  R losowy seed  |  ESC powr\u00f3t",
        'ru': "ENTER \u0441\u0442\u0430\u0440\u0442  |  R \u0441\u043b\u0443\u0447\u0430\u0439\u043d\u044b\u0439 \u0441\u0438\u0434  |  ESC \u043d\u0430\u0437\u0430\u0434",
        'es': "ENTER iniciar  |  R semilla aleatoria  |  ESC volver",
    },

    # ── SERVER CREATOR / CO-OP ──
    "SERVER CREATOR": {
        'pl': "TWORZENIE SERWERA",
        'ru': "\u0421\u041e\u0417\u0414\u0410\u041d\u0418\u0415 \u0421\u0415\u0420\u0412\u0415\u0420\u0410",
        'es': "CREAR SERVIDOR",
    },
    "--- Configure your game ---": {
        'pl': "--- Skonfiguruj gr\u0119 ---",
        'ru': "--- \u041d\u0430\u0441\u0442\u0440\u043e\u0439\u0442\u0435 \u0438\u0433\u0440\u0443 ---",
        'es': "--- Configura tu partida ---",
    },
    "Port": {
        'pl': "Port",
        'ru': "\u041f\u043e\u0440\u0442",
        'es': "Puerto",
    },
    "Max Players": {
        'pl': "Maks. graczy",
        'ru': "\u041c\u0430\u043a\u0441. \u0438\u0433\u0440\u043e\u043a\u043e\u0432",
        'es': "M\u00e1x. jugadores",
    },
    "Shared Map": {
        'pl': "Wsp\u00f3lna mapa",
        'ru': "\u041e\u0431\u0449\u0430\u044f \u043a\u0430\u0440\u0442\u0430",
        'es': "Mapa compartido",
    },
    "Respawn Mode": {
        'pl': "Tryb odrodzenia",
        'ru': "\u0420\u0435\u0436\u0438\u043c \u0432\u043e\u0437\u0440\u043e\u0436\u0434\u0435\u043d\u0438\u044f",
        'es': "Modo de reaparici\u00f3n",
    },
    "Starting Wave": {
        'pl': "Fala startowa",
        'ru': "\u041d\u0430\u0447\u0430\u043b\u044c\u043d\u0430\u044f \u0432\u043e\u043b\u043d\u0430",
        'es': "Oleada inicial",
    },
    "Starting Sector": {
        'pl': "Sektor startowy",
        'ru': "\u041d\u0430\u0447\u0430\u043b\u044c\u043d\u044b\u0439 \u0441\u0435\u043a\u0442\u043e\u0440",
        'es': "Sector inicial",
    },
    "Starting Lives": {
        'pl': "\u017bycia startowe",
        'ru': "\u041d\u0430\u0447\u0430\u043b\u044c\u043d\u044b\u0435 \u0436\u0438\u0437\u043d\u0438",
        'es': "Vidas iniciales",
    },
    "Asteroid Count": {
        'pl': "Ilo\u015b\u0107 asteroid",
        'ru': "\u041a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e \u0430\u0441\u0442\u0435\u0440\u043e\u0438\u0434\u043e\u0432",
        'es': "N\u00fam. de asteroides",
    },
    "Boss Waves": {
        'pl': "Fale boss\u00f3w",
        'ru': "\u0412\u043e\u043b\u043d\u044b \u0431\u043e\u0441\u0441\u043e\u0432",
        'es': "Oleadas de jefes",
    },
    "UFO Spawns": {
        'pl': "Pojawianie UFO",
        'ru': "\u041f\u043e\u044f\u0432\u043b\u0435\u043d\u0438\u0435 UFO",
        'es': "Aparici\u00f3n de OVNIs",
    },
    "Wave Events": {
        'pl': "Eventy fali",
        'ru': "\u0421\u043e\u0431\u044b\u0442\u0438\u044f \u0432\u043e\u043b\u043d\u044b",
        'es': "Eventos de oleada",
    },
    "Starting Modules": {
        'pl': "Modu\u0142y startowe",
        'ru': "\u041d\u0430\u0447\u0430\u043b\u044c\u043d\u044b\u0435 \u043c\u043e\u0434\u0443\u043b\u0438",
        'es': "M\u00f3dulos iniciales",
    },
    "--- START SERVER ---": {
        'pl': "--- URUCHOM SERWER ---",
        'ru': "--- \u0417\u0410\u041f\u0423\u0421\u0422\u0418\u0422\u042c \u0421\u0415\u0420\u0412\u0415\u0420 ---",
        'es': "--- INICIAR SERVIDOR ---",
    },
    "Wave Clear": {
        'pl': "Koniec fali",
        'ru': "\u041a\u043e\u043d\u0435\u0446 \u0432\u043e\u043b\u043d\u044b",
        'es': "Fin de oleada",
    },
    "Score (10K pts)": {
        'pl': "Wynik (10K pkt)",
        'ru': "\u0421\u0447\u0451\u0442 (10K \u043e\u0447\u043a.)",
        'es': "Puntos (10K pts)",
    },
    "Timer (2 min)": {
        'pl': "Timer (2 min)",
        'ru': "\u0422\u0430\u0439\u043c\u0435\u0440 (2 \u043c\u0438\u043d)",
        'es': "Temporizador (2 min)",
    },
    "CO-OP (LOCAL)": {
        'pl': "CO-OP (LOKALNY)",
        'ru': "\u041a\u041e\u041e\u041f (\u041b\u041e\u041a\u0410\u041b\u042c\u041d\u042b\u0419)",
        'es': "COOPERATIVO (LOCAL)",
    },
    "--- Configure your local game ---": {
        'pl': "--- Skonfiguruj lokaln\u0105 gr\u0119 ---",
        'ru': "--- \u041d\u0430\u0441\u0442\u0440\u043e\u0439\u0442\u0435 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u0443\u044e \u0438\u0433\u0440\u0443 ---",
        'es': "--- Configura tu partida local ---",
    },
    "P1 Name": {
        'pl': "Nazwa G1",
        'ru': "\u0418\u043c\u044f \u04181",
        'es': "Nombre J1",
    },
    "P1 Ship Color": {
        'pl': "Kolor statku G1",
        'ru': "\u0426\u0432\u0435\u0442 \u043a\u043e\u0440\u0430\u0431\u043b\u044f \u04181",
        'es': "Color nave J1",
    },
    "P2 Name": {
        'pl': "Nazwa G2",
        'ru': "\u0418\u043c\u044f \u04182",
        'es': "Nombre J2",
    },
    "P2 Ship Color": {
        'pl': "Kolor statku G2",
        'ru': "\u0426\u0432\u0435\u0442 \u043a\u043e\u0440\u0430\u0431\u043b\u044f \u04182",
        'es': "Color nave J2",
    },
    "P2 Controls": {
        'pl': "Sterowanie G2",
        'ru': "\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435 \u04182",
        'es': "Controles J2",
    },
    "--- START CO-OP ---": {
        'pl': "--- ROZPOCZNIJ CO-OP ---",
        'ru': "--- \u041d\u0410\u0427\u0410\u0422\u042c \u041a\u041e\u041e\u041f ---",
        'es': "--- INICIAR COOPERATIVO ---",
    },
    "Keyboard (WASD+JKLH)": {
        'pl': "Klawiatura (WASD+JKLH)",
        'ru': "\u041a\u043b\u0430\u0432\u0438\u0430\u0442\u0443\u0440\u0430 (WASD+JKLH)",
        'es': "Teclado (WASD+JKLH)",
    },

    # ── LOBBY ──
    "GAME LOBBY": {
        'pl': "LOBBY GRY",
        'ru': "\u041b\u041e\u0411\u0411\u0418 \u0418\u0413\u0420\u042b",
        'es': "SALA DE ESPERA",
    },
    "--- PLAYERS ---": {
        'pl': "--- GRACZE ---",
        'ru': "--- \u0418\u0413\u0420\u041e\u041a\u0418 ---",
        'es': "--- JUGADORES ---",
    },
    "ALL PLAYERS READY!  Press ENTER or SPACE to start": {
        'pl': "WSZYSCY GOTOWI!  ENTER lub SPACJA aby zacz\u0105\u0107",
        'ru': "\u0412\u0421\u0415 \u0413\u041e\u0422\u041e\u0412\u042b!  ENTER \u0438\u043b\u0438 \u041f\u0420\u041e\u0411\u0415\u041b \u0434\u043b\u044f \u0441\u0442\u0430\u0440\u0442\u0430",
        'es': "\u00a1TODOS LISTOS!  Pulsa ENTER o ESPACIO para empezar",
    },
    "Waiting for players to ready up...": {
        'pl': "Oczekiwanie na gotowo\u015b\u0107 graczy...",
        'ru': "\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435 \u0433\u043e\u0442\u043e\u0432\u043d\u043e\u0441\u0442\u0438 \u0438\u0433\u0440\u043e\u043a\u043e\u0432...",
        'es': "Esperando a que los jugadores est\u00e9n listos...",
    },
    "Failed to start server.": {
        'pl': "Nie uda\u0142o si\u0119 uruchomi\u0107 serwera.",
        'ru': "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0437\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u044c \u0441\u0435\u0440\u0432\u0435\u0440.",
        'es': "Error al iniciar el servidor.",
    },
    "ESC = cancel": {
        'pl': "ESC = anuluj",
        'ru': "ESC = \u043e\u0442\u043c\u0435\u043d\u0430",
        'es': "ESC = cancelar",
    },
    "JOIN GAME": {
        'pl': "DO\u0141\u0104CZ DO GRY",
        'ru': "\u041f\u0420\u0418\u0421\u041e\u0415\u0414\u0418\u041d\u0418\u0422\u042c\u0421\u042f",
        'es': "UNIRSE A PARTIDA",
    },
    "--- LAN Servers ---": {
        'pl': "--- Serwery LAN ---",
        'ru': "--- \u0421\u0435\u0440\u0432\u0435\u0440\u044b LAN ---",
        'es': "--- Servidores LAN ---",
    },
    "Searching for games on LAN...": {
        'pl': "Szukanie gier w sieci LAN...",
        'ru': "\u041f\u043e\u0438\u0441\u043a \u0438\u0433\u0440 \u0432 \u0441\u0435\u0442\u0438 LAN...",
        'es': "Buscando partidas en LAN...",
    },
    "Enter IP manually...": {
        'pl': "Wpisz IP r\u0119cznie...",
        'ru': "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 IP \u0432\u0440\u0443\u0447\u043d\u0443\u044e...",
        'es': "Introducir IP manualmente...",
    },
    "Enter host IP (or IP:port):": {
        'pl': "Wpisz IP hosta (lub IP:port):",
        'ru': "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 IP \u0445\u043e\u0441\u0442\u0430 (IP:\u043f\u043e\u0440\u0442):",
        'es': "Introduce IP del host (o IP:puerto):",
    },
    "ENTER to connect  |  ESC to cancel": {
        'pl': "ENTER po\u0142\u0105cz  |  ESC anuluj",
        'ru': "ENTER \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0438\u0442\u044c\u0441\u044f  |  ESC \u043e\u0442\u043c\u0435\u043d\u0430",
        'es': "ENTER conectar  |  ESC cancelar",
    },
    "ESC to go back  |  UP/DOWN to select  |  ENTER to join": {
        'pl': "ESC wr\u00f3\u0107  |  G\u00d3RA/D\u00d3\u0141 wybierz  |  ENTER do\u0142\u0105cz",
        'ru': "ESC \u043d\u0430\u0437\u0430\u0434  |  \u0412\u0412\u0415\u0420\u0425/\u0412\u041d\u0418\u0417 \u0432\u044b\u0431\u043e\u0440  |  ENTER \u0432\u043e\u0439\u0442\u0438",
        'es': "ESC volver  |  ARRIBA/ABAJO elegir  |  ENTER unirse",
    },
    "Waiting for lobby info...": {
        'pl': "Oczekiwanie na info lobby...",
        'ru': "\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435 \u0434\u0430\u043d\u043d\u044b\u0445 \u043b\u043e\u0431\u0431\u0438...",
        'es': "Esperando info del lobby...",
    },
    "You are READY!  (ENTER to unready)": {
        'pl': "JESTE\u015a GOTOWY!  (ENTER aby odwo\u0142a\u0107)",
        'ru': "\u0412\u042b \u0413\u041e\u0422\u041e\u0412\u042b!  (ENTER \u0434\u043b\u044f \u043e\u0442\u043c\u0435\u043d\u044b)",
        'es': "\u00a1EST\u00c1S LISTO!  (ENTER para cancelar)",
    },
    "Press ENTER or SPACE to READY UP": {
        'pl': "ENTER lub SPACJA aby si\u0119 przygotowa\u0107",
        'ru': "ENTER \u0438\u043b\u0438 \u041f\u0420\u041e\u0411\u0415\u041b \u0434\u043b\u044f \u0433\u043e\u0442\u043e\u0432\u043d\u043e\u0441\u0442\u0438",
        'es': "Pulsa ENTER o ESPACIO para PREPARARTE",
    },
    "Waiting for host to start the game...": {
        'pl': "Oczekiwanie na start gry przez hosta...",
        'ru': "\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435 \u0441\u0442\u0430\u0440\u0442\u0430 \u043e\u0442 \u0445\u043e\u0441\u0442\u0430...",
        'es': "Esperando a que el host inicie la partida...",
    },
    "ESC = disconnect": {
        'pl': "ESC = roz\u0142\u0105cz",
        'ru': "ESC = \u043e\u0442\u043a\u043b\u044e\u0447\u0438\u0442\u044c\u0441\u044f",
        'es': "ESC = desconectar",
    },

    # ── PORTAL EFFECTS ──
    "WARP": {
        'pl': "WARP",
        'ru': "\u0412\u0410\u0420\u041f",
        'es': "SALTO",
    },
    "TWIST": {
        'pl': "SKRR\u0118T",
        'ru': "\u0412\u0418\u0420\u0410\u0416",
        'es': "GIRO",
    },
    "FLIP": {
        'pl': "ODWR\u00d3T",
        'ru': "\u041f\u0415\u0420\u0415\u0412\u041e\u0420\u041e\u0422",
        'es': "VOLTERETA",
    },
    "SLOW": {
        'pl': "WOLNO",
        'ru': "\u041c\u0415\u0414\u041b.",
        'es': "LENTO",
    },
    "FAST": {
        'pl': "SZYBKO",
        'ru': "\u0411\u042b\u0421\u0422\u0420.",
        'es': "R\u00c1PIDO",
    },

    # ── SHIP COLORS ──
    "White": {
        'pl': "Bia\u0142y",
        'ru': "\u0411\u0435\u043b\u044b\u0439",
        'es': "Blanco",
    },
    "Red": {
        'pl': "Czerwony",
        'ru': "\u041a\u0440\u0430\u0441\u043d\u044b\u0439",
        'es': "Rojo",
    },
    "Blue": {
        'pl': "Niebieski",
        'ru': "\u0421\u0438\u043d\u0438\u0439",
        'es': "Azul",
    },
    "Green": {
        'pl': "Zielony",
        'ru': "\u0417\u0435\u043b\u0451\u043d\u044b\u0439",
        'es': "Verde",
    },
    "Yellow": {
        'pl': "\u017b\u00f3\u0142ty",
        'ru': "\u0416\u0451\u043b\u0442\u044b\u0439",
        'es': "Amarillo",
    },
    "Purple": {
        'pl': "Fioletowy",
        'ru': "\u0424\u0438\u043e\u043b\u0435\u0442\u043e\u0432\u044b\u0439",
        'es': "Morado",
    },
    "Cyan": {
        'pl': "B\u0142\u0119kitny",
        'ru': "\u0413\u043e\u043b\u0443\u0431\u043e\u0439",
        'es': "Cian",
    },
    "Orange": {
        'pl': "Pomara\u0144czowy",
        'ru': "\u041e\u0440\u0430\u043d\u0436\u0435\u0432\u044b\u0439",
        'es': "Naranja",
    },
    "Pink": {
        'pl': "R\u00f3\u017cowy",
        'ru': "\u0420\u043e\u0437\u043e\u0432\u044b\u0439",
        'es': "Rosa",
    },

    # ── MISC ──
    "SINGLEPLAYER": {
        'pl': "JEDNOOSOBOWA",
        'ru': "\u041e\u0414\u0418\u041d\u041e\u0427\u041d\u0410\u042f",
        'es': "UN JUGADOR",
    },
    "MAIN": {
        'pl': "MENU",
        'ru': "\u041c\u0415\u041d\u042e",
        'es': "MEN\u00da",
    },
    "Restart": {
        'pl': "Od nowa",
        'ru': "\u041f\u0435\u0440\u0435\u0437\u0430\u043f\u0443\u0441\u043a",
        'es': "Reiniciar",
    },
    "VSync": {
        'pl': "VSync",
        'ru': "VSync",
        'es': "VSync",
    },
    "--- SINGLE PLAYER ---": {
        'pl': "--- GRA JEDNOOSOBOWA ---",
        'ru': "--- \u041e\u0414\u0418\u041d\u041e\u0427\u041d\u0410\u042f \u0418\u0413\u0420\u0410 ---",
        'es': "--- UN JUGADOR ---",
    },
}
