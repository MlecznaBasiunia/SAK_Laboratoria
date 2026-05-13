import math
import random
from raylib import rl
from config import (SCREEN_W, SCREEN_H, HUNTER_SPEED, HUNTER_RADIUS,
                    HUNTER_POINTS, HUNTER_SHOOT_INTERVAL, HUNTER_AIM_ERROR,
                    HUNTER_HP, SHIP_VERTS)
from utils import (vec2, color, rotate, ghost_positions_topo,
                   torus_direction, apply_wrap)
from bullet import Bullet


class HunterDrone:
    def __init__(self, x=None, y=None):
        if x is None:
            side = random.randint(0, 3)
            if side == 0: x, y = random.uniform(0, SCREEN_W), -20
            elif side == 1: x, y = random.uniform(0, SCREEN_W), SCREEN_H + 20
            elif side == 2: x, y = -20, random.uniform(0, SCREEN_H)
            else: x, y = SCREEN_W + 20, random.uniform(0, SCREEN_H)
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0
        self.radius = HUNTER_RADIUS
        self.speed = HUNTER_SPEED
        self.points = HUNTER_POINTS
        self.hp = HUNTER_HP
        self.alive = True
        self.shoot_timer = HUNTER_SHOOT_INTERVAL
        self.time = 0.0
        self.portal_cooldown = 0.0

    def update(self, dt, target_x, target_y):
        self.time += dt
        self.portal_cooldown = max(0, self.portal_cooldown - dt)
        dx, dy = torus_direction(self.x, self.y, target_x, target_y)
        dist = math.hypot(dx, dy)
        if dist > 5:
            nx, ny = dx / dist, dy / dist
            self.vx += nx * self.speed * 2.5 * dt
            self.vy += ny * self.speed * 2.5 * dt
        spd = math.hypot(self.vx, self.vy)
        if spd > self.speed:
            self.vx = self.vx / spd * self.speed
            self.vy = self.vy / spd * self.speed
        self.x += self.vx * dt
        self.y += self.vy * dt
        apply_wrap(self)
        if spd > 10:
            self.angle = math.atan2(self.vx, -self.vy)
        self.shoot_timer -= dt

    def try_shoot(self, target_x, target_y):
        if self.shoot_timer > 0:
            return None
        self.shoot_timer = HUNTER_SHOOT_INTERVAL
        dx, dy = torus_direction(self.x, self.y, target_x, target_y)
        angle = math.atan2(dx, -dy) + random.uniform(-HUNTER_AIM_ERROR, HUNTER_AIM_ERROR)
        b = Bullet(self.x, self.y, angle)
        b.lifetime = 1.8
        return b

    def take_hit(self):
        self.hp -= 1
        return self.hp <= 0

    def _draw_at(self, cx, cy, mirror=False):
        size = self.radius
        pts = [(0, -size * 1.3), (size, size * 0.3),
               (0, size * 0.8), (-size, size * 0.3)]
        draw_angle = -self.angle if mirror else self.angle
        rotated = []
        for px, py in pts:
            rx, ry = rotate(px, py, draw_angle)
            rotated.append((cx + rx, cy + ry))
        pulse = 0.7 + 0.3 * math.sin(self.time * 5)
        col = color(255, int(50 * pulse), int(50 * pulse))
        n = len(rotated)
        for i in range(n):
            rl.DrawLineV(vec2(rotated[i][0], rotated[i][1]),
                         vec2(rotated[(i + 1) % n][0], rotated[(i + 1) % n][1]), col)
        eye_offset = size * 0.3
        for side in [-1, 1]:
            ex, ey = rotate(side * eye_offset * 0.5, -size * 0.3, draw_angle)
            rl.DrawCircleV(vec2(cx + ex, cy + ey), 2, color(255, 0, 0))
        if self.hp > 1:
            rl.DrawCircleLines(int(cx), int(cy), size + 3, color(255, 50, 50, 80))

    def draw(self):
        for gx, gy, mirror in ghost_positions_topo(self.x, self.y, self.radius):
            self._draw_at(gx, gy, mirror)


class MirrorEnemy:
    def __init__(self, ship_x, ship_y, ship_angle):
        self.x = (ship_x + SCREEN_W / 2) % SCREEN_W
        self.y = (ship_y + SCREEN_H / 2) % SCREEN_H
        self.angle = ship_angle + math.pi
        self.vx = 0.0
        self.vy = 0.0
        self.radius = 14
        self.points = 800
        self.hp = 3
        self.alive = True
        self.shoot_timer = 1.5
        self.time = 0.0
        self.portal_cooldown = 0.0
        self.target_history = []
        self.delay = 0.8

    def update(self, dt, target_x, target_y):
        self.time += dt
        self.portal_cooldown = max(0, self.portal_cooldown - dt)
        self.target_history.append((self.time, target_x, target_y))
        while self.target_history and self.target_history[0][0] < self.time - self.delay - 0.1:
            self.target_history.pop(0)
        delayed_x, delayed_y = target_x, target_y
        for t, tx, ty in self.target_history:
            if t >= self.time - self.delay:
                delayed_x, delayed_y = tx, ty
                break
        dx, dy = torus_direction(self.x, self.y, delayed_x, delayed_y)
        dist = math.hypot(dx, dy)
        if dist > 40:
            nx, ny = dx / dist, dy / dist
            self.vx += nx * 200 * dt
            self.vy += ny * 200 * dt
        spd = math.hypot(self.vx, self.vy)
        if spd > 150:
            self.vx = self.vx / spd * 150
            self.vy = self.vy / spd * 150
        self.x += self.vx * dt
        self.y += self.vy * dt
        apply_wrap(self)
        if dist > 5:
            self.angle = math.atan2(dx, -dy)
        self.shoot_timer -= dt

    def try_shoot(self, target_x, target_y):
        if self.shoot_timer > 0:
            return None
        self.shoot_timer = 1.2
        dx, dy = torus_direction(self.x, self.y, target_x, target_y)
        angle = math.atan2(dx, -dy) + random.uniform(-0.2, 0.2)
        b = Bullet(self.x, self.y, angle)
        b.lifetime = 1.5
        return b

    def take_hit(self):
        self.hp -= 1
        return self.hp <= 0

    def _draw_at(self, cx, cy, mirror=False):
        draw_angle = -self.angle if mirror else self.angle
        pulse = 0.5 + 0.5 * math.sin(self.time * 8)
        col = color(255, int(100 * pulse), 255, int(180 + 75 * pulse))
        pts = []
        for px, py in SHIP_VERTS:
            rx, ry = rotate(px, py, draw_angle)
            pts.append((cx + rx, cy + ry))
        rl.DrawTriangleLines(
            vec2(pts[0][0], pts[0][1]), vec2(pts[1][0], pts[1][1]),
            vec2(pts[2][0], pts[2][1]), col)
        offset = 3 * math.sin(self.time * 12)
        pts2 = [(p[0] + offset, p[1]) for p in pts]
        rl.DrawTriangleLines(
            vec2(pts2[0][0], pts2[0][1]), vec2(pts2[1][0], pts2[1][1]),
            vec2(pts2[2][0], pts2[2][1]), color(255, 0, 255, 60))

    def draw(self):
        for gx, gy, mirror in ghost_positions_topo(self.x, self.y, self.radius):
            self._draw_at(gx, gy, mirror)
