import math
import random
from raylib import rl
from config import (SCREEN_W, SCREEN_H, UFO_SHOOT_INTERVAL, UFO_AIM_ERROR,
                    UFO_POINTS_LARGE, UFO_POINTS_SMALL)
from utils import vec2, color, ghost_positions_topo, apply_wrap
from bullet import Bullet


class UFO:
    def __init__(self, ufo_type="large"):
        self.ufo_type = ufo_type
        if ufo_type == "large":
            self.radius = 22
            self.speed = 80
            self.points = UFO_POINTS_LARGE
            self.shoot_interval = UFO_SHOOT_INTERVAL
        else:
            self.radius = 12
            self.speed = 140
            self.points = UFO_POINTS_SMALL
            self.shoot_interval = UFO_SHOOT_INTERVAL * 0.7

        if random.random() < 0.5:
            self.x = -self.radius
            self.dir = 1
        else:
            self.x = SCREEN_W + self.radius
            self.dir = -1

        self.y = random.uniform(SCREEN_H * 0.15, SCREEN_H * 0.85)
        self.vx = self.speed * self.dir
        self.vy = 0
        self.angle = 0.0
        self.alive = True
        self.shoot_timer = self.shoot_interval * 0.5
        self.wave_time = 0
        self.wave_freq = random.uniform(1.5, 3.0)
        self.portal_cooldown = 0.0

    def update(self, dt):
        self.wave_time += dt
        self.portal_cooldown = max(0, self.portal_cooldown - dt)
        self.vy = math.sin(self.wave_time * self.wave_freq) * self.speed * 0.5
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.y = self.y % SCREEN_H
        if self.dir == 1 and self.x > SCREEN_W + self.radius * 2:
            self.alive = False
        elif self.dir == -1 and self.x < -self.radius * 2:
            self.alive = False
        self.shoot_timer -= dt

    def try_shoot(self, target_x, target_y):
        if self.shoot_timer > 0:
            return None
        self.shoot_timer = self.shoot_interval
        dx = target_x - self.x
        dy = target_y - self.y
        angle = math.atan2(dx, -dy) + random.uniform(-UFO_AIM_ERROR, UFO_AIM_ERROR)
        b = Bullet(self.x, self.y, angle)
        b.lifetime = 2.0
        return b

    def _draw_at(self, cx, cy, mirror=False):
        r = self.radius
        col = color(100, 255, 100) if self.ufo_type == "large" else color(255, 100, 255)
        pts_top = 8
        for i in range(pts_top):
            a1 = math.pi + math.pi * i / pts_top
            a2 = math.pi + math.pi * (i + 1) / pts_top
            x1 = cx + math.cos(a1) * r * 0.6
            y1 = cy + math.sin(a1) * r * 0.5
            x2 = cx + math.cos(a2) * r * 0.6
            y2 = cy + math.sin(a2) * r * 0.5
            rl.DrawLineV(vec2(x1, y1), vec2(x2, y2), col)
        rl.DrawLineV(vec2(cx - r, cy), vec2(cx + r, cy), col)
        rl.DrawLineV(vec2(cx - r, cy), vec2(cx - r * 0.5, cy + r * 0.4), col)
        rl.DrawLineV(vec2(cx - r * 0.5, cy + r * 0.4), vec2(cx + r * 0.5, cy + r * 0.4), col)
        rl.DrawLineV(vec2(cx + r * 0.5, cy + r * 0.4), vec2(cx + r, cy), col)

    def draw(self):
        for gx, gy, mirror in ghost_positions_topo(self.x, self.y, self.radius):
            self._draw_at(gx, gy, mirror)
