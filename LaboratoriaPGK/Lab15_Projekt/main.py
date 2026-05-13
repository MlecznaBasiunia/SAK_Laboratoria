import math
import random
import hashlib
import json
import os
import threading
import time as _time
from raylib import rl, colors, ffi
from config import (SCREEN_W, SCREEN_H, ASTEROID_COUNT, ASTEROID_POINTS,
                    POWERUP_DROP_CHANCE, START_LIVES, COMBO_TIMEOUT,
                    SHAKE_DECAY, UFO_SPAWN_INTERVAL_MIN, UFO_SPAWN_INTERVAL_MAX,
                    PORTAL_SPAWN_INTERVAL_MIN, PORTAL_SPAWN_INTERVAL_MAX,
                    GRAV_WELL_SPAWN_INTERVAL_MIN, GRAV_WELL_SPAWN_INTERVAL_MAX,
                    GRAV_WELL_CORE_RADIUS, GRAVITY_BOMB_RADIUS, GRAVITY_BOMB_STRENGTH,
                    GRAVITY_BOMB_DURATION, WAVE_EVENT_INTERVAL_MIN,
                    WAVE_EVENT_INTERVAL_MAX, WAVE_EVENT_DURATION,
                    VELOCITY_SCORE_BONUS, DISTANCE_SCORE_BONUS, SWARM_COUNT,
                    WRAP_SCORE_PER_WRAP, WRAP_SCORE_DECAY,
                    BOSS_WAVE_INTERVAL, TOPOLOGY_NAMES,
                    HEAT_TRAIL_DAMAGE_RADIUS, CRYSTAL_HP, CRYSTAL_POINTS_MULT,
                    MAX_SPEED,
                    MP_RESPAWN_SCORE, MP_RESPAWN_TIMER, MP_RESPAWN_MODES)
from ship import Ship, SHIP_SKINS, SKIN_NAMES
from asteroid import (Asteroid, spawn_asteroids, spawn_swarm,
                      FACTION_ATTRACT, FACTION_REPEL)
from particle import (explosion, thrust_particles, portal_particles,
                      gravity_well_particles, chain_explosion, warp_flash,
                      heat_trail, topology_border_particle, smear_particles)
from powerup import maybe_spawn_powerup, PowerUp, POWERUP_TYPES
from ufo import UFO
from portal import Portal, spawn_portal_pair
from gravity_well import GravityWell, spawn_gravity_well
from hunter import HunterDrone, MirrorEnemy
from boss import create_boss, Behemoth, SwarmQueen, MirrorLord
from wave import (get_wave_asteroid_count, get_wave_specials, get_perk_choices,
                  get_wave_event, is_boss_wave, get_wave_topology,
                  PERKS, WAVE_EVENTS, MODULES,
                  Sector, get_sector_num, SECTOR_WAVES)
from utils import (vec2, color, ghost_positions, dist_wrapped, circle_collision,
                   torus_direction, set_topology, get_topology)
from sound import SoundSystem
from network import GameServer, GameClient, LANScanner, GAME_PORT, DEFAULT_MAX_CLIENTS
from lang import T, set_language, get_language, LANGUAGES, LANGUAGE_NAMES

# Global sound system — initialized after window creation
snd = None  # type: SoundSystem

# ── Unicode font & text helpers ──
_game_font = None  # loaded after rl.InitWindow


def _load_game_font():
    """Try to load a Unicode-capable font from system fonts."""
    global _game_font
    font_paths = [
        b"C:/Windows/Fonts/arial.ttf",
        b"C:/Windows/Fonts/segoeui.ttf",
        b"C:/Windows/Fonts/tahoma.ttf",
    ]
    # Character ranges: ASCII + Latin Extended (Polish/Spanish) + Cyrillic (Russian)
    chars = list(range(32, 127)) + list(range(160, 592)) + list(range(1024, 1280))
    for path in font_paths:
        try:
            from raylib._raylib_cffi import ffi as _ffi
            arr = _ffi.new("int[]", chars)
            font = rl.LoadFontEx(path, 72, arr, len(chars))
            if font.baseSize > 0:
                rl.SetTextureFilter(font.texture, 1)  # bilinear
                _game_font = font
                return
        except Exception:
            continue


def draw_text(text, x, y, size, col):
    """Draw text using the loaded Unicode font, or fallback to default."""
    if isinstance(text, str):
        text = text.encode('utf-8')
    if _game_font:
        rl.DrawTextEx(_game_font, text, vec2(x, y), float(size),
                      max(1.0, float(size) / 20.0), col)
    else:
        rl.DrawText(text, int(x), int(y), int(size), col)


def measure_text(text, size):
    """Measure text width using the loaded Unicode font, or fallback."""
    if isinstance(text, str):
        text = text.encode('utf-8')
    if _game_font:
        v = rl.MeasureTextEx(_game_font, text, float(size),
                             max(1.0, float(size) / 20.0))
        return int(v.x)
    return rl.MeasureText(text, int(size))

KEY_SPACE = 32
KEY_ENTER = 257
KEY_1 = 49
KEY_2 = 50
KEY_3 = 51
KEY_ESC = 256
KEY_UP = 265
KEY_DOWN = 264
KEY_LEFT = 263
KEY_RIGHT = 262
KEY_F = 70

RESOLUTIONS = [
    (800, 600),
    (1024, 768),
    (1280, 720),
    (1280, 800),
    (1366, 768),
    (1600, 900),
    (1800, 1000),
    (1920, 1080),
    (2560, 1440),
]

FPS_OPTIONS = [30, 60, 75, 120, 144, 240, 0]  # 0 = unlimited
FPS_LABELS = ["30", "60", "75", "120", "144", "240", "Unlimited"]

LEADERBOARD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscores.json")
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
LEADERBOARD_MAX = 10
NAME_MAX_LEN = 16

# ── Raylib key code <-> human-readable name mappings ──

_RLKEY_NAMES = {
    32: "SPACE", 39: "'", 44: ",", 45: "-", 46: ".", 47: "/",
    48: "0", 49: "1", 50: "2", 51: "3", 52: "4", 53: "5",
    54: "6", 55: "7", 56: "8", 57: "9", 59: ";", 61: "=",
    65: "A", 66: "B", 67: "C", 68: "D", 69: "E", 70: "F",
    71: "G", 72: "H", 73: "I", 74: "J", 75: "K", 76: "L",
    77: "M", 78: "N", 79: "O", 80: "P", 81: "Q", 82: "R",
    83: "S", 84: "T", 85: "U", 86: "V", 87: "W", 88: "X",
    89: "Y", 90: "Z",
    91: "[", 92: "\\", 93: "]", 96: "`",
    256: "ESC", 257: "ENTER", 258: "TAB", 259: "BACKSPACE",
    260: "INSERT", 261: "DELETE", 262: "RIGHT", 263: "LEFT",
    264: "DOWN", 265: "UP", 266: "PAGE_UP", 267: "PAGE_DOWN",
    268: "HOME", 269: "END",
    280: "CAPS_LOCK", 281: "SCROLL_LOCK", 282: "NUM_LOCK",
    283: "PRINT_SCREEN", 284: "PAUSE",
    290: "F1", 291: "F2", 292: "F3", 293: "F4", 294: "F5", 295: "F6",
    296: "F7", 297: "F8", 298: "F9", 299: "F10", 300: "F11", 301: "F12",
    340: "LEFT_SHIFT", 341: "LEFT_CTRL", 342: "LEFT_ALT",
    344: "RIGHT_SHIFT", 345: "RIGHT_CTRL", 346: "RIGHT_ALT",
}
_RLKEY_BY_NAME = {v: k for k, v in _RLKEY_NAMES.items()}

# Raylib gamepad button codes -> human-readable names
_GP_BUTTON_NAMES = {
    1: "A", 2: "B", 3: "X", 4: "Y",
    5: "LB", 6: "RB", 7: "Back", 8: "Start", 9: "Guide",
    10: "L-Stick", 11: "R-Stick",
    12: "D-Up", 13: "D-Right", 14: "D-Down", 15: "D-Left",
}
# Special axis-based bindings (negative value = axis id, mapped in code)
_GP_AXIS_NAMES = {
    -1: "L-Stick X",  # left stick horizontal (for rotation)
    -2: "RT (Axis)",  # right trigger axis
}
_GP_ALL_NAMES = {}
_GP_ALL_NAMES.update(_GP_BUTTON_NAMES)
_GP_ALL_NAMES.update(_GP_AXIS_NAMES)
_GP_BY_NAME = {v: k for k, v in _GP_ALL_NAMES.items()}

# ── Default key bindings ──

DEFAULT_KB_P1 = {
    'thrust':     265,  # UP
    'brake':      264,  # DOWN
    'left':       263,  # LEFT
    'right':      262,  # RIGHT
    'shoot':      32,   # SPACE
    'alt_brake':  90,   # Z
    'alt1':       88,   # X  (gravity bomb)
    'alt2':       67,   # C  (hyperspace)
    'strafe_l':   65,   # A
    'strafe_r':   68,   # D
}

DEFAULT_KB_P2 = {
    'left':       65,   # A
    'right':      68,   # D
    'thrust':     87,   # W
    'brake':      83,   # S
    'shoot':      74,   # J
    'alt_brake':  72,   # H
    'alt1':       75,   # K
    'alt2':       76,   # L
    'strafe_l':   81,   # Q
    'strafe_r':   69,   # E
}

# Gamepad binding: positive int = button id, negative int = special axis mapping
# -1 = left stick X axis (rotation), -2 = right trigger axis (shoot)
DEFAULT_GP = {
    'left':       -1,   # L-Stick X (negative direction handled in code)
    'right':      -1,   # L-Stick X (positive direction handled in code)
    'thrust':     1,    # A button
    'brake':      14,   # D-Down
    'shoot':      -2,   # RT axis
    'alt_brake':  2,    # B
    'alt1':       3,    # X
    'alt2':       4,    # Y
    'strafe_l':   5,    # LB
    'strafe_r':   6,    # RB
}

# Action labels for display in controls menu
_BIND_ACTIONS = [
    ('thrust',    'Thrust'),
    ('brake',     'Brake / Down'),
    ('left',      'Rotate Left'),
    ('right',     'Rotate Right'),
    ('shoot',     'Shoot'),
    ('alt_brake', 'Alt Brake'),
    ('alt1',      'Gravity Bomb'),
    ('alt2',      'Hyperspace'),
    ('strafe_l',  'Strafe Left'),
    ('strafe_r',  'Strafe Right'),
]


def _load_settings():
    """Load user settings from JSON file. Returns dict (empty on missing/corrupt)."""
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_settings(data):
    """Save user settings dict to JSON file."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Ship color palette for multiplayer
SHIP_COLORS = [
    ("White",   (255, 255, 255)),
    ("Red",     (255, 80, 80)),
    ("Blue",    (100, 150, 255)),
    ("Green",   (80, 255, 80)),
    ("Yellow",  (255, 255, 80)),
    ("Purple",  (200, 100, 255)),
    ("Cyan",    (80, 255, 255)),
    ("Orange",  (255, 160, 50)),
    ("Pink",    (255, 120, 200)),
]


def load_leaderboard():
    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return sorted(data, key=lambda e: e["score"], reverse=True)[:LEADERBOARD_MAX]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return []


def save_leaderboard(entries):
    entries = sorted(entries, key=lambda e: e["score"], reverse=True)[:LEADERBOARD_MAX]
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def qualifies_for_leaderboard(score, entries):
    if len(entries) < LEADERBOARD_MAX:
        return True
    return score > entries[-1]["score"]


class GravityBombField:
    """Tymczasowe pole grawitacyjne z gravity bomb pocisku."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.lifetime = GRAVITY_BOMB_DURATION
        self.radius = GRAVITY_BOMB_RADIUS
        self.strength = GRAVITY_BOMB_STRENGTH
        self.alive = True
        self.time = 0.0

    def update(self, dt):
        self.time += dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def apply_gravity(self, obj, dt):
        dx, dy = torus_direction(obj.x, obj.y, self.x, self.y)
        dist = math.hypot(dx, dy)
        if dist > self.radius or dist < 5:
            return
        force = self.strength / (dist * dist + 100)
        nx, ny = dx / dist, dy / dist
        obj.vx += nx * force * dt
        obj.vy += ny * force * dt

    def draw(self):
        t = self.time
        alpha = int(200 * (self.lifetime / GRAVITY_BOMB_DURATION))
        for gx, gy in ghost_positions(self.x, self.y, self.radius):
            for i in range(3):
                r = self.radius * (0.3 + 0.7 * ((t * 0.8 + i * 0.33) % 1.0))
                a = int(alpha * 0.3 * (1.0 - r / self.radius))
                rl.DrawCircleLines(int(gx), int(gy), r, color(200, 50, 255, max(0, a)))
            rl.DrawCircleV(vec2(gx, gy), 6, color(200, 100, 255, alpha // 2))


class Game:
    def __init__(self):
        self.state = "main_menu"
        self.menu_sel = 0
        self.pause_sel = 0
        self.menu_time = 0.0
        self._go_sel = 0
        self._controls_return_to = "main_menu"
        self._options_return_to = "main_menu"
        self._opt_sel = 0
        # ---- Key bindings (configurable) ----
        self._kb_p1 = dict(DEFAULT_KB_P1)
        self._kb_p2 = dict(DEFAULT_KB_P2)
        self._gp_binds = dict(DEFAULT_GP)
        # Controls menu state
        self._ctrl_section = 0       # 0=Keyboard P1, 1=Keyboard P2, 2=Xbox Gamepad
        self._ctrl_sel = 0           # selected row in current section
        self._ctrl_listening = False  # waiting for key/button press
        self._ctrl_listen_action = None  # which action is being rebound
        # Leaderboard
        self._leaderboard = load_leaderboard()
        self._name_input = ""
        self._name_entry_done = False
        self._name_cursor_blink = 0.0
        self._new_entry_rank = -1  # podswietlenie nowego wpisu
        # Graphics settings
        self._fullscreen = False
        self._borderless = False
        self._vsync = False
        self._show_fps = True
        self._fps_idx = 1  # default 60
        # Visual effects toggles
        self._fx_border_particles = True
        self._fx_speed_smear = True
        self._fx_asteroid_speed_color = True
        self._fx_bloom = True
        # Seed system
        self.game_seed = None  # None = random/unseeded
        self._seed_input = ""
        self._seed_cursor_blink = 0.0
        # Multiplayer
        self._server = None       # GameServer (host mode)
        self._client = None       # GameClient (join mode)
        self._scanner = None      # LANScanner (join lobby)
        self._mp_mode = None      # "host" | "client" | None
        self._mp_sel = 0          # submenu cursor
        self._sp_sel = 0
        self._join_sel = 0        # selected server in list
        self._join_ip_input = ""
        self._join_ip_active = False
        self._join_connecting = False
        self._mp_ship2 = None     # remote player ship
        self._mp_name = "Player"
        self._mp_editing_name = False
        self._mp_ship_color_idx = 0  # index into SHIP_COLORS
        self._ship_skin_idx = 0  # index into SHIP_SKINS (P1 / host / singleplayer)
        self._net_send_timer = 0.0
        self._lobby_send_timer = 0.0
        self._mp_shared_map = True  # shared map by default
        # Server creator state
        self._sc_sel = 0           # cursor in server creator
        self._sc_port = str(GAME_PORT)
        self._sc_max_players = 2   # total players including host
        self._sc_start_wave = 1
        self._sc_start_sector = 1
        self._sc_start_lives = START_LIVES
        self._sc_asteroid_count = ASTEROID_COUNT
        self._sc_shared_map = True
        self._sc_sandbox = False
        self._sc_boss_waves = True
        self._sc_ufo_spawns = True
        self._sc_wave_events = True
        self._sc_start_modules = []  # list of module IDs
        self._sc_editing_field = None  # which field is being text-edited
        self._mp_game_config = {}    # active game config during MP play
        self._net_bullets_ship1 = []  # client-side bullet data from host
        self._net_bullets_ship2 = []
        self._mp_host_name = ""      # host player name (seen by client)
        self._mp_client_name = ""    # client player name (seen by host)
        # Co-op (local) state
        self._coop_p2_control = 0    # 0 = "Keyboard (WASD)", 1 = "Gamepad"
        self._coop_p2_name = "P2"
        self._coop_p2_color_idx = 3  # Green by default
        self._coop_p2_skin_idx = 0  # P2 ship skin in co-op
        self._coop_editing_p2_name = False
        self._res_idx = self._find_res_idx(SCREEN_W, SCREEN_H)
        # Load saved user settings (overrides defaults above)
        self._load_user_settings()
        # Dekoracyjne asteroidy w tle menu
        self._menu_asteroids = []
        for _ in range(12):
            a = Asteroid(random.uniform(0, SCREEN_W), random.uniform(0, SCREEN_H), "large")
            a.vx *= 0.3
            a.vy *= 0.3
            self._menu_asteroids.append(a)
        self._init_game_state()

    @staticmethod
    def _find_res_idx(w, h):
        for i, (rw, rh) in enumerate(RESOLUTIONS):
            if rw == w and rh == h:
                return i
        return 6  # default 1800x1000

    def _apply_resolution(self, w, h):
        """Zmienia rozdzielczosc okna i aktualizuje wszystkie moduly."""
        import config
        import utils
        import asteroid
        import ship as ship_mod
        import portal as portal_mod
        import gravity_well as gw_mod
        import ufo as ufo_mod
        import hunter as hunter_mod
        import boss as boss_mod

        config.SCREEN_W = w
        config.SCREEN_H = h
        # Propagate to all modules that cache SCREEN_W/SCREEN_H
        for mod in [utils, asteroid, portal_mod, gw_mod, ufo_mod, hunter_mod, boss_mod, ship_mod]:
            if hasattr(mod, 'SCREEN_W'):
                mod.SCREEN_W = w
            if hasattr(mod, 'SCREEN_H'):
                mod.SCREEN_H = h

        rl.SetWindowSize(w, h)
        # Re-center window on monitor
        mon = rl.GetCurrentMonitor()
        mon_w = rl.GetMonitorWidth(mon)
        mon_h = rl.GetMonitorHeight(mon)
        if not self._fullscreen and not self._borderless:
            rl.SetWindowPosition(max(0, (mon_w - w) // 2), max(0, (mon_h - h) // 2))

        # Update menu asteroids positions
        for a in self._menu_asteroids:
            a.x = a.x % w
            a.y = a.y % h

    # ---- Settings persistence ----

    def _load_user_settings(self):
        """Load saved settings from JSON and apply to instance variables."""
        s = _load_settings()
        if not s:
            return
        # Graphics
        gfx = s.get('graphics', {})
        if gfx:
            self._fullscreen = gfx.get('fullscreen', self._fullscreen)
            self._borderless = gfx.get('borderless', self._borderless)
            self._vsync = gfx.get('vsync', self._vsync)
            self._show_fps = gfx.get('show_fps', self._show_fps)
            self._fps_idx = gfx.get('fps_idx', self._fps_idx)
            if 0 <= self._fps_idx < len(FPS_OPTIONS):
                pass
            else:
                self._fps_idx = 1
            self._fx_border_particles = gfx.get('border_particles', self._fx_border_particles)
            self._fx_speed_smear = gfx.get('speed_smear', self._fx_speed_smear)
            self._fx_asteroid_speed_color = gfx.get('asteroid_speed_color', self._fx_asteroid_speed_color)
            self._fx_bloom = gfx.get('bloom', self._fx_bloom)
            saved_res = gfx.get('res_idx', self._res_idx)
            if 0 <= saved_res < len(RESOLUTIONS):
                self._res_idx = saved_res
        # Audio
        audio = s.get('audio', {})
        if audio:
            # Will be applied after snd is created (deferred)
            self._saved_sfx = audio.get('sfx', True)
            self._saved_music = audio.get('music', True)
        # Language
        lang = s.get('language', 'en')
        if lang in LANGUAGES:
            set_language(lang)
        # Ship customization
        ship = s.get('ship', {})
        if ship:
            self._mp_ship_color_idx = ship.get('color_idx', self._mp_ship_color_idx)
            if self._mp_ship_color_idx >= len(SHIP_COLORS):
                self._mp_ship_color_idx = 0
            self._ship_skin_idx = ship.get('skin_idx', self._ship_skin_idx)
            if self._ship_skin_idx >= len(SHIP_SKINS):
                self._ship_skin_idx = 0
        # Controls
        ctrl = s.get('controls', {})
        if ctrl.get('kb_p1'):
            for k, v in ctrl['kb_p1'].items():
                if k in self._kb_p1 and isinstance(v, int):
                    self._kb_p1[k] = v
        if ctrl.get('kb_p2'):
            for k, v in ctrl['kb_p2'].items():
                if k in self._kb_p2 and isinstance(v, int):
                    self._kb_p2[k] = v
        if ctrl.get('gamepad'):
            for k, v in ctrl['gamepad'].items():
                if k in self._gp_binds and isinstance(v, int):
                    self._gp_binds[k] = v

    def _save_user_settings(self):
        """Save current settings to JSON file."""
        s = {
            'graphics': {
                'fullscreen': self._fullscreen,
                'borderless': self._borderless,
                'vsync': self._vsync,
                'show_fps': self._show_fps,
                'fps_idx': self._fps_idx,
                'res_idx': self._res_idx,
                'border_particles': self._fx_border_particles,
                'speed_smear': self._fx_speed_smear,
                'asteroid_speed_color': self._fx_asteroid_speed_color,
                'bloom': self._fx_bloom,
            },
            'audio': {
                'sfx': snd.sfx_enabled if snd else True,
                'music': snd.music_enabled if snd else True,
            },
            'controls': {
                'kb_p1': dict(self._kb_p1),
                'kb_p2': dict(self._kb_p2),
                'gamepad': dict(self._gp_binds),
            },
            'language': get_language(),
            'ship': {
                'color_idx': self._mp_ship_color_idx,
                'skin_idx': self._ship_skin_idx,
            },
        }
        _save_settings(s)

    def _init_game_state(self):
        import config
        sw, sh = config.SCREEN_W, config.SCREEN_H
        # Seed the RNG for seeded runs
        if self.game_seed:
            random.seed(self.game_seed)
        set_topology(get_wave_topology(1))
        self.ship = Ship(sw // 2, sh // 2)
        # Client in shared map mode starts with empty asteroids (host will send them)
        if self._mp_mode == "client" and self._mp_shared_map:
            self.asteroids = []
        else:
            self.asteroids = spawn_asteroids(ASTEROID_COUNT, sw // 2, sh // 2)
        self.particles = []
        self.powerups = []
        self.ufos = []
        self.ufo_bullets = []
        self.portals = []
        self.gravity_wells = []
        self.gravity_bomb_fields = []
        self.hunters = []
        self.mirrors = []
        self.enemy_bullets = []
        self.boss = None
        self.boss_bullets = []
        self.score = 0
        self.lives = START_LIVES
        self.level = 1
        self.respawn_timer = 0.0
        self.combo = 0
        self.combo_timer = 0.0
        self.combo_multiplier = 1
        self.shake_amount = 0.0
        self.shake_time = 0.0
        self.flash_time = 0.0
        self.powerup_msg = ""
        self.powerup_msg_time = 0.0

        # Spawn timers
        self.ufo_timer = random.uniform(UFO_SPAWN_INTERVAL_MIN, UFO_SPAWN_INTERVAL_MAX)
        self.portal_timer = random.uniform(PORTAL_SPAWN_INTERVAL_MIN, PORTAL_SPAWN_INTERVAL_MAX)
        self.grav_well_timer = random.uniform(GRAV_WELL_SPAWN_INTERVAL_MIN, GRAV_WELL_SPAWN_INTERVAL_MAX)

        # Wave system
        self.wave_event_timer = random.uniform(WAVE_EVENT_INTERVAL_MIN, WAVE_EVENT_INTERVAL_MAX)
        self.active_event = None
        self.event_time_left = 0.0
        self.event_msg = ""
        self.event_msg_time = 0.0

        # Perk selection
        self.perk_selection_active = False
        self.perk_choices = []
        self.owned_perks = set()

        # Dynamic jitter
        self.dynamic_jitter = 0.0

        # Risk-reward: lurking bonus
        self.lurk_timer = 0.0

        # Hunter/mirror spawn
        self.hunter_timer = 40.0
        self.mirror_timer = 60.0

        # Wrap score multiplier
        self.wrap_score_mult = 1.0

        # Nuke every 10 counter
        self.shot_counter = 0
        self._shot_counter_p2 = 0

        # Blackout event
        self.blackout = False

        # Sector system
        self.sector = Sector(1)
        self.sector_transition_time = 0.0
        self.sector_announce_msg = ""
        self.sector_announce_time = 0.0

        # Bloom / sound-reactivity
        self.bloom_energy = 0.0
        self._overheat_snd_played = False
        self._overheat_snd_p2 = False

        # Network events buffer (host accumulates, sends to clients)
        self._net_events = []

        # Multiplayer respawn system
        self.lives_ship2 = START_LIVES
        self.respawn_timer_ship2 = 0.0
        self.ship2_dead_permanently = False
        self.ship1_dead_permanently = False
        self.mp_respawn_mode = "wave"  # "wave", "score", "timer"
        self.mp_respawn_score_threshold = 0  # score when partner died + MP_RESPAWN_SCORE
        self.mp_respawn_death_time = 0.0     # time.time() when partner died
        self._mp_spectating = False          # True when local player is dead but game continues

    def screen_shake(self, amount):
        if "bigger_explosions" in self.owned_perks:
            amount *= 1.5
        self.shake_amount = max(self.shake_amount, amount)
        self.shake_time = amount / SHAKE_DECAY

    def _emit_event(self, evt):
        """Buffer a visual/audio event for network broadcast to clients."""
        if self._mp_mode == "host":
            self._net_events.append(evt)

    def add_score(self, points, velocity_bonus=0, distance_bonus=0):
        self.combo += 1
        self.combo_timer = COMBO_TIMEOUT
        if self.combo >= 10:
            self.combo_multiplier = 4
        elif self.combo >= 5:
            self.combo_multiplier = 2
        else:
            self.combo_multiplier = 1
        if self.combo in (5, 10):
            snd.play('combo')
            self.bloom_energy = min(1.0, self.bloom_energy + 0.1)

        total = points + velocity_bonus + distance_bonus
        mult = self.combo_multiplier
        if "double_score" in self.owned_perks:
            mult *= 2
        # Wrap-based score multiplier
        mult *= self.wrap_score_mult
        self.score += int(total * mult)

    def destroy_asteroid(self, asteroid, bullet=None):
        """Niszczy asteroide."""
        # Crystal: wymaga wielu trafien
        if asteroid.special == "crystal" and asteroid.hp > 0:
            if not asteroid.take_hit():
                # Nie zniszczona jeszcze
                self.particles.extend(explosion(asteroid.x, asteroid.y, 8, 60, (0, 255, 255)))
                self.screen_shake(2)
                snd.play('crystal_hit')
                self._emit_event({"t": "exp", "x": asteroid.x, "y": asteroid.y,
                                   "n": 8, "s": 60, "c": [0, 255, 255]})
                self._emit_event({"t": "shk", "a": 2})
                self._emit_event({"t": "snd", "n": "crystal_hit"})
                return False  # not destroyed

        base = ASTEROID_POINTS.get(asteroid.size, 50)
        if asteroid.special == "crystal":
            base *= CRYSTAL_POINTS_MULT

        # Velocity scoring
        vel_bonus = int(math.hypot(asteroid.vx, asteroid.vy) * VELOCITY_SCORE_BONUS * base)
        dist_bonus = 0
        if bullet:
            d = dist_wrapped(bullet.origin_x, bullet.origin_y, asteroid.x, asteroid.y)
            dist_bonus = int(d * DISTANCE_SCORE_BONUS * base)

        self.add_score(base, vel_bonus, dist_bonus)

        # Particle
        color_map = {
            "normal": (255, 200, 50), "explosive": (255, 80, 30),
            "fast": (150, 150, 255), "spiky": (255, 50, 50),
            "ice": (100, 220, 255), "splitter": (255, 200, 0),
            "magnetic": (200, 0, 255), "ghost": (150, 150, 200),
            "growing": (100, 255, 100), "chain": (255, 120, 0),
            "crystal": (0, 255, 255), "parasite": (180, 255, 0),
            "virus": (255, 0, 100),
        }
        pc = color_map.get(asteroid.special, (255, 200, 50))
        count = {"large": 25, "medium": 18, "small": 12}.get(asteroid.size, 15)
        if "bigger_explosions" in self.owned_perks:
            count = int(count * 1.6)
        self.particles.extend(explosion(asteroid.x, asteroid.y, count, 120, pc))

        shake = {"large": 8, "medium": 4, "small": 2}.get(asteroid.size, 3)
        self.screen_shake(shake)
        snd.play('explosion', 0.5 + shake * 0.06)
        self.bloom_energy = min(1.0, self.bloom_energy + 0.08 + shake * 0.01)

        # Emit network events for client
        self._emit_event({"t": "exp", "x": asteroid.x, "y": asteroid.y,
                           "n": count, "s": 120, "c": list(pc)})
        self._emit_event({"t": "shk", "a": shake})
        self._emit_event({"t": "snd", "n": "explosion", "v": 0.5 + shake * 0.06})

        # Explosive
        if asteroid.special == "explosive":
            blast_radius = asteroid.radius * 3
            self.screen_shake(12)
            self.flash_time = 0.15
            snd.play('big_explosion')
            self.bloom_energy = min(1.0, self.bloom_energy + 0.3)
            self.particles.extend(explosion(asteroid.x, asteroid.y, 40, 200, (255, 100, 0), 0.8, 3.5))
            self._emit_event({"t": "exp", "x": asteroid.x, "y": asteroid.y,
                               "n": 40, "s": 200, "c": [255, 100, 0]})
            self._emit_event({"t": "shk", "a": 12})
            self._emit_event({"t": "fls", "d": 0.15})
            self._emit_event({"t": "snd", "n": "big_explosion"})
            to_destroy = []
            for a in self.asteroids:
                if a is not asteroid and a.alive and dist_wrapped(asteroid.x, asteroid.y, a.x, a.y) < blast_radius:
                    if a.size in ("small", "medium"):
                        to_destroy.append(a)
            for a in to_destroy:
                if a in self.asteroids:
                    self.asteroids.remove(a)
                    self.add_score(ASTEROID_POINTS.get(a.size, 50))
                    self.particles.extend(explosion(a.x, a.y, 15, 100, pc))
                    self._emit_event({"t": "exp", "x": a.x, "y": a.y,
                                       "n": 15, "s": 100, "c": list(pc)})

        # Chain reaction
        if asteroid.special == "chain":
            chain_radius = asteroid.radius * 4
            self.screen_shake(15)
            self.flash_time = 0.2
            snd.play('big_explosion')
            self.bloom_energy = min(1.0, self.bloom_energy + 0.35)
            self.particles.extend(chain_explosion(asteroid.x, asteroid.y))
            self._emit_event({"t": "cexp", "x": asteroid.x, "y": asteroid.y})
            self._emit_event({"t": "shk", "a": 15})
            self._emit_event({"t": "fls", "d": 0.2})
            self._emit_event({"t": "snd", "n": "big_explosion"})
            to_chain = []
            for a in self.asteroids:
                if a is not asteroid and a.alive and dist_wrapped(asteroid.x, asteroid.y, a.x, a.y) < chain_radius:
                    to_chain.append(a)
            for a in to_chain:
                if a in self.asteroids:
                    self.asteroids.remove(a)
                    self.destroy_asteroid(a)

        # Virus: infekuje sasiednie asteroidy
        if asteroid.special == "virus":
            infect_radius = asteroid.radius * 5
            for a in self.asteroids:
                if a is not asteroid and a.alive and not a.infected:
                    if dist_wrapped(asteroid.x, asteroid.y, a.x, a.y) < infect_radius:
                        a.infected = True
                        a.infected_timer = 0.0
                        self.particles.extend(explosion(a.x, a.y, 5, 40, (255, 0, 100)))

        # Crystal: guaranteed powerup (module)
        if asteroid.special == "crystal":
            pu = PowerUp(asteroid.x, asteroid.y, kind="module")
            self.powerups.append(pu)
        else:
            # Normal power-up drop
            pu = maybe_spawn_powerup(asteroid.x, asteroid.y, POWERUP_DROP_CHANCE)
            if pu:
                self.powerups.append(pu)

        # Split
        children = asteroid.split()
        self.asteroids.extend(children)

        # Lurk timer reset
        self.lurk_timer = 0.0
        return True  # destroyed

    def start_perk_selection(self):
        self.perk_selection_active = True
        self.perk_choices = get_perk_choices(self.owned_perks, self.level)
        snd.play('wave_clear')
        self.bloom_energy = min(1.0, self.bloom_energy + 0.3)

    def select_perk(self, index):
        if index >= len(self.perk_choices):
            return
        perk_id = self.perk_choices[index]
        self.owned_perks.add(perk_id)
        self.ship.perks = self.owned_perks

        if perk_id == "extra_life":
            self.lives += 1
            # In multiplayer, give P2 an extra life too
            if self._mp_mode in ("host", "coop") and self._mp_ship2:
                self.lives_ship2 += 1
            self.owned_perks.discard("extra_life")

        # Mutations
        perk_info = PERKS.get(perk_id, {})
        if "mutation" in perk_info:
            self.ship.apply_mutation(perk_info["mutation"])

        # Sync perks/mutations to ship2
        self._sync_ship2_perks()

        self.perk_selection_active = False
        self.powerup_msg = perk_info.get("name", perk_id.upper())
        self.powerup_msg_time = 2.0
        snd.play('perk')
        self._start_next_wave()

    def _sync_ship2_perks(self):
        """Mirror all perks, mutations, and modules from ship1 to ship2."""
        if not self._mp_ship2 or self._mp_mode not in ("host", "coop"):
            return
        self._mp_ship2.perks = set(self.owned_perks)
        self._mp_ship2.mutations = set(self.ship.mutations)
        # Sync ship evolution verts
        self._mp_ship2.ship_verts = list(self.ship.ship_verts)
        self._mp_ship2.ship_size = self.ship.ship_size

    def _enemy_target(self, ex, ey):
        """Return (x, y) of the closest alive ship to (ex, ey), or (None, None)."""
        s1 = self.ship if self.ship.alive else None
        s2 = self._mp_ship2 if (self._mp_ship2 and self._mp_ship2.alive) else None
        if s1 and s2:
            d1 = dist_wrapped(ex, ey, s1.x, s1.y)
            d2 = dist_wrapped(ex, ey, s2.x, s2.y)
            return (s1.x, s1.y) if d1 <= d2 else (s2.x, s2.y)
        if s1:
            return s1.x, s1.y
        if s2:
            return s2.x, s2.y
        return None, None

    def _start_next_wave(self):
        self.level += 1

        # Sector transition check
        new_sector_num = get_sector_num(self.level)
        if new_sector_num != self.sector.number:
            self.sector = Sector(new_sector_num)
            self.sector_transition_time = 4.0
            self.sector_announce_msg = f"SECTOR {new_sector_num}: {self.sector.name}"
            self.sector_announce_time = 5.0
            self.screen_shake(8)

        # Topology change
        new_topo = get_wave_topology(self.level)
        old_topo = get_topology()
        set_topology(new_topo)
        if new_topo != old_topo:
            self.event_msg = f"TOPOLOGY: {TOPOLOGY_NAMES.get(new_topo, '?')}"
            self.event_msg_time = 3.0
            self.screen_shake(5)

        # Sector modifiers for asteroid count
        ast_mult = self.sector.get_asteroid_count_mult()
        speed_mult = self.sector.get_asteroid_speed_mult()

        # Boss wave?
        _cfg_boss = self._mp_game_config.get('boss_waves', True) if self._mp_game_config else True
        if is_boss_wave(self.level) and _cfg_boss:
            self.boss = create_boss(self.level, self.ship.x, self.ship.y, self.ship.angle)
            count = max(3, int(get_wave_asteroid_count(self.level) // 2 * ast_mult))
            self.asteroids = spawn_asteroids(
                count, self.ship.x, self.ship.y,
                get_wave_specials(self.level))
        else:
            self.boss = None
            count = int(get_wave_asteroid_count(self.level) * ast_mult)
            specials = get_wave_specials(self.level)
            self.asteroids = spawn_asteroids(count, self.ship.x, self.ship.y, specials)

        # Apply sector speed modifier to spawned asteroids
        if speed_mult != 1.0:
            for a in self.asteroids:
                a.vx *= speed_mult
                a.vy *= speed_mult

        # Apply crystal vein modifier - replace some normal asteroids with crystals
        if self.sector.get_crystal_chance_mult() > 1.0:
            crystal_mult = self.sector.get_crystal_chance_mult()
            for i, a in enumerate(self.asteroids):
                if a.special is None and random.random() < 0.15 * crystal_mult:
                    self.asteroids[i] = Asteroid(a.x, a.y, a.size, special="crystal")

        self.ufo_timer = random.uniform(UFO_SPAWN_INTERVAL_MIN, UFO_SPAWN_INTERVAL_MAX)
        evt_mult = self.sector.get_event_timer_mult()
        self.wave_event_timer = random.uniform(
            WAVE_EVENT_INTERVAL_MIN * evt_mult,
            WAVE_EVENT_INTERVAL_MAX * evt_mult)

        # Spawn portals (more pairs in later waves, sector modifier)
        num_pairs = int((1 + self.level // 5) * self.sector.get_portal_count_mult())
        new_portals = spawn_portal_pair(min(num_pairs, 3))
        self.portals.extend(new_portals)

        # Gravity well timer with sector modifier
        gw_mult = self.sector.get_gravity_well_timer_mult()
        self.grav_well_timer = random.uniform(
            GRAV_WELL_SPAWN_INTERVAL_MIN * gw_mult,
            GRAV_WELL_SPAWN_INTERVAL_MAX * gw_mult)

        hunter_mult = self.sector.get_hunter_timer_mult()
        if self.level >= 4:
            self.hunter_timer = random.uniform(15 * hunter_mult, 30 * hunter_mult)
        if self.level >= 6:
            self.mirror_timer = random.uniform(25, 45)

    def _apply_wave_event(self, event):
        action = event["action"]
        self.event_msg = event["name"]
        self.event_msg_time = 3.0

        if action == "reverse":
            for a in self.asteroids:
                a.vx = -a.vx
                a.vy = -a.vy
        elif action == "freeze":
            self.active_event = "freeze"
            self.event_time_left = WAVE_EVENT_DURATION
        elif action == "swarm":
            if self.ship.alive:
                self.asteroids.extend(spawn_swarm(SWARM_COUNT, self.ship.x, self.ship.y))
        elif action == "gravity_surge":
            self.active_event = "gravity_surge"
            self.event_time_left = WAVE_EVENT_DURATION * 1.5
        elif action == "no_wrap_y":
            self.active_event = "no_wrap_y"
            self.event_time_left = WAVE_EVENT_DURATION
        elif action == "blackout":
            self.active_event = "blackout"
            self.blackout = True
            self.event_time_left = WAVE_EVENT_DURATION * 1.5
        elif action == "fracture":
            self.active_event = "fracture"
            self.event_time_left = WAVE_EVENT_DURATION
        elif action == "gravity_pulse":
            self.active_event = "gravity_pulse"
            self.event_time_left = WAVE_EVENT_DURATION * 2

    def update(self, dt):
        # ---- STATE DISPATCH ----
        if self.state == "main_menu":
            self._update_main_menu(dt)
            return
        if self.state == "paused":
            self._update_pause_menu(dt)
            return
        if self.state == "game_over":
            self._update_game_over(dt)
            return
        if self.state == "controls":
            self._update_controls(dt)
            return
        if self.state == "options":
            self._update_options(dt)
            return
        if self.state == "high_scores":
            if rl.IsKeyPressed(KEY_ESC) or rl.IsKeyPressed(KEY_ENTER):
                self.state = "main_menu"
                self._new_entry_rank = -1
            return
        if self.state == "name_entry":
            self._update_name_entry(dt)
            return
        if self.state == "seed_entry":
            self._update_seed_entry(dt)
            return
        if self.state == "sp_menu":
            self._update_sp_menu(dt)
            return
        if self.state == "mp_menu":
            self._update_mp_menu(dt)
            return
        if self.state == "server_creator":
            self._update_server_creator(dt)
            return
        if self.state == "coop_creator":
            self._update_coop_creator(dt)
            return
        if self.state == "host_lobby":
            self._update_host_lobby(dt)
            return
        if self.state == "join_lobby":
            self._update_join_lobby(dt)
            return
        if self.state == "client_lobby":
            self._update_client_lobby(dt)
            return

        # ---- playing ----

        # ESC -> pause
        if rl.IsKeyPressed(KEY_ESC):
            self.state = "paused"
            self.pause_sel = 0
            return

        # ---- PERK SELECTION ----
        if self.perk_selection_active:
            if rl.IsKeyPressed(KEY_1) and len(self.perk_choices) >= 1:
                self.select_perk(0)
            elif rl.IsKeyPressed(KEY_2) and len(self.perk_choices) >= 2:
                self.select_perk(1)
            elif rl.IsKeyPressed(KEY_3) and len(self.perk_choices) >= 3:
                self.select_perk(2)
            return

        # ---- COMBO ----
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 0
                self.combo_multiplier = 1

        # ---- SHAKE / FLASH / MSG ----
        if self.shake_time > 0:
            self.shake_time -= dt
            self.shake_amount *= max(0, 1.0 - SHAKE_DECAY * dt)
        else:
            self.shake_amount = 0
        self.flash_time = max(0, self.flash_time - dt)
        self.powerup_msg_time = max(0, self.powerup_msg_time - dt)
        self.event_msg_time = max(0, self.event_msg_time - dt)
        self.sector_announce_time = max(0, self.sector_announce_time - dt)
        self.sector_transition_time = max(0, self.sector_transition_time - dt)

        # ---- BLOOM DECAY ----
        self.bloom_energy = max(0.0, self.bloom_energy - dt * 1.5)

        # ---- DYNAMIC MUSIC ----
        _mi = min(0.3, self.level * 0.025)
        _mi += min(0.2, len(self.asteroids) * 0.008)
        _mi += min(0.2, self.combo * 0.015)
        if self.active_event:
            _mi += 0.1
        _mi += self.bloom_energy * 0.2
        _mi = min(1.0, _mi)
        _boss_active = self.boss is not None and self.boss.alive
        snd.update_music(_mi, self.sector.number, _boss_active)

        # ---- CLIENT SHARED MAP: skip game logic, only receive state ----
        _is_client_shared = (self._mp_mode == "client" and self._mp_shared_map)
        if _is_client_shared:
            # Client in shared map mode: don't run game logic, just sync + render
            self._mp_network_tick(dt)

            # Interpolate asteroids locally between snapshots (smooth motion)
            for a in self.asteroids:
                a.x += a.vx * dt
                a.y += a.vy * dt
                a.angle += a.rot_speed * dt
                a.do_wrap()

            # Interpolate ship positions
            if self.ship.alive:
                self.ship.x += self.ship.vx * dt
                self.ship.y += self.ship.vy * dt
            if self._mp_ship2 and self._mp_ship2.alive:
                self._mp_ship2.x += self._mp_ship2.vx * dt
                self._mp_ship2.y += self._mp_ship2.vy * dt

            # Thrust particles for both ships
            if self.ship.alive and self.ship.thrusting:
                self.particles.extend(thrust_particles(
                    self.ship.x, self.ship.y, self.ship.angle,
                    self.ship.vx, self.ship.vy))
            if self._mp_ship2 and self._mp_ship2.alive and self._mp_ship2.thrusting:
                self.particles.extend(thrust_particles(
                    self._mp_ship2.x, self._mp_ship2.y, self._mp_ship2.angle,
                    self._mp_ship2.vx, self._mp_ship2.vy))

            # Update particles (visual)
            for p in self.particles:
                p.update(dt)
            self.particles = [p for p in self.particles if p.alive]
            return

        # ---- WAVE EVENTS ----
        if self.active_event:
            self.event_time_left -= dt
            if self.event_time_left <= 0:
                if self.active_event == "blackout":
                    self.blackout = False
                self.active_event = None

        _cfg_wave_events = self._mp_game_config.get('wave_events', True) if self._mp_game_config else True
        self.wave_event_timer -= dt
        if self.wave_event_timer <= 0 and len(self.asteroids) > 3 and _cfg_wave_events:
            evt_m = self.sector.get_event_timer_mult()
            self.wave_event_timer = random.uniform(
                WAVE_EVENT_INTERVAL_MIN * evt_m, WAVE_EVENT_INTERVAL_MAX * evt_m)
            event = get_wave_event(self.level)
            # Swarm sector biases toward swarm events
            if self.sector.favors_swarm_events() and random.random() < 0.4:
                event = WAVE_EVENTS[2]  # METEOR SHOWER
            self._apply_wave_event(event)

        # ---- DYNAMIC JITTER ----
        target_jitter = len(self.asteroids) * 0.003
        if self.active_event == "fracture":
            target_jitter *= 3
        self.dynamic_jitter += (target_jitter - self.dynamic_jitter) * dt * 2

        # ---- TOPOLOGY BORDER PARTICLES (ambient) ----
        if self._fx_border_particles:
            from utils import get_topology
            topo = get_topology()
            if topo != 0 and random.random() < 0.3:
                topo_cols = {1: (100, 50, 50), 2: (255, 100, 0),
                             3: (255, 0, 255), 4: (100, 200, 100)}
                bc = topo_cols.get(topo, (200, 200, 255))
                # Spawn on relevant edges
                edge = random.choice(["top", "bottom", "left", "right"])
                if edge == "top":
                    px, py = random.uniform(0, SCREEN_W), 2
                elif edge == "bottom":
                    px, py = random.uniform(0, SCREEN_W), SCREEN_H - 2
                elif edge == "left":
                    px, py = 2, random.uniform(0, SCREEN_H)
                else:
                    px, py = SCREEN_W - 2, random.uniform(0, SCREEN_H)
                self.particles.append(topology_border_particle(px, py, bc))

        # ---- LURK BONUS ----
        if len(self.asteroids) == 1 and self.asteroids[0].size == "large":
            self.lurk_timer += dt

        # ---- WRAP SCORE MULTIPLIER ----
        if self.ship.alive and self.ship.wrap_count > 0:
            added = self.ship.wrap_count * WRAP_SCORE_PER_WRAP
            self.wrap_score_mult = min(3.0, self.wrap_score_mult + added)
            self.ship.wrap_count = 0
        if self._mp_ship2 and self._mp_ship2.alive and self._mp_ship2.wrap_count > 0:
            added = self._mp_ship2.wrap_count * WRAP_SCORE_PER_WRAP
            self.wrap_score_mult = min(3.0, self.wrap_score_mult + added)
            self._mp_ship2.wrap_count = 0
        self.wrap_score_mult = max(1.0, self.wrap_score_mult - WRAP_SCORE_DECAY * dt)

        # ---- SHIP ----
        time_scale = 1.0
        if self.active_event == "freeze":
            time_scale = 0.05

        if self.ship.alive:
            old_sx, old_sy = self.ship.x, self.ship.y
            new_bullets = self.ship.update(dt, input_map=self._build_p1_input_map())
            self.ship.do_wrap()

            # Shoot sound
            if new_bullets:
                snd.play('shoot', 0.6)

            # Overheat sound
            if self.ship.overheated and not self._overheat_snd_played:
                snd.play('overheat')
                self._overheat_snd_played = True
            if not self.ship.overheated:
                self._overheat_snd_played = False

            # Border particles on wrap
            if self._fx_border_particles and self.ship.wrap_count > 0:
                from utils import get_topology
                topo = get_topology()
                topo_cols = {0: (200, 200, 255), 1: (100, 50, 50),
                             2: (255, 100, 0), 3: (255, 0, 255), 4: (100, 200, 100)}
                bc = topo_cols.get(topo, (200, 200, 255))
                for _ in range(5):
                    self.particles.append(topology_border_particle(old_sx, old_sy, bc))
                    self.particles.append(topology_border_particle(self.ship.x, self.ship.y, bc))

            # Speed smear particles for ship
            if self._fx_speed_smear:
                spd = math.hypot(self.ship.vx, self.ship.vy)
                if spd > MAX_SPEED * 0.6 and random.random() < 0.4:
                    self.particles.extend(smear_particles(
                        self.ship.x, self.ship.y, self.ship.vx, self.ship.vy))

            # Nuke every 10 perk
            if "nuke_every_10" in self.owned_perks and new_bullets:
                for nb in new_bullets:
                    if nb.kind == "normal" and not getattr(nb, 'is_backfire', False):
                        self.shot_counter += 1
                        if self.shot_counter >= 10:
                            self.shot_counter = 0
                            # Turn this bullet into a nuke effect
                            nuke_targets = [a for a in self.asteroids
                                            if a.size == "small"
                                            and dist_wrapped(nb.x, nb.y, a.x, a.y) < 200]
                            for a in nuke_targets[:5]:
                                if a in self.asteroids:
                                    self.asteroids.remove(a)
                                    self.add_score(ASTEROID_POINTS.get(a.size, 50))
                                    self.particles.extend(explosion(a.x, a.y, 10, 80, (255, 50, 50)))
                            if nuke_targets:
                                self.screen_shake(8)
                                self.flash_time = 0.1

            # bullet_inherit_vel perk
            if "bullet_inherit_vel" in self.owned_perks:
                for nb in new_bullets:
                    nb.vx += self.ship.vx * 0.3
                    nb.vy += self.ship.vy * 0.3

            # Thrust particles
            if self.ship.thrusting:
                self.particles.extend(thrust_particles(
                    self.ship.x, self.ship.y, self.ship.angle,
                    self.ship.vx, self.ship.vy))
                # Heat trail
                if self.ship.heat > 0.5:
                    self.particles.extend(heat_trail(
                        self.ship.x, self.ship.y,
                        self.ship.vx, self.ship.vy, self.ship.heat))

            # Afterburner mutation: fire trail damages small asteroids
            if "afterburner" in self.ship.mutations and self.ship.thrusting:
                trail_x = self.ship.x - math.sin(self.ship.angle) * 20
                trail_y = self.ship.y + math.cos(self.ship.angle) * 20
                to_burn = []
                for a in self.asteroids:
                    if a.size == "small" and dist_wrapped(trail_x, trail_y, a.x, a.y) < HEAT_TRAIL_DAMAGE_RADIUS * 3:
                        to_burn.append(a)
                for a in to_burn:
                    if a in self.asteroids:
                        self.asteroids.remove(a)
                        self.destroy_asteroid(a)

            # Set homing targets
            targets = self.asteroids + self.ufos + self.hunters + self.mirrors
            if self.boss and self.boss.alive:
                targets.append(self.boss)
            for b in self.ship.bullets:
                if b.kind == "homing":
                    b.homing_targets = targets
        else:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0 and self.lives > 0:
                self.ship.reset(SCREEN_W // 2, SCREEN_H // 2)

        # ---- CO-OP: update ship2 with local P2 input ----
        if self._mp_mode == "coop" and self._mp_ship2 and self._mp_ship2.alive:
            p2_input = self._capture_coop_p2_input()
            new_bul2 = self._mp_ship2.update(dt, p2_input)
            self._mp_ship2.do_wrap()
            if new_bul2:
                snd.play('shoot', 0.5)

            # Overheat sound for P2
            if self._mp_ship2.overheated and not self._overheat_snd_p2:
                snd.play('overheat')
                self._overheat_snd_p2 = True
            if not self._mp_ship2.overheated:
                self._overheat_snd_p2 = False

            # Thrust particles for P2
            if self._mp_ship2.thrusting:
                self.particles.extend(thrust_particles(
                    self._mp_ship2.x, self._mp_ship2.y, self._mp_ship2.angle,
                    self._mp_ship2.vx, self._mp_ship2.vy))
                if self._mp_ship2.heat > 0.5:
                    self.particles.extend(heat_trail(
                        self._mp_ship2.x, self._mp_ship2.y,
                        self._mp_ship2.vx, self._mp_ship2.vy, self._mp_ship2.heat))

            # Speed smear for P2
            if self._fx_speed_smear:
                spd2 = math.hypot(self._mp_ship2.vx, self._mp_ship2.vy)
                if spd2 > MAX_SPEED * 0.6 and random.random() < 0.4:
                    self.particles.extend(smear_particles(
                        self._mp_ship2.x, self._mp_ship2.y,
                        self._mp_ship2.vx, self._mp_ship2.vy))

            # Afterburner mutation for P2
            if "afterburner" in self._mp_ship2.mutations and self._mp_ship2.thrusting:
                trail_x = self._mp_ship2.x - math.sin(self._mp_ship2.angle) * 20
                trail_y = self._mp_ship2.y + math.cos(self._mp_ship2.angle) * 20
                to_burn = []
                for a in self.asteroids:
                    if a.size == "small" and dist_wrapped(trail_x, trail_y, a.x, a.y) < HEAT_TRAIL_DAMAGE_RADIUS * 3:
                        to_burn.append(a)
                for a in to_burn:
                    if a in self.asteroids:
                        self.asteroids.remove(a)
                        self.destroy_asteroid(a)

            # Nuke every 10 perk for P2
            if "nuke_every_10" in self.owned_perks and new_bul2:
                for nb in new_bul2:
                    if nb.kind == "normal" and not getattr(nb, 'is_backfire', False):
                        self._shot_counter_p2 += 1
                        if self._shot_counter_p2 >= 10:
                            self._shot_counter_p2 = 0
                            nuke_targets = [a for a in self.asteroids
                                            if a.size == "small"
                                            and dist_wrapped(nb.x, nb.y, a.x, a.y) < 200]
                            for a in nuke_targets[:5]:
                                if a in self.asteroids:
                                    self.asteroids.remove(a)
                                    self.add_score(ASTEROID_POINTS.get(a.size, 50))
                                    self.particles.extend(explosion(a.x, a.y, 10, 80, (255, 50, 50)))
                            if nuke_targets:
                                self.screen_shake(8)
                                self.flash_time = 0.1

            # Bullet inherit velocity perk for P2
            if "bullet_inherit_vel" in self.owned_perks and new_bul2:
                for nb in new_bul2:
                    nb.vx += self._mp_ship2.vx * 0.3
                    nb.vy += self._mp_ship2.vy * 0.3

            # Homing targets for P2 bullets
            targets = self.asteroids + self.ufos + self.hunters + self.mirrors
            if self.boss and self.boss.alive:
                targets.append(self.boss)
            for b in self._mp_ship2.bullets:
                if b.kind == "homing":
                    b.homing_targets = targets

        # ---- SHIP2 RESPAWN (multiplayer host / co-op) ----
        if self._mp_mode in ("host", "coop") and self._mp_ship2:
            if not self._mp_ship2.alive and not self.ship2_dead_permanently:
                self.respawn_timer_ship2 -= dt
                if self.respawn_timer_ship2 <= 0 and self.lives_ship2 > 0:
                    self._mp_ship2.reset(SCREEN_W // 2 + 80, SCREEN_H // 2)

            # ---- Partner respawn checks ----
            has_dead_partner = (self.ship1_dead_permanently or self.ship2_dead_permanently)
            if has_dead_partner and not self._mp_all_dead():
                if self.mp_respawn_mode == "score":
                    if self.score >= self.mp_respawn_score_threshold:
                        if self.ship1_dead_permanently:
                            self._try_respawn_partner("ship1")
                        elif self.ship2_dead_permanently:
                            self._try_respawn_partner("ship2")
                elif self.mp_respawn_mode == "timer":
                    if _time.time() - self.mp_respawn_death_time >= MP_RESPAWN_TIMER:
                        if self.ship1_dead_permanently:
                            self._try_respawn_partner("ship1")
                        elif self.ship2_dead_permanently:
                            self._try_respawn_partner("ship2")
                # "wave" mode is handled in wave clear section

        # ---- ASTEROIDY ----
        for a in self.asteroids:
            a_time_scale = time_scale
            if "slow_asteroids" in self.owned_perks:
                a_time_scale *= 0.7
            a.update(dt, a_time_scale)

            # No wrap Y event
            if self.active_event == "no_wrap_y":
                a.x = a.x % SCREEN_W
                if a.y < -50 or a.y > SCREEN_H + 50:
                    a.vy = -a.vy
                    a.y = max(-50, min(SCREEN_H + 50, a.y))
            else:
                a.do_wrap()

            # Magnetic force
            if a.special == "magnetic":
                targets = [o for o in self.asteroids if o is not a and o.size == "small"]
                a.apply_magnetic_force(targets + self.ship.bullets, dt)

            # Speed smear for fast asteroids
            if self._fx_speed_smear:
                aspd = math.hypot(a.vx, a.vy)
                if aspd > 180 and random.random() < 0.2:
                    from asteroid import SPECIAL_COLORS
                    ac = SPECIAL_COLORS.get(a.special, (255, 255, 255))
                    self.particles.extend(smear_particles(a.x, a.y, a.vx, a.vy, ac))

        # Faction forces between asteroids
        faction_asteroids = [a for a in self.asteroids
                             if a.special in FACTION_ATTRACT or a.special in FACTION_REPEL]
        for i, a in enumerate(faction_asteroids):
            for b in faction_asteroids[i + 1:]:
                a.apply_faction_force(b, dt)
                b.apply_faction_force(a, dt)

        # Parasite target reassignment
        for a in self.asteroids:
            if a.special == "parasite":
                if a.parasite_target is None or not a.parasite_target.alive:
                    candidates = [o for o in self.asteroids
                                  if o is not a and o.special != "parasite" and o.size == "large"]
                    if not candidates:
                        candidates = [o for o in self.asteroids
                                      if o is not a and o.special != "parasite"]
                    if candidates:
                        a.parasite_target = random.choice(candidates)

        # Gravity pulse event: pull everything to center
        if self.active_event == "gravity_pulse":
            cx, cy = SCREEN_W / 2, SCREEN_H / 2
            for a in self.asteroids:
                dx, dy = torus_direction(a.x, a.y, cx, cy)
                dist = math.hypot(dx, dy)
                if dist > 10:
                    force = 5000 / (dist + 50)
                    a.vx += (dx / dist) * force * dt
                    a.vy += (dy / dist) * force * dt

        # Remove dead asteroids (from parasite eating etc)
        self.asteroids = [a for a in self.asteroids if a.alive]

        # ---- BOSS ----
        if self.boss and self.boss.alive:
            etx, ety = self._enemy_target(self.boss.x, self.boss.y)
            tx = etx if etx is not None else SCREEN_W / 2
            ty = ety if ety is not None else SCREEN_H / 2
            self.boss.update(dt, tx, ty)

            # Behemoth layer shedding
            if isinstance(self.boss, Behemoth) and self.boss.should_shed_layer():
                self.screen_shake(15)
                self.flash_time = 0.15
                self.particles.extend(explosion(self.boss.x, self.boss.y, 30, 150, (255, 100, 0)))
                # Shed asteroids
                for i in range(4):
                    angle = math.tau * i / 4 + random.uniform(-0.3, 0.3)
                    spd = random.uniform(60, 120)
                    vx = math.cos(angle) * spd
                    vy = math.sin(angle) * spd
                    self.asteroids.append(
                        Asteroid(self.boss.x, self.boss.y, "medium", "normal", vx, vy))

            # SwarmQueen minion spawning
            if isinstance(self.boss, SwarmQueen) and self.boss.should_spawn():
                for i in range(3):
                    angle = random.uniform(0, math.tau)
                    spd = random.uniform(80, 150)
                    vx = math.cos(angle) * spd
                    vy = math.sin(angle) * spd
                    self.asteroids.append(
                        Asteroid(self.boss.x, self.boss.y, "small", "fast", vx, vy))
                self.particles.extend(explosion(self.boss.x, self.boss.y, 10, 60, (255, 180, 0)))

            # MirrorLord shooting
            if isinstance(self.boss, MirrorLord):
                etx, ety = self._enemy_target(self.boss.x, self.boss.y)
                if etx is not None:
                    bullet = self.boss.try_shoot(etx, ety)
                    if bullet:
                        self.boss_bullets.append(bullet)

        # Boss bullets
        for b in self.boss_bullets:
            b.update(dt)
        self.boss_bullets = [b for b in self.boss_bullets if b.alive]

        # ---- PORTALE ----
        self.portal_timer -= dt
        if self.portal_timer <= 0:
            new_portals = spawn_portal_pair()
            self.portals.extend(new_portals)
            self.portal_timer = random.uniform(PORTAL_SPAWN_INTERVAL_MIN, PORTAL_SPAWN_INTERVAL_MAX)

        for p in self.portals:
            p.update(dt)
            if random.random() < 0.3:
                col_map = {
                    "normal": (200, 200, 255), "angle_twist": (255, 200, 0),
                    "reverse_velocity": (255, 50, 50), "speed_boost": (50, 255, 100),
                    "speed_slow": (50, 100, 255),
                }
                pc = col_map.get(p.effect, (200, 200, 255))
                self.particles.extend(portal_particles(p.x, p.y, p.radius, pc, 1))

        self.portals = [p for p in self.portals if p.alive]

        # Teleportation
        teleportable = []
        if self.ship.alive:
            teleportable.append(self.ship)
        teleportable.extend(self.asteroids)
        teleportable.extend(self.ship.bullets)
        # Ship2 (co-op / host) can also use portals
        if self._mp_mode in ("host", "coop") and self._mp_ship2:
            if self._mp_ship2.alive:
                teleportable.append(self._mp_ship2)
            teleportable.extend(self._mp_ship2.bullets)

        for portal in self.portals:
            for obj in teleportable:
                if portal.try_teleport(obj):
                    self.particles.extend(warp_flash(obj.x, obj.y))
                    if obj is self.ship or obj is self._mp_ship2:
                        snd.play('portal')

        # ---- GRAVITY WELLS ----
        self.grav_well_timer -= dt
        if self.grav_well_timer <= 0:
            sx = self.ship.x if self.ship.alive else None
            sy = self.ship.y if self.ship.alive else None
            strength = 2.0 if self.active_event == "gravity_surge" else 1.0
            gw = spawn_gravity_well(sx, sy)
            gw.strength *= strength
            self.gravity_wells.append(gw)
            self.grav_well_timer = random.uniform(GRAV_WELL_SPAWN_INTERVAL_MIN, GRAV_WELL_SPAWN_INTERVAL_MAX)

        for gw in self.gravity_wells:
            gw.update(dt)
            if random.random() < 0.15:
                self.particles.extend(gravity_well_particles(gw.x, gw.y, gw.attract_radius))

            for a in self.asteroids:
                consumed = gw.apply_gravity(a, dt)
                if consumed:
                    a.alive = False
                    self.particles.extend(explosion(a.x, a.y, 15, 80, (150, 100, 255)))

            if self.ship.alive:
                consumed = gw.apply_gravity(self.ship, dt)
                if consumed and self.ship.take_hit():
                    self._kill_ship()

            # Ship2 gravity
            if self._mp_mode in ("host", "coop") and self._mp_ship2 and self._mp_ship2.alive:
                consumed = gw.apply_gravity(self._mp_ship2, dt)
                if consumed and self._mp_ship2.take_hit():
                    self._kill_ship2()

            for b in self.ship.bullets:
                gw.apply_gravity(b, dt * 0.3)

            # Ship2 bullets gravity
            if self._mp_mode in ("host", "coop") and self._mp_ship2:
                for b in self._mp_ship2.bullets:
                    gw.apply_gravity(b, dt * 0.3)

        self.gravity_wells = [gw for gw in self.gravity_wells if gw.alive]
        self.asteroids = [a for a in self.asteroids if a.alive]

        # ---- GRAVITY BOMB FIELDS ----
        for gbf in self.gravity_bomb_fields:
            gbf.update(dt)
            for a in self.asteroids:
                gbf.apply_gravity(a, dt)
        self.gravity_bomb_fields = [g for g in self.gravity_bomb_fields if g.alive]

        # ---- UFO ----
        _cfg_ufo = self._mp_game_config.get('ufo_spawns', True) if self._mp_game_config else True
        self.ufo_timer -= dt
        if self.ufo_timer <= 0 and _cfg_ufo:
            ufo_type = "small" if random.random() < 0.3 else "large"
            self.ufos.append(UFO(ufo_type))
            self.ufo_timer = random.uniform(UFO_SPAWN_INTERVAL_MIN, UFO_SPAWN_INTERVAL_MAX)

        for u in self.ufos:
            u.update(dt)
            etx, ety = self._enemy_target(u.x, u.y)
            if etx is not None:
                bullet = u.try_shoot(etx, ety)
                if bullet:
                    self.ufo_bullets.append(bullet)
        self.ufos = [u for u in self.ufos if u.alive]

        for b in self.ufo_bullets:
            b.update(dt)
        self.ufo_bullets = [b for b in self.ufo_bullets if b.alive]

        # ---- HUNTERS ----
        self.hunter_timer -= dt
        if self.hunter_timer <= 0 and self.level >= 4 and len(self.hunters) < 2:
            self.hunters.append(HunterDrone())
            self.hunter_timer = random.uniform(25, 45)

        for h in self.hunters:
            etx, ety = self._enemy_target(h.x, h.y)
            tx = etx if etx is not None else SCREEN_W / 2
            ty = ety if ety is not None else SCREEN_H / 2
            h.update(dt, tx, ty)
            if etx is not None:
                bullet = h.try_shoot(tx, ty)
                if bullet:
                    self.enemy_bullets.append(bullet)

        # ---- MIRRORS ----
        self.mirror_timer -= dt
        any_ship_alive = self.ship.alive or (self._mp_ship2 and self._mp_ship2.alive)
        if self.mirror_timer <= 0 and self.level >= 6 and len(self.mirrors) < 1 and any_ship_alive:
            src = self.ship if self.ship.alive else self._mp_ship2
            self.mirrors.append(MirrorEnemy(src.x, src.y, src.angle))
            self.mirror_timer = random.uniform(35, 55)

        for m in self.mirrors:
            etx, ety = self._enemy_target(m.x, m.y)
            tx = etx if etx is not None else SCREEN_W / 2
            ty = ety if ety is not None else SCREEN_H / 2
            m.update(dt, tx, ty)
            if etx is not None:
                bullet = m.try_shoot(tx, ty)
                if bullet:
                    self.enemy_bullets.append(bullet)

        # Enemy bullets
        for b in self.enemy_bullets:
            b.update(dt)
        self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]

        # ---- POWERUPS ----
        for p in self.powerups:
            p.update(dt)
            # Magnet perk — pull toward closest alive ship
            if "magnet_pickup" in self.owned_perks:
                magnet_ships = []
                if self.ship.alive:
                    magnet_ships.append(self.ship)
                if self._mp_mode in ("host", "coop") and self._mp_ship2 and self._mp_ship2.alive:
                    magnet_ships.append(self._mp_ship2)
                for ms in magnet_ships:
                    dx, dy = torus_direction(p.x, p.y, ms.x, ms.y)
                    dist = math.hypot(dx, dy)
                    if dist < 200 and dist > 5:
                        force = 300 / dist
                        p.vx += (dx / dist) * force
                        p.vy += (dy / dist) * force
        self.powerups = [p for p in self.powerups if p.alive]

        # ---- PARTICLES ----
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

        # ---- HOST: apply remote input BEFORE collisions ----
        if self._mp_mode == "host" and self._server and self._mp_ship2:
            remote_input = self._server.get_client_input()
            if remote_input and self._mp_ship2.alive:
                self._apply_remote_input(self._mp_ship2, remote_input, dt)
                # Thrust particles for remote ship2
                if self._mp_ship2.thrusting:
                    self.particles.extend(thrust_particles(
                        self._mp_ship2.x, self._mp_ship2.y, self._mp_ship2.angle,
                        self._mp_ship2.vx, self._mp_ship2.vy))
                    if self._mp_ship2.heat > 0.5:
                        self.particles.extend(heat_trail(
                            self._mp_ship2.x, self._mp_ship2.y,
                            self._mp_ship2.vx, self._mp_ship2.vy, self._mp_ship2.heat))
                # Homing targets for ship2 bullets
                targets = self.asteroids + self.ufos + self.hunters + self.mirrors
                if self.boss and self.boss.alive:
                    targets.append(self.boss)
                for b in self._mp_ship2.bullets:
                    if b.kind == "homing":
                        b.homing_targets = targets

        # ---- KOLIZJE ----
        self._handle_collisions()

        # ---- MULTIPLAYER SYNC ----
        self._mp_network_tick(dt)

        # ---- NASTEPNY LEVEL ----
        non_ghost_asteroids = [a for a in self.asteroids if a.special != "ghost"]
        wave_clear = len(non_ghost_asteroids) == 0 and len(self.ufos) == 0
        wave_clear = wave_clear and len(self.hunters) == 0 and len(self.mirrors) == 0
        if self.boss and self.boss.alive:
            wave_clear = False
        if wave_clear:
            # Kill leftover ghosts
            for a in self.asteroids:
                if a.special == "ghost":
                    self.particles.extend(explosion(a.x, a.y, 8, 60, (150, 150, 200)))
            self.asteroids = [a for a in self.asteroids if a.special != "ghost"]
            if self.lurk_timer > 5:
                bonus = int(self.lurk_timer * 100)
                self.score += bonus
                self.powerup_msg = f"LURK BONUS +{bonus}"
                self.powerup_msg_time = 2.0
            # Wave-clear partner respawn (MP)
            if self._mp_mode in ("host", "coop") and self.mp_respawn_mode == "wave":
                if self.ship1_dead_permanently:
                    self._try_respawn_partner("ship1")
                if self.ship2_dead_permanently:
                    self._try_respawn_partner("ship2")

            self.start_perk_selection()

    def _mp_cleanup(self):
        """Clean up multiplayer resources."""
        if self._server:
            self._server.stop()
            self._server = None
        if self._client:
            self._client.disconnect()
            self._client = None
        if self._scanner:
            self._scanner.stop()
            self._scanner = None
        self._mp_mode = None
        self._mp_ship2 = None
        self._mp_game_config = {}
        self._net_bullets_ship1 = []
        self._net_bullets_ship2 = []

    # ---- MULTIPLAYER NETWORKING ----

    def _mp_network_tick(self, dt):
        """Called every frame during gameplay for multiplayer sync."""
        if self._mp_mode is None:
            return

        self._net_send_timer += dt

        if self._mp_mode == "host" and self._server:
            # Remote input already applied before collisions (see update())
            # Track client name for display
            client_names = self._server.get_client_names()
            if client_names:
                self._mp_client_name = client_names[0][0]

            # Send state ~30 times/sec
            if self._net_send_timer >= 0.033:
                self._net_send_timer = 0.0
                state = self._build_state_snapshot()
                self._server.broadcast_state(state)

            # Check disconnect
            if self._server.client_count == 0 and self._server.status == "waiting":
                self.powerup_msg = "Player disconnected!"
                self.powerup_msg_time = 3.0
                self._mp_ship2 = None

        elif self._mp_mode == "client" and self._client:
            # Send our input
            if self._net_send_timer >= 0.033:
                self._net_send_timer = 0.0
                inp = self._capture_local_input()
                self._client.send_input(inp)

            # Receive state from host
            state = self._client.get_state()
            if state:
                self._apply_state_snapshot(state)

            # Check disconnect
            if not self._client.connected:
                self.powerup_msg = "Disconnected from host!"
                self.powerup_msg_time = 3.0
                self._mp_mode = None

    def _build_p1_input_map(self):
        """Build an input_map dict for P1 ship using configurable keyboard bindings."""
        from ship import KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SPACE, KEY_Z, KEY_X, KEY_C, KEY_A, KEY_D
        kb = self._kb_p1
        inp = {}
        inp[KEY_LEFT] = bool(rl.IsKeyDown(kb['left']))
        inp[KEY_RIGHT] = bool(rl.IsKeyDown(kb['right']))
        inp[KEY_UP] = bool(rl.IsKeyDown(kb['thrust']))
        inp[KEY_DOWN] = bool(rl.IsKeyDown(kb['brake']))
        inp[KEY_SPACE] = bool(rl.IsKeyDown(kb['shoot']))
        inp[KEY_Z] = bool(rl.IsKeyDown(kb['alt_brake']))
        inp[('p', KEY_X)] = bool(rl.IsKeyPressed(kb['alt1']))
        inp[('p', KEY_C)] = bool(rl.IsKeyPressed(kb['alt2']))
        inp[KEY_A] = bool(rl.IsKeyDown(kb['strafe_l']))
        inp[KEY_D] = bool(rl.IsKeyDown(kb['strafe_r']))
        return inp

    def _capture_local_input(self):
        """Capture current keyboard state as a dict (uses configurable P1 bindings)."""
        kb = self._kb_p1
        return {
            'up': bool(rl.IsKeyDown(kb['thrust'])),
            'down': bool(rl.IsKeyDown(kb['brake'])),
            'left': bool(rl.IsKeyDown(kb['left'])),
            'right': bool(rl.IsKeyDown(kb['right'])),
            'space': bool(rl.IsKeyDown(kb['shoot'])),
            'z': bool(rl.IsKeyDown(kb['alt_brake'])),
            'x': bool(rl.IsKeyPressed(kb['alt1'])),
            'c': bool(rl.IsKeyPressed(kb['alt2'])),
            'a': bool(rl.IsKeyDown(kb['strafe_l'])),
            'd': bool(rl.IsKeyDown(kb['strafe_r'])),
        }

    def _apply_remote_input(self, ship, inp, dt):
        """Simulate inputs on a Ship object based on remote input dict."""
        import config
        from utils import apply_wrap

        thrust = config.THRUST
        max_spd = config.MAX_SPEED

        # Rotation
        if inp.get('left'):
            ship.angle -= config.ROT_SPEED * dt
        if inp.get('right'):
            ship.angle += config.ROT_SPEED * dt

        # Thrust
        ship.thrusting = inp.get('up', False) and not ship.overheated
        if ship.thrusting:
            dir_x = math.sin(ship.angle)
            dir_y = -math.cos(ship.angle)
            ship.vx += thrust * dir_x * dt
            ship.vy += thrust * dir_y * dt

        # Brake
        if inp.get('z') or inp.get('down'):
            speed = math.hypot(ship.vx, ship.vy)
            if speed > 0:
                decel = config.BRAKE_FORCE * dt
                if decel >= speed:
                    ship.vx = 0.0
                    ship.vy = 0.0
                else:
                    factor = (speed - decel) / speed
                    ship.vx *= factor
                    ship.vy *= factor

        # Friction
        speed = math.hypot(ship.vx, ship.vy)
        if speed > 0 and not inp.get('z') and not inp.get('down'):
            decel = config.FRICTION * dt
            if decel >= speed:
                ship.vx = 0.0
                ship.vy = 0.0
            else:
                factor = (speed - decel) / speed
                ship.vx *= factor
                ship.vy *= factor

        # Speed cap
        speed = math.hypot(ship.vx, ship.vy)
        if speed > max_spd:
            factor = max_spd / speed
            ship.vx *= factor
            ship.vy *= factor

        # Move
        ship.x += ship.vx * dt
        ship.y += ship.vy * dt
        apply_wrap(ship)

        # Shooting
        if inp.get('space') and ship.shoot_cooldown <= 0 and len(ship.bullets) < 6:
            ship.shoot_cooldown = config.SHOOT_COOLDOWN
            from bullet import Bullet
            b = Bullet(ship.x, ship.y, ship.angle)
            ship.bullets.append(b)
            snd.play('shoot', 0.4)

        ship.shoot_cooldown = max(0, ship.shoot_cooldown - dt)

        # Update bullets
        for b in ship.bullets:
            b.update(dt)
        ship.bullets = [b for b in ship.bullets if b.alive]

        # Invulnerability
        if ship.invuln_time > 0:
            ship.invuln_time -= dt
            ship.invulnerable = ship.invuln_time > 0
        else:
            ship.invulnerable = False

    def _build_state_snapshot(self):
        """Build a lightweight dict of game state for network transmission."""
        s = {
            'ship1': {'x': self.ship.x, 'y': self.ship.y, 'a': self.ship.angle,
                       'vx': self.ship.vx, 'vy': self.ship.vy,
                       't': self.ship.thrusting, 'alive': self.ship.alive,
                       'heat': self.ship.heat,
                       'inv': self.ship.invulnerable,
                       'sh': self.ship.shield_hits,
                       'col': list(self.ship.ship_color),
                       'skin': self.ship.ship_skin},
            'score': self.score,
            'level': self.level,
            'lives': self.lives,
            'lives2': self.lives_ship2,
            'shared': self._mp_shared_map,
            'bloom': round(self.bloom_energy, 3),
            'flash': round(self.flash_time, 3),
            'shake': round(self.shake_amount, 2),
            'shake_t': round(self.shake_time, 2),
            'n1': self._mp_name,  # host name
            # Multiplayer death / respawn state
            's1dp': self.ship1_dead_permanently,
            's2dp': self.ship2_dead_permanently,
            'rmode': self.mp_respawn_mode,
            'rscore': self.mp_respawn_score_threshold,
            'rdtime': round(max(0, MP_RESPAWN_TIMER - (_time.time() - self.mp_respawn_death_time)), 1) if self.mp_respawn_death_time > 0 else 0,
            'gstate': self.state,  # so client knows about game_over / name_entry
        }
        if self._mp_ship2:
            s['ship2'] = {'x': self._mp_ship2.x, 'y': self._mp_ship2.y,
                          'a': self._mp_ship2.angle,
                          'vx': self._mp_ship2.vx, 'vy': self._mp_ship2.vy,
                          't': self._mp_ship2.thrusting, 'alive': self._mp_ship2.alive,
                          'inv': self._mp_ship2.invulnerable,
                          'sh': self._mp_ship2.shield_hits,
                          'col': list(self._mp_ship2.ship_color),
                          'skin': self._mp_ship2.ship_skin}
            # Get client name from server
            if self._server:
                client_names = self._server.get_client_names()
                if client_names:
                    s['n2'] = client_names[0][0]

        # Asteroids — include rot_speed for smooth client rendering
        if self._mp_shared_map:
            s['ast'] = [{'x': a.x, 'y': a.y, 'r': a.radius,
                          'vx': a.vx, 'vy': a.vy, 'a': a.angle,
                          'rs': a.rot_speed,
                          'sp': a.special or 'n', 'sz': a.size,
                          'id': id(a) % 100000}
                         for a in self.asteroids[:80]]
        else:
            s['ast'] = [{'x': a.x, 'y': a.y, 'r': a.radius,
                          'sp': a.special or 'n', 'sz': a.size}
                         for a in self.asteroids[:60]]

        # Bullets (ship1) — include velocity for rendering on client
        s['bul1'] = [{'x': b.x, 'y': b.y, 'vx': b.vx, 'vy': b.vy,
                       'r': b.radius, 'k': b.kind}
                      for b in self.ship.bullets[:20]]
        # Bullets (ship2)
        if self._mp_ship2:
            s['bul2'] = [{'x': b.x, 'y': b.y, 'vx': b.vx, 'vy': b.vy,
                           'r': b.radius, 'k': b.kind}
                          for b in self._mp_ship2.bullets[:20]]

        # Powerups
        s['pwr'] = [{'x': p.x, 'y': p.y, 'k': p.kind,
                     'mid': p.module_id if p.kind == 'module' else None}
                    for p in self.powerups[:20]]

        # UFOs
        s['ufos'] = [{'x': u.x, 'y': u.y, 'r': u.radius, 'vx': u.vx, 'vy': u.vy,
                      'tp': u.ufo_type, 'wt': u.wave_time}
                     for u in self.ufos if u.alive]

        # Hunters
        s['hnt'] = [{'x': h.x, 'y': h.y, 'r': h.radius, 'vx': h.vx, 'vy': h.vy,
                     'a': h.angle, 'hp': h.hp, 't': h.time}
                    for h in self.hunters if h.alive]

        # Mirrors
        s['mir'] = [{'x': m.x, 'y': m.y, 'r': m.radius, 'a': m.angle,
                     'hp': m.hp, 't': m.time}
                    for m in self.mirrors if m.alive]

        # Boss
        if self.boss and self.boss.alive:
            bt = type(self.boss).__name__
            bd = {'x': self.boss.x, 'y': self.boss.y, 'r': self.boss.radius,
                  'a': self.boss.angle, 'hp': self.boss.hp, 'mhp': self.boss.max_hp,
                  'bt': bt, 't': getattr(self.boss, 'time', 0),
                  'rs': getattr(self.boss, 'rot_speed', 0)}
            if hasattr(self.boss, 'verts'):
                bd['verts'] = self.boss.verts
            if hasattr(self.boss, 'layers_shed'):
                bd['ls'] = self.boss.layers_shed
            if hasattr(self.boss, 'shield_active'):
                bd['sa'] = self.boss.shield_active
            s['boss'] = bd

        # Enemy bullets (all types — drawn as simple colored circles)
        s['ebul'] = ([{'x': b.x, 'y': b.y, 'r': b.radius, 'tp': 'u'}
                      for b in self.ufo_bullets if b.alive] +
                     [{'x': b.x, 'y': b.y, 'r': b.radius, 'tp': 'e'}
                      for b in self.enemy_bullets if b.alive] +
                     [{'x': b.x, 'y': b.y, 'r': b.radius, 'tp': 'b'}
                      for b in self.boss_bullets if b.alive])

        # ---- WORLD OBJECTS ----
        # Portals (with partner linkage via index)
        s['ptl'] = []
        for p in self.portals:
            pd = {'x': p.x, 'y': p.y, 'r': p.radius, 'ef': p.effect,
                  'lt': round(p.lifetime, 2), 't': round(p.time, 2)}
            if p.partner and p.partner in self.portals:
                pd['pi'] = self.portals.index(p.partner)
            else:
                pd['pi'] = -1
            s['ptl'].append(pd)

        # Gravity wells
        s['gw'] = [{'x': g.x, 'y': g.y, 'r': g.radius, 'ar': g.attract_radius,
                     'cr': g.core_radius, 'str': round(g.strength, 2),
                     'lt': round(g.lifetime, 2), 't': round(g.time, 2)}
                    for g in self.gravity_wells if g.alive]

        # Gravity bomb fields
        s['gbf'] = [{'x': g.x, 'y': g.y, 'r': g.radius,
                      'lt': round(g.lifetime, 2), 't': round(g.time, 2)}
                     for g in self.gravity_bomb_fields if g.alive]

        # ---- VISUAL / HUD STATE ----
        s['aevt'] = self.active_event or ''
        s['aevt_t'] = round(self.event_time_left, 1) if self.active_event else 0
        s['bkout'] = self.blackout
        s['combo'] = self.combo
        s['combo_m'] = self.combo_multiplier
        s['pmsg'] = self.powerup_msg if self.powerup_msg_time > 0 else ''
        s['pmsg_t'] = round(self.powerup_msg_time, 2)
        s['emsg'] = self.event_msg if self.event_msg_time > 0 else ''
        s['emsg_t'] = round(self.event_msg_time, 2)
        s['wsm'] = round(self.wrap_score_mult, 2)
        s['djit'] = round(self.dynamic_jitter, 4)
        s['topo'] = get_topology()
        s['sec'] = self.sector.number
        s['sec_at'] = round(self.sector_announce_time, 2)
        s['sec_am'] = self.sector_announce_msg if self.sector_announce_time > 0 else ''
        s['sec_tt'] = round(self.sector_transition_time, 2)

        # Perks and perk selection
        s['perks'] = list(self.owned_perks)
        s['perk_sel'] = self.perk_selection_active
        if self.perk_selection_active:
            s['perk_ch'] = self.perk_choices

        # Network events (explosions, shake, sounds etc.)
        if self._net_events:
            s['evt'] = self._net_events[:50]  # cap to avoid huge payloads
            self._net_events.clear()

        return s

    def _apply_state_snapshot(self, state):
        """Client-side: apply received game state with interpolation."""
        shared = state.get('shared', False)

        # Update host ship position (we see it as ship2 from our perspective)
        s1 = state.get('ship1')
        if s1:
            if not self._mp_ship2:
                self._mp_ship2 = Ship(s1['x'], s1['y'])
            self._mp_ship2.x = s1['x']
            self._mp_ship2.y = s1['y']
            self._mp_ship2.angle = s1['a']
            self._mp_ship2.vx = s1['vx']
            self._mp_ship2.vy = s1['vy']
            self._mp_ship2.thrusting = s1.get('t', False)
            self._mp_ship2.alive = s1.get('alive', True)
            self._mp_ship2.heat = s1.get('heat', 0)
            self._mp_ship2.invulnerable = s1.get('inv', False)
            self._mp_ship2.shield_hits = s1.get('sh', 0)
            if 'col' in s1:
                self._mp_ship2.ship_color = tuple(s1['col'])
            if 'skin' in s1:
                self._mp_ship2.set_skin(s1['skin'])

        # Our own ship position from server
        s2 = state.get('ship2')
        if s2:
            self.ship.x = s2['x']
            self.ship.y = s2['y']
            self.ship.angle = s2['a']
            self.ship.vx = s2['vx']
            self.ship.vy = s2['vy']
            self.ship.thrusting = s2.get('t', False)
            self.ship.alive = s2.get('alive', True)
            self.ship.invulnerable = s2.get('inv', False)
            self.ship.shield_hits = s2.get('sh', 0)
            if 'col' in s2:
                self.ship.ship_color = tuple(s2['col'])
            if 'skin' in s2:
                self.ship.set_skin(s2['skin'])

        # Score/level
        self.score = state.get('score', self.score)
        self.level = state.get('level', self.level)
        # Lives: swap for client perspective (host's ship2 = our ship, host's ship1 = our partner)
        self.lives = state.get('lives2', self.lives)

        # Bloom, flash, shake from host
        self.bloom_energy = max(self.bloom_energy, state.get('bloom', 0))
        if state.get('flash', 0) > self.flash_time:
            self.flash_time = state['flash']
        if state.get('shake', 0) > self.shake_amount:
            self.shake_amount = state['shake']
            self.shake_time = state.get('shake_t', self.shake_amount / SHAKE_DECAY)

        # Player names
        self._mp_host_name = state.get('n1', 'Host')
        self._mp_client_name = state.get('n2', self._mp_name)

        # Replay events (explosions, shake, sounds, etc.)
        for evt in state.get('evt', []):
            self._replay_net_event(evt)

        # Reconstruct asteroids from host data (shared map)
        if shared:
            ast_data = state.get('ast', [])
            # Build ID-based lookup of existing asteroids for reuse
            old_by_id = {}
            for a in self.asteroids:
                aid = getattr(a, '_net_id', None)
                if aid is not None:
                    old_by_id[aid] = a
            new_asts = []
            for ad in ast_data:
                net_id = ad.get('id', 0)
                existing = old_by_id.get(net_id)
                if existing and existing.size == ad['sz']:
                    # Reuse existing asteroid object — just update position/velocity
                    existing.x = ad['x']
                    existing.y = ad['y']
                    existing.vx = ad.get('vx', 0)
                    existing.vy = ad.get('vy', 0)
                    existing.angle = ad.get('a', 0)
                    existing.rot_speed = ad.get('rs', existing.rot_speed)
                    existing.radius = ad['r']
                    new_asts.append(existing)
                else:
                    # New asteroid — create with explicit vx/vy
                    sp = ad.get('sp', 'n')
                    special = 'normal' if sp == 'n' else sp
                    a = Asteroid(ad['x'], ad['y'], ad['sz'], special,
                                 ad.get('vx', 0), ad.get('vy', 0))
                    a.angle = ad.get('a', 0)
                    a.rot_speed = ad.get('rs', a.rot_speed)
                    a.radius = ad['r']
                    if sp == 'n':
                        a.special = None
                    a._net_id = net_id
                    new_asts.append(a)
            self.asteroids = new_asts

        # Reconstruct bullets from host data
        bul1_data = state.get('bul1', [])
        bul2_data = state.get('bul2', [])
        # These are visual-only bullet proxies for the client
        self._net_bullets_ship1 = bul1_data
        self._net_bullets_ship2 = bul2_data

        # Reconstruct powerups from host data (client doesn't run game logic)
        pwr_data = state.get('pwr', [])
        self.powerups = []
        for pd in pwr_data:
            p = PowerUp(pd['x'], pd['y'], kind=pd['k'],
                        module_id=pd.get('mid'))
            self.powerups.append(p)

        # Reconstruct UFOs
        ufo_data = state.get('ufos', [])
        self.ufos = []
        for ud in ufo_data:
            u = UFO(ud.get('tp', 'large'))
            u.x = ud['x']
            u.y = ud['y']
            u.vx = ud.get('vx', 0)
            u.vy = ud.get('vy', 0)
            u.wave_time = ud.get('wt', 0)
            self.ufos.append(u)

        # Reconstruct Hunters
        hunter_data = state.get('hnt', [])
        self.hunters = []
        for hd in hunter_data:
            h = HunterDrone(hd['x'], hd['y'])
            h.vx = hd.get('vx', 0)
            h.vy = hd.get('vy', 0)
            h.angle = hd.get('a', 0)
            h.hp = hd.get('hp', 1)
            h.time = hd.get('t', 0)
            self.hunters.append(h)

        # Reconstruct Mirrors (constructor transforms coords, so override after)
        mirror_data = state.get('mir', [])
        self.mirrors = []
        for md in mirror_data:
            m = MirrorEnemy(0, 0, 0)
            m.x = md['x']
            m.y = md['y']
            m.angle = md.get('a', 0)
            m.hp = md.get('hp', 1)
            m.time = md.get('t', 0)
            self.mirrors.append(m)

        # Reconstruct Boss
        boss_data = state.get('boss')
        if boss_data:
            bt = boss_data.get('bt', 'Boss')
            if bt == 'SwarmQueen':
                self.boss = SwarmQueen(1)
            elif bt == 'MirrorLord':
                self.boss = MirrorLord(1, 0, 0, 0)
            else:
                self.boss = Behemoth(1)
            self.boss.x = boss_data['x']
            self.boss.y = boss_data['y']
            self.boss.radius = boss_data['r']
            self.boss.angle = boss_data.get('a', 0)
            self.boss.hp = boss_data.get('hp', 1)
            self.boss.max_hp = boss_data.get('mhp', 1)
            self.boss.time = boss_data.get('t', 0)
            self.boss.rot_speed = boss_data.get('rs', 0)
            if 'verts' in boss_data:
                self.boss.verts = boss_data['verts']
            if 'ls' in boss_data:
                self.boss.layers_shed = boss_data['ls']
            if 'sa' in boss_data:
                self.boss.shield_active = boss_data['sa']
        else:
            self.boss = None

        # Reconstruct enemy bullets (visual proxies for drawing)
        from types import SimpleNamespace
        self.ufo_bullets = []
        self.enemy_bullets = []
        self.boss_bullets = []
        for bd in state.get('ebul', []):
            proxy = SimpleNamespace(x=bd['x'], y=bd['y'], radius=bd['r'], alive=True)
            tp = bd.get('tp', 'e')
            if tp == 'u':
                self.ufo_bullets.append(proxy)
            elif tp == 'b':
                self.boss_bullets.append(proxy)
            else:
                self.enemy_bullets.append(proxy)

        # Partner lives (host's ship1 = our ship2/partner)
        if 'lives' in state:
            self.lives_ship2 = state['lives']

        # Multiplayer death / respawn state from host
        if 's1dp' in state:
            # For client: host's ship1 = our ship2, host's ship2 = our ship1
            self.ship2_dead_permanently = state['s1dp']
            self.ship1_dead_permanently = state['s2dp']
            self.mp_respawn_mode = state.get('rmode', 'wave')
            self.mp_respawn_score_threshold = state.get('rscore', 0)
            self.mp_respawn_death_time = state.get('rdtime', 0)

        # ---- RECONSTRUCT PORTALS (with partner linkage) ----
        ptl_data = state.get('ptl', [])
        new_portals = []
        for pd in ptl_data:
            p = Portal(pd['x'], pd['y'], pd.get('ef', 'normal'))
            p.radius = pd.get('r', p.radius)
            p.lifetime = pd.get('lt', p.lifetime)
            p.time = pd.get('t', 0)
            p.alive = p.lifetime > 0
            new_portals.append(p)
        # Link partners by index
        for i, pd in enumerate(ptl_data):
            pi = pd.get('pi', -1)
            if 0 <= pi < len(new_portals) and pi != i:
                new_portals[i].partner = new_portals[pi]
        self.portals = new_portals

        # ---- RECONSTRUCT GRAVITY WELLS ----
        gw_data = state.get('gw', [])
        new_gw = []
        for gd in gw_data:
            gw = GravityWell(gd['x'], gd['y'])
            gw.radius = gd.get('r', gw.radius)
            gw.attract_radius = gd.get('ar', gw.attract_radius)
            gw.core_radius = gd.get('cr', gw.core_radius)
            gw.strength = gd.get('str', gw.strength)
            gw.lifetime = gd.get('lt', gw.lifetime)
            gw.time = gd.get('t', 0)
            gw.alive = gw.lifetime > 0
            new_gw.append(gw)
        self.gravity_wells = new_gw

        # ---- RECONSTRUCT GRAVITY BOMB FIELDS ----
        gbf_data = state.get('gbf', [])
        new_gbf = []
        for gd in gbf_data:
            g = GravityBombField(gd['x'], gd['y'])
            g.radius = gd.get('r', g.radius)
            g.lifetime = gd.get('lt', g.lifetime)
            g.time = gd.get('t', 0)
            g.alive = g.lifetime > 0
            new_gbf.append(g)
        self.gravity_bomb_fields = new_gbf

        # ---- VISUAL / HUD STATE ----
        if 'aevt' in state:
            evt_name = state['aevt']
            self.active_event = evt_name if evt_name else None
            self.event_time_left = state.get('aevt_t', 0)
        if 'bkout' in state:
            self.blackout = state['bkout']
        if 'combo' in state:
            self.combo = state['combo']
        if 'combo_m' in state:
            self.combo_multiplier = state['combo_m']
        if 'pmsg' in state:
            self.powerup_msg = state['pmsg']
            self.powerup_msg_time = state.get('pmsg_t', 0)
        if 'emsg' in state:
            self.event_msg = state['emsg']
            self.event_msg_time = state.get('emsg_t', 0)
        if 'wsm' in state:
            self.wrap_score_mult = state['wsm']
        if 'djit' in state:
            self.dynamic_jitter = state['djit']

        # ---- TOPOLOGY ----
        if 'topo' in state:
            set_topology(state['topo'])

        # ---- SECTOR ----
        sec_num = state.get('sec', 0)
        if sec_num > 0 and sec_num != self.sector.number:
            self.sector = Sector(sec_num)
        if 'sec_at' in state:
            self.sector_announce_time = state['sec_at']
        if 'sec_am' in state and state['sec_am']:
            self.sector_announce_msg = state['sec_am']
        if 'sec_tt' in state:
            self.sector_transition_time = state['sec_tt']

        # ---- PERKS & PERK SELECTION ----
        if 'perks' in state:
            self.owned_perks = set(state['perks'])
            self.ship.perks = self.owned_perks
        if 'perk_sel' in state:
            self.perk_selection_active = state['perk_sel']
        if 'perk_ch' in state:
            self.perk_choices = state['perk_ch']

        # Sync game state transitions from host (game_over, name_entry)
        host_state = state.get('gstate')
        if host_state in ('game_over', 'name_entry') and self.state == 'playing':
            self._go_sel = 0
            if qualifies_for_leaderboard(self.score, self._leaderboard):
                self.state = "name_entry"
                self._name_input = ""
                self._name_entry_done = False
                self._name_cursor_blink = 0.0
            else:
                self.state = "game_over"

    def _replay_net_event(self, evt):
        """Replay a single network event on the client (particles, sounds, shake)."""
        t = evt.get('t')
        if t == 'exp':
            # Explosion particles
            c = tuple(evt.get('c', [255, 200, 50]))
            self.particles.extend(explosion(
                evt['x'], evt['y'], evt.get('n', 15), evt.get('s', 120), c))
        elif t == 'cexp':
            # Chain explosion
            self.particles.extend(chain_explosion(evt['x'], evt['y']))
        elif t == 'shk':
            # Screen shake
            a = evt.get('a', 5)
            self.shake_amount = max(self.shake_amount, a)
            self.shake_time = a / SHAKE_DECAY
        elif t == 'fls':
            # Flash
            self.flash_time = max(self.flash_time, evt.get('d', 0.15))
        elif t == 'snd':
            # Sound effect
            snd.play(evt.get('n', ''), evt.get('v', 1.0))

    def _kill_ship(self):
        self.lives -= 1
        self.particles.extend(explosion(self.ship.x, self.ship.y, 35, 180,
                                        (255, 255, 255), 0.8, 3.0))
        self.screen_shake(15)
        snd.play('ship_die')
        self.bloom_energy = min(1.0, self.bloom_energy + 0.5)
        self._emit_event({"t": "exp", "x": self.ship.x, "y": self.ship.y,
                           "n": 35, "s": 180, "c": [255, 255, 255]})
        self._emit_event({"t": "shk", "a": 15})
        self._emit_event({"t": "snd", "n": "ship_die"})
        if self.lives <= 0:
            if self._mp_mode:
                # Multiplayer: mark permanently dead, check if ALL dead
                self.ship1_dead_permanently = True
                if self._mp_all_dead():
                    self._mp_game_over()
                else:
                    # Record death for partner respawn tracking
                    self.mp_respawn_score_threshold = self.score + MP_RESPAWN_SCORE
                    self.mp_respawn_death_time = _time.time()
            else:
                # Singleplayer: immediate game over
                self._go_sel = 0
                if qualifies_for_leaderboard(self.score, self._leaderboard):
                    self.state = "name_entry"
                    self._name_input = ""
                    self._name_entry_done = False
                    self._name_cursor_blink = 0.0
                else:
                    self.state = "game_over"
        else:
            self.respawn_timer = 1.5

    def _kill_ship2(self):
        """Kill ship2 in multiplayer. Mirrors _kill_ship logic."""
        self.lives_ship2 -= 1
        self.particles.extend(explosion(self._mp_ship2.x, self._mp_ship2.y,
                                        35, 180, (100, 255, 100), 0.8, 3.0))
        self.screen_shake(12)
        snd.play('ship_die')
        self._emit_event({"t": "exp", "x": self._mp_ship2.x, "y": self._mp_ship2.y,
                           "n": 35, "s": 180, "c": [100, 255, 100]})
        self._emit_event({"t": "shk", "a": 12})
        self._emit_event({"t": "snd", "n": "ship_die"})
        self._mp_ship2.alive = False
        if self.lives_ship2 <= 0:
            self.ship2_dead_permanently = True
            if self._mp_all_dead():
                self._mp_game_over()
            else:
                self.mp_respawn_score_threshold = self.score + MP_RESPAWN_SCORE
                self.mp_respawn_death_time = _time.time()
        else:
            self.respawn_timer_ship2 = 1.5

    def _mp_all_dead(self):
        """Check if all ships in multiplayer are permanently dead."""
        ship1_dead = self.ship1_dead_permanently or self.lives <= 0
        ship2_dead = not self._mp_ship2 or self.ship2_dead_permanently or self.lives_ship2 <= 0
        return ship1_dead and ship2_dead

    def _mp_game_over(self):
        """Trigger game over in multiplayer."""
        self._go_sel = 0
        if qualifies_for_leaderboard(self.score, self._leaderboard):
            self.state = "name_entry"
            self._name_input = ""
            self._name_entry_done = False
            self._name_cursor_blink = 0.0
        else:
            self.state = "game_over"

    def _try_respawn_partner(self, who):
        """Attempt to respawn a permanently dead partner. who = 'ship1' or 'ship2'."""
        if who == "ship1" and self.ship1_dead_permanently:
            self.ship1_dead_permanently = False
            self.lives = 1
            self.ship.reset(SCREEN_W // 2, SCREEN_H // 2)
            self.powerup_msg = f"{self._mp_name} RESPAWNED!"
            self.powerup_msg_time = 2.0
            self._emit_event({"t": "snd", "n": "powerup"})
            snd.play('powerup')
        elif who == "ship2" and self.ship2_dead_permanently and self._mp_ship2:
            self.ship2_dead_permanently = False
            self.lives_ship2 = 1
            self._mp_ship2.reset(SCREEN_W // 2 + 80, SCREEN_H // 2)
            client_name = self._mp_client_name or "P2"
            self.powerup_msg = f"{client_name} RESPAWNED!"
            self.powerup_msg_time = 2.0
            self._emit_event({"t": "snd", "n": "powerup"})
            snd.play('powerup')

    def _handle_collisions(self):
        # ---- Bullet <-> Asteroid ----
        asteroids_to_destroy = []
        for b in self.ship.bullets:
            if not b.alive:
                continue
            for a in self.asteroids:
                if not a.alive:
                    continue
                if circle_collision(b.x, b.y, b.radius, a.x, a.y, a.radius):
                    if a.special == "ghost" and b.kind != "homing":
                        continue

                    # Gravity bomb detonation
                    if b.kind == "gravity_bomb":
                        self.gravity_bomb_fields.append(GravityBombField(b.x, b.y))
                        self.particles.extend(explosion(b.x, b.y, 25, 100, (200, 50, 255)))
                        self.screen_shake(8)
                        b.alive = False
                        break

                    # Crystal: multi-hit
                    if a.special == "crystal" and a.hp > 1:
                        a.hp -= 1
                        self.particles.extend(explosion(a.x, a.y, 8, 60, (0, 255, 255)))
                        self.screen_shake(2)
                        if b.pierce and not b.pierced_once:
                            b.pierced_once = True
                        else:
                            b.alive = False
                        break

                    if b.pierce and not b.pierced_once:
                        b.pierced_once = True
                    else:
                        b.alive = False

                    if a not in [x[0] for x in asteroids_to_destroy]:
                        asteroids_to_destroy.append((a, b))
                    break

        for a, b in asteroids_to_destroy:
            if a in self.asteroids:
                self.asteroids.remove(a)
                self.destroy_asteroid(a, b)

        # ---- Bullet <-> Boss ----
        if self.boss and self.boss.alive:
            for b in self.ship.bullets:
                if not b.alive:
                    continue
                if circle_collision(b.x, b.y, b.radius, self.boss.x, self.boss.y, self.boss.radius):
                    b.alive = False
                    if self.boss.take_hit():
                        self.boss.alive = False
                        self.add_score(self.boss.points)
                        self.particles.extend(explosion(self.boss.x, self.boss.y, 50, 250, (255, 200, 0), 1.0, 4.0))
                        self.screen_shake(25)
                        self.flash_time = 0.3
                        self.powerup_msg = "BOSS DESTROYED!"
                        self.powerup_msg_time = 3.0
                        snd.play('big_explosion')
                        self.bloom_energy = min(1.0, self.bloom_energy + 0.5)
                        self._emit_event({"t": "exp", "x": self.boss.x, "y": self.boss.y,
                                           "n": 50, "s": 250, "c": [255, 200, 0]})
                        self._emit_event({"t": "shk", "a": 25})
                        self._emit_event({"t": "fls", "d": 0.3})
                        self._emit_event({"t": "snd", "n": "big_explosion"})
                        # Drop powerups
                        for _ in range(3):
                            pu = PowerUp(
                                self.boss.x + random.uniform(-30, 30),
                                self.boss.y + random.uniform(-30, 30))
                            self.powerups.append(pu)
                    else:
                        self.particles.extend(explosion(self.boss.x, self.boss.y, 8, 60, (255, 150, 50)))
                        snd.play('boss_hit')
                        self.bloom_energy = min(1.0, self.bloom_energy + 0.1)
                        self._emit_event({"t": "exp", "x": self.boss.x, "y": self.boss.y,
                                           "n": 8, "s": 60, "c": [255, 150, 50]})
                        self._emit_event({"t": "snd", "n": "boss_hit"})
                    break

        # ---- Bullet <-> UFO ----
        for b in self.ship.bullets:
            if not b.alive:
                continue
            for u in self.ufos:
                if circle_collision(b.x, b.y, b.radius, u.x, u.y, u.radius):
                    b.alive = False
                    u.alive = False
                    self.add_score(u.points)
                    self.particles.extend(explosion(u.x, u.y, 30, 150, (100, 255, 100)))
                    self.screen_shake(10)
                    self._emit_event({"t": "exp", "x": u.x, "y": u.y,
                                       "n": 30, "s": 150, "c": [100, 255, 100]})
                    self._emit_event({"t": "shk", "a": 10})
                    self._emit_event({"t": "snd", "n": "explosion"})
                    break

        # ---- Bullet <-> Hunter ----
        for b in self.ship.bullets:
            if not b.alive:
                continue
            for h in self.hunters:
                if circle_collision(b.x, b.y, b.radius, h.x, h.y, h.radius):
                    b.alive = False
                    if h.take_hit():
                        h.alive = False
                        self.add_score(h.points)
                        self.particles.extend(explosion(h.x, h.y, 25, 140, (255, 50, 50)))
                        self.screen_shake(8)
                        self._emit_event({"t": "exp", "x": h.x, "y": h.y,
                                           "n": 25, "s": 140, "c": [255, 50, 50]})
                        self._emit_event({"t": "shk", "a": 8})
                    else:
                        self.particles.extend(explosion(h.x, h.y, 8, 60, (255, 100, 100)))
                        self._emit_event({"t": "exp", "x": h.x, "y": h.y,
                                           "n": 8, "s": 60, "c": [255, 100, 100]})
                    self._emit_event({"t": "snd", "n": "explosion"})
                    break

        # ---- Bullet <-> Mirror ----
        for b in self.ship.bullets:
            if not b.alive:
                continue
            for m in self.mirrors:
                if circle_collision(b.x, b.y, b.radius, m.x, m.y, m.radius):
                    b.alive = False
                    if m.take_hit():
                        m.alive = False
                        self.add_score(m.points)
                        self.particles.extend(explosion(m.x, m.y, 30, 160, (255, 0, 255)))
                        self.screen_shake(10)
                        self._emit_event({"t": "exp", "x": m.x, "y": m.y,
                                           "n": 30, "s": 160, "c": [255, 0, 255]})
                        self._emit_event({"t": "shk", "a": 10})
                    else:
                        self.particles.extend(explosion(m.x, m.y, 8, 60, (255, 100, 255)))
                        self._emit_event({"t": "exp", "x": m.x, "y": m.y,
                                           "n": 8, "s": 60, "c": [255, 100, 255]})
                    self._emit_event({"t": "snd", "n": "explosion"})
                    break

        # ---- Ship <-> Asteroid ----
        if self.ship.alive:
            for a in self.asteroids:
                if not a.alive:
                    continue
                if circle_collision(self.ship.x, self.ship.y, self.ship.radius, a.x, a.y, a.radius):
                    if a.special == "ghost":
                        continue
                    if self.ship.thrust_shield_timer > 0:
                        snd.play('shield_hit')
                        if a in self.asteroids:
                            self.asteroids.remove(a)
                            self.destroy_asteroid(a)
                        break
                    if self.ship.take_hit():
                        self._kill_ship()
                        break
                    else:
                        snd.play('shield_hit')
                        if a in self.asteroids:
                            self.asteroids.remove(a)
                            self.destroy_asteroid(a)
                        break

        # ---- Ship <-> Boss ----
        if self.boss and self.boss.alive and self.ship.alive:
            if circle_collision(self.ship.x, self.ship.y, self.ship.radius,
                                self.boss.x, self.boss.y, self.boss.radius):
                if self.ship.take_hit():
                    self._kill_ship()

        # ---- Ship <-> enemy bullets (UFO + hunter + mirror + boss) ----
        all_enemy_bullets = self.ufo_bullets + self.enemy_bullets + self.boss_bullets
        for b in all_enemy_bullets:
            if not b.alive:
                continue
            if not self.ship.alive:
                break
            if circle_collision(self.ship.x, self.ship.y, self.ship.radius, b.x, b.y, b.radius):
                b.alive = False
                if self.ship.thrust_shield_timer > 0:
                    continue
                if self.ship.take_hit():
                    self._kill_ship()
                    break

        # ---- Ship <-> UFO / Hunter / Mirror (collision) ----
        for enemy_list, col_color in [(self.ufos, (100, 255, 100)),
                                       (self.hunters, (255, 50, 50)),
                                       (self.mirrors, (255, 0, 255))]:
            for e in enemy_list:
                if not self.ship.alive:
                    break
                if circle_collision(self.ship.x, self.ship.y, self.ship.radius,
                                    e.x, e.y, e.radius):
                    e.alive = False
                    pts = getattr(e, 'points', 0)
                    if pts:
                        self.add_score(pts)
                    self.particles.extend(explosion(e.x, e.y, 30, 150, col_color))
                    self._emit_event({"t": "exp", "x": e.x, "y": e.y,
                                       "n": 30, "s": 150, "c": list(col_color)})
                    if self.ship.take_hit():
                        self._kill_ship()
                        break

        # ---- Ship <-> Powerup ----
        if self.ship.alive:
            for p in self.powerups:
                if not p.alive:
                    continue
                if circle_collision(self.ship.x, self.ship.y, self.ship.radius + 8,
                                    p.x, p.y, p.radius):
                    p.alive = False
                    snd.play('powerup')
                    self._emit_event({"t": "snd", "n": "powerup"})
                    if p.kind == "nuke":
                        nuke_targets = [a for a in self.asteroids if a.size in ("small", "medium")]
                        for a in nuke_targets:
                            if a in self.asteroids:
                                self.asteroids.remove(a)
                            self.add_score(ASTEROID_POINTS.get(a.size, 50))
                            self.particles.extend(explosion(a.x, a.y, 10, 100, (255, 50, 50)))
                            self._emit_event({"t": "exp", "x": a.x, "y": a.y,
                                               "n": 10, "s": 100, "c": [255, 50, 50]})
                        self.screen_shake(20)
                        self.flash_time = 0.2
                        self.powerup_msg = "NUKE"
                        self.powerup_msg_time = 2.0
                        self._emit_event({"t": "shk", "a": 20})
                        self._emit_event({"t": "fls", "d": 0.2})
                    elif p.kind == "module":
                        # Module pickup
                        if p.module_id:
                            self.ship.add_module(p.module_id)
                            mod_info = MODULES.get(p.module_id, {})
                            self.powerup_msg = f"MODULE: {mod_info.get('name', p.module_id)}"
                            self.powerup_msg_time = 2.0
                    elif p.kind == "shield":
                        self.ship.shield_hits = max(self.ship.shield_hits, 2)
                        self.powerup_msg = "SHIELD"
                        self.powerup_msg_time = 2.0
                    elif p.kind == "speedboost":
                        self.ship.apply_powerup("speedboost")
                        self.powerup_msg = "SPEED BOOST"
                        self.powerup_msg_time = 2.0
                    else:
                        self.ship.apply_powerup(p.kind)
                        info = POWERUP_TYPES.get(p.kind, {})
                        self.powerup_msg = info.get("desc", p.kind.upper())
                        self.powerup_msg_time = 2.0

        # ---- Ship2 <-> Powerup (host/co-op) ----
        if self._mp_mode in ("host", "coop") and self._mp_ship2 and self._mp_ship2.alive:
            for p in self.powerups:
                if not p.alive:
                    continue
                if circle_collision(self._mp_ship2.x, self._mp_ship2.y,
                                    self._mp_ship2.radius + 8, p.x, p.y, p.radius):
                    p.alive = False
                    snd.play('powerup')
                    self._emit_event({"t": "snd", "n": "powerup"})
                    if p.kind == "nuke":
                        nuke_targets = [a for a in self.asteroids if a.size in ("small", "medium")]
                        for a in nuke_targets:
                            if a in self.asteroids:
                                self.asteroids.remove(a)
                            self.add_score(ASTEROID_POINTS.get(a.size, 50))
                            self.particles.extend(explosion(a.x, a.y, 10, 100, (255, 50, 50)))
                            self._emit_event({"t": "exp", "x": a.x, "y": a.y,
                                               "n": 10, "s": 100, "c": [255, 50, 50]})
                        self.screen_shake(20)
                        self.flash_time = 0.2
                        self.powerup_msg = "NUKE"
                        self.powerup_msg_time = 2.0
                        self._emit_event({"t": "shk", "a": 20})
                        self._emit_event({"t": "fls", "d": 0.2})
                    elif p.kind == "module":
                        if p.module_id:
                            self._mp_ship2.add_module(p.module_id)
                            mod_info = MODULES.get(p.module_id, {})
                            self.powerup_msg = f"P2 MODULE: {mod_info.get('name', p.module_id)}"
                            self.powerup_msg_time = 2.0
                    elif p.kind == "shield":
                        self._mp_ship2.shield_hits = max(self._mp_ship2.shield_hits, 2)
                        self.powerup_msg = "P2 SHIELD"
                        self.powerup_msg_time = 2.0
                    elif p.kind == "speedboost":
                        self._mp_ship2.apply_powerup("speedboost")
                        self.powerup_msg = "P2 SPEED BOOST"
                        self.powerup_msg_time = 2.0
                    else:
                        self._mp_ship2.apply_powerup(p.kind)
                        info = POWERUP_TYPES.get(p.kind, {})
                        self.powerup_msg = "P2 " + info.get("desc", p.kind.upper())
                        self.powerup_msg_time = 2.0

        # Gravity bomb bullets detonation on lifetime end
        for b in self.ship.bullets:
            if b.kind == "gravity_bomb" and not b.alive:
                self.gravity_bomb_fields.append(GravityBombField(b.x, b.y))
                self.particles.extend(explosion(b.x, b.y, 25, 100, (200, 50, 255)))
                self.screen_shake(8)
        # Ship2 gravity bombs
        if self._mp_mode in ("host", "coop") and self._mp_ship2:
            for b in self._mp_ship2.bullets:
                if b.kind == "gravity_bomb" and not b.alive:
                    self.gravity_bomb_fields.append(GravityBombField(b.x, b.y))
                    self.particles.extend(explosion(b.x, b.y, 25, 100, (200, 50, 255)))
                    self.screen_shake(8)

        # ---- SHIP2 COLLISIONS (multiplayer host / co-op) ----
        if self._mp_mode in ("host", "coop") and self._mp_ship2 and self._mp_ship2.alive:
            # Ship2 bullets vs asteroids
            s2_destroy = []
            for b in self._mp_ship2.bullets:
                if not b.alive:
                    continue
                for a in self.asteroids:
                    if not a.alive:
                        continue
                    if circle_collision(b.x, b.y, b.radius, a.x, a.y, a.radius):
                        if a.special == "ghost":
                            continue
                        b.alive = False
                        if a not in [x[0] for x in s2_destroy]:
                            s2_destroy.append((a, b))
                        break
            for a, b in s2_destroy:
                if a in self.asteroids:
                    self.asteroids.remove(a)
                    self.destroy_asteroid(a, b)

            # Ship2 bullets vs Boss
            if self.boss and self.boss.alive:
                for b in self._mp_ship2.bullets:
                    if not b.alive:
                        continue
                    if circle_collision(b.x, b.y, b.radius, self.boss.x, self.boss.y, self.boss.radius):
                        b.alive = False
                        if self.boss.take_hit():
                            self.boss.alive = False
                            self.add_score(self.boss.points)
                            self.particles.extend(explosion(self.boss.x, self.boss.y, 50, 250, (255, 200, 0), 1.0, 4.0))
                            self.screen_shake(25)
                            self.flash_time = 0.3
                            self.powerup_msg = "BOSS DESTROYED!"
                            self.powerup_msg_time = 3.0
                            snd.play('big_explosion')
                            self.bloom_energy = min(1.0, self.bloom_energy + 0.5)
                            self._emit_event({"t": "exp", "x": self.boss.x, "y": self.boss.y,
                                               "n": 50, "s": 250, "c": [255, 200, 0]})
                            self._emit_event({"t": "shk", "a": 25})
                            self._emit_event({"t": "fls", "d": 0.3})
                            self._emit_event({"t": "snd", "n": "big_explosion"})
                            for _ in range(3):
                                pu = PowerUp(
                                    self.boss.x + random.uniform(-30, 30),
                                    self.boss.y + random.uniform(-30, 30))
                                self.powerups.append(pu)
                        else:
                            self.particles.extend(explosion(self.boss.x, self.boss.y, 8, 60, (255, 150, 50)))
                            snd.play('boss_hit')
                            self.bloom_energy = min(1.0, self.bloom_energy + 0.1)
                            self._emit_event({"t": "exp", "x": self.boss.x, "y": self.boss.y,
                                               "n": 8, "s": 60, "c": [255, 150, 50]})
                            self._emit_event({"t": "snd", "n": "boss_hit"})
                        break

            # Ship2 bullets vs UFO
            for b in self._mp_ship2.bullets:
                if not b.alive:
                    continue
                for u in self.ufos:
                    if circle_collision(b.x, b.y, b.radius, u.x, u.y, u.radius):
                        b.alive = False
                        u.alive = False
                        self.add_score(u.points)
                        self.particles.extend(explosion(u.x, u.y, 30, 150, (100, 255, 100)))
                        self.screen_shake(10)
                        self._emit_event({"t": "exp", "x": u.x, "y": u.y,
                                           "n": 30, "s": 150, "c": [100, 255, 100]})
                        self._emit_event({"t": "shk", "a": 10})
                        self._emit_event({"t": "snd", "n": "explosion"})
                        break

            # Ship2 bullets vs Hunter
            for b in self._mp_ship2.bullets:
                if not b.alive:
                    continue
                for h in self.hunters:
                    if circle_collision(b.x, b.y, b.radius, h.x, h.y, h.radius):
                        b.alive = False
                        if h.take_hit():
                            h.alive = False
                            self.add_score(h.points)
                            self.particles.extend(explosion(h.x, h.y, 25, 140, (255, 50, 50)))
                            self.screen_shake(8)
                            self._emit_event({"t": "exp", "x": h.x, "y": h.y,
                                               "n": 25, "s": 140, "c": [255, 50, 50]})
                            self._emit_event({"t": "shk", "a": 8})
                        else:
                            self.particles.extend(explosion(h.x, h.y, 8, 60, (255, 100, 100)))
                            self._emit_event({"t": "exp", "x": h.x, "y": h.y,
                                               "n": 8, "s": 60, "c": [255, 100, 100]})
                        self._emit_event({"t": "snd", "n": "explosion"})
                        break

            # Ship2 bullets vs Mirror
            for b in self._mp_ship2.bullets:
                if not b.alive:
                    continue
                for m in self.mirrors:
                    if circle_collision(b.x, b.y, b.radius, m.x, m.y, m.radius):
                        b.alive = False
                        if m.take_hit():
                            m.alive = False
                            self.add_score(m.points)
                            self.particles.extend(explosion(m.x, m.y, 30, 160, (255, 0, 255)))
                            self.screen_shake(10)
                            self._emit_event({"t": "exp", "x": m.x, "y": m.y,
                                               "n": 30, "s": 160, "c": [255, 0, 255]})
                            self._emit_event({"t": "shk", "a": 10})
                        else:
                            self.particles.extend(explosion(m.x, m.y, 8, 60, (255, 100, 255)))
                            self._emit_event({"t": "exp", "x": m.x, "y": m.y,
                                               "n": 8, "s": 60, "c": [255, 100, 255]})
                        self._emit_event({"t": "snd", "n": "explosion"})
                        break

            # Ship2 vs asteroids
            if not self._mp_ship2.invulnerable:
                for a in self.asteroids:
                    if not a.alive or not self._mp_ship2.alive:
                        continue
                    if circle_collision(self._mp_ship2.x, self._mp_ship2.y,
                                        self._mp_ship2.radius, a.x, a.y, a.radius):
                        if a.special == "ghost":
                            continue
                        if self._mp_ship2.thrust_shield_timer > 0:
                            snd.play('shield_hit')
                            if a in self.asteroids:
                                self.asteroids.remove(a)
                                self.destroy_asteroid(a)
                            break
                        if self._mp_ship2.take_hit():
                            self._kill_ship2()
                        else:
                            snd.play('shield_hit')
                            if a in self.asteroids:
                                self.asteroids.remove(a)
                                self.destroy_asteroid(a)
                        break

            # Ship2 vs Boss
            if self.boss and self.boss.alive and self._mp_ship2.alive:
                if circle_collision(self._mp_ship2.x, self._mp_ship2.y, self._mp_ship2.radius,
                                    self.boss.x, self.boss.y, self.boss.radius):
                    if self._mp_ship2.take_hit():
                        self._kill_ship2()

            # Ship2 vs enemy bullets
            all_enemy = self.ufo_bullets + self.enemy_bullets + self.boss_bullets
            for b in all_enemy:
                if not b.alive or not self._mp_ship2.alive:
                    continue
                if circle_collision(self._mp_ship2.x, self._mp_ship2.y,
                                    self._mp_ship2.radius, b.x, b.y, b.radius):
                    b.alive = False
                    if self._mp_ship2.thrust_shield_timer > 0:
                        continue
                    if self._mp_ship2.take_hit():
                        self._kill_ship2()
                        break

            # Ship2 vs UFO / Hunter / Mirror (body collision)
            for enemy_list, col_color in [(self.ufos, (100, 255, 100)),
                                           (self.hunters, (255, 50, 50)),
                                           (self.mirrors, (255, 0, 255))]:
                for e in enemy_list:
                    if not self._mp_ship2.alive:
                        break
                    if circle_collision(self._mp_ship2.x, self._mp_ship2.y, self._mp_ship2.radius,
                                        e.x, e.y, e.radius):
                        e.alive = False
                        pts = getattr(e, 'points', 0)
                        if pts:
                            self.add_score(pts)
                        self.particles.extend(explosion(e.x, e.y, 30, 150, col_color))
                        self._emit_event({"t": "exp", "x": e.x, "y": e.y,
                                           "n": 30, "s": 150, "c": list(col_color)})
                        if self._mp_ship2.take_hit():
                            self._kill_ship2()
                            break
                    break

        # ---- CLEANUP ----
        self.ufos = [u for u in self.ufos if u.alive]
        self.hunters = [h for h in self.hunters if h.alive]
        self.mirrors = [m for m in self.mirrors if m.alive]
        self.ufo_bullets = [b for b in self.ufo_bullets if b.alive]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]
        self.boss_bullets = [b for b in self.boss_bullets if b.alive]
        self.ship.bullets = [b for b in self.ship.bullets if b.alive]
        if self._mp_ship2:
            self._mp_ship2.bullets = [b for b in self._mp_ship2.bullets if b.alive]

    # ==================== RYSOWANIE ====================

    def draw(self):
        if self.state == "main_menu":
            self._draw_main_menu()
            return
        if self.state == "controls":
            self._draw_controls()
            return
        if self.state == "options":
            self._draw_options()
            return
        if self.state == "high_scores":
            self._draw_high_scores()
            return
        if self.state == "seed_entry":
            self._draw_seed_entry()
            return
        if self.state == "sp_menu":
            self._draw_sp_menu()
            return
        if self.state == "mp_menu":
            self._draw_mp_menu()
            return
        if self.state == "server_creator":
            self._draw_server_creator()
            return
        if self.state == "coop_creator":
            self._draw_coop_creator()
            return
        if self.state == "host_lobby":
            self._draw_host_lobby()
            return
        if self.state == "join_lobby":
            self._draw_join_lobby()
            return
        if self.state == "client_lobby":
            self._draw_client_lobby()
            return

        # --- playing / paused / game_over / name_entry all draw the game world ---
        sx, sy = 0, 0
        if self.shake_amount > 0.5:
            sx = random.uniform(-self.shake_amount, self.shake_amount)
            sy = random.uniform(-self.shake_amount, self.shake_amount)
        if self.active_event == "fracture":
            sx += random.uniform(-4, 4)
            sy += random.uniform(-4, 4)

        rl.BeginDrawing()

        if self.flash_time > 0:
            a = int(100 * (self.flash_time / 0.2))
            rl.ClearBackground(color(a, a // 2, 0))
        elif self.blackout:
            rl.ClearBackground(color(5, 5, 10))
        else:
            tr, tg, tb = self.sector.bg_tint
            rl.ClearBackground(color(tr, tg, tb))

        # Sector background: stars and nebula
        self._draw_sector_background()

        if sx != 0 or sy != 0:
            cam = ffi.new("Camera2D *")
            cam.offset.x = sx
            cam.offset.y = sy
            cam.target.x = 0
            cam.target.y = 0
            cam.rotation = 0
            cam.zoom = 1.0
            rl.BeginMode2D(cam[0])

        self._draw_topology_borders()

        if not self.blackout:
            for gw in self.gravity_wells:
                gw.draw()

        for p in self.portals:
            p.draw()

        for gbf in self.gravity_bomb_fields:
            gbf.draw()

        if self.blackout:
            for a in self.asteroids:
                if self.ship.alive:
                    d = dist_wrapped(self.ship.x, self.ship.y, a.x, a.y)
                    if d < 200:
                        a.draw()
                else:
                    a.draw()
        else:
            for a in self.asteroids:
                a.draw()

        if self.boss and self.boss.alive:
            self.boss.draw()

        for p in self.powerups:
            p.draw()
        for u in self.ufos:
            u.draw()
        for h in self.hunters:
            h.draw()
        for m in self.mirrors:
            m.draw()

        for b in self.ufo_bullets:
            for gx, gy in ghost_positions(b.x, b.y, b.radius):
                rl.DrawCircleV(vec2(gx, gy), b.radius + 1, color(255, 80, 80))
        for b in self.enemy_bullets:
            for gx, gy in ghost_positions(b.x, b.y, b.radius):
                rl.DrawCircleV(vec2(gx, gy), b.radius + 1, color(255, 50, 50))
        for b in self.boss_bullets:
            for gx, gy in ghost_positions(b.x, b.y, b.radius):
                rl.DrawCircleV(vec2(gx, gy), b.radius + 1, color(255, 0, 255))

        self.ship.draw()

        # Draw player nickname above own ship (multiplayer)
        if self._mp_mode and self.ship.alive:
            from utils import ghost_positions_topo
            for gx, gy, _ in ghost_positions_topo(self.ship.x, self.ship.y, 20):
                my_name = self._mp_name.encode()
                nw = measure_text(my_name, 12)
                cr, cg, cb = self.ship.ship_color
                draw_text(my_name, int(gx - nw // 2), int(gy - 30), 12,
                            color(cr, cg, cb, 180))
                break

        # Draw second player ship (multiplayer)
        if self._mp_ship2 and self._mp_ship2.alive:
            self._mp_ship2.draw()
            # Draw P2 bullets (host/coop mode: real bullet objects)
            if self._mp_mode in ("host", "coop"):
                for b in self._mp_ship2.bullets:
                    b.draw()
            # Player nickname label
            from utils import ghost_positions_topo
            for gx, gy, _ in ghost_positions_topo(self._mp_ship2.x, self._mp_ship2.y, 20):
                if self._mp_mode == "coop":
                    other_name = self._coop_p2_name or "P2"
                elif self._mp_mode == "host":
                    # Show client's name
                    other_name = self._mp_client_name or "P2"
                    if not other_name and self._server:
                        names = self._server.get_client_names()
                        other_name = names[0][0] if names else "P2"
                else:
                    # Client: show host's name
                    other_name = self._mp_host_name or "P1"
                label = other_name.encode()
                nw = measure_text(label, 12)
                cr, cg, cb = self._mp_ship2.ship_color
                draw_text(label, int(gx - nw // 2), int(gy - 30), 12,
                            color(cr, cg, cb, 180))
                break

        # Client: draw bullets from network data (both ships)
        if self._mp_mode == "client":
            # Ship1 bullets (host's ship — we see as P1/host)
            for bd in self._net_bullets_ship1:
                bx, by = bd.get('x', 0), bd.get('y', 0)
                br = bd.get('r', 3)
                for gx, gy in ghost_positions(bx, by, br):
                    rl.DrawCircleV(vec2(gx, gy), br + 1, color(255, 255, 100))
            # Ship2 bullets (our bullets as seen by server)
            for bd in self._net_bullets_ship2:
                bx, by = bd.get('x', 0), bd.get('y', 0)
                br = bd.get('r', 3)
                for gx, gy in ghost_positions(bx, by, br):
                    rl.DrawCircleV(vec2(gx, gy), br + 1, color(100, 255, 255))

        for p in self.particles:
            p.draw()

        # ---- BLOOM / SOUND-REACTIVITY GLOW ----
        if self._fx_bloom and self.bloom_energy > 0.05:
            import config as _cfg
            _sw, _sh = _cfg.SCREEN_W, _cfg.SCREEN_H

            # Ship glow halo
            if self.ship.alive:
                heat_glow = self.ship.heat * 0.5
                glow_r = 25 + int(30 * (self.bloom_energy + heat_glow))
                glow_a = int(25 * (self.bloom_energy + heat_glow))
                if glow_a > 0:
                    rl.DrawCircleV(vec2(self.ship.x, self.ship.y),
                                   glow_r, color(100, 150, 255, min(60, glow_a)))
                # Speed-based bloom
                spd = math.hypot(self.ship.vx, self.ship.vy)
                if spd > MAX_SPEED * 0.6:
                    s_int = (spd - MAX_SPEED * 0.6) / (MAX_SPEED * 0.4)
                    sa = int(20 * s_int * self.bloom_energy)
                    if sa > 0:
                        rl.DrawCircleV(vec2(self.ship.x, self.ship.y),
                                       15 + int(20 * s_int), color(180, 200, 255, min(40, sa)))

            # Boss glow
            if self.boss and self.boss.alive:
                ba = int(30 * self.bloom_energy)
                if ba > 0:
                    rl.DrawCircleV(vec2(self.boss.x, self.boss.y),
                                   self.boss.radius + 20, color(255, 100, 50, min(40, ba)))

            # Bright-particle bloom (limit to 25 for perf)
            _bloom_n = 0
            for p in self.particles:
                if _bloom_n > 25:
                    break
                if p.size > 1.5 and p.lifetime > p.max_lifetime * 0.5:
                    t = p.lifetime / p.max_lifetime
                    ga = int(18 * t * self.bloom_energy)
                    if ga > 1:
                        rl.DrawCircleV(vec2(p.x, p.y),
                                       p.size * 4, color(p.r, p.g, p.b, min(30, ga)))
                        _bloom_n += 1

            # Screen-wide energy pulse
            if self.bloom_energy > 0.3:
                pa = int(12 * (self.bloom_energy - 0.3) / 0.7)
                if pa > 0:
                    rl.DrawRectangle(0, 0, _sw, _sh, color(255, 200, 100, min(20, pa)))

        if sx != 0 or sy != 0:
            rl.EndMode2D()

        self._draw_hud()

        if self.boss and self.boss.alive:
            self._draw_boss_hp()

        if self.event_msg_time > 0:
            alpha = int(255 * min(1, self.event_msg_time))
            msg = self.event_msg.encode()
            tw = measure_text(msg, 36)
            draw_text(msg, SCREEN_W // 2 - tw // 2, SCREEN_H // 2 + 30, 36,
                        color(255, 200, 0, alpha))

        if self.active_event:
            ev_text = f"[{self.active_event.upper()} {self.event_time_left:.1f}s]".encode()
            draw_text(ev_text, SCREEN_W // 2 - measure_text(ev_text, 16) // 2,
                        SCREEN_H - 30, 16, color(255, 200, 0, 180))

        # Sector transition announcement
        if self.sector_announce_time > 0:
            self._draw_sector_announcement()

        if self.perk_selection_active:
            self._draw_perk_selection()

        # Overlays
        if self.state == "name_entry":
            self._draw_name_entry()
        elif self.state == "game_over":
            self._draw_game_over()
        elif self.state == "paused":
            self._draw_pause_menu()

        self._draw_fps_counter()
        rl.EndDrawing()

    def _draw_sector_background(self):
        """Rysuje gwiazdy i mglawice sektora."""
        import config
        sw, sh = config.SCREEN_W, config.SCREEN_H
        sect = self.sector

        # Stars
        for sx, sy, size, (sr, sg, sb) in sect.stars:
            px = int(sx * sw)
            py = int(sy * sh)
            if size <= 1:
                rl.DrawPixel(px, py, color(sr, sg, sb))
            else:
                rl.DrawCircleV(vec2(px, py), size * 0.5, color(sr, sg, sb, 160))

        # Nebula clouds
        for nx, ny, nr, na in sect.nebula_clouds:
            px = int(nx * sw)
            py = int(ny * sh)
            pr = int(nr * max(sw, sh))
            cr, cg, cb = sect.primary
            rl.DrawCircleV(vec2(px, py), pr, color(cr, cg, cb, na))
            # Second layer, secondary color
            cr2, cg2, cb2 = sect.secondary
            rl.DrawCircleV(vec2(px, py), pr * 0.6, color(cr2, cg2, cb2, na // 2))

        # Sector transition flash
        if self.sector_transition_time > 2.0:
            flash_a = int(60 * ((self.sector_transition_time - 2.0) / 2.0))
            cr, cg, cb = sect.primary
            rl.DrawRectangle(0, 0, sw, sh, color(cr, cg, cb, flash_a))

    def _draw_sector_announcement(self):
        """Rysuje ogloszenie nowego sektora."""
        import config
        sw, sh = config.SCREEN_W, config.SCREEN_H
        t = self.sector_announce_time
        sect = self.sector
        sr, sg, sb = sect.primary

        # Fade in/out
        if t > 4.0:
            alpha = int(255 * (5.0 - t))
        elif t < 1.5:
            alpha = int(255 * (t / 1.5))
        else:
            alpha = 255

        # Background bar
        bar_alpha = int(alpha * 0.4)
        bar_y = sh // 2 - 60
        rl.DrawRectangle(0, bar_y, sw, 120, color(0, 0, 0, bar_alpha))

        # Sector number line
        line1 = f"--- ENTERING SECTOR {sect.number} ---".encode()
        tw1 = measure_text(line1, 20)
        draw_text(line1, sw // 2 - tw1 // 2, bar_y + 15, 20, color(sr, sg, sb, alpha))

        # Sector name
        line2 = sect.name.upper().encode()
        tw2 = measure_text(line2, 40)
        draw_text(line2, sw // 2 - tw2 // 2, bar_y + 40, 40, color(sr, sg, sb, alpha))

        # Modifier
        if sect.modifier:
            line3 = f"[{sect.modifier['name']}] - {sect.modifier['desc']}".encode()
            tw3 = measure_text(line3, 16)
            draw_text(line3, sw // 2 - tw3 // 2, bar_y + 88, 16,
                        color(255, 255, 200, int(alpha * 0.8)))

    def _draw_topology_borders(self):
        """Rysuje krawedzie topologii."""
        topo = get_topology()
        if topo == 0:  # TORUS - all edges wrap
            return
        # Cylinder: top/bottom are walls
        if topo == 1:
            rl.DrawLineV(vec2(0, 0), vec2(SCREEN_W, 0), color(100, 50, 50, 80))
            rl.DrawLineV(vec2(0, SCREEN_H), vec2(SCREEN_W, SCREEN_H), color(100, 50, 50, 80))
        # Mobius: left/right are twist-wrapped, top/bottom walls
        elif topo == 2:
            rl.DrawLineV(vec2(0, 0), vec2(0, SCREEN_H), color(255, 100, 0, 60))
            rl.DrawLineV(vec2(SCREEN_W, 0), vec2(SCREEN_W, SCREEN_H), color(255, 100, 0, 60))
            rl.DrawLineV(vec2(0, 0), vec2(SCREEN_W, 0), color(100, 50, 50, 80))
            rl.DrawLineV(vec2(0, SCREEN_H), vec2(SCREEN_W, SCREEN_H), color(100, 50, 50, 80))
        # Klein: left/right twist-wrapped
        elif topo == 3:
            rl.DrawLineV(vec2(0, 0), vec2(0, SCREEN_H), color(255, 0, 255, 60))
            rl.DrawLineV(vec2(SCREEN_W, 0), vec2(SCREEN_W, SCREEN_H), color(255, 0, 255, 60))
        # Sphere: edges jitter
        elif topo == 4:
            c = color(100, 200, 100, 40)
            rl.DrawRectangleLines(2, 2, SCREEN_W - 4, SCREEN_H - 4, c)

    def _draw_boss_hp(self):
        """Boss health bar at top of screen."""
        bar_w = 400
        bar_h = 12
        bx = SCREEN_W // 2 - bar_w // 2
        by = 8
        hp_frac = self.boss.hp / self.boss.max_hp

        rl.DrawRectangle(bx - 1, by - 1, bar_w + 2, bar_h + 2, color(100, 100, 100))
        rl.DrawRectangle(bx, by, bar_w, bar_h, color(40, 0, 0))
        fill_w = int(bar_w * hp_frac)
        r = int(255 * (1 - hp_frac))
        g = int(255 * hp_frac)
        rl.DrawRectangle(bx, by, fill_w, bar_h, color(r, g, 0))

        name = self.boss.boss_type.upper().encode()
        tw = measure_text(name, 14)
        draw_text(name, SCREEN_W // 2 - tw // 2, by + bar_h + 4, 14, color(255, 200, 100))

    def _draw_hud(self):
        # Score
        draw_text(T("SCORE: {score}").format(score=self.score).encode(), 20, 20, 24, colors.RAYWHITE)

        # Level + topology
        topo_name = TOPOLOGY_NAMES.get(get_topology(), "?")
        draw_text(T("WAVE {wave}  [{topo}]").format(wave=self.level, topo=topo_name).encode(), 20, 50, 18, colors.GRAY)

        # Sector info
        sr, sg, sb = self.sector.primary
        sect_text = T("SECTOR {num}: {name}").format(num=self.sector.number, name=self.sector.name).encode()
        draw_text(sect_text, 20, 72, 14, color(sr, sg, sb, 180))
        if self.sector.modifier:
            mod_text = self.sector.modifier["name"].encode()
            draw_text(mod_text, 20, 88, 12, color(sr, sg, sb, 120))

        # Lives
        for i in range(self.lives):
            cx = SCREEN_W - 30 - i * 30
            cy = 30
            rl.DrawTriangleLines(
                vec2(cx, cy - 10), vec2(cx - 7, cy + 7), vec2(cx + 7, cy + 7),
                colors.RAYWHITE)

        # Combo
        if self.combo >= 3:
            combo_text = T("COMBO x{combo}  (x{mult})").format(combo=self.combo, mult=self.combo_multiplier).encode()
            col = color(255, 255, 0) if self.combo_multiplier >= 2 else color(200, 200, 200)
            tw = measure_text(combo_text, 20)
            draw_text(combo_text, SCREEN_W // 2 - tw // 2, 20, 20, col)

        # Wrap score multiplier
        if self.wrap_score_mult > 1.05:
            wt = T("WRAP x{mult}").format(mult=f"{self.wrap_score_mult:.1f}").encode()
            tw = measure_text(wt, 16)
            draw_text(wt, SCREEN_W // 2 - tw // 2, 44, 16, color(100, 200, 255))

        # ---- Heat bar ----
        heat_bar_w = 120
        heat_bar_h = 8
        hx = SCREEN_W - heat_bar_w - 20
        hy = 60
        rl.DrawRectangle(hx - 1, hy - 1, heat_bar_w + 2, heat_bar_h + 2, color(60, 60, 60))
        fill = int(heat_bar_w * self.ship.heat)
        if self.ship.overheated:
            bar_col = color(255, 50, 50)
        elif self.ship.heat >= 0.75:
            bar_col = color(255, 200, 0)
        else:
            bar_col = color(200, 100, 0)
        rl.DrawRectangle(hx, hy, fill, heat_bar_h, bar_col)
        draw_text(T("HEAT").encode(), hx, hy - 14, 12, color(180, 100, 0))
        if self.ship.overheated:
            draw_text(T("OVERHEAT!").encode(), hx + heat_bar_w + 5, hy - 2, 12, color(255, 50, 50))

        # ---- Module slots ----
        mod_y = hy + 22
        draw_text(T("MODULES:").encode(), hx, mod_y, 12, color(150, 150, 150))
        mod_y += 16
        for i, mod_id in enumerate(self.ship.modules):
            mod_info = MODULES.get(mod_id, {})
            r, g, b = mod_info.get("color", (200, 200, 200))
            name = mod_info.get("name", mod_id.upper())
            draw_text(name.encode(), hx + 4, mod_y + i * 16, 12, color(r, g, b))
        # Empty slots
        for i in range(len(self.ship.modules), 4):
            draw_text(b"---", hx + 4, mod_y + i * 16, 12, color(60, 60, 60))

        # ---- Active powerups ----
        py = 80
        timers = [
            (self.ship.multishot_time, "MULTI-SHOT", (0, 200, 255)),
            (self.ship.rapidfire_time, "RAPID FIRE", (255, 100, 0)),
            (self.ship.speedboost_time, "SPEED BOOST", (255, 255, 0)),
            (self.ship.bouncing_time, "BOUNCING", (0, 255, 200)),
            (self.ship.homing_time, "HOMING", (255, 200, 0)),
        ]
        for val, name, col_rgb in timers:
            if val > 0:
                t = f"{name} {val:.1f}s".encode()
                draw_text(t, 20, py, 16, color(*col_rgb))
                py += 20
        if self.ship.shield_hits > 0:
            t = T("SHIELD x{n}").format(n=self.ship.shield_hits).encode()
            draw_text(t, 20, py, 16, color(0, 255, 100))
            py += 20

        # Mutations
        if self.ship.mutations:
            py += 5
            for mut in sorted(self.ship.mutations):
                draw_text(f"[{mut.upper()}]".encode(), 20, py, 12, color(200, 200, 100))
                py += 15

        # Posiadane perki
        if self.owned_perks:
            py += 10
            draw_text(T("PERKS:").encode(), 20, py, 14, color(180, 180, 180))
            py += 18
            for perk_id in sorted(self.owned_perks):
                if perk_id in PERKS:
                    info = PERKS[perk_id]
                    draw_text(info["name"].encode(), 24, py, 12, color(*info["color"], 180))
                    py += 15

        # Alt-fire indicators
        alt_y = SCREEN_H - 60
        if "gravity_shot" in self.owned_perks or self.ship.has_module("gravity"):
            ready = self.ship.alt_cooldown <= 0
            c = color(200, 50, 255) if ready else color(100, 30, 100)
            cd = "" if ready else f" ({self.ship.alt_cooldown:.1f}s)"
            draw_text(f"[X] GRAV BOMB{cd}".encode(), SCREEN_W - 200, alt_y, 14, c)
            alt_y += 18
        if "hyperspace_shot" in self.owned_perks or self.ship.has_module("hyper"):
            ready = self.ship.alt_cooldown <= 0
            c = color(100, 150, 255) if ready else color(50, 70, 120)
            cd = "" if ready else f" ({self.ship.alt_cooldown:.1f}s)"
            draw_text(f"[C] HYPERSPACE{cd}".encode(), SCREEN_W - 200, alt_y, 14, c)

        # Powerup pickup message
        if self.powerup_msg_time > 0:
            alpha = int(255 * min(1, self.powerup_msg_time))
            msg = self.powerup_msg.encode()
            tw = measure_text(msg, 32)
            draw_text(msg, SCREEN_W // 2 - tw // 2, SCREEN_H // 2 - 80, 32,
                        color(255, 255, 100, alpha))

        # Seed display
        if self.game_seed:
            seed_text = T("SEED: {seed}").format(seed=self.game_seed).encode()
            draw_text(seed_text, 20, SCREEN_H - 25, 14, color(100, 100, 100))

        # Multiplayer indicator
        if self._mp_mode == "coop":
            mp_label = T("[CO-OP] Local").encode()
            draw_text(mp_label, SCREEN_W // 2 - measure_text(mp_label, 14) // 2, SCREEN_H - 25, 14, color(255, 200, 100))
        elif self._mp_mode == "host":
            mp_label = T("[HOST] Multiplayer").encode()
            draw_text(mp_label, SCREEN_W // 2 - measure_text(mp_label, 14) // 2, SCREEN_H - 25, 14, color(100, 255, 100))
        elif self._mp_mode == "client":
            mp_label = T("[CLIENT] Multiplayer").encode()
            draw_text(mp_label, SCREEN_W // 2 - measure_text(mp_label, 14) // 2, SCREEN_H - 25, 14, color(100, 200, 255))

        # Multiplayer / Co-Op: ship2 lives display
        if self._mp_mode and self._mp_ship2:
            if self._mp_mode == "coop":
                p2_name = self._coop_p2_name or "P2"
            elif self._mp_mode == "host":
                p2_name = self._mp_client_name or "P2"
            else:
                p2_name = self._mp_host_name or "P1"
            p2_lives = self.lives_ship2
            p2_text = f"{p2_name}: ".encode()
            draw_text(p2_text, SCREEN_W - 200, 50, 14, color(180, 180, 180))
            for i in range(p2_lives):
                cx = SCREEN_W - 110 + i * 18
                cy2 = 54
                rl.DrawTriangleLines(
                    vec2(cx, cy2 - 6), vec2(cx - 5, cy2 + 5), vec2(cx + 5, cy2 + 5),
                    color(100, 255, 100))
            if self.ship2_dead_permanently:
                draw_text(T("DEAD").encode(), SCREEN_W - 110, 54, 14, color(255, 80, 80))

        # Spectator mode overlay
        if self._mp_mode and not self.ship.alive and self.ship1_dead_permanently:
            spec_text = T("SPECTATING").encode()
            stw = measure_text(spec_text, 36)
            pulse_a = int(120 + 80 * math.sin(_time.time() * 3))
            draw_text(spec_text, SCREEN_W // 2 - stw // 2, SCREEN_H // 2 + 60, 36,
                        color(255, 255, 255, pulse_a))
            # Show respawn info
            if self.mp_respawn_mode == "wave":
                hint = T("Respawn at wave clear").encode()
            elif self.mp_respawn_mode == "score":
                pts_left = max(0, self.mp_respawn_score_threshold - self.score)
                hint = T("Respawn at {score} pts").format(score=f"{pts_left:,}").encode()
            elif self.mp_respawn_mode == "timer":
                if self._mp_mode == "client":
                    secs_left = max(0, self.mp_respawn_death_time)  # client receives remaining seconds
                else:
                    secs_left = max(0, MP_RESPAWN_TIMER - (_time.time() - self.mp_respawn_death_time))
                hint = T("Respawn in {time}s").format(time=int(secs_left)).encode()
            else:
                hint = b""
            if hint:
                hw = measure_text(hint, 18)
                draw_text(hint, SCREEN_W // 2 - hw // 2, SCREEN_H // 2 + 100, 18,
                            color(200, 200, 200, 160))

    def _draw_perk_selection(self):
        overlay = color(0, 0, 0, 200)
        rl.DrawRectangle(0, 0, SCREEN_W, SCREEN_H, overlay)

        title = T("WAVE CLEARED - CHOOSE A PERK").encode()
        tw = measure_text(title, 36)
        draw_text(title, SCREEN_W // 2 - tw // 2, 120, 36, colors.RAYWHITE)

        total_w = len(self.perk_choices) * 280
        start_x = SCREEN_W // 2 - total_w // 2

        for i, perk_id in enumerate(self.perk_choices):
            info = PERKS[perk_id]
            bx = start_x + i * 280
            by = 220
            bw = 250
            bh = 200

            r, g, b = info["color"]
            rl.DrawRectangleLines(bx, by, bw, bh, color(r, g, b))
            rl.DrawRectangle(bx + 1, by + 1, bw - 2, bh - 2, color(r // 6, g // 6, b // 6))

            key_text = f"[{i + 1}]".encode()
            ktw = measure_text(key_text, 28)
            draw_text(key_text, bx + bw // 2 - ktw // 2, by + 20, 28, color(r, g, b))

            name_text = info["name"].encode()
            ntw = measure_text(name_text, 22)
            draw_text(name_text, bx + bw // 2 - ntw // 2, by + 65, 22, color(r, g, b))

            desc_text = info["desc"].encode()
            dtw = measure_text(desc_text, 16)
            draw_text(desc_text, bx + bw // 2 - dtw // 2, by + 110, 16, color(200, 200, 200))

            # Mutation tag
            if "mutation" in info:
                draw_text(T("MUTATION").encode(), bx + bw // 2 - 35, by + 140, 14, color(255, 200, 100))

            if perk_id in self.owned_perks and perk_id != "extra_life":
                draw_text(T("(OWNED)").encode(), bx + bw // 2 - 30, by + 165, 14, color(255, 255, 0))

    def _draw_game_over(self):
        overlay = color(0, 0, 0, 180)
        rl.DrawRectangle(0, 0, SCREEN_W, SCREEN_H, overlay)

        go = T("GAME OVER").encode()
        tw = measure_text(go, 60)
        draw_text(go, SCREEN_W // 2 - tw // 2, SCREEN_H // 2 - 100, 60, colors.RAYWHITE)

        score_t = T("Final Score: {score}").format(score=self.score).encode()
        tw2 = measure_text(score_t, 28)
        draw_text(score_t, SCREEN_W // 2 - tw2 // 2, SCREEN_H // 2 - 30, 28, colors.GRAY)

        level_t = T("Wave: {wave}").format(wave=self.level).encode()
        tw3 = measure_text(level_t, 22)
        draw_text(level_t, SCREEN_W // 2 - tw3 // 2, SCREEN_H // 2 + 5, 22, colors.GRAY)

        if self.owned_perks:
            perks_t = T("Perks: {n}").format(n=len(self.owned_perks)).encode()
            tw4 = measure_text(perks_t, 18)
            draw_text(perks_t, SCREEN_W // 2 - tw4 // 2, SCREEN_H // 2 + 35, 18, colors.GRAY)

        if self.game_seed:
            seed_t = T("Seed: {seed}").format(seed=self.game_seed).encode()
            tw5 = measure_text(seed_t, 16)
            draw_text(seed_t, SCREEN_W // 2 - tw5 // 2, SCREEN_H // 2 + 58, 16,
                        color(200, 180, 100))

        options = ["Restart", "High Scores", "Main Menu"]
        oy = SCREEN_H // 2 + 80
        sel = self._go_sel
        for i, opt in enumerate(options):
            text = T(opt).encode()
            tw = measure_text(text, 24)
            x = SCREEN_W // 2 - tw // 2
            y = oy + i * 40
            if i == sel:
                draw_text(b"> ", x - 24, y, 24, color(255, 255, 100))
                draw_text(text, x, y, 24, color(255, 255, 100))
            else:
                draw_text(text, x, y, 24, color(180, 180, 180))

    # ====================================================================
    #  GAME OVER update
    # ====================================================================

    def _update_game_over(self, dt):
        snd.update_music(0.05, 1, False)
        options = ["Restart", "High Scores", "Main Menu"]
        options_count = len(options)

        if rl.IsKeyPressed(KEY_UP):
            self._go_sel = (self._go_sel - 1) % options_count
            snd.play('menu_select')
        if rl.IsKeyPressed(KEY_DOWN):
            self._go_sel = (self._go_sel + 1) % options_count
            snd.play('menu_select')

        # Mouse hover
        my = rl.GetMouseY()
        oy = SCREEN_H // 2 + 80
        for i in range(options_count):
            y = oy + i * 40
            if y <= my <= y + 28:
                self._go_sel = i

        confirm = rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE)
        if rl.IsMouseButtonPressed(0):
            for i in range(options_count):
                y = oy + i * 40
                if y <= my <= y + 28:
                    confirm = True
                    self._go_sel = i

        if confirm:
            snd.play('menu_confirm')
            sel = options[self._go_sel]
            if sel == "Restart":
                self._init_game_state()
                if self._mp_mode == "coop":
                    # Recreate P2 ship for co-op restart
                    _, p1_col = SHIP_COLORS[self._mp_ship_color_idx]
                    self.ship.ship_color = p1_col
                    self.ship.set_skin(self._ship_skin_idx)
                    self._mp_ship2 = Ship(SCREEN_W // 2 + 80, SCREEN_H // 2)
                    _, p2_col = SHIP_COLORS[self._coop_p2_color_idx]
                    self._mp_ship2.ship_color = p2_col
                    self._mp_ship2.set_skin(self._coop_p2_skin_idx)
                    self.mp_respawn_mode = self._mp_game_config.get('respawn_mode', 'wave')
                    for mod_id in self._mp_game_config.get('start_modules', []):
                        self.ship.add_module(mod_id)
                        self._mp_ship2.add_module(mod_id)
                self.state = "playing"
            elif sel == "High Scores":
                self._leaderboard = load_leaderboard()
                self.state = "high_scores"
            elif sel == "Main Menu":
                self._mp_cleanup()
                self.state = "main_menu"
                self.menu_sel = 0

    # ====================================================================
    #  MAIN MENU
    # ====================================================================

    MAIN_MENU_OPTIONS = ["Single Player", "Multiplayer", "High Scores", "Options", "Controls", "Quit"]

    def _animate_menu_bg(self, dt):
        self.menu_time += dt
        for a in self._menu_asteroids:
            a.x += a.vx * dt
            a.y += a.vy * dt
            a.angle += a.rot_speed * dt
            a.x %= SCREEN_W
            a.y %= SCREEN_H
        snd.update_music(0.1, 1, False)

    def _menu_nav(self, opts, sel_attr):
        """Generic menu navigation.  Returns (new_sel, confirmed)."""
        sel = getattr(self, sel_attr)
        if rl.IsKeyPressed(KEY_UP):
            sel = (sel - 1) % len(opts)
            snd.play('menu_select')
        if rl.IsKeyPressed(KEY_DOWN):
            sel = (sel + 1) % len(opts)
            snd.play('menu_select')

        my = rl.GetMouseY()
        menu_start_y = 360
        for i in range(len(opts)):
            y = menu_start_y + i * 50
            if y <= my <= y + 32:
                sel = i

        confirm = rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE)
        if rl.IsMouseButtonPressed(0):
            for i in range(len(opts)):
                y = menu_start_y + i * 50
                if y <= my <= y + 32:
                    confirm = True
                    sel = i

        setattr(self, sel_attr, sel)
        return sel, confirm

    def _draw_menu_frame(self, title_text, opts, sel, subtitle=None):
        """Draw the common menu chrome (bg, title, options list)."""
        rl.BeginDrawing()
        rl.ClearBackground(colors.BLACK)

        for a in self._menu_asteroids:
            a.draw()
        rl.DrawRectangle(0, 0, SCREEN_W, SCREEN_H, color(0, 0, 0, 140))

        t = self.menu_time
        pulse = 0.8 + 0.2 * math.sin(t * 2.5)

        title_size = 60
        title = b"ASTEROIDS"
        tw = measure_text(title, title_size)
        tx = SCREEN_W // 2 - tw // 2
        ty = 140

        offsets = [(-3, -2), (3, 2), (-2, 3)]
        for ox, oy in offsets:
            ghost_a = int(40 * pulse)
            dx = ox * (1.0 + 0.5 * math.sin(t * 1.5 + ox))
            dy = oy * (1.0 + 0.5 * math.cos(t * 1.8 + oy))
            draw_text(title, int(tx + dx), int(ty + dy), title_size,
                        color(100, 100, 255, ghost_a))
        draw_text(title, tx, ty, title_size, color(255, 255, 255, int(255 * pulse)))

        sub = b"ON STEROIDS"
        sub_size = 36
        stw = measure_text(sub, sub_size)
        sub_pulse = 0.6 + 0.4 * math.sin(t * 3.0 + 1.0)
        draw_text(sub, SCREEN_W // 2 - stw // 2, ty + 70, sub_size,
                    color(255, 200, 0, int(255 * sub_pulse)))

        line_y = 320
        line_w = 300
        rl.DrawLineV(vec2(SCREEN_W // 2 - line_w // 2, line_y),
                     vec2(SCREEN_W // 2 + line_w // 2, line_y),
                     color(255, 255, 255, 40))

        # Subtitle (section name)
        if subtitle:
            stb = T(subtitle).encode()
            stbw = measure_text(stb, 20)
            draw_text(stb, SCREEN_W // 2 - stbw // 2, 338, 20, color(255, 200, 100, 200))

        menu_start_y = 360
        for i, opt in enumerate(opts):
            text = T(opt).encode()
            size = 28
            tw = measure_text(text, size)
            x = SCREEN_W // 2 - tw // 2
            y = menu_start_y + i * 50

            if i == sel:
                sel_pulse = 0.7 + 0.3 * math.sin(t * 5.0)
                col = color(255, 255, 100, int(255 * sel_pulse))
                draw_text(b"> ", x - 30, y, size, col)
                draw_text(text, x, y, size, col)
                rl.DrawLineV(vec2(x, y + size + 4), vec2(x + tw, y + size + 4),
                             color(255, 255, 100, int(80 * sel_pulse)))
            else:
                draw_text(text, x, y, size, color(180, 180, 180))

        footer = b"(c) Asteroids on Steroids Made by Pawel Golawski"
        fw = measure_text(footer, 14)
        draw_text(footer, SCREEN_W // 2 - fw // 2, SCREEN_H - 40, 14, color(80, 80, 80))
        self._draw_fps_counter()
        rl.EndDrawing()

    # ---- MAIN MENU ----

    def _update_main_menu(self, dt):
        self._animate_menu_bg(dt)
        opts = self.MAIN_MENU_OPTIONS
        sel, confirm = self._menu_nav(opts, 'menu_sel')
        if confirm:
            snd.play('menu_confirm')
            chosen = opts[sel]
            if chosen == "Single Player":
                self.state = "sp_menu"
                self._sp_sel = 0
            elif chosen == "Multiplayer":
                self.state = "mp_menu"
                self._mp_sel = 0
            elif chosen == "High Scores":
                self._leaderboard = load_leaderboard()
                self.state = "high_scores"
            elif chosen == "Options":
                self.state = "options"
                self._options_return_to = "main_menu"
                self._opt_sel = 0
            elif chosen == "Controls":
                self.state = "controls"
                self._controls_return_to = "main_menu"
                self._ctrl_section = 0
                self._ctrl_sel = 0
                self._ctrl_listening = False
            elif chosen == "Quit":
                rl.CloseWindow()
                raise SystemExit(0)

    def _draw_main_menu(self):
        self._draw_menu_frame("MAIN", self.MAIN_MENU_OPTIONS, self.menu_sel)

    # ---- SINGLE PLAYER SUBMENU ----

    SP_MENU_OPTIONS = ["Ship Color", "Ship Skin", "Start Game", "Seeded Run", "Back"]

    def _update_sp_menu(self, dt):
        self._animate_menu_bg(dt)
        if rl.IsKeyPressed(KEY_ESC):
            self.state = "main_menu"
            self.menu_sel = 0
            return
        opts = self.SP_MENU_OPTIONS
        sel, confirm = self._menu_nav(opts, '_sp_sel')
        chosen = opts[sel]
        # Ship Color / Ship Skin: left/right cycling
        if chosen == "Ship Color":
            if rl.IsKeyPressed(KEY_LEFT):
                self._mp_ship_color_idx = (self._mp_ship_color_idx - 1) % len(SHIP_COLORS)
                snd.play('menu_select')
            if rl.IsKeyPressed(KEY_RIGHT):
                self._mp_ship_color_idx = (self._mp_ship_color_idx + 1) % len(SHIP_COLORS)
                snd.play('menu_select')
        elif chosen == "Ship Skin":
            if rl.IsKeyPressed(KEY_LEFT):
                self._ship_skin_idx = (self._ship_skin_idx - 1) % len(SHIP_SKINS)
                snd.play('menu_select')
            if rl.IsKeyPressed(KEY_RIGHT):
                self._ship_skin_idx = (self._ship_skin_idx + 1) % len(SHIP_SKINS)
                snd.play('menu_select')
        if confirm:
            snd.play('menu_confirm')
            if chosen == "Ship Color":
                self._mp_ship_color_idx = (self._mp_ship_color_idx + 1) % len(SHIP_COLORS)
            elif chosen == "Ship Skin":
                self._ship_skin_idx = (self._ship_skin_idx + 1) % len(SHIP_SKINS)
            elif chosen == "Start Game":
                self._mp_mode = None
                self.game_seed = None
                self._init_game_state()
                self.ship.ship_color = SHIP_COLORS[self._mp_ship_color_idx][1]
                self.ship.set_skin(self._ship_skin_idx)
                self.state = "playing"
            elif chosen == "Seeded Run":
                self.state = "seed_entry"
                self._seed_input = ""
                self._seed_cursor_blink = 0.0
            elif chosen == "Back":
                self.state = "main_menu"
                self.menu_sel = 0

    def _draw_sp_menu(self):
        rl.BeginDrawing()
        rl.ClearBackground(colors.BLACK)
        for a in self._menu_asteroids:
            a.draw()
        rl.DrawRectangle(0, 0, SCREEN_W, SCREEN_H, color(0, 0, 0, 140))

        t = self.menu_time
        pulse = 0.8 + 0.2 * math.sin(t * 2.5)

        title_size = 60
        title = b"ASTEROIDS"
        tw = measure_text(title, title_size)
        tx = SCREEN_W // 2 - tw // 2
        ty = 100

        offsets = [(-3, -2), (3, 2), (-2, 3)]
        for ox, oy in offsets:
            ghost_a = int(40 * pulse)
            dx = ox * (1.0 + 0.5 * math.sin(t * 1.5 + ox))
            dy = oy * (1.0 + 0.5 * math.cos(t * 1.8 + oy))
            draw_text(title, int(tx + dx), int(ty + dy), title_size,
                        color(100, 100, 255, ghost_a))
        draw_text(title, tx, ty, title_size, color(255, 255, 255, int(255 * pulse)))

        sub = b"ON STEROIDS"
        sub_size = 36
        stw = measure_text(sub, sub_size)
        sub_pulse = 0.6 + 0.4 * math.sin(t * 3.0 + 1.0)
        draw_text(sub, SCREEN_W // 2 - stw // 2, ty + 65, sub_size,
                    color(255, 200, 0, int(255 * sub_pulse)))

        stb = T("--- SINGLE PLAYER ---").encode()
        stbw = measure_text(stb, 20)
        draw_text(stb, SCREEN_W // 2 - stbw // 2, 260, 20, color(255, 200, 100, 200))

        # Menu options
        opts = self.SP_MENU_OPTIONS
        menu_start_y = 290
        for i, opt in enumerate(opts):
            y = menu_start_y + i * 44
            is_sel = (i == self._sp_sel)
            sel_pulse = 0.7 + 0.3 * math.sin(t * 5.0)

            if opt == "Ship Color":
                col_name, col_rgb = SHIP_COLORS[self._mp_ship_color_idx]
                label = T("Ship Color") + ": < " + T(col_name) + " >"
                text = label.encode()
                tw2 = measure_text(text, 24)
                x = SCREEN_W // 2 - tw2 // 2
                prefix = b"> " if is_sel else b"  "
                col = color(255, 255, 100, int(255 * sel_pulse)) if is_sel else color(200, 200, 200)
                draw_text(prefix + text, x - 14, y, 24, col)
                cr, cg, cb = col_rgb
                rl.DrawRectangle(x + tw2 + 10, y + 3, 18, 18, color(cr, cg, cb))
                rl.DrawRectangleLines(x + tw2 + 10, y + 3, 18, 18, color(255, 255, 255, 80))
            elif opt == "Ship Skin":
                skin_name = SKIN_NAMES[self._ship_skin_idx]
                label = T("Ship Skin") + ": < " + T(skin_name) + " >"
                text = label.encode()
                tw2 = measure_text(text, 24)
                x = SCREEN_W // 2 - tw2 // 2
                prefix = b"> " if is_sel else b"  "
                col = color(255, 255, 100, int(255 * sel_pulse)) if is_sel else color(200, 200, 200)
                draw_text(prefix + text, x - 14, y, 24, col)
                # Preview mini ship
                _, hull, _, _ = SHIP_SKINS[self._ship_skin_idx]
                pcr, pcg, pcb = SHIP_COLORS[self._mp_ship_color_idx][1]
                preview_x = x + tw2 + 20
                preview_y = y + 12
                scale = 0.6
                for j in range(len(hull)):
                    px1, py1 = hull[j]
                    px2, py2 = hull[(j + 1) % len(hull)]
                    rl.DrawLineV(vec2(preview_x + px1 * scale, preview_y + py1 * scale),
                                 vec2(preview_x + px2 * scale, preview_y + py2 * scale),
                                 color(pcr, pcg, pcb))
            else:
                text = T(opt).encode()
                tw2 = measure_text(text, 24)
                x = SCREEN_W // 2 - tw2 // 2
                if is_sel:
                    col = color(255, 255, 100, int(255 * sel_pulse))
                    draw_text(b"> ", x - 24, y, 24, col)
                    draw_text(text, x, y, 24, col)
                else:
                    draw_text(text, x, y, 24, color(180, 180, 180))

        footer = b"(c) Asteroids on Steroids"
        fw = measure_text(footer, 14)
        draw_text(footer, SCREEN_W // 2 - fw // 2, SCREEN_H - 40, 14, color(80, 80, 80))
        self._draw_fps_counter()
        rl.EndDrawing()

    # ---- MULTIPLAYER SUBMENU ----

    MP_MENU_OPTIONS = ["Player Name", "Ship Color", "Ship Skin", "Co-Op (Local)", "Host Game", "Join Game", "Back"]

    def _update_mp_menu(self, dt):
        self._animate_menu_bg(dt)

        # Name editing mode
        if self._mp_editing_name:
            while True:
                ch = rl.GetCharPressed()
                if ch == 0:
                    break
                if 32 <= ch <= 126 and len(self._mp_name) < NAME_MAX_LEN:
                    self._mp_name += chr(ch)
            if rl.IsKeyPressed(259) or rl.IsKeyPressedRepeat(259):
                self._mp_name = self._mp_name[:-1]
            if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_ESC):
                if not self._mp_name.strip():
                    self._mp_name = "Player"
                self._mp_editing_name = False
            return

        if rl.IsKeyPressed(KEY_ESC):
            self.state = "main_menu"
            self.menu_sel = 1
            return
        opts = self.MP_MENU_OPTIONS
        sel, confirm = self._menu_nav(opts, '_mp_sel')
        # Ship Color / Ship Skin: LEFT/RIGHT to cycle without confirming
        if opts[sel] == "Ship Color":
            if rl.IsKeyPressed(KEY_LEFT):
                self._mp_ship_color_idx = (self._mp_ship_color_idx - 1) % len(SHIP_COLORS)
                snd.play('menu_select')
            if rl.IsKeyPressed(KEY_RIGHT):
                self._mp_ship_color_idx = (self._mp_ship_color_idx + 1) % len(SHIP_COLORS)
                snd.play('menu_select')
        elif opts[sel] == "Ship Skin":
            if rl.IsKeyPressed(KEY_LEFT):
                self._ship_skin_idx = (self._ship_skin_idx - 1) % len(SHIP_SKINS)
                snd.play('menu_select')
            if rl.IsKeyPressed(KEY_RIGHT):
                self._ship_skin_idx = (self._ship_skin_idx + 1) % len(SHIP_SKINS)
                snd.play('menu_select')

        if confirm:
            snd.play('menu_confirm')
            chosen = opts[sel]
            if chosen == "Player Name":
                self._mp_editing_name = True
            elif chosen == "Ship Color":
                self._mp_ship_color_idx = (self._mp_ship_color_idx + 1) % len(SHIP_COLORS)
            elif chosen == "Ship Skin":
                self._ship_skin_idx = (self._ship_skin_idx + 1) % len(SHIP_SKINS)
            elif chosen == "Co-Op (Local)":
                self._open_coop_creator()
            elif chosen == "Host Game":
                self._open_server_creator()
            elif chosen == "Join Game":
                self._start_join_lobby()
            elif chosen == "Back":
                self.state = "main_menu"
                self.menu_sel = 1

    def _draw_mp_menu(self):
        rl.BeginDrawing()
        rl.ClearBackground(colors.BLACK)
        for a in self._menu_asteroids:
            a.draw()
        rl.DrawRectangle(0, 0, SCREEN_W, SCREEN_H, color(0, 0, 0, 140))

        t = self.menu_time
        pulse = 0.8 + 0.2 * math.sin(t * 2.5)
        title = T("MULTIPLAYER").encode()
        tw = measure_text(title, 48)
        draw_text(title, SCREEN_W // 2 - tw // 2, 180, 48,
                    color(100, 200, 255, int(255 * pulse)))

        cy = 360
        opts = self.MP_MENU_OPTIONS
        for i, opt in enumerate(opts):
            is_sel = (i == self._mp_sel)
            if opt == "Player Name":
                label = T("Player Name") + ": "
                val = self._mp_name
                if self._mp_editing_name:
                    if int(t * 2) % 2 == 0:
                        val += "_"
                    label_text = (label + val).encode()
                    draw_text(b"> " + label_text, SCREEN_W // 2 - 200, cy, 24,
                                color(100, 200, 255))
                elif is_sel:
                    sp = 0.7 + 0.3 * math.sin(t * 5.0)
                    label_text = (label + val).encode()
                    draw_text(b"> " + label_text, SCREEN_W // 2 - 200, cy, 24,
                                color(255, 255, 100, int(255 * sp)))
                else:
                    label_text = (label + val).encode()
                    draw_text(b"  " + label_text, SCREEN_W // 2 - 200, cy, 24,
                                color(200, 200, 200))
            elif opt == "Ship Color":
                col_name, col_rgb = SHIP_COLORS[self._mp_ship_color_idx]
                label_text = (T("Ship Color") + ": < " + T(col_name) + " >").encode()
                prefix = b"> " if is_sel else b"  "
                if is_sel:
                    sp = 0.7 + 0.3 * math.sin(t * 5.0)
                    draw_text(prefix + label_text, SCREEN_W // 2 - 200, cy, 24,
                                color(255, 255, 100, int(255 * sp)))
                else:
                    draw_text(prefix + label_text, SCREEN_W // 2 - 200, cy, 24,
                                color(200, 200, 200))
                # Color preview swatch
                cr, cg, cb = col_rgb
                sx = SCREEN_W // 2 + 200
                rl.DrawRectangle(sx, cy + 2, 20, 20, color(cr, cg, cb))
                rl.DrawRectangleLines(sx, cy + 2, 20, 20, color(255, 255, 255, 100))
            elif opt == "Ship Skin":
                skin_name = SKIN_NAMES[self._ship_skin_idx]
                label_text = (T("Ship Skin") + ": < " + T(skin_name) + " >").encode()
                prefix = b"> " if is_sel else b"  "
                if is_sel:
                    sp = 0.7 + 0.3 * math.sin(t * 5.0)
                    draw_text(prefix + label_text, SCREEN_W // 2 - 200, cy, 24,
                                color(255, 255, 100, int(255 * sp)))
                else:
                    draw_text(prefix + label_text, SCREEN_W // 2 - 200, cy, 24,
                                color(200, 200, 200))
                # Preview mini ship
                _, hull, _, _ = SHIP_SKINS[self._ship_skin_idx]
                pcr, pcg, pcb = SHIP_COLORS[self._mp_ship_color_idx][1]
                preview_x = SCREEN_W // 2 + 210
                preview_y = cy + 14
                scale = 0.6
                for j in range(len(hull)):
                    px1, py1 = hull[j]
                    px2, py2 = hull[(j + 1) % len(hull)]
                    rl.DrawLineV(vec2(preview_x + px1 * scale, preview_y + py1 * scale),
                                 vec2(preview_x + px2 * scale, preview_y + py2 * scale),
                                 color(pcr, pcg, pcb))
            else:
                if is_sel:
                    sp = 0.7 + 0.3 * math.sin(t * 5.0)
                    draw_text(f"> {T(opt)}".encode(), SCREEN_W // 2 - 200, cy, 24,
                                color(255, 255, 100, int(255 * sp)))
                else:
                    draw_text(f"  {T(opt)}".encode(), SCREEN_W // 2 - 200, cy, 24,
                                color(200, 200, 200))
            cy += 50

        self._draw_fps_counter()
        rl.EndDrawing()

    # ---- SERVER CREATOR ----

    # All available modules from wave.py
    _ALL_MODULES = ["rapid", "pierce", "split", "homing", "gravity", "bounce", "hyper"]

    def _open_server_creator(self):
        """Open the server creator screen with default settings."""
        self._sc_sel = 0
        self._sc_port = str(GAME_PORT)
        self._sc_max_players = 2
        self._sc_start_wave = 1
        self._sc_start_sector = 1
        self._sc_start_lives = START_LIVES
        self._sc_asteroid_count = ASTEROID_COUNT
        self._sc_shared_map = True
        self._sc_sandbox = False
        self._sc_boss_waves = True
        self._sc_ufo_spawns = True
        self._sc_wave_events = True
        self._sc_start_modules = []
        self._sc_editing_field = None
        self._sc_respawn_mode = 0  # index into MP_RESPAWN_MODES
        self.state = "server_creator"

    # Server creator row definitions: (label, field_key, type)
    # type: "int_field", "toggle", "list_toggle", "action"
    _SC_ROWS = [
        ("Port",              "_sc_port",           "text_field"),
        ("Max Players",       "_sc_max_players",    "int_adj"),
        ("Shared Map",        "_sc_shared_map",     "toggle"),
        ("Respawn Mode",      "_sc_respawn_mode",   "respawn_sel"),
        ("Starting Wave",     "_sc_start_wave",     "int_adj"),
        ("Starting Sector",   "_sc_start_sector",   "int_adj"),
        ("Starting Lives",    "_sc_start_lives",    "int_adj"),
        ("Asteroid Count",    "_sc_asteroid_count", "int_adj"),
        ("Boss Waves",        "_sc_boss_waves",     "toggle"),
        ("UFO Spawns",        "_sc_ufo_spawns",     "toggle"),
        ("Wave Events",       "_sc_wave_events",    "toggle"),
        ("Starting Modules",  "_sc_start_modules",  "module_sel"),
        ("--- START SERVER ---", None,              "action_start"),
    ]
    _RESPAWN_LABELS = ["Wave Clear", "Score (10K pts)", "Timer (2 min)"]

    def _update_server_creator(self, dt):
        self._animate_menu_bg(dt)
        rows = self._SC_ROWS

        # Text field editing mode
        if self._sc_editing_field is not None:
            while True:
                ch = rl.GetCharPressed()
                if ch == 0:
                    break
                if 32 <= ch <= 126 and len(self._sc_port) < 10:
                    self._sc_port += chr(ch)
            if rl.IsKeyPressed(259) or rl.IsKeyPressedRepeat(259):
                self._sc_port = self._sc_port[:-1]
            if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_ESC):
                self._sc_editing_field = None
            return

        if rl.IsKeyPressed(KEY_ESC):
            self.state = "mp_menu"
            self._mp_sel = 1
            return

        # Navigation
        if rl.IsKeyPressed(KEY_UP):
            self._sc_sel = (self._sc_sel - 1) % len(rows)
            snd.play('menu_select')
        if rl.IsKeyPressed(KEY_DOWN):
            self._sc_sel = (self._sc_sel + 1) % len(rows)
            snd.play('menu_select')

        label, field, rtype = rows[self._sc_sel]

        if rtype == "text_field":
            if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE):
                self._sc_editing_field = field
                snd.play('menu_confirm')
        elif rtype == "int_adj":
            adj = 0
            if rl.IsKeyPressed(KEY_LEFT) or rl.IsKeyPressed(KEY_RIGHT):
                adj = 1 if rl.IsKeyPressed(KEY_RIGHT) else -1
                snd.play('menu_select')
            if adj != 0:
                val = getattr(self, field)
                if field == "_sc_max_players":
                    val = max(2, min(8, val + adj))
                elif field == "_sc_start_wave":
                    val = max(1, min(50, val + adj))
                elif field == "_sc_start_sector":
                    val = max(1, min(10, val + adj))
                elif field == "_sc_start_lives":
                    val = max(1, min(99, val + adj))
                elif field == "_sc_asteroid_count":
                    val = max(1, min(30, val + adj))
                setattr(self, field, val)
        elif rtype == "toggle":
            if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE) or \
               rl.IsKeyPressed(KEY_LEFT) or rl.IsKeyPressed(KEY_RIGHT):
                setattr(self, field, not getattr(self, field))
                snd.play('menu_select')
        elif rtype == "respawn_sel":
            if rl.IsKeyPressed(KEY_LEFT) or rl.IsKeyPressed(KEY_RIGHT) or \
               rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE):
                direction = -1 if rl.IsKeyPressed(KEY_LEFT) else 1
                self._sc_respawn_mode = (self._sc_respawn_mode + direction) % len(MP_RESPAWN_MODES)
                snd.play('menu_select')
        elif rtype == "module_sel":
            if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE):
                # Cycle through modules, add/remove
                snd.play('menu_select')
                # Toggle next not-in-list module, or clear if all present
                available = [m for m in self._ALL_MODULES if m not in self._sc_start_modules]
                if available:
                    self._sc_start_modules.append(available[0])
                else:
                    self._sc_start_modules.clear()
            if rl.IsKeyPressed(KEY_LEFT) and self._sc_start_modules:
                self._sc_start_modules.pop()
                snd.play('menu_select')
            if rl.IsKeyPressed(KEY_RIGHT):
                available = [m for m in self._ALL_MODULES if m not in self._sc_start_modules]
                if available:
                    self._sc_start_modules.append(available[0])
                    snd.play('menu_select')
        elif rtype == "action_start":
            if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE):
                snd.play('menu_confirm')
                self._start_hosting_from_creator()

    def _start_hosting_from_creator(self):
        """Create and start the server with creator settings, then go to lobby."""
        try:
            port = int(self._sc_port)
        except ValueError:
            port = GAME_PORT

        config = {
            'shared_map': self._sc_shared_map,
            'start_wave': self._sc_start_wave,
            'start_sector': self._sc_start_sector,
            'start_lives': self._sc_start_lives,
            'asteroid_count': self._sc_asteroid_count,
            'boss_waves': self._sc_boss_waves,
            'ufo_spawns': self._sc_ufo_spawns,
            'wave_events': self._sc_wave_events,
            'start_modules': self._sc_start_modules,
            'respawn_mode': MP_RESPAWN_MODES[self._sc_respawn_mode],
        }

        if self._server:
            self._server.stop()
        self._server = GameServer(
            player_name=self._mp_name,
            port=port,
            max_clients=self._sc_max_players - 1,  # max_clients = total - host
            server_config=config
        )
        self._server.start()
        self._mp_mode = "host"
        self._mp_shared_map = self._sc_shared_map
        self.state = "host_lobby"

    def _draw_server_creator(self):
        rl.BeginDrawing()
        rl.ClearBackground(colors.BLACK)
        for a in self._menu_asteroids:
            a.draw()
        rl.DrawRectangle(0, 0, SCREEN_W, SCREEN_H, color(0, 0, 0, 170))

        t = self.menu_time
        title = T("SERVER CREATOR").encode()
        tw = measure_text(title, 44)
        draw_text(title, SCREEN_W // 2 - tw // 2, 60, 44, color(100, 255, 100))

        subtitle = T("--- Configure your game ---").encode()
        sw = measure_text(subtitle, 18)
        draw_text(subtitle, SCREEN_W // 2 - sw // 2, 110, 18, color(140, 140, 200))

        rows = self._SC_ROWS
        cy = 150
        left_x = SCREEN_W // 2 - 280
        val_x = SCREEN_W // 2 + 60

        for i, (label, field, rtype) in enumerate(rows):
            is_sel = (i == self._sc_sel)
            sel_pulse = 0.7 + 0.3 * math.sin(t * 5.0) if is_sel else 0

            if rtype == "action_start":
                # Start button
                cy += 10
                btn_text = T(label).encode()
                btw = measure_text(btn_text, 26)
                if is_sel:
                    c = color(100, 255, 100, int(255 * sel_pulse))
                    draw_text(b"> ", SCREEN_W // 2 - btw // 2 - 25, cy, 26, c)
                    draw_text(btn_text, SCREEN_W // 2 - btw // 2, cy, 26, c)
                else:
                    draw_text(btn_text, SCREEN_W // 2 - btw // 2, cy, 26, color(80, 200, 80))
                cy += 36
                continue

            # Label
            lbl_col = color(255, 255, 100, int(255 * sel_pulse)) if is_sel else color(200, 200, 200)
            prefix = b"> " if is_sel else b"  "
            draw_text(prefix + T(label).encode(), left_x, cy, 20, lbl_col)

            # Value
            val_col = color(255, 255, 255) if is_sel else color(170, 170, 170)
            val_str = ""
            if rtype == "text_field":
                editing = self._sc_editing_field == field
                val_str = getattr(self, field)
                if editing and int(t * 2) % 2 == 0:
                    val_str += "_"
                if editing:
                    # Draw field box
                    fw, fh = 160, 28
                    rl.DrawRectangle(val_x - 4, cy - 2, fw, fh, color(20, 20, 40))
                    rl.DrawRectangleLines(val_x - 4, cy - 2, fw, fh, color(100, 200, 255))
                val_col = color(100, 200, 255) if editing else val_col
            elif rtype == "int_adj":
                val = getattr(self, field)
                val_str = f"< {val} >"
            elif rtype == "toggle":
                val = getattr(self, field)
                val_str = T("ON") if val else T("OFF")
                val_col = color(100, 255, 100) if val else color(255, 80, 80)
            elif rtype == "respawn_sel":
                idx = getattr(self, field)
                val_str = f"< {T(self._RESPAWN_LABELS[idx])} >"
            elif rtype == "module_sel":
                mods = getattr(self, field)
                if mods:
                    val_str = ", ".join(m.upper() for m in mods) + "  [</>]"
                else:
                    val_str = "(none)  [ENTER to add]"

            draw_text(val_str.encode(), val_x, cy, 20, val_col)
            cy += 32

        # Footer
        cy += 20
        hints = [
            "UP/DOWN = navigate  |  LEFT/RIGHT = adjust  |  ENTER = toggle/edit",
            "ESC = back to menu",
        ]
        for h in hints:
            hw = measure_text(h.encode(), 14)
            draw_text(h.encode(), SCREEN_W // 2 - hw // 2, cy, 14, color(100, 100, 100))
            cy += 20

        self._draw_fps_counter()
        rl.EndDrawing()

    # ---- CO-OP (LOCAL) ----

    # P2 keyboard mapping: WASD + J(shoot), K(alt1), L(alt2), H(brake), Q/E(strafe)
    _COOP_KB_MAP = {
        'left':  65,   # A
        'right': 68,   # D
        'up':    87,   # W
        'down':  83,   # S
        'shoot': 74,   # J
        'brake': 72,   # H
        'alt1':  75,   # K (gravity bomb)
        'alt2':  76,   # L (hyperspace)
        'strafe_l': 81,  # Q
        'strafe_r': 69,  # E
    }

    _COOP_CONTROL_LABELS = ["Keyboard (WASD+JKLH)", "Xbox Gamepad"]

    def _capture_coop_p2_input(self):
        """Build an input_map dict for co-op player 2 (uses configurable bindings)."""
        from ship import KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SPACE, KEY_Z, KEY_X, KEY_C, KEY_A, KEY_D
        inp = {}

        if self._coop_p2_control == 1 and rl.IsGamepadAvailable(0):
            # Gamepad mode — use configurable gamepad bindings
            gp = 0
            dead = 0.25
            gb = self._gp_binds

            def _gp_down(action):
                code = gb[action]
                if code == -1:
                    return False  # axis — handled separately for left/right
                if code == -2:
                    return rl.GetGamepadAxisMovement(gp, rl.GAMEPAD_AXIS_RIGHT_TRIGGER) > 0.3
                return bool(rl.IsGamepadButtonDown(gp, code))

            def _gp_pressed(action):
                code = gb[action]
                if code <= 0:
                    return False
                return bool(rl.IsGamepadButtonPressed(gp, code))

            # Rotation: stick axis if bound to -1, otherwise button
            if gb['left'] == -1:
                ax_x = rl.GetGamepadAxisMovement(gp, rl.GAMEPAD_AXIS_LEFT_X)
                inp[KEY_LEFT] = ax_x < -dead
                inp[KEY_RIGHT] = ax_x > dead
            else:
                inp[KEY_LEFT] = _gp_down('left')
                inp[KEY_RIGHT] = _gp_down('right')

            inp[KEY_UP] = _gp_down('thrust')
            inp[KEY_DOWN] = _gp_down('brake')
            inp[KEY_SPACE] = _gp_down('shoot')
            inp[KEY_Z] = _gp_down('alt_brake')
            inp[('p', KEY_X)] = _gp_pressed('alt1')
            inp[('p', KEY_C)] = _gp_pressed('alt2')
            inp[KEY_A] = _gp_down('strafe_l')
            inp[KEY_D] = _gp_down('strafe_r')
        else:
            # Keyboard mode — use configurable P2 keyboard bindings
            km = self._kb_p2
            inp[KEY_LEFT] = bool(rl.IsKeyDown(km['left']))
            inp[KEY_RIGHT] = bool(rl.IsKeyDown(km['right']))
            inp[KEY_UP] = bool(rl.IsKeyDown(km['thrust']))
            inp[KEY_DOWN] = bool(rl.IsKeyDown(km['brake']))
            inp[KEY_SPACE] = bool(rl.IsKeyDown(km['shoot']))
            inp[KEY_Z] = bool(rl.IsKeyDown(km['alt_brake']))
            inp[('p', KEY_X)] = bool(rl.IsKeyPressed(km['alt1']))
            inp[('p', KEY_C)] = bool(rl.IsKeyPressed(km['alt2']))
            inp[KEY_A] = bool(rl.IsKeyDown(km['strafe_l']))
            inp[KEY_D] = bool(rl.IsKeyDown(km['strafe_r']))
        return inp

    def _open_coop_creator(self):
        """Open the co-op game creator screen."""
        self._sc_sel = 0
        self._sc_start_wave = 1
        self._sc_start_sector = 1
        self._sc_start_lives = START_LIVES
        self._sc_asteroid_count = ASTEROID_COUNT
        self._sc_boss_waves = True
        self._sc_ufo_spawns = True
        self._sc_wave_events = True
        self._sc_start_modules = []
        self._sc_respawn_mode = 0
        self._coop_editing_p2_name = False
        self._coop_editing_p1_name = False
        self.state = "coop_creator"

    _COOP_ROWS = [
        ("P1 Name",           "_mp_name",            "p1_name"),
        ("P1 Ship Color",     "_mp_ship_color_idx",  "p1_color"),
        ("P1 Ship Skin",      "_ship_skin_idx",      "p1_skin"),
        ("P2 Name",           "_coop_p2_name",       "coop_name"),
        ("P2 Ship Color",     "_coop_p2_color_idx",  "coop_color"),
        ("P2 Ship Skin",      "_coop_p2_skin_idx",   "coop_skin"),
        ("P2 Controls",       "_coop_p2_control",    "coop_ctrl"),
        ("Respawn Mode",      "_sc_respawn_mode",    "respawn_sel"),
        ("Starting Wave",     "_sc_start_wave",      "int_adj"),
        ("Starting Sector",   "_sc_start_sector",    "int_adj"),
        ("Starting Lives",    "_sc_start_lives",     "int_adj"),
        ("Asteroid Count",    "_sc_asteroid_count",  "int_adj"),
        ("Boss Waves",        "_sc_boss_waves",      "toggle"),
        ("UFO Spawns",        "_sc_ufo_spawns",      "toggle"),
        ("Wave Events",       "_sc_wave_events",     "toggle"),
        ("Starting Modules",  "_sc_start_modules",   "module_sel"),
        ("--- START CO-OP ---", None,                "action_start"),
    ]

    def _update_coop_creator(self, dt):
        self._animate_menu_bg(dt)
        rows = self._COOP_ROWS

        # P1 name editing mode
        if self._coop_editing_p1_name:
            while True:
                ch = rl.GetCharPressed()
                if ch == 0:
                    break
                if 32 <= ch <= 126 and len(self._mp_name) < NAME_MAX_LEN:
                    self._mp_name += chr(ch)
            if rl.IsKeyPressed(259) or rl.IsKeyPressedRepeat(259):
                self._mp_name = self._mp_name[:-1]
            if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_ESC):
                if not self._mp_name.strip():
                    self._mp_name = "Player"
                self._coop_editing_p1_name = False
            return

        # P2 name editing mode
        if self._coop_editing_p2_name:
            while True:
                ch = rl.GetCharPressed()
                if ch == 0:
                    break
                if 32 <= ch <= 126 and len(self._coop_p2_name) < NAME_MAX_LEN:
                    self._coop_p2_name += chr(ch)
            if rl.IsKeyPressed(259) or rl.IsKeyPressedRepeat(259):
                self._coop_p2_name = self._coop_p2_name[:-1]
            if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_ESC):
                if not self._coop_p2_name.strip():
                    self._coop_p2_name = "P2"
                self._coop_editing_p2_name = False
            return

        if rl.IsKeyPressed(KEY_ESC):
            self.state = "mp_menu"
            self._mp_sel = 2
            return

        # Navigation
        if rl.IsKeyPressed(KEY_UP):
            self._sc_sel = (self._sc_sel - 1) % len(rows)
            snd.play('menu_select')
        if rl.IsKeyPressed(KEY_DOWN):
            self._sc_sel = (self._sc_sel + 1) % len(rows)
            snd.play('menu_select')

        label, field, rtype = rows[self._sc_sel]

        if rtype == "p1_name":
            if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE):
                self._coop_editing_p1_name = True
                snd.play('menu_confirm')
        elif rtype == "p1_color":
            if rl.IsKeyPressed(KEY_LEFT) or rl.IsKeyPressed(KEY_RIGHT):
                d = 1 if rl.IsKeyPressed(KEY_RIGHT) else -1
                self._mp_ship_color_idx = (self._mp_ship_color_idx + d) % len(SHIP_COLORS)
                snd.play('menu_select')
            if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE):
                self._mp_ship_color_idx = (self._mp_ship_color_idx + 1) % len(SHIP_COLORS)
                snd.play('menu_select')
        elif rtype == "p1_skin":
            if rl.IsKeyPressed(KEY_LEFT) or rl.IsKeyPressed(KEY_RIGHT):
                d = 1 if rl.IsKeyPressed(KEY_RIGHT) else -1
                self._ship_skin_idx = (self._ship_skin_idx + d) % len(SHIP_SKINS)
                snd.play('menu_select')
            if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE):
                self._ship_skin_idx = (self._ship_skin_idx + 1) % len(SHIP_SKINS)
                snd.play('menu_select')
        elif rtype == "coop_name":
            if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE):
                self._coop_editing_p2_name = True
                snd.play('menu_confirm')
        elif rtype == "coop_color":
            if rl.IsKeyPressed(KEY_LEFT) or rl.IsKeyPressed(KEY_RIGHT):
                d = 1 if rl.IsKeyPressed(KEY_RIGHT) else -1
                self._coop_p2_color_idx = (self._coop_p2_color_idx + d) % len(SHIP_COLORS)
                snd.play('menu_select')
            if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE):
                self._coop_p2_color_idx = (self._coop_p2_color_idx + 1) % len(SHIP_COLORS)
                snd.play('menu_select')
        elif rtype == "coop_skin":
            if rl.IsKeyPressed(KEY_LEFT) or rl.IsKeyPressed(KEY_RIGHT):
                d = 1 if rl.IsKeyPressed(KEY_RIGHT) else -1
                self._coop_p2_skin_idx = (self._coop_p2_skin_idx + d) % len(SHIP_SKINS)
                snd.play('menu_select')
            if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE):
                self._coop_p2_skin_idx = (self._coop_p2_skin_idx + 1) % len(SHIP_SKINS)
                snd.play('menu_select')
        elif rtype == "coop_ctrl":
            if rl.IsKeyPressed(KEY_LEFT) or rl.IsKeyPressed(KEY_RIGHT) or \
               rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE):
                self._coop_p2_control = (self._coop_p2_control + 1) % len(self._COOP_CONTROL_LABELS)
                snd.play('menu_select')
        elif rtype == "int_adj":
            adj = 0
            if rl.IsKeyPressed(KEY_LEFT) or rl.IsKeyPressed(KEY_RIGHT):
                adj = 1 if rl.IsKeyPressed(KEY_RIGHT) else -1
                snd.play('menu_select')
            if adj != 0:
                val = getattr(self, field)
                if field == "_sc_start_wave":
                    val = max(1, min(50, val + adj))
                elif field == "_sc_start_sector":
                    val = max(1, min(10, val + adj))
                elif field == "_sc_start_lives":
                    val = max(1, min(99, val + adj))
                elif field == "_sc_asteroid_count":
                    val = max(1, min(30, val + adj))
                setattr(self, field, val)
        elif rtype == "toggle":
            if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE) or \
               rl.IsKeyPressed(KEY_LEFT) or rl.IsKeyPressed(KEY_RIGHT):
                setattr(self, field, not getattr(self, field))
                snd.play('menu_select')
        elif rtype == "respawn_sel":
            if rl.IsKeyPressed(KEY_LEFT) or rl.IsKeyPressed(KEY_RIGHT) or \
               rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE):
                direction = -1 if rl.IsKeyPressed(KEY_LEFT) else 1
                self._sc_respawn_mode = (self._sc_respawn_mode + direction) % len(MP_RESPAWN_MODES)
                snd.play('menu_select')
        elif rtype == "module_sel":
            if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE):
                snd.play('menu_select')
                available = [m for m in self._ALL_MODULES if m not in self._sc_start_modules]
                if available:
                    self._sc_start_modules.append(available[0])
                else:
                    self._sc_start_modules.clear()
            if rl.IsKeyPressed(KEY_LEFT) and self._sc_start_modules:
                self._sc_start_modules.pop()
                snd.play('menu_select')
            if rl.IsKeyPressed(KEY_RIGHT):
                available = [m for m in self._ALL_MODULES if m not in self._sc_start_modules]
                if available:
                    self._sc_start_modules.append(available[0])
                    snd.play('menu_select')
        elif rtype == "action_start":
            if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE):
                snd.play('menu_confirm')
                self._start_coop_game()

    def _start_coop_game(self):
        """Start a local co-op game."""
        import config as _cfg
        old_ast = _cfg.ASTEROID_COUNT
        _cfg.ASTEROID_COUNT = self._sc_asteroid_count
        old_lives = _cfg.START_LIVES
        _cfg.START_LIVES = self._sc_start_lives

        self._mp_mode = "coop"
        self._mp_shared_map = True
        self.game_seed = None
        self._init_game_state()
        self.mp_respawn_mode = MP_RESPAWN_MODES[self._sc_respawn_mode]

        # Apply config
        start_wave = self._sc_start_wave
        if start_wave > 1:
            self.level = start_wave
        for mod_id in self._sc_start_modules:
            self.ship.add_module(mod_id)

        # Restore config
        _cfg.ASTEROID_COUNT = old_ast
        _cfg.START_LIVES = old_lives

        # Apply P1 ship color + skin
        _, p1_col = SHIP_COLORS[self._mp_ship_color_idx]
        self.ship.ship_color = p1_col
        self.ship.set_skin(self._ship_skin_idx)

        # Create P2 ship
        self._mp_ship2 = Ship(SCREEN_W // 2 + 80, SCREEN_H // 2)
        _, p2_col = SHIP_COLORS[self._coop_p2_color_idx]
        self._mp_ship2.ship_color = p2_col
        self._mp_ship2.set_skin(self._coop_p2_skin_idx)
        for mod_id in self._sc_start_modules:
            self._mp_ship2.add_module(mod_id)

        # Store config for respawn/game_over logic
        self._mp_game_config = {
            'boss_waves': self._sc_boss_waves,
            'ufo_spawns': self._sc_ufo_spawns,
            'wave_events': self._sc_wave_events,
            'respawn_mode': MP_RESPAWN_MODES[self._sc_respawn_mode],
        }

        self.state = "playing"

    def _draw_coop_creator(self):
        rl.BeginDrawing()
        rl.ClearBackground(colors.BLACK)
        for a in self._menu_asteroids:
            a.draw()
        rl.DrawRectangle(0, 0, SCREEN_W, SCREEN_H, color(0, 0, 0, 170))

        t = self.menu_time
        title = T("CO-OP (LOCAL)").encode()
        tw = measure_text(title, 44)
        draw_text(title, SCREEN_W // 2 - tw // 2, 60, 44, color(255, 200, 100))

        subtitle = T("--- Configure your local game ---").encode()
        sw = measure_text(subtitle, 18)
        draw_text(subtitle, SCREEN_W // 2 - sw // 2, 110, 18, color(140, 140, 200))

        rows = self._COOP_ROWS
        cy = 150
        left_x = SCREEN_W // 2 - 280
        val_x = SCREEN_W // 2 + 60

        for i, (label, field, rtype) in enumerate(rows):
            is_sel = (i == self._sc_sel)
            sel_pulse = 0.7 + 0.3 * math.sin(t * 5.0) if is_sel else 0

            if rtype == "action_start":
                cy += 10
                btn_text = T(label).encode()
                btw = measure_text(btn_text, 26)
                if is_sel:
                    c = color(255, 200, 100, int(255 * sel_pulse))
                    draw_text(b"> ", SCREEN_W // 2 - btw // 2 - 25, cy, 26, c)
                    draw_text(btn_text, SCREEN_W // 2 - btw // 2, cy, 26, c)
                else:
                    draw_text(btn_text, SCREEN_W // 2 - btw // 2, cy, 26, color(200, 160, 80))
                cy += 36
                continue

            # Label
            lbl_col = color(255, 255, 100, int(255 * sel_pulse)) if is_sel else color(200, 200, 200)
            prefix = b"> " if is_sel else b"  "
            draw_text(prefix + T(label).encode(), left_x, cy, 20, lbl_col)

            # Value
            val_col = color(255, 255, 255) if is_sel else color(170, 170, 170)
            val_str = ""

            if rtype == "p1_name":
                val_str = self._mp_name
                if self._coop_editing_p1_name:
                    if int(t * 2) % 2 == 0:
                        val_str += "_"
                    val_col = color(100, 200, 255)
                    fw, fh = 160, 28
                    rl.DrawRectangle(val_x - 4, cy - 2, fw, fh, color(20, 20, 40))
                    rl.DrawRectangleLines(val_x - 4, cy - 2, fw, fh, color(100, 200, 255))
            elif rtype == "p1_color":
                col_name, col_rgb = SHIP_COLORS[self._mp_ship_color_idx]
                val_str = f"< {T(col_name)} >"
                cr, cg, cb = col_rgb
                sx = val_x + measure_text(val_str.encode(), 20) + 10
                rl.DrawRectangle(sx, cy + 1, 18, 18, color(cr, cg, cb))
                rl.DrawRectangleLines(sx, cy + 1, 18, 18, color(255, 255, 255, 80))
            elif rtype == "coop_name":
                val_str = self._coop_p2_name
                if self._coop_editing_p2_name:
                    if int(t * 2) % 2 == 0:
                        val_str += "_"
                    val_col = color(100, 200, 255)
                    fw, fh = 160, 28
                    rl.DrawRectangle(val_x - 4, cy - 2, fw, fh, color(20, 20, 40))
                    rl.DrawRectangleLines(val_x - 4, cy - 2, fw, fh, color(100, 200, 255))
            elif rtype == "coop_color":
                col_name, col_rgb = SHIP_COLORS[self._coop_p2_color_idx]
                val_str = f"< {T(col_name)} >"
                cr, cg, cb = col_rgb
                sx = val_x + measure_text(val_str.encode(), 20) + 10
                rl.DrawRectangle(sx, cy + 1, 18, 18, color(cr, cg, cb))
                rl.DrawRectangleLines(sx, cy + 1, 18, 18, color(255, 255, 255, 80))
            elif rtype == "p1_skin":
                skin_name = SKIN_NAMES[self._ship_skin_idx]
                val_str = f"< {T(skin_name)} >"
                # Mini ship preview
                _, hull, _, _ = SHIP_SKINS[self._ship_skin_idx]
                pcr, pcg, pcb = SHIP_COLORS[self._mp_ship_color_idx][1]
                sx = val_x + measure_text(val_str.encode(), 20) + 10
                scale = 0.45
                for j in range(len(hull)):
                    px1, py1 = hull[j]
                    px2, py2 = hull[(j + 1) % len(hull)]
                    rl.DrawLineV(vec2(sx + px1 * scale, cy + 10 + py1 * scale),
                                 vec2(sx + px2 * scale, cy + 10 + py2 * scale),
                                 color(pcr, pcg, pcb))
            elif rtype == "coop_skin":
                skin_name = SKIN_NAMES[self._coop_p2_skin_idx]
                val_str = f"< {T(skin_name)} >"
                # Mini ship preview
                _, hull, _, _ = SHIP_SKINS[self._coop_p2_skin_idx]
                pcr, pcg, pcb = SHIP_COLORS[self._coop_p2_color_idx][1]
                sx = val_x + measure_text(val_str.encode(), 20) + 10
                scale = 0.45
                for j in range(len(hull)):
                    px1, py1 = hull[j]
                    px2, py2 = hull[(j + 1) % len(hull)]
                    rl.DrawLineV(vec2(sx + px1 * scale, cy + 10 + py1 * scale),
                                 vec2(sx + px2 * scale, cy + 10 + py2 * scale),
                                 color(pcr, pcg, pcb))
            elif rtype == "coop_ctrl":
                ctrl_label = self._COOP_CONTROL_LABELS[self._coop_p2_control]
                val_str = f"< {T(ctrl_label)} >"
                # Show gamepad status
                if self._coop_p2_control == 1:
                    if rl.IsGamepadAvailable(0):
                        draw_text(b"  [CONNECTED]", val_x + measure_text(val_str.encode(), 20) + 8, cy + 4, 14, color(100, 255, 100))
                    else:
                        draw_text(b"  [NOT FOUND]", val_x + measure_text(val_str.encode(), 20) + 8, cy + 4, 14, color(255, 80, 80))
            elif rtype == "int_adj":
                val = getattr(self, field)
                val_str = f"< {val} >"
            elif rtype == "toggle":
                val = getattr(self, field)
                val_str = T("ON") if val else T("OFF")
                val_col = color(100, 255, 100) if val else color(255, 80, 80)
            elif rtype == "respawn_sel":
                idx = getattr(self, field)
                val_str = f"< {T(self._RESPAWN_LABELS[idx])} >"
            elif rtype == "module_sel":
                mods = getattr(self, field)
                if mods:
                    val_str = ", ".join(m.upper() for m in mods) + "  [</>]"
                else:
                    val_str = "(none)  [ENTER to add]"

            draw_text(val_str.encode(), val_x, cy, 20, val_col)
            cy += 32

        # Footer
        cy += 10
        hints = [
            "UP/DOWN = navigate  |  LEFT/RIGHT = adjust  |  ENTER = toggle/edit",
            "ESC = back to menu",
        ]
        for h in hints:
            hw = measure_text(h.encode(), 14)
            draw_text(h.encode(), SCREEN_W // 2 - hw // 2, cy, 14, color(100, 100, 100))
            cy += 20

        # P2 controls reference
        cy += 5
        if self._coop_p2_control == 0:
            ctrl_ref = b"P2 Controls: W/A/S/D=move  J=shoot  H=brake  K/L=alt-fire  Q/E=strafe"
        else:
            ctrl_ref = b"P2 Controls: L-Stick=rotate  A=thrust  RT=shoot  B=brake  X/Y=alt-fire  LB/RB=strafe"
        crw = measure_text(ctrl_ref, 13) 
        draw_text(ctrl_ref, SCREEN_W // 2 - crw // 2, cy, 13, color(120, 120, 180))

        self._draw_fps_counter()
        rl.EndDrawing()

    # ---- HOST LOBBY (with ready-up) ----

    def _host_start_game(self):
        """Host triggers game start with server config."""
        self._server.start_game()
        self._mp_mode = "host"
        cfg = self._server.server_config
        self.game_seed = None
        import config as _cfg
        old_ast_count = _cfg.ASTEROID_COUNT
        _cfg.ASTEROID_COUNT = cfg.get('asteroid_count', ASTEROID_COUNT)
        old_start_lives = _cfg.START_LIVES
        _cfg.START_LIVES = cfg.get('start_lives', START_LIVES)
        self._mp_shared_map = cfg.get('shared_map', True)
        self._init_game_state()
        self.mp_respawn_mode = cfg.get('respawn_mode', 'wave')
        start_wave = cfg.get('start_wave', 1)
        if start_wave > 1:
            self.level = start_wave
        for mod_id in cfg.get('start_modules', []):
            self.ship.add_module(mod_id)
        _cfg.ASTEROID_COUNT = old_ast_count
        _cfg.START_LIVES = old_start_lives
        # Apply host ship color + skin
        _, host_col = SHIP_COLORS[self._mp_ship_color_idx]
        self.ship.ship_color = host_col
        self.ship.set_skin(self._ship_skin_idx)
        self._mp_ship2 = Ship(SCREEN_W // 2 + 80, SCREEN_H // 2)
        # Apply client ship color + skin from join message
        if self._server:
            client_col = self._server.get_first_client_color()
            self._mp_ship2.ship_color = tuple(client_col)
            client_skin = self._server.get_first_client_skin()
            self._mp_ship2.set_skin(client_skin)
        for mod_id in cfg.get('start_modules', []):
            self._mp_ship2.add_module(mod_id)
        self._mp_game_config = cfg
        self.state = "playing"

    def _update_host_lobby(self, dt):
        self._animate_menu_bg(dt)
        if rl.IsKeyPressed(KEY_ESC):
            if self._server:
                self._server.stop()
                self._server = None
            self.state = "server_creator"
            return

        # Broadcast lobby state periodically
        if self._server:
            self._lobby_send_timer += dt
            if self._lobby_send_timer >= 0.25:
                self._lobby_send_timer = 0.0
                self._server.broadcast_lobby()

        # ENTER = start game (bypass, whoever is ready joins)
        if rl.IsKeyPressed(KEY_ENTER) and self._server and self._server.client_count > 0:
            ready_count = self._server.get_ready_count()
            if ready_count > 0:
                snd.play('menu_confirm')
                self._host_start_game()
                return

        # SPACE = start only if all ready
        if rl.IsKeyPressed(KEY_SPACE) and self._server and self._server.all_ready():
            snd.play('menu_confirm')
            self._host_start_game()
            return

    def _draw_host_lobby(self):
        rl.BeginDrawing()
        rl.ClearBackground(colors.BLACK)
        for a in self._menu_asteroids:
            a.draw()
        rl.DrawRectangle(0, 0, SCREEN_W, SCREEN_H, color(0, 0, 0, 160))

        t = self.menu_time
        title = T("GAME LOBBY").encode()
        tw = measure_text(title, 48)
        draw_text(title, SCREEN_W // 2 - tw // 2, 60, 48, color(100, 255, 100))

        cy = 130
        if self._server:
            ip_text = f"IP: {self._server.local_ip}:{self._server.port}".encode()
            draw_text(ip_text, SCREEN_W // 2 - 200, cy, 20, color(180, 180, 180))
            cy += 28
            map_text = f"Map: {'Shared' if self._mp_shared_map else 'Separate'}  |  Max: {self._server.max_clients + 1}".encode()
            draw_text(map_text, SCREEN_W // 2 - 200, cy, 20, color(180, 180, 180))
            cy += 40

            # Player list header
            draw_text(T("--- PLAYERS ---").encode(), SCREEN_W // 2 - 70, cy, 20, color(150, 150, 200))
            cy += 35

            # Host entry (always ready)
            host_label = f"  {self._mp_name}  [HOST]  READY".encode()
            draw_text(host_label, SCREEN_W // 2 - 200, cy, 22, color(100, 255, 100))
            cy += 34

            # Client entries
            client_names = self._server.get_client_names()
            for name, ready in client_names:
                ready_str = "READY" if ready else "NOT READY"
                ready_col = color(100, 255, 100) if ready else color(255, 100, 100)
                entry = f"  {name}".encode()
                draw_text(entry, SCREEN_W // 2 - 200, cy, 22, color(220, 220, 220))
                rs = f"  {ready_str}".encode()
                draw_text(rs, SCREEN_W // 2 + 80, cy, 22, ready_col)
                cy += 34

            cy += 20

            # Waiting indicator
            if self._server.client_count == 0:
                dots = "." * (int(t * 2) % 4)
                wait = f"Waiting for players to join{dots}".encode()
                ww = measure_text(wait, 22)
                draw_text(wait, SCREEN_W // 2 - ww // 2, cy, 22, color(180, 180, 255))
                cy += 40

                info_lines = [
                    "Other players on LAN will see this game automatically.",
                    "Outside your network: share your IP address.",
                ]
                for line in info_lines:
                    draw_text(line.encode(), SCREEN_W // 2 - 250, cy, 15,
                                color(120, 120, 120))
                    cy += 22
            else:
                # Start instructions
                ready_count = self._server.get_ready_count()
                total = self._server.client_count
                all_rdy = self._server.all_ready()

                cy += 10
                if all_rdy:
                    pulse_a = int(180 + 75 * math.sin(t * 4))
                    txt = T("ALL PLAYERS READY!  Press ENTER or SPACE to start").encode()
                    txw = measure_text(txt, 22)
                    draw_text(txt, SCREEN_W // 2 - txw // 2, cy, 22,
                                color(100, 255, 100, pulse_a))
                elif ready_count > 0:
                    txt = f"ENTER = force start with {ready_count} ready player(s)".encode()
                    txw = measure_text(txt, 20)
                    draw_text(txt, SCREEN_W // 2 - txw // 2, cy, 20,
                                color(255, 200, 100))
                else:
                    txt = T("Waiting for players to ready up...").encode()
                    txw = measure_text(txt, 20)
                    draw_text(txt, SCREEN_W // 2 - txw // 2, cy, 20,
                                color(200, 200, 100))
        else:
            draw_text(T("Failed to start server.").encode(), SCREEN_W // 2 - 130, cy, 22,
                        color(255, 80, 80))

        back = T("ESC = cancel").encode()
        bw = measure_text(back, 16)
        draw_text(back, SCREEN_W // 2 - bw // 2, SCREEN_H - 50, 16, color(100, 100, 100))

        self._draw_fps_counter()
        rl.EndDrawing()

    # ---- JOIN LOBBY ----

    def _start_join_lobby(self):
        if self._scanner:
            self._scanner.stop()
        self._scanner = LANScanner()
        self._scanner.start()
        self._join_sel = 0
        self._join_ip_input = ""
        self._join_ip_active = False
        self._join_connecting = False
        if self._client:
            self._client.disconnect()
        self._client = GameClient(player_name=self._mp_name,
                                         ship_color=SHIP_COLORS[self._mp_ship_color_idx][1],
                                         ship_skin=self._ship_skin_idx)
        self.state = "join_lobby"

    def _update_join_lobby(self, dt):
        self._animate_menu_bg(dt)

        if rl.IsKeyPressed(KEY_ESC):
            if self._join_ip_active:
                self._join_ip_active = False
                return
            if self._scanner:
                self._scanner.stop()
                self._scanner = None
            if self._client:
                self._client.disconnect()
                self._client = None
            self.state = "mp_menu"
            self._mp_sel = 2
            return

        # If connection succeeded, go to client lobby (ready-up screen)
        if self._client and self._client.connected and self._client.status == "lobby":
            if self._scanner:
                self._scanner.stop()
                self._scanner = None
            self.state = "client_lobby"
            return

        servers = self._scanner.get_servers() if self._scanner else []

        # ---- IP input mode ----
        if self._join_ip_active:
            while True:
                ch = rl.GetCharPressed()
                if ch == 0:
                    break
                if (32 <= ch <= 126) and len(self._join_ip_input) < 40:
                    self._join_ip_input += chr(ch)
            if rl.IsKeyPressed(259) or rl.IsKeyPressedRepeat(259):
                self._join_ip_input = self._join_ip_input[:-1]
            if rl.IsKeyPressed(KEY_ENTER) and self._join_ip_input.strip():
                self._try_connect(self._join_ip_input.strip())
            return

        # ---- normal nav ----
        total = len(servers) + 1  # +1 for "Enter IP manually"
        if rl.IsKeyPressed(KEY_UP):
            self._join_sel = (self._join_sel - 1) % total
            snd.play('menu_select')
        if rl.IsKeyPressed(KEY_DOWN):
            self._join_sel = (self._join_sel + 1) % total
            snd.play('menu_select')

        if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE):
            snd.play('menu_confirm')
            if self._join_sel < len(servers):
                srv = servers[self._join_sel]
                self._try_connect(srv['ip'], srv['port'])
            else:
                self._join_ip_active = True
                self._join_ip_input = ""

    def _try_connect(self, ip, port=GAME_PORT):
        """Attempt connection in a background thread."""
        if self._join_connecting:
            return
        # Parse ip:port format
        if ':' in ip:
            parts = ip.rsplit(':', 1)
            ip = parts[0]
            try:
                port = int(parts[1])
            except ValueError:
                pass
        self._join_connecting = True
        self._client = GameClient(player_name=self._mp_name,
                                         ship_color=SHIP_COLORS[self._mp_ship_color_idx][1],
                                         ship_skin=self._ship_skin_idx)

        def _do():
            self._client.connect(ip, port)
            self._join_connecting = False

        threading.Thread(target=_do, daemon=True).start()

    def _draw_join_lobby(self):
        rl.BeginDrawing()
        rl.ClearBackground(colors.BLACK)
        for a in self._menu_asteroids:
            a.draw()
        rl.DrawRectangle(0, 0, SCREEN_W, SCREEN_H, color(0, 0, 0, 160))

        t = self.menu_time
        title = T("JOIN GAME").encode()
        tw = measure_text(title, 48)
        draw_text(title, SCREEN_W // 2 - tw // 2, 80, 48, color(100, 200, 255))

        cy = 160
        # Status line
        if self._client and self._client.status not in ("idle",):
            st = self._client.status_msg.encode()
            stw = measure_text(st, 18)
            c = color(100, 255, 100) if self._client.status == "connected" else \
                color(255, 200, 100) if self._client.status == "connecting" else \
                color(255, 80, 80)
            draw_text(st, SCREEN_W // 2 - stw // 2, cy, 18, c)
            cy += 30

        # LAN servers header
        draw_text(T("--- LAN Servers ---").encode(), SCREEN_W // 2 - 85, cy, 18, color(150, 150, 200))
        cy += 30

        servers = self._scanner.get_servers() if self._scanner else []
        if not servers:
            draw_text(T("Searching for games on LAN...").encode(), SCREEN_W // 2 - 150, cy, 18,
                        color(120, 120, 120))
            dots = "." * (int(t * 2) % 4)
            draw_text(dots.encode(), SCREEN_W // 2 + 160, cy, 18, color(120, 120, 120))
            cy += 40
        else:
            for i, srv in enumerate(servers):
                is_sel = (i == self._join_sel)
                line = f"{srv['name']}  -  {srv['ip']}:{srv['port']}  ({srv['players']}/{srv['max']})".encode()
                if is_sel:
                    sel_pulse = 0.7 + 0.3 * math.sin(t * 5.0)
                    c = color(255, 255, 100, int(255 * sel_pulse))
                    draw_text(b"> ", SCREEN_W // 2 - 280, cy, 22, c)
                    draw_text(line, SCREEN_W // 2 - 250, cy, 22, c)
                else:
                    draw_text(line, SCREEN_W // 2 - 250, cy, 22, color(200, 200, 200))
                cy += 36

        # "Enter IP manually" option
        cy += 10
        manual_idx = len(servers)
        is_sel_manual = (self._join_sel == manual_idx) and not self._join_ip_active
        if is_sel_manual:
            sel_pulse = 0.7 + 0.3 * math.sin(t * 5.0)
            c = color(255, 200, 100, int(255 * sel_pulse))
            txt = ("> " + T("Enter IP manually...")).encode()
            draw_text(txt, SCREEN_W // 2 - 140, cy, 22, c)
        else:
            draw_text(("  " + T("Enter IP manually...")).encode(), SCREEN_W // 2 - 140, cy, 22,
                        color(150, 150, 150))
        cy += 40

        # IP input field (active)
        if self._join_ip_active:
            draw_text(T("Enter host IP (or IP:port):").encode(), SCREEN_W // 2 - 150, cy, 18,
                        color(200, 200, 200))
            cy += 30
            field_w = 400
            field_h = 40
            fx = SCREEN_W // 2 - field_w // 2
            rl.DrawRectangle(fx, cy, field_w, field_h, color(20, 20, 30))
            rl.DrawRectangleLines(fx, cy, field_w, field_h, color(100, 200, 255))

            display = self._join_ip_input
            if int(t * 2) % 2 == 0:
                display += "_"
            draw_text(display.encode(), fx + 10, cy + 8, 22, color(255, 255, 255))
            cy += 50
            draw_text(T("ENTER to connect  |  ESC to cancel").encode(), SCREEN_W // 2 - 170, cy, 16,
                        color(120, 120, 120))

        # Footer
        back = T("ESC to go back  |  UP/DOWN to select  |  ENTER to join").encode()
        bw = measure_text(back, 16)
        draw_text(back, SCREEN_W // 2 - bw // 2, SCREEN_H - 50, 16, color(100, 100, 100))

        self._draw_fps_counter()
        rl.EndDrawing()

    # ---- CLIENT LOBBY (ready-up) ----

    def _client_enter_game(self):
        """Client transitions from lobby to actual gameplay."""
        self._mp_mode = "client"
        self.game_seed = None
        cfg = getattr(self._client, 'server_config', {}) or {}
        self._mp_shared_map = cfg.get('shared_map', True)
        import config as _cfg
        old_ast = _cfg.ASTEROID_COUNT
        old_lives = _cfg.START_LIVES
        _cfg.ASTEROID_COUNT = cfg.get('asteroid_count', ASTEROID_COUNT)
        _cfg.START_LIVES = cfg.get('start_lives', START_LIVES)
        self._init_game_state()
        self.mp_respawn_mode = cfg.get('respawn_mode', 'wave')
        start_wave = cfg.get('start_wave', 1)
        if start_wave > 1:
            self.level = start_wave
        for mod_id in cfg.get('start_modules', []):
            self.ship.add_module(mod_id)
        _cfg.ASTEROID_COUNT = old_ast
        _cfg.START_LIVES = old_lives
        # Apply client ship color + skin
        _, client_col = SHIP_COLORS[self._mp_ship_color_idx]
        self.ship.ship_color = client_col
        self.ship.set_skin(self._ship_skin_idx)
        self._mp_game_config = cfg
        self.state = "playing"

    def _update_client_lobby(self, dt):
        self._animate_menu_bg(dt)

        if rl.IsKeyPressed(KEY_ESC):
            if self._client:
                self._client.disconnect()
                self._client = None
            self.state = "mp_menu"
            self._mp_sel = 2
            return

        # Toggle ready
        if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE):
            if self._client and self._client.connected:
                self._client.toggle_ready()
                snd.play('menu_confirm')

        # Game started by host?
        if self._client and self._client.game_started:
            self._client_enter_game()
            return

        # Disconnected?
        if self._client and not self._client.connected:
            self.powerup_msg = self._client.status_msg or "Disconnected"
            self.powerup_msg_time = 3.0
            self.state = "mp_menu"
            self._mp_sel = 2
            return

    def _draw_client_lobby(self):
        rl.BeginDrawing()
        rl.ClearBackground(colors.BLACK)
        for a in self._menu_asteroids:
            a.draw()
        rl.DrawRectangle(0, 0, SCREEN_W, SCREEN_H, color(0, 0, 0, 160))

        t = self.menu_time
        title = T("GAME LOBBY").encode()
        tw = measure_text(title, 48)
        draw_text(title, SCREEN_W // 2 - tw // 2, 60, 48, color(100, 200, 255))

        cy = 130
        if self._client:
            host_text = f"Host: {self._client.host_name}".encode()
            draw_text(host_text, SCREEN_W // 2 - 200, cy, 20, color(180, 180, 180))
            cy += 40

            # Player list
            draw_text(T("--- PLAYERS ---").encode(), SCREEN_W // 2 - 70, cy, 20, color(150, 150, 200))
            cy += 35

            players = []
            with self._client._lock:
                players = list(self._client.lobby_players)

            if players:
                for p in players:
                    name = p.get('name', '?')
                    ready = p.get('ready', False)
                    is_host = p.get('host', False)
                    tag = " [HOST]" if is_host else ""
                    ready_str = "READY" if ready else "NOT READY"
                    ready_col = color(100, 255, 100) if ready else color(255, 100, 100)
                    entry_text = f"  {name}{tag}".encode()
                    draw_text(entry_text, SCREEN_W // 2 - 200, cy, 22, color(220, 220, 220))
                    draw_text(f"  {ready_str}".encode(), SCREEN_W // 2 + 80, cy, 22, ready_col)
                    cy += 34
            else:
                draw_text(T("Waiting for lobby info...").encode(), SCREEN_W // 2 - 200, cy, 20,
                            color(150, 150, 150))
                cy += 34

            cy += 30
            # Ready toggle button
            if self._client.is_ready:
                pulse_a = int(180 + 75 * math.sin(t * 4))
                txt = T("You are READY!  (ENTER to unready)").encode()
                txw = measure_text(txt, 22)
                draw_text(txt, SCREEN_W // 2 - txw // 2, cy, 22,
                            color(100, 255, 100, pulse_a))
            else:
                txt = T("Press ENTER or SPACE to READY UP").encode()
                txw = measure_text(txt, 22)
                pulse_a = int(180 + 75 * math.sin(t * 3))
                draw_text(txt, SCREEN_W // 2 - txw // 2, cy, 22,
                            color(255, 200, 100, pulse_a))
            cy += 40
            draw_text(T("Waiting for host to start the game...").encode(),
                        SCREEN_W // 2 - 180, cy, 16, color(140, 140, 140))

        back = T("ESC = disconnect").encode()
        bw = measure_text(back, 16)
        draw_text(back, SCREEN_W // 2 - bw // 2, SCREEN_H - 50, 16, color(100, 100, 100))

        self._draw_fps_counter()
        rl.EndDrawing()

    # ====================================================================
    #  PAUSE MENU
    # ====================================================================

    PAUSE_OPTIONS = ["Resume", "Restart Wave", "Options", "Controls", "Main Menu", "Quit"]

    def _update_pause_menu(self, dt):
        # Music keeps playing quietly when paused
        snd.update_music(0.15, self.sector.number, False)

        opts = self.PAUSE_OPTIONS

        if rl.IsKeyPressed(KEY_ESC):
            self.state = "playing"
            return

        if rl.IsKeyPressed(KEY_UP):
            self.pause_sel = (self.pause_sel - 1) % len(opts)
            snd.play('menu_select')
        if rl.IsKeyPressed(KEY_DOWN):
            self.pause_sel = (self.pause_sel + 1) % len(opts)
            snd.play('menu_select')

        # Mouse hover
        my = rl.GetMouseY()
        oy = SCREEN_H // 2 - 60
        for i in range(len(opts)):
            y = oy + i * 45
            if y <= my <= y + 30:
                self.pause_sel = i

        confirm = rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE)
        if rl.IsMouseButtonPressed(0):
            for i in range(len(opts)):
                y = oy + i * 45
                if y <= my <= y + 30:
                    confirm = True
                    self.pause_sel = i

        if confirm:
            snd.play('menu_confirm')
            sel = opts[self.pause_sel]
            if sel == "Resume":
                self.state = "playing"
            elif sel == "Restart Wave":
                self._init_game_state()
                self.state = "playing"
            elif sel == "Options":
                self.state = "options"
                self._options_return_to = "paused"
                self._opt_sel = 0
            elif sel == "Controls":
                self.state = "controls"
                self._controls_return_to = "paused"
                self._ctrl_section = 0
                self._ctrl_sel = 0
                self._ctrl_listening = False
            elif sel == "Main Menu":
                self._mp_cleanup()
                self.state = "main_menu"
                self.menu_sel = 0
            elif sel == "Quit":
                rl.CloseWindow()
                raise SystemExit(0)

    def _draw_pause_menu(self):
        # Dim overlay over the game
        rl.DrawRectangle(0, 0, SCREEN_W, SCREEN_H, color(0, 0, 0, 180))

        title = T("PAUSED").encode()
        tw = measure_text(title, 48)
        draw_text(title, SCREEN_W // 2 - tw // 2, SCREEN_H // 2 - 140, 48, colors.RAYWHITE)

        opts = self.PAUSE_OPTIONS
        oy = SCREEN_H // 2 - 60
        for i, opt in enumerate(opts):
            text = T(opt).encode()
            size = 24
            tw = measure_text(text, size)
            x = SCREEN_W // 2 - tw // 2
            y = oy + i * 45

            if i == self.pause_sel:
                draw_text(b"> ", x - 24, y, size, color(255, 255, 100))
                draw_text(text, x, y, size, color(255, 255, 100))
            else:
                draw_text(text, x, y, size, color(180, 180, 180))

    # ====================================================================
    #  CONTROLS SCREEN
    # ====================================================================

    _CTRL_SECTIONS = ["Keyboard P1", "Keyboard P2 (Co-op)", "Xbox Gamepad"]

    def _get_ctrl_binds(self):
        """Return the binding dict for current controls section."""
        if self._ctrl_section == 0:
            return self._kb_p1
        elif self._ctrl_section == 1:
            return self._kb_p2
        else:
            return self._gp_binds

    def _get_ctrl_defaults(self):
        """Return the default binding dict for current controls section."""
        if self._ctrl_section == 0:
            return DEFAULT_KB_P1
        elif self._ctrl_section == 1:
            return DEFAULT_KB_P2
        else:
            return DEFAULT_GP

    def _ctrl_key_name(self, code):
        """Human-readable name for a key/button code in current section."""
        if self._ctrl_section <= 1:
            return _RLKEY_NAMES.get(code, f"Key {code}")
        else:
            return _GP_ALL_NAMES.get(code, f"Btn {code}")

    def _ctrl_num_rows(self):
        """Number of selectable rows: actions + Reset Defaults + Save & Back."""
        return len(_BIND_ACTIONS) + 2

    def _update_controls(self, dt):
        self.menu_time += dt
        import config
        sw, sh = config.SCREEN_W, config.SCREEN_H
        for a in self._menu_asteroids:
            a.x += a.vx * dt
            a.y += a.vy * dt
            a.angle += a.rot_speed * dt
            a.x %= sw
            a.y %= sh

        # If listening for a key/button press
        if self._ctrl_listening:
            if rl.IsKeyPressed(KEY_ESC):
                # Cancel rebinding
                self._ctrl_listening = False
                self._ctrl_listen_action = None
                return

            if self._ctrl_section <= 1:
                # Keyboard — detect any key press
                for code in range(32, 350):
                    if code == KEY_ESC:
                        continue
                    if rl.IsKeyPressed(code):
                        binds = self._get_ctrl_binds()
                        binds[self._ctrl_listen_action] = code
                        self._ctrl_listening = False
                        self._ctrl_listen_action = None
                        return
            else:
                # Gamepad — detect button press or axis
                if rl.IsGamepadAvailable(0):
                    gp = 0
                    # Check buttons (1-15)
                    for btn in range(1, 16):
                        if rl.IsGamepadButtonPressed(gp, btn):
                            self._gp_binds[self._ctrl_listen_action] = btn
                            self._ctrl_listening = False
                            self._ctrl_listen_action = None
                            return
                    # Check right trigger axis
                    rt = rl.GetGamepadAxisMovement(gp, rl.GAMEPAD_AXIS_RIGHT_TRIGGER)
                    if rt > 0.5:
                        self._gp_binds[self._ctrl_listen_action] = -2
                        self._ctrl_listening = False
                        self._ctrl_listen_action = None
                        return
                    # Check left stick X axis (full push)
                    lx = abs(rl.GetGamepadAxisMovement(gp, rl.GAMEPAD_AXIS_LEFT_X))
                    if lx > 0.8:
                        self._gp_binds[self._ctrl_listen_action] = -1
                        self._ctrl_listening = False
                        self._ctrl_listen_action = None
                        return
            return

        # ESC — go back
        if rl.IsKeyPressed(KEY_ESC):
            self.state = self._controls_return_to
            return

        # Tab to switch section
        if rl.IsKeyPressed(258):  # TAB
            self._ctrl_section = (self._ctrl_section + 1) % 3
            self._ctrl_sel = 0

        # Mouse click on section tabs
        if rl.IsMouseButtonPressed(0):
            mx, my = rl.GetMouseX(), rl.GetMouseY()
            tab_y = 80
            tab_w = 200
            total_w = tab_w * 3 + 20
            tab_x0 = SCREEN_W // 2 - total_w // 2
            if tab_y <= my <= tab_y + 30:
                for i in range(3):
                    tx = tab_x0 + i * (tab_w + 10)
                    if tx <= mx <= tx + tab_w:
                        if self._ctrl_section != i:
                            self._ctrl_section = i
                            self._ctrl_sel = 0
                        break

        # Navigate rows
        num_rows = self._ctrl_num_rows()
        if rl.IsKeyPressed(KEY_UP):
            self._ctrl_sel = (self._ctrl_sel - 1) % num_rows
            snd.play('menu_select')
        if rl.IsKeyPressed(KEY_DOWN):
            self._ctrl_sel = (self._ctrl_sel + 1) % num_rows
            snd.play('menu_select')

        # Mouse hover
        my = rl.GetMouseY()
        oy = 165
        row_h = 32
        for i in range(num_rows):
            y = oy + i * row_h
            if y <= my <= y + 26:
                self._ctrl_sel = i

        # Confirm (ENTER/SPACE/click)
        confirm = rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE)
        if rl.IsMouseButtonPressed(0):
            for i in range(num_rows):
                y = oy + i * row_h
                if y <= my <= y + 26:
                    confirm = True
                    self._ctrl_sel = i

        if confirm:
            sel = self._ctrl_sel
            if sel < len(_BIND_ACTIONS):
                # Start listening for new key/button
                action_id = _BIND_ACTIONS[sel][0]
                self._ctrl_listening = True
                self._ctrl_listen_action = action_id
                snd.play('menu_confirm')
            elif sel == len(_BIND_ACTIONS):
                # Reset Defaults
                if self._ctrl_section == 0:
                    self._kb_p1 = dict(DEFAULT_KB_P1)
                elif self._ctrl_section == 1:
                    self._kb_p2 = dict(DEFAULT_KB_P2)
                else:
                    self._gp_binds = dict(DEFAULT_GP)
                snd.play('menu_confirm')
            elif sel == len(_BIND_ACTIONS) + 1:
                # Save & Back
                self._save_user_settings()
                snd.play('menu_confirm')
                self.state = self._controls_return_to

    def _draw_controls(self):
        import config
        sw, sh = config.SCREEN_W, config.SCREEN_H

        rl.BeginDrawing()
        rl.ClearBackground(colors.BLACK)

        for a in self._menu_asteroids:
            a.draw()
        rl.DrawRectangle(0, 0, sw, sh, color(0, 0, 0, 160))

        title = T("CONTROLS").encode()
        tw = measure_text(title, 44)
        draw_text(title, sw // 2 - tw // 2, 30, 44, colors.RAYWHITE)

        # Section tabs
        tab_y = 80
        tab_w = 200
        total_w = tab_w * 3 + 20
        tab_x0 = sw // 2 - total_w // 2
        for i, label in enumerate(self._CTRL_SECTIONS):
            tx = tab_x0 + i * (tab_w + 10)
            is_active = (i == self._ctrl_section)
            if is_active:
                rl.DrawRectangle(tx, tab_y, tab_w, 30, color(255, 255, 100, 40))
                rl.DrawRectangleLines(tx, tab_y, tab_w, 30, color(255, 255, 100))
                col_t = color(255, 255, 100)
            else:
                rl.DrawRectangleLines(tx, tab_y, tab_w, 30, color(100, 100, 100))
                col_t = color(150, 150, 150)
            lbl = T(label).encode()
            lw = measure_text(lbl, 18)
            draw_text(lbl, tx + tab_w // 2 - lw // 2, tab_y + 6, 18, col_t)

        # Tab switch hint
        hint_tab = T("TAB to switch section").encode()
        htw = measure_text(hint_tab, 12)
        draw_text(hint_tab, sw // 2 - htw // 2, tab_y + 35, 12, color(100, 100, 120))

        # Separator
        sep_y = 130
        rl.DrawLineV(vec2(sw // 2 - 280, sep_y), vec2(sw // 2 + 280, sep_y),
                     color(255, 255, 255, 40))

        # Header
        hdr_y = 140
        label_x = sw // 2 - 250
        key_x = sw // 2 + 40
        draw_text(T("ACTION").encode(), label_x, hdr_y, 16, color(120, 120, 160))
        draw_text(T("BINDING").encode(), key_x, hdr_y, 16, color(120, 120, 160))

        # Binding rows
        binds = self._get_ctrl_binds()
        oy = 165
        row_h = 32
        num_rows = self._ctrl_num_rows()

        for i, (action_id, action_label) in enumerate(_BIND_ACTIONS):
            y = oy + i * row_h
            is_sel = (i == self._ctrl_sel)
            is_listening = self._ctrl_listening and self._ctrl_listen_action == action_id

            if is_listening:
                # Blinking "Press a key..." prompt
                blink = int(self.menu_time * 4) % 2 == 0
                col_l = color(255, 100, 100) if blink else color(180, 50, 50)
                col_v = col_l
                val_text = T(">> Press a key... <<") if self._ctrl_section <= 1 else T(">> Press a button... <<")
            elif is_sel:
                col_l = color(255, 255, 100)
                col_v = color(255, 255, 200)
                draw_text(b">", label_x - 18, y, 20, col_l)
                val_text = self._ctrl_key_name(binds.get(action_id, 0))
            else:
                col_l = color(200, 200, 200)
                col_v = color(150, 150, 150)
                val_text = self._ctrl_key_name(binds.get(action_id, 0))

            draw_text(T(action_label).encode(), label_x, y, 20, col_l)
            draw_text(val_text.encode(), key_x, y, 20, col_v)

        # Reset Defaults row
        reset_idx = len(_BIND_ACTIONS)
        reset_y = oy + reset_idx * row_h + 10
        is_sel_reset = (self._ctrl_sel == reset_idx)
        reset_text = T("Reset Defaults").encode()
        rtw = measure_text(reset_text, 22)
        rx = sw // 2 - rtw // 2
        if is_sel_reset:
            rl.DrawRectangleLines(rx - 12, reset_y - 4, rtw + 24, 30, color(255, 100, 100))
            draw_text(reset_text, rx, reset_y, 22, color(255, 100, 100))
        else:
            draw_text(reset_text, rx, reset_y, 22, color(180, 120, 120))

        # Save & Back row
        save_idx = len(_BIND_ACTIONS) + 1
        save_y = oy + save_idx * row_h + 20
        is_sel_save = (self._ctrl_sel == save_idx)
        save_text = T("Save & Back").encode()
        stw = measure_text(save_text, 26)
        sx = sw // 2 - stw // 2
        if is_sel_save:
            rl.DrawRectangleLines(sx - 16, save_y - 6, stw + 32, 38, color(255, 255, 100))
            draw_text(save_text, sx, save_y, 26, color(255, 255, 100))
        else:
            draw_text(save_text, sx, save_y, 26, color(180, 180, 180))

        # Footer
        footer_y = save_y + 55
        rl.DrawLineV(vec2(sw // 2 - 280, footer_y), vec2(sw // 2 + 280, footer_y),
                     color(255, 255, 255, 40))
        footer_y += 10
        tips = [
            T("Click an action or press ENTER to rebind. ESC to cancel."),
            T("ESC to go back without saving."),
        ]
        for tip in tips:
            draw_text(tip.encode(), sw // 2 - 240, footer_y, 14, color(120, 120, 140))
            footer_y += 20

        self._draw_fps_counter()
        rl.EndDrawing()

    # ====================================================================
    #  NAME ENTRY (after game over, if qualifies for leaderboard)
    # ====================================================================

    def _update_name_entry(self, dt):
        self._name_cursor_blink += dt

        # Read keyboard chars via raylib GetCharPressed
        while True:
            ch = rl.GetCharPressed()
            if ch == 0:
                break
            # Printable ASCII + extended
            if 32 <= ch <= 126 and len(self._name_input) < NAME_MAX_LEN:
                self._name_input += chr(ch)

        # Backspace (initial press + repeat)
        if rl.IsKeyPressed(259) or rl.IsKeyPressedRepeat(259):
            self._name_input = self._name_input[:-1]

        # Enter: submit
        if rl.IsKeyPressed(KEY_ENTER) and len(self._name_input.strip()) > 0:
            self._submit_score()
        # ESC: skip (submit as "???")
        if rl.IsKeyPressed(KEY_ESC):
            if len(self._name_input.strip()) == 0:
                self._name_input = "???"
            self._submit_score()

    def _submit_score(self):
        name = self._name_input.strip() or "???"
        entry = {
            "name": name,
            "score": self.score,
            "wave": self.level,
            "date": _time.strftime("%Y-%m-%d %H:%M"),
            "seed": self.game_seed or "",
            "mode": "CO-OP" if self._mp_mode == "coop" else ("MP" if self._mp_mode else "SP"),
        }
        self._leaderboard.append(entry)
        self._leaderboard = sorted(self._leaderboard, key=lambda e: e["score"], reverse=True)[:LEADERBOARD_MAX]
        save_leaderboard(self._leaderboard)
        # Find rank of new entry
        self._new_entry_rank = -1
        for i, e in enumerate(self._leaderboard):
            if e is entry:
                self._new_entry_rank = i
                break
        self.state = "high_scores"

    def _draw_name_entry(self):
        rl.DrawRectangle(0, 0, SCREEN_W, SCREEN_H, color(0, 0, 0, 200))

        # Title
        go = T("GAME OVER").encode()
        tw = measure_text(go, 50)
        draw_text(go, SCREEN_W // 2 - tw // 2, SCREEN_H // 2 - 180, 50, colors.RAYWHITE)

        # Score
        score_t = T("Score: {score}   Wave: {wave}").format(score=self.score, wave=self.level).encode()
        tw2 = measure_text(score_t, 24)
        draw_text(score_t, SCREEN_W // 2 - tw2 // 2, SCREEN_H // 2 - 120, 24, color(255, 255, 100))

        # NEW HIGH SCORE
        hs = T("NEW HIGH SCORE!").encode()
        tw3 = measure_text(hs, 28)
        pulse = int(200 + 55 * math.sin(self._name_cursor_blink * 4))
        draw_text(hs, SCREEN_W // 2 - tw3 // 2, SCREEN_H // 2 - 80, 28, color(255, 200, 0, pulse))

        # Prompt
        prompt = T("Enter your name:").encode()
        tw4 = measure_text(prompt, 22)
        draw_text(prompt, SCREEN_W // 2 - tw4 // 2, SCREEN_H // 2 - 30, 22, color(200, 200, 200))

        # Input field
        field_w = 400
        field_h = 44
        fx = SCREEN_W // 2 - field_w // 2
        fy = SCREEN_H // 2 + 10
        rl.DrawRectangle(fx, fy, field_w, field_h, color(20, 20, 30))
        rl.DrawRectangleLines(fx, fy, field_w, field_h, color(100, 100, 200))

        # Text
        display = self._name_input
        # Cursor blink
        if int(self._name_cursor_blink * 2) % 2 == 0:
            display += "_"
        text = display.encode()
        draw_text(text, fx + 12, fy + 10, 24, color(255, 255, 255))

        # Hints
        hint1 = T("ENTER to confirm  |  ESC to skip").encode()
        hw = measure_text(hint1, 16)
        draw_text(hint1, SCREEN_W // 2 - hw // 2, fy + 60, 16, color(120, 120, 120))

        chars_left = f"{len(self._name_input)}/{NAME_MAX_LEN}".encode()
        draw_text(chars_left, fx + field_w - 60, fy + field_h + 8, 14, color(80, 80, 80))

    # ====================================================================
    #  HIGH SCORES SCREEN
    # ====================================================================

    def _draw_high_scores(self):
        rl.BeginDrawing()
        rl.ClearBackground(colors.BLACK)

        # Background
        for a in self._menu_asteroids:
            a.draw()
        rl.DrawRectangle(0, 0, SCREEN_W, SCREEN_H, color(0, 0, 0, 180))

        title = T("HIGH SCORES").encode()
        tw = measure_text(title, 44)
        draw_text(title, SCREEN_W // 2 - tw // 2, 50, 44, color(255, 255, 100))

        # Separator
        rl.DrawLineV(vec2(SCREEN_W // 2 - 300, 110), vec2(SCREEN_W // 2 + 300, 110),
                     color(255, 255, 100, 40))

        # Column headers
        cy = 130
        hx_rank = SCREEN_W // 2 - 300
        hx_name = SCREEN_W // 2 - 240
        hx_score = SCREEN_W // 2 + 20
        hx_wave = SCREEN_W // 2 + 140
        hx_mode = SCREEN_W // 2 + 195
        hx_date = SCREEN_W // 2 + 240

        draw_text(b"#", hx_rank, cy, 18, color(150, 150, 150))
        draw_text(T("NAME").encode(), hx_name, cy, 18, color(150, 150, 150))
        draw_text(T("SCORE").encode(), hx_score, cy, 18, color(150, 150, 150))
        draw_text(T("WAVE").encode(), hx_wave, cy, 18, color(150, 150, 150))
        draw_text(T("MODE").encode(), hx_mode, cy, 18, color(150, 150, 150))
        draw_text(T("DATE").encode(), hx_date, cy, 18, color(150, 150, 150))
        cy += 30

        rl.DrawLineV(vec2(SCREEN_W // 2 - 280, cy), vec2(SCREEN_W // 2 + 340, cy),
                     color(255, 255, 255, 20))
        cy += 10

        if not self._leaderboard:
            empty = T("No scores yet. Play a game!").encode()
            ew = measure_text(empty, 20)
            draw_text(empty, SCREEN_W // 2 - ew // 2, cy + 40, 20, color(120, 120, 120))
        else:
            for i, entry in enumerate(self._leaderboard):
                is_new = (i == self._new_entry_rank)

                # Rank colors
                if i == 0:
                    rank_col = color(255, 215, 0)      # gold
                elif i == 1:
                    rank_col = color(192, 192, 200)     # silver
                elif i == 2:
                    rank_col = color(205, 127, 50)      # bronze
                else:
                    rank_col = color(160, 160, 160)

                if is_new:
                    # Highlight new entry
                    blink = int(self.menu_time * 3) % 2
                    if blink:
                        rank_col = color(255, 255, 100)
                    rl.DrawRectangle(hx_rank - 5, cy - 3, 630, 28, color(255, 255, 100, 20))

                draw_text(f"{i + 1}.".encode(), hx_rank, cy, 20, rank_col)
                draw_text(entry.get("name", "???").encode(), hx_name, cy, 20, rank_col)
                draw_text(f"{entry['score']:,}".encode(), hx_score, cy, 20, rank_col)
                draw_text(f"{entry.get('wave', '?')}".encode(), hx_wave, cy, 20, rank_col)
                mode = entry.get("mode", "SP")
                mode_col = color(100, 200, 255) if mode == "MP" else color(150, 150, 150)
                draw_text(mode.encode(), hx_mode, cy, 18, mode_col)
                draw_text(entry.get("date", "").encode(), hx_date, cy, 16, color(100, 100, 100))
                cy += 34

        # Footer
        cy = max(cy + 30, SCREEN_H - 80)
        back = T("Press ESC or ENTER to go back").encode()
        bw = measure_text(back, 20)
        draw_text(back, SCREEN_W // 2 - bw // 2, cy, 20, color(180, 180, 180))

        self._draw_fps_counter()
        rl.EndDrawing()

    # ====================================================================
    #  SEED ENTRY SCREEN
    # ====================================================================

    def _update_seed_entry(self, dt):
        self._seed_cursor_blink += dt
        snd.update_music(0.1, 1, False)

        # Read characters
        while True:
            ch = rl.GetCharPressed()
            if ch == 0:
                break
            if 32 <= ch <= 126 and len(self._seed_input) < 20:
                self._seed_input += chr(ch)

        # Backspace
        if rl.IsKeyPressed(259) or rl.IsKeyPressedRepeat(259):
            self._seed_input = self._seed_input[:-1]

        # R = generate random seed
        if rl.IsKeyPressed(82) and len(self._seed_input) == 0:  # 'R'
            self._seed_input = hashlib.md5(
                str(_time.time()).encode()).hexdigest()[:8].upper()

        # Enter = start with seed
        if rl.IsKeyPressed(KEY_ENTER) and len(self._seed_input.strip()) > 0:
            self.game_seed = self._seed_input.strip()
            snd.play('menu_confirm')
            self._init_game_state()
            self.ship.ship_color = SHIP_COLORS[self._mp_ship_color_idx][1]
            self.ship.set_skin(self._ship_skin_idx)
            self.state = "playing"

        # ESC = back
        if rl.IsKeyPressed(KEY_ESC):
            self.state = "main_menu"
            self.menu_sel = 0

    def _draw_seed_entry(self):
        rl.BeginDrawing()
        rl.ClearBackground(colors.BLACK)

        # Background asteroids
        for a in self._menu_asteroids:
            a.draw()
        rl.DrawRectangle(0, 0, SCREEN_W, SCREEN_H, color(0, 0, 0, 160))

        # Title
        title = T("SEEDED RUN").encode()
        tw = measure_text(title, 48)
        draw_text(title, SCREEN_W // 2 - tw // 2, SCREEN_H // 2 - 160, 48,
                    color(255, 200, 100))

        # Description
        desc = T("Enter a seed for a deterministic run.").encode()
        dw = measure_text(desc, 18)
        draw_text(desc, SCREEN_W // 2 - dw // 2, SCREEN_H // 2 - 100, 18,
                    color(180, 180, 180))
        desc2 = T("Same seed = same asteroid spawns, events, and layout.").encode()
        dw2 = measure_text(desc2, 16)
        draw_text(desc2, SCREEN_W // 2 - dw2 // 2, SCREEN_H // 2 - 75, 16,
                    color(140, 140, 140))

        # Input field
        field_w = 400
        field_h = 44
        fx = SCREEN_W // 2 - field_w // 2
        fy = SCREEN_H // 2 - 20
        rl.DrawRectangle(fx, fy, field_w, field_h, color(20, 20, 30))
        rl.DrawRectangleLines(fx, fy, field_w, field_h, color(255, 200, 100))

        display = self._seed_input
        if int(self._seed_cursor_blink * 2) % 2 == 0:
            display += "_"
        draw_text(display.encode(), fx + 12, fy + 10, 24, color(255, 255, 255))

        # Hints
        hint1 = T("ENTER to start  |  R for random seed  |  ESC to go back").encode()
        hw = measure_text(hint1, 16)
        draw_text(hint1, SCREEN_W // 2 - hw // 2, fy + 60, 16, color(120, 120, 120))

        chars_left = f"{len(self._seed_input)}/20".encode()
        draw_text(chars_left, fx + field_w - 55, fy + field_h + 8, 14, color(80, 80, 80))

        self._draw_fps_counter()
        rl.EndDrawing()

    # ====================================================================
    #  OPTIONS SCREEN
    # ====================================================================

    # Option rows: name, type
    # Types: "choice_lr" (left/right to change), "toggle", "action"
    def _draw_fps_counter(self):
        if self._show_fps:
            import config
            fps_text = f"FPS: {rl.GetFPS()}".encode()
            draw_text(fps_text, config.SCREEN_W - 100, 10, 18, color(0, 255, 0))

    OPTIONS_ROWS = [
        ("Resolution",          "choice_lr"),
        ("Fullscreen",          "toggle"),
        ("Borderless Windowed", "toggle"),
        ("VSync",               "toggle"),
        ("FPS Limit",           "choice_lr"),
        ("Show FPS",            "toggle"),
        ("--- Visual FX ---",   "separator"),
        ("Border Particles",    "toggle"),
        ("Speed Smear",         "toggle"),
        ("Asteroid Speed Color","toggle"),
        ("Bloom Effect",        "toggle"),
        ("--- Audio ---",       "separator"),
        ("Sound Effects",       "toggle"),
        ("Music",               "toggle"),
        ("--- Language ---",    "separator"),
        ("Language",            "choice_lr"),
        ("Apply & Back",        "action"),
    ]

    def _update_options(self, dt):
        self.menu_time += dt
        # Animate background asteroids
        import config
        sw, sh = config.SCREEN_W, config.SCREEN_H
        for a in self._menu_asteroids:
            a.x += a.vx * dt
            a.y += a.vy * dt
            a.angle += a.rot_speed * dt
            a.x %= sw
            a.y %= sh

        rows = self.OPTIONS_ROWS
        num = len(rows)

        if rl.IsKeyPressed(KEY_ESC):
            self.state = self._options_return_to
            return

        if rl.IsKeyPressed(KEY_UP):
            self._opt_sel = (self._opt_sel - 1) % num
            while rows[self._opt_sel][1] == "separator":
                self._opt_sel = (self._opt_sel - 1) % num
        if rl.IsKeyPressed(KEY_DOWN):
            self._opt_sel = (self._opt_sel + 1) % num
            while rows[self._opt_sel][1] == "separator":
                self._opt_sel = (self._opt_sel + 1) % num

        # Mouse hover
        my = rl.GetMouseY()
        oy = 150
        row_h = 38
        for i in range(num):
            if rows[i][1] == "separator":
                continue
            y = oy + i * row_h
            if y <= my <= y + 30:
                self._opt_sel = i

        row_name, row_type = rows[self._opt_sel]

        # Left/Right for choice_lr rows
        left = rl.IsKeyPressed(KEY_LEFT)
        right = rl.IsKeyPressed(KEY_RIGHT)

        if row_name == "Resolution":
            if left:
                self._res_idx = (self._res_idx - 1) % len(RESOLUTIONS)
            if right:
                self._res_idx = (self._res_idx + 1) % len(RESOLUTIONS)
        elif row_name == "FPS Limit":
            if left:
                self._fps_idx = (self._fps_idx - 1) % len(FPS_OPTIONS)
            if right:
                self._fps_idx = (self._fps_idx + 1) % len(FPS_OPTIONS)
        elif row_name == "Language":
            cur = LANGUAGES.index(get_language())
            if left:
                cur = (cur - 1) % len(LANGUAGES)
                set_language(LANGUAGES[cur])
            if right:
                cur = (cur + 1) % len(LANGUAGES)
                set_language(LANGUAGES[cur])

        # Enter / Space / Mouse click for toggle and action
        confirm = rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE)
        if rl.IsMouseButtonPressed(0):
            for i in range(num):
                y = oy + i * row_h
                if y <= my <= y + 30:
                    confirm = True
                    self._opt_sel = i
                    row_name, row_type = rows[i]

        if confirm:
            if row_name == "Fullscreen":
                self._fullscreen = not self._fullscreen
            elif row_name == "Borderless Windowed":
                self._borderless = not self._borderless
            elif row_name == "VSync":
                self._vsync = not self._vsync
            elif row_name == "Show FPS":
                self._show_fps = not self._show_fps
            elif row_name == "Border Particles":
                self._fx_border_particles = not self._fx_border_particles
            elif row_name == "Speed Smear":
                self._fx_speed_smear = not self._fx_speed_smear
            elif row_name == "Asteroid Speed Color":
                self._fx_asteroid_speed_color = not self._fx_asteroid_speed_color
            elif row_name == "Bloom Effect":
                self._fx_bloom = not self._fx_bloom
            elif row_name == "Sound Effects":
                snd.sfx_enabled = not snd.sfx_enabled
            elif row_name == "Music":
                snd.music_enabled = not snd.music_enabled
            elif row_name == "Resolution":
                self._res_idx = (self._res_idx + 1) % len(RESOLUTIONS)
            elif row_name == "FPS Limit":
                self._fps_idx = (self._fps_idx + 1) % len(FPS_OPTIONS)
            elif row_name == "Language":
                cur = LANGUAGES.index(get_language())
                cur = (cur + 1) % len(LANGUAGES)
                set_language(LANGUAGES[cur])
            elif row_name == "Apply & Back":
                self._apply_all_options()
                self.state = self._options_return_to

        # Also allow left/right on toggle to change
        if row_type == "toggle" and (left or right):
            if row_name == "Fullscreen":
                self._fullscreen = not self._fullscreen
            elif row_name == "Borderless Windowed":
                self._borderless = not self._borderless
            elif row_name == "VSync":
                self._vsync = not self._vsync
            elif row_name == "Show FPS":
                self._show_fps = not self._show_fps
            elif row_name == "Border Particles":
                self._fx_border_particles = not self._fx_border_particles
            elif row_name == "Speed Smear":
                self._fx_speed_smear = not self._fx_speed_smear
            elif row_name == "Asteroid Speed Color":
                self._fx_asteroid_speed_color = not self._fx_asteroid_speed_color
            elif row_name == "Bloom Effect":
                self._fx_bloom = not self._fx_bloom
            elif row_name == "Sound Effects":
                snd.sfx_enabled = not snd.sfx_enabled
            elif row_name == "Music":
                snd.music_enabled = not snd.music_enabled

    def _apply_all_options(self):
        """Zastosuj wszystkie ustawienia graficzne."""
        global SCREEN_W, SCREEN_H
        import config
        rw, rh = RESOLUTIONS[self._res_idx]

        # Fullscreen / borderless handling
        is_fs = rl.IsWindowFullscreen()
        is_bl = bool(rl.IsWindowState(32768))  # FLAG_BORDERLESS_WINDOWED_MODE

        if self._fullscreen and not self._borderless:
            # Exclusive fullscreen
            if is_bl:
                rl.ToggleBorderlessWindowed()
            self._apply_resolution(rw, rh)
            if not is_fs:
                rl.ToggleFullscreen()
        elif self._borderless and not self._fullscreen:
            # Borderless windowed
            if is_fs:
                rl.ToggleFullscreen()
            self._apply_resolution(rw, rh)
            if not is_bl:
                rl.ToggleBorderlessWindowed()
        else:
            # Windowed
            if is_fs:
                rl.ToggleFullscreen()
            if is_bl:
                rl.ToggleBorderlessWindowed()
            self._apply_resolution(rw, rh)

        # VSync
        if self._vsync:
            rl.SetWindowState(64)  # FLAG_VSYNC_HINT
        else:
            rl.ClearWindowState(64)

        # Update module-level globals for main.py
        SCREEN_W = config.SCREEN_W
        SCREEN_H = config.SCREEN_H

        # Visual effects
        import asteroid as asteroid_mod
        asteroid_mod.SPEED_COLOR_ENABLED = self._fx_asteroid_speed_color

        # FPS
        fps = FPS_OPTIONS[self._fps_idx]
        if fps == 0:
            rl.SetTargetFPS(0)  # unlimited
        else:
            rl.SetTargetFPS(fps)

        # Persist settings to disk
        self._save_user_settings()

    def _get_option_value_str(self, row_name):
        if row_name == "Resolution":
            w, h = RESOLUTIONS[self._res_idx]
            return f"< {w} x {h} >"
        elif row_name == "Fullscreen":
            return T("ON") if self._fullscreen else T("OFF")
        elif row_name == "Borderless Windowed":
            return T("ON") if self._borderless else T("OFF")
        elif row_name == "VSync":
            return T("ON") if self._vsync else T("OFF")
        elif row_name == "FPS Limit":
            return f"< {FPS_LABELS[self._fps_idx]} >"
        elif row_name == "Show FPS":
            return T("ON") if self._show_fps else T("OFF")
        elif row_name == "Border Particles":
            return T("ON") if self._fx_border_particles else T("OFF")
        elif row_name == "Speed Smear":
            return T("ON") if self._fx_speed_smear else T("OFF")
        elif row_name == "Asteroid Speed Color":
            return T("ON") if self._fx_asteroid_speed_color else T("OFF")
        elif row_name == "Bloom Effect":
            return T("ON") if self._fx_bloom else T("OFF")
        elif row_name == "Sound Effects":
            return T("ON") if snd.sfx_enabled else T("OFF")
        elif row_name == "Music":
            return T("ON") if snd.music_enabled else T("OFF")
        elif row_name == "Language":
            return f"< {LANGUAGE_NAMES[get_language()]} >"
        elif row_name == "Apply & Back":
            return ""
        return ""

    def _draw_options(self):
        import config
        sw, sh = config.SCREEN_W, config.SCREEN_H

        rl.BeginDrawing()
        rl.ClearBackground(colors.BLACK)

        # Background asteroids
        for a in self._menu_asteroids:
            a.draw()
        rl.DrawRectangle(0, 0, sw, sh, color(0, 0, 0, 160))

        title = T("OPTIONS").encode()
        tw = measure_text(title, 44)
        draw_text(title, sw // 2 - tw // 2, 60, 44, colors.RAYWHITE)

        # Separator
        rl.DrawLineV(vec2(sw // 2 - 250, 120), vec2(sw // 2 + 250, 120),
                     color(255, 255, 255, 40))

        rows = self.OPTIONS_ROWS
        oy = 150
        row_h = 38
        label_x = sw // 2 - 240
        value_x = sw // 2 + 60

        for i, (name, rtype) in enumerate(rows):
            y = oy + i * row_h
            is_sel = (i == self._opt_sel)

            if rtype == "separator":
                rl.DrawLineV(vec2(label_x, y + 12), vec2(value_x + 120, y + 12),
                             color(255, 255, 255, 30))
                label = T(name.replace("---", "").strip()).encode()
                draw_text(label, label_x, y + 2, 14, color(120, 120, 160))
                continue

            if name == "Apply & Back":
                text = T("Apply & Back").encode()
                tw = measure_text(text, 26)
                bx = sw // 2 - tw // 2
                if is_sel:
                    rl.DrawRectangleLines(bx - 16, y - 6, tw + 32, 38, color(255, 255, 100))
                    draw_text(text, bx, y, 26, color(255, 255, 100))
                else:
                    draw_text(text, bx, y, 26, color(180, 180, 180))
                continue

            label = T(name).encode()
            val = self._get_option_value_str(name).encode()

            if is_sel:
                col_l = color(255, 255, 100)
                col_v = color(255, 255, 200)
                draw_text(b">", label_x - 20, y, 22, col_l)
            else:
                col_l = color(200, 200, 200)
                col_v = color(150, 150, 150)

            draw_text(label, label_x, y, 22, col_l)
            draw_text(val, value_x, y, 22, col_v)

            if is_sel and rtype == "choice_lr":
                hint = T("LEFT/RIGHT to change").encode()
                draw_text(hint, value_x, y + 24, 12, color(120, 120, 120))
            elif is_sel and rtype == "toggle":
                hint = T("ENTER to toggle").encode()
                draw_text(hint, value_x, y + 24, 12, color(120, 120, 120))

        # Footer info
        fy = oy + len(rows) * row_h + 20
        rl.DrawLineV(vec2(sw // 2 - 250, fy), vec2(sw // 2 + 250, fy),
                     color(255, 255, 255, 40))
        fy += 15
        info_lines = [
            T("Changes are applied when you select 'Apply & Back'."),
            T("Fullscreen and Borderless are mutually exclusive."),
            T("VSync syncs to your monitor refresh rate."),
            T("FPS Limit of 0 (Unlimited) removes the frame cap."),
        ]
        for line in info_lines:
            draw_text(line.encode(), sw // 2 - 240, fy, 14, color(120, 120, 140))
            fy += 22

        # Current display info
        fy += 15
        cur_fps = rl.GetFPS()
        mon = rl.GetCurrentMonitor()
        mon_w = rl.GetMonitorWidth(mon)
        mon_h = rl.GetMonitorHeight(mon)
        mon_hz = rl.GetMonitorRefreshRate(mon)
        info = f"Monitor: {mon_w}x{mon_h} @ {mon_hz}Hz  |  Current FPS: {cur_fps}".encode()
        iw = measure_text(info, 14)
        draw_text(info, sw // 2 - iw // 2, fy, 14, color(80, 160, 80))

        # ESC hint
        esc = T("ESC to go back without applying").encode()
        ew = measure_text(esc, 14)
        draw_text(esc, sw // 2 - ew // 2, sh - 40, 14, color(100, 100, 100))

        self._draw_fps_counter()
        rl.EndDrawing()


# ---- MAIN ----
rl.InitWindow(SCREEN_W, SCREEN_H, b"Asteroids on Steroids")
rl.SetExitKey(0)  # Wylacz domyslne zamykanie przez ESC
rl.SetTargetFPS(60)

# Load Unicode font for localization
_load_game_font()

# Initialize audio system
snd = SoundSystem()

game = Game()
# Apply deferred saved settings (audio needs snd, graphics need window)
if hasattr(game, '_saved_sfx'):
    snd.sfx_enabled = game._saved_sfx
if hasattr(game, '_saved_music'):
    snd.music_enabled = game._saved_music
game._apply_all_options()  # apply saved resolution/fullscreen/vsync/fps

while not rl.WindowShouldClose():
    dt = rl.GetFrameTime()
    game.update(dt)
    game.draw()

game._mp_cleanup()
snd.cleanup()
if _game_font:
    rl.UnloadFont(_game_font)
rl.CloseWindow()
