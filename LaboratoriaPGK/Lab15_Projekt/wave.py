import math
import random
from config import (WAVE_BASE_ASTEROIDS, WAVE_ASTEROID_INCREMENT,
                    SWARM_COUNT, PERK_CHOICES, BOSS_WAVE_INTERVAL,
                    TOPOLOGY_CHANGE_WAVES, TORUS, CYLINDER, MOBIUS, KLEIN, SPHERE,
                    SCREEN_W, SCREEN_H)


# ---- MODULY BRONI ----
MODULES = {
    "rapid":   {"name": "RAPID",   "color": (255, 100, 0),   "desc": "Szybszy ogien"},
    "pierce":  {"name": "PIERCE",  "color": (0, 200, 255),   "desc": "Pociski przebijaja cel"},
    "split":   {"name": "SPLIT",   "color": (255, 200, 0),   "desc": "Potrojny strzal"},
    "homing":  {"name": "HOMING",  "color": (200, 255, 0),   "desc": "Lekkie naprowadzanie"},
    "gravity": {"name": "GRAVITY", "color": (200, 50, 255),  "desc": "Bomba graw. [X]"},
    "bounce":  {"name": "BOUNCE",  "color": (0, 255, 200),   "desc": "Pociski sie odbijaja"},
    "hyper":   {"name": "HYPER",   "color": (100, 150, 255), "desc": "Strzal przez torus [C]"},
}


# ---- PERKI ----
PERKS = {
    "pierce": {
        "name": "PIERCING SHOTS",
        "desc": "Pociski przebijaja 1 asteroide",
        "color": (0, 200, 255),
    },
    "bouncing_perk": {
        "name": "RICOCHET",
        "desc": "Pociski odbijaja sie od krawedzi",
        "color": (0, 255, 200),
    },
    "homing_perk": {
        "name": "HOMING",
        "desc": "Pociski lekko naprowadzaja",
        "color": (255, 200, 0),
    },
    "double_score": {
        "name": "DOUBLE SCORE",
        "desc": "Podwojne punkty",
        "color": (255, 255, 0),
    },
    "magnet_pickup": {
        "name": "MAGNET",
        "desc": "Przyciaga power-upy",
        "color": (200, 0, 255),
    },
    "slow_asteroids": {
        "name": "SLOW FIELD",
        "desc": "Asteroidy o 30% wolniejsze",
        "color": (100, 150, 255),
    },
    "extra_life": {
        "name": "EXTRA LIFE",
        "desc": "+1 zycie",
        "color": (0, 255, 0),
    },
    "bigger_explosions": {
        "name": "BIG BOOM",
        "desc": "Wieksze eksplozje",
        "color": (255, 100, 0),
    },
    "thrust_shield": {
        "name": "THRUST SHIELD",
        "desc": "Ciag daje tarcze",
        "color": (0, 255, 150),
    },
    "gravity_shot": {
        "name": "GRAVITY BOMB",
        "desc": "Alt-fire: bomba graw. [X]",
        "color": (200, 50, 255),
    },
    "hyperspace_shot": {
        "name": "HYPERSPACE SHOT",
        "desc": "Alt-fire: strzal przez torus [C]",
        "color": (100, 150, 255),
    },
    "bullet_inherit_vel": {
        "name": "VELOCITY BULLETS",
        "desc": "Pociski dziedzicza 30% predkosci",
        "color": (255, 180, 100),
    },
    "nuke_every_10": {
        "name": "NUKE CADENCE",
        "desc": "Co 10ty strzal to nuke",
        "color": (255, 50, 50),
    },
    # Mutacje statku
    "mut_strafe": {
        "name": "STRAFE ENGINE",
        "desc": "A/D = ruch boczny",
        "color": (150, 200, 255),
        "mutation": "strafe",
    },
    "mut_backfire": {
        "name": "BACKFIRE",
        "desc": "Strzal tez do tylu",
        "color": (255, 150, 150),
        "mutation": "backfire",
    },
    "mut_evolved": {
        "name": "EVOLVED HULL",
        "desc": "Ulepszone nadwozie + tarcza",
        "color": (200, 255, 200),
        "mutation": "evolved",
    },
    "mut_afterburner": {
        "name": "AFTERBURNER",
        "desc": "Ciag niszczy male asteroidy",
        "color": (255, 200, 0),
        "mutation": "afterburner",
    },
}


# ---- EVENTY ----
WAVE_EVENTS = [
    {"name": "REVERSE!", "action": "reverse", "color": (255, 200, 0)},
    {"name": "FREEZE!", "action": "freeze", "color": (100, 200, 255)},
    {"name": "METEOR SHOWER!", "action": "swarm", "color": (255, 100, 50)},
    {"name": "GRAVITY SURGE!", "action": "gravity_surge", "color": (200, 100, 255)},
    {"name": "NO WRAP Y!", "action": "no_wrap_y", "color": (255, 50, 50)},
    {"name": "BLACKOUT!", "action": "blackout", "color": (50, 50, 80)},
    {"name": "FRACTURE!", "action": "fracture", "color": (255, 150, 50)},
    {"name": "GRAVITY PULSE!", "action": "gravity_pulse", "color": (180, 100, 255)},
]

TOPOLOGY_CYCLE = [TORUS, CYLINDER, MOBIUS, KLEIN, SPHERE]


def get_wave_asteroid_count(wave_num):
    return WAVE_BASE_ASTEROIDS + (wave_num - 1) * WAVE_ASTEROID_INCREMENT


def get_wave_specials(wave_num):
    base = ["explosive", "fast", "spiky", "ice"]
    if wave_num >= 3:
        base.extend(["splitter", "magnetic"])
    if wave_num >= 5:
        base.extend(["ghost", "growing"])
    if wave_num >= 7:
        base.extend(["chain", "crystal"])
    if wave_num >= 9:
        base.extend(["parasite", "virus"])
    return base


def is_boss_wave(wave_num):
    return wave_num > 1 and wave_num % BOSS_WAVE_INTERVAL == 0


def get_wave_topology(wave_num):
    """Topologia zalezy od numeru fali."""
    cycle_idx = (wave_num // TOPOLOGY_CHANGE_WAVES) % len(TOPOLOGY_CYCLE)
    return TOPOLOGY_CYCLE[cycle_idx]


def get_perk_choices(owned_perks, wave_num):
    available = [k for k in PERKS if k not in owned_perks or k == "extra_life"]
    # Mutacje dopiero od wave 3
    if wave_num < 3:
        available = [k for k in available if not k.startswith("mut_")]
    # Szalone perki od wave 6
    if wave_num < 6:
        available = [k for k in available if k not in ("bullet_inherit_vel", "nuke_every_10")]
    if not available:
        available = list(PERKS.keys())
    return random.sample(available, min(PERK_CHOICES, len(available)))


def get_wave_event(wave_num):
    events = WAVE_EVENTS[:5]  # Base events
    if wave_num >= 5:
        events = WAVE_EVENTS[:7]  # + blackout, fracture
    if wave_num >= 8:
        events = WAVE_EVENTS      # + gravity pulse
    return random.choice(events)


# ---- PROCEDURALNE SEKTORY ----
SECTOR_WAVES = 5  # fal na sektor (zgrane z boss wave interval)

SECTOR_PREFIXES = [
    "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Theta", "Omega",
    "Nova", "Nebula", "Void", "Crimson", "Azure", "Phantom", "Iron",
    "Storm", "Shadow", "Crystal", "Frost", "Ember", "Pulse", "Drift",
    "Obsidian", "Nexus", "Helix", "Vortex", "Eclipse", "Zenith",
]
SECTOR_SUFFIXES = [
    "Reach", "Expanse", "Frontier", "Corridor", "Cluster", "Rift",
    "Depths", "Fields", "Zone", "Sector", "Abyss", "Passage",
    "Crossing", "Wastes", "Dominion", "Terminus", "Gate", "Edge",
]

SECTOR_MODIFIERS = [
    {"name": "DENSE FIELD",     "key": "dense",         "desc": "+40% asteroidow"},
    {"name": "FAST ROCKS",      "key": "fast_rocks",     "desc": "Asteroidy szybsze o 50%"},
    {"name": "GRAVITY ZONE",    "key": "gravity_zone",   "desc": "Wiecej studni grawitacji"},
    {"name": "PORTAL STORM",    "key": "portal_storm",   "desc": "Podwojne portale"},
    {"name": "HUNTER GROUNDS",  "key": "hunter_grounds", "desc": "Wczesniejsze/czestsze huntery"},
    {"name": "CRYSTAL VEIN",    "key": "crystal_vein",   "desc": "Wiecej krysztalowych asteroidow"},
    {"name": "CALM SPACE",      "key": "calm",           "desc": "Mniej eventow, wolniejsze asteroidy"},
    {"name": "SWARM SECTOR",    "key": "swarm",          "desc": "Czestsze rojowe eventy"},
]


class Sector:
    """Proceduralnie generowany sektor kosmiczny."""
    def __init__(self, sector_num):
        self.number = sector_num
        self.seed = sector_num * 7919 + 42
        rng = random.Random(self.seed)

        # Nazwa proceduralna
        self.name = f"{rng.choice(SECTOR_PREFIXES)} {rng.choice(SECTOR_SUFFIXES)}"

        # Kolory sektora (tlo, akcenty)
        hue = rng.random()
        self.primary = _hue_to_rgb(hue, 0.6, 0.7)
        self.secondary = _hue_to_rgb((hue + 0.3) % 1.0, 0.5, 0.5)
        self.bg_tint = (
            int(self.primary[0] * 0.06),
            int(self.primary[1] * 0.06),
            int(self.primary[2] * 0.06),
        )

        # Gwiazdy w tle (stale dla danego sektora)
        self.stars = []
        for _ in range(80 + sector_num * 5):
            sx = rng.uniform(0, 1)  # znormalizowane 0-1
            sy = rng.uniform(0, 1)
            brightness = rng.randint(40, 200)
            size = rng.choice([1, 1, 1, 2, 2, 3])
            # Kolor gwiazdy: mix z kolorem sektora
            if rng.random() < 0.3:
                sr, sg, sb = self.primary
                star_col = (
                    min(255, brightness + sr // 4),
                    min(255, brightness + sg // 4),
                    min(255, brightness + sb // 4),
                )
            else:
                star_col = (brightness, brightness, brightness)
            self.stars.append((sx, sy, size, star_col))

        # Mgławica (opcjonalna)
        self.nebula_clouds = []
        if rng.random() < 0.6:
            for _ in range(rng.randint(2, 5)):
                nx = rng.uniform(0.1, 0.9)
                ny = rng.uniform(0.1, 0.9)
                nr = rng.uniform(0.08, 0.2)  # znormalizowany promien
                na = rng.randint(6, 18)
                self.nebula_clouds.append((nx, ny, nr, na))

        # Modyfikator gameplay
        if sector_num <= 1:
            self.modifier = None
        else:
            self.modifier = rng.choice(SECTOR_MODIFIERS)

        # Czas trwania animacji przejscia
        self.transition_time = 0.0

    def get_asteroid_count_mult(self):
        if self.modifier and self.modifier["key"] == "dense":
            return 1.4
        if self.modifier and self.modifier["key"] == "calm":
            return 0.8
        return 1.0

    def get_asteroid_speed_mult(self):
        if self.modifier and self.modifier["key"] == "fast_rocks":
            return 1.5
        if self.modifier and self.modifier["key"] == "calm":
            return 0.7
        return 1.0

    def get_gravity_well_timer_mult(self):
        if self.modifier and self.modifier["key"] == "gravity_zone":
            return 0.4
        return 1.0

    def get_portal_count_mult(self):
        if self.modifier and self.modifier["key"] == "portal_storm":
            return 2.0
        return 1.0

    def get_hunter_timer_mult(self):
        if self.modifier and self.modifier["key"] == "hunter_grounds":
            return 0.5
        return 1.0

    def get_crystal_chance_mult(self):
        if self.modifier and self.modifier["key"] == "crystal_vein":
            return 3.0
        return 1.0

    def get_event_timer_mult(self):
        if self.modifier and self.modifier["key"] == "calm":
            return 2.0
        if self.modifier and self.modifier["key"] == "swarm":
            return 0.6
        return 1.0

    def favors_swarm_events(self):
        return self.modifier and self.modifier["key"] == "swarm"


def get_sector_num(wave_num):
    """Zwraca numer sektora dla danej fali (1-based)."""
    return max(1, (wave_num - 1) // SECTOR_WAVES + 1)


def _hue_to_rgb(h, s, v):
    """HSV -> RGB (0-255)."""
    i = int(h * 6)
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    i %= 6
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    return (int(r * 255), int(g * 255), int(b * 255))
