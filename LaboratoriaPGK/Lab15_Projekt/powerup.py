import math
import random
from raylib import rl
from config import POWERUP_RADIUS, POWERUP_LIFETIME
from utils import vec2, color, wrap, ghost_positions
from wave import MODULES

# Instant effects + module drops
POWERUP_TYPES = {
    "shield":     {"color": (0, 255, 100),   "label": "S", "desc": "SHIELD"},
    "nuke":       {"color": (255, 50, 50),   "label": "N", "desc": "NUKE"},
    "speedboost": {"color": (255, 255, 0),   "label": "B", "desc": "SPEED BOOST"},
    "module":     {"color": (255, 255, 255), "label": "?", "desc": "MODULE"},
}

# Modul-only drops
MODULE_DROP_CHANCE = 0.35  # szansa na module zamiast instant


class PowerUp:
    def __init__(self, x, y, kind=None, module_id=None):
        self.x = x
        self.y = y
        if kind is None:
            if random.random() < MODULE_DROP_CHANCE:
                kind = "module"
            else:
                kind = random.choice(["shield", "nuke", "speedboost"])
        self.kind = kind
        self.module_id = module_id
        if kind == "module" and module_id is None:
            self.module_id = random.choice(list(MODULES.keys()))
        self.radius = POWERUP_RADIUS
        self.lifetime = POWERUP_LIFETIME
        self.alive = True
        self.time = 0.0
        self.vx = 0.0
        self.vy = 0.0

    def update(self, dt):
        self.time += dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.95
        self.vy *= 0.95
        self.x, self.y = wrap(self.x, self.y)

    def draw(self):
        if self.kind == "module" and self.module_id and self.module_id in MODULES:
            info = MODULES[self.module_id]
            r, g, b = info["color"]
            label = info["name"][0].encode()
        elif self.kind in POWERUP_TYPES:
            info = POWERUP_TYPES[self.kind]
            r, g, b = info["color"]
            label = info["label"].encode()
        else:
            return

        pulse = 0.7 + 0.3 * math.sin(self.time * 5.0)
        alpha = int(255 * pulse)
        if self.lifetime < 2.0:
            if int(self.time * 8) % 2 == 0:
                return

        for gx, gy in ghost_positions(self.x, self.y, self.radius):
            rl.DrawCircleLines(int(gx), int(gy), self.radius, color(r, g, b, alpha))
            if self.kind == "module":
                # Kwadratowy ksztalt dla modulow
                hs = self.radius * 0.7
                rl.DrawRectangleLines(int(gx - hs), int(gy - hs),
                                      int(hs * 2), int(hs * 2), color(r, g, b, alpha // 2))
            else:
                rl.DrawCircleLines(int(gx), int(gy), self.radius * 0.6, color(r, g, b, alpha // 2))
            tw = rl.MeasureText(label, 14)
            rl.DrawText(label, int(gx - tw // 2), int(gy - 7), 14, color(r, g, b, alpha))


def maybe_spawn_powerup(x, y, chance):
    if random.random() < chance:
        return PowerUp(x, y)
    return None
