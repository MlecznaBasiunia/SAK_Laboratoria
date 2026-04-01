# ---- Ekran ----
SCREEN_W = 1200
SCREEN_H = 800

# ---- Statek ----
THRUST = 300.0       # siła ciągu – wyraźne przyspieszenie bez natychmiastowości
FRICTION = 80.0      # tarcie addytywne – zatrzymanie po ~2-3 s dryfu
ROT_SPEED = 4.0      # prędkość kątowa statku (rad/s) – pełny obrót w ~1.5 s
MAX_SPEED = 350.0    # limit prędkości statku
BRAKE_FORCE = 600.0  # hamulec awaryjny – ~4x silniejszy od tarcia

# Wierzchołki statku (nos = -Y)
SHIP_VERTS = [(0, -18), (-12, 12), (12, 12)]
SHIP_SIZE = 18       # promień bounding do ghost rendering

# Płomień
FLAME_VERTS = [(-7, 12), (0, 28), (7, 12)]

# ---- Asteroidy (Zadanie **) ----
# Trzy klasy rozmiarów: (promień, min_speed, max_speed, num_verts)
ASTEROID_SIZES = {
    "large":  (45, 30, 70, 11),
    "medium": (25, 50, 120, 9),
    "small":  (12, 80, 180, 7),
}
ASTEROID_JITTER = 0.4     # zakres losowego przesunięcia promienia wierzchołka (±40%)
ASTEROID_ROT_MIN = 0.3    # min prędkość kątowa asteroidy (rad/s)
ASTEROID_ROT_MAX = 1.5    # max prędkość kątowa asteroidy (rad/s)
ASTEROID_COUNT = 8        # ile asteroid na starcie

DEBUG = False
