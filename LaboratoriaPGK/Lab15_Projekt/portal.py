import math
import random
from raylib import rl
from config import (SCREEN_W, SCREEN_H, PORTAL_LIFETIME, PORTAL_RADIUS,
                    PORTAL_ACTIVATION_RADIUS, PORTAL_COOLDOWN, PORTAL_MAX_PAIRS)
from utils import vec2, color, dist_wrapped, ghost_positions
from lang import T

# Efekty portali
PORTAL_EFFECTS = [
    "normal",           # zachowana predkosc i kat
    "angle_twist",      # losowy obrot kata
    "reverse_velocity", # odwraca predkosc
    "speed_boost",      # przyspiesza
    "speed_slow",       # spowalnia
]


class Portal:
    def __init__(self, x, y, effect="normal"):
        self.x = x
        self.y = y
        self.radius = PORTAL_RADIUS
        self.effect = effect
        self.partner = None
        self.lifetime = PORTAL_LIFETIME
        self.alive = True
        self.time = 0.0

    def update(self, dt):
        self.time += dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def try_teleport(self, obj):
        if not self.partner or not self.partner.alive:
            return False
        if getattr(obj, 'portal_cooldown', 0) > 0:
            return False
        if dist_wrapped(self.x, self.y, obj.x, obj.y) > PORTAL_ACTIVATION_RADIUS:
            return False

        # Teleportuj
        obj.x = self.partner.x
        obj.y = self.partner.y
        obj.portal_cooldown = PORTAL_COOLDOWN

        # Efekt portalu
        eff = self.effect
        if eff == "angle_twist" and hasattr(obj, 'angle'):
            twist = random.uniform(-math.pi / 3, math.pi / 3)
            obj.angle += twist
            if hasattr(obj, 'vx'):
                speed = math.hypot(obj.vx, obj.vy)
                obj.vx = math.sin(obj.angle) * speed
                obj.vy = -math.cos(obj.angle) * speed
        elif eff == "reverse_velocity":
            if hasattr(obj, 'vx'):
                obj.vx = -obj.vx
                obj.vy = -obj.vy
        elif eff == "speed_boost":
            if hasattr(obj, 'vx'):
                obj.vx *= 1.8
                obj.vy *= 1.8
        elif eff == "speed_slow":
            if hasattr(obj, 'vx'):
                obj.vx *= 0.4
                obj.vy *= 0.4

        return True

    def draw(self):
        fading = self.lifetime < 3.0
        for gx, gy in ghost_positions(self.x, self.y, self.radius):
            self._draw_at(gx, gy, fading)

    def _draw_at(self, cx, cy, fading):
        t = self.time
        base_alpha = 255
        if fading:
            base_alpha = int(255 * (self.lifetime / 3.0))

        # Kolor zalezy od efektu
        col_map = {
            "normal":           (200, 200, 255),
            "angle_twist":      (255, 200, 0),
            "reverse_velocity": (255, 50, 50),
            "speed_boost":      (50, 255, 100),
            "speed_slow":       (50, 100, 255),
        }
        r, g, b = col_map.get(self.effect, (200, 200, 255))

        ring_r = self.radius + 3 * math.sin(t * 3)
        rl.DrawCircleLines(int(cx), int(cy), ring_r, color(r, g, b, base_alpha))

        inner = self.radius * 0.6
        segments = 6
        for i in range(segments):
            a1 = t * 2 + math.tau * i / segments
            a2 = t * 2 + math.tau * (i + 0.4) / segments
            x1 = cx + math.cos(a1) * inner
            y1 = cy + math.sin(a1) * inner
            x2 = cx + math.cos(a2) * inner
            y2 = cy + math.sin(a2) * inner
            rl.DrawLineV(vec2(x1, y1), vec2(x2, y2), color(r, g, b, base_alpha // 2))

        core_r = 4 + 2 * math.sin(t * 5)
        rl.DrawCircleV(vec2(cx, cy), core_r, color(r, g, b, base_alpha // 3))

        # Etykieta efektu
        labels = {"normal": "WARP", "angle_twist": "TWIST",
                  "reverse_velocity": "FLIP", "speed_boost": "FAST",
                  "speed_slow": "SLOW"}
        label = T(labels.get(self.effect, "?")).encode()
        tw = rl.MeasureText(label, 10)
        rl.DrawText(label, int(cx - tw // 2), int(cy + self.radius + 5), 10,
                    color(r, g, b, base_alpha // 2))


def spawn_portal_pair(num_pairs=1):
    """Tworzy 1+ par portali z losowymi efektami."""
    all_portals = []
    for _ in range(min(num_pairs, PORTAL_MAX_PAIRS)):
        margin = 80
        x1 = random.uniform(margin, SCREEN_W - margin)
        y1 = random.uniform(margin, SCREEN_H - margin)
        for _attempt in range(20):
            x2 = random.uniform(margin, SCREEN_W - margin)
            y2 = random.uniform(margin, SCREEN_H - margin)
            if dist_wrapped(x1, y1, x2, y2) > 300:
                break

        effect = random.choice(PORTAL_EFFECTS)
        p1 = Portal(x1, y1, effect)
        p2 = Portal(x2, y2, effect)
        p1.partner = p2
        p2.partner = p1
        all_portals.extend([p1, p2])
    return all_portals
