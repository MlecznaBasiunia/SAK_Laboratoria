# ---- Ekran ----
SCREEN_W = 800
SCREEN_H = 600
TARGET_FPS = 60

# ---- Statek ----
THRUST = 300.0
FRICTION = 80.0
ROT_SPEED = 4.0
MAX_SPEED = 350.0
BRAKE_FORCE = 600.0

SHIP_VERTS = [(0, -18), (-12, 12), (12, 12)]
SHIP_SIZE = 18
SHIP_RADIUS = 14
FLAME_VERTS = [(-7, 12), (0, 28), (7, 12)]

# ---- Asteroidy: trzy poziomy ----
# level: (radius, speed_min, speed_max, num_verts, score_value)
ASTEROID_LEVELS = {
    3: (45, 30,  70,  11, 20),   # duża – wolna, mało punktów
    2: (25, 60,  130, 9,  50),   # średnia
    1: (12, 100, 200, 7,  100),  # mała – szybka, dużo punktów
}
ASTEROID_JITTER = 0.4
ASTEROID_ROT_MIN = 0.3
ASTEROID_ROT_MAX = 1.5

# ---- Fale ----
WAVE_INITIAL = 4         # asteroid w pierwszej fali (wszystkie level 3)
WAVE_INCREMENT = 1       # +1 asteroida co falę
WAVE_DELAY = 2.0         # sekundy przerwy między falami

# ---- Pociski ----
BULLET_SPEED = 600.0
BULLET_TTL = 1.2
BULLET_RADIUS = 2
BULLET_LIMIT = 5

# ---- Eksplozja ----
EXPLOSION_DURATION = 0.4
EXPLOSION_SCALE = 1.8

# ---- Tło ----
STARS_COUNT = 120

# ---- HUD ----
HUD_FONT = 22
HUD_MARGIN = 12
TITLE_FONT = 56
SUBTITLE_FONT = 24

# ---- Zasoby ----
SOUND_SHOOT = "assets/shoot.wav"
SOUND_EXPLODE = "assets/explode.wav"
TEXTURE_STARS = "assets/stars.png"
SCORES_FILE = "scores.txt"

# ---- Klawisze ----
KEY_LEFT = 263
KEY_RIGHT = 262
KEY_UP = 265
KEY_Z = 90
KEY_SPACE = 32
KEY_ENTER = 257
KEY_R = 82
KEY_ESC = 256

DEBUG = False
