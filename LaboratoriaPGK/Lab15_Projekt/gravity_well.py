import math
import random
from raylib import rl
from config import (SCREEN_W, SCREEN_H, GRAV_WELL_LIFETIME,
                    GRAV_WELL_ATTRACT_RADIUS, GRAV_WELL_STRENGTH,
                    GRAV_WELL_CORE_RADIUS, GRAV_WELL_VISUAL_RADIUS,
                    SAFE_SPAWN_RADIUS)
from utils import vec2, color, torus_direction, dist_wrapped, ghost_positions


class GravityWell:
    def __init__(self, x, y, strength_mult=1.0):
        self.x = x
        self.y = y
        self.lifetime = GRAV_WELL_LIFETIME
        self.alive = True
        self.time = 0.0
        self.radius = GRAV_WELL_VISUAL_RADIUS
        self.core_radius = GRAV_WELL_CORE_RADIUS
        self.attract_radius = GRAV_WELL_ATTRACT_RADIUS
        self.strength = GRAV_WELL_STRENGTH * strength_mult

    def update(self, dt):
        self.time += dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def apply_gravity(self, obj, dt):
        dx, dy = torus_direction(obj.x, obj.y, self.x, self.y)
        dist = math.hypot(dx, dy)
        if dist > self.attract_radius or dist < 1:
            return False
        force = min(self.strength / (dist * dist), 800)
        nx, ny = dx / dist, dy / dist
        obj.vx += nx * force * dt
        obj.vy += ny * force * dt
        return dist < self.core_radius

    def draw(self):
        fading = self.lifetime < 3.0
        base_alpha = int(255 * (self.lifetime / 3.0)) if fading else 255
        for gx, gy in ghost_positions(self.x, self.y, self.attract_radius):
            self._draw_at(gx, gy, base_alpha)

    def _draw_at(self, cx, cy, base_alpha):
        t = self.time
        for i in range(4):
            r = self.attract_radius * (0.3 + 0.7 * ((t * 0.5 + i * 0.25) % 1.0))
            a = int(base_alpha * 0.15 * (1.0 - r / self.attract_radius))
            rl.DrawCircleLines(int(cx), int(cy), r, color(150, 80, 255, max(0, a)))
        arms = 3
        for i in range(arms):
            base_angle = t * 1.5 + math.tau * i / arms
            for s in range(12):
                frac = s / 12
                angle = base_angle + frac * 1.5
                dist = self.attract_radius * (1.0 - frac) * 0.8
                x1 = cx + math.cos(angle) * dist
                y1 = cy + math.sin(angle) * dist
                frac2 = (s + 1) / 12
                angle2 = base_angle + frac2 * 1.5
                dist2 = self.attract_radius * (1.0 - frac2) * 0.8
                x2 = cx + math.cos(angle2) * dist2
                y2 = cy + math.sin(angle2) * dist2
                a = int(base_alpha * 0.4 * frac)
                rl.DrawLineV(vec2(x1, y1), vec2(x2, y2), color(180, 100, 255, a))
        core_r = self.core_radius + 2 * math.sin(t * 6)
        rl.DrawCircleV(vec2(cx, cy), core_r, color(200, 150, 255, base_alpha // 2))


def spawn_gravity_well(safe_x=None, safe_y=None):
    margin = 60
    for _ in range(20):
        x = random.uniform(margin, SCREEN_W - margin)
        y = random.uniform(margin, SCREEN_H - margin)
        if safe_x is not None:
            if dist_wrapped(x, y, safe_x, safe_y) < SAFE_SPAWN_RADIUS:
                continue
        return GravityWell(x, y)
    return GravityWell(SCREEN_W / 2, SCREEN_H / 4)
