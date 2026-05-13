import math
from raylib import rl
from config import (BULLET_SPEED, BULLET_RADIUS, BULLET_LIFETIME,
                    SCREEN_W, SCREEN_H, BOUNCING_BOUNCES, HOMING_TURN_RATE)
from utils import (vec2, color, ghost_positions, torus_direction, apply_wrap)


class Bullet:
    def __init__(self, x, y, angle, speed_bonus=0, kind="normal"):
        self.x = x
        self.y = y
        self.radius = BULLET_RADIUS
        self.kind = kind
        self.alive = True
        self.lifetime = BULLET_LIFETIME
        self.pierce = False
        self.pierced_once = False
        self.origin_x = x
        self.origin_y = y

        speed = BULLET_SPEED + speed_bonus
        self.vx = math.sin(angle) * speed
        self.vy = -math.cos(angle) * speed
        self.angle = angle

        self.bounces_left = BOUNCING_BOUNCES if kind == "bouncing" else 0
        self.homing_targets = None
        self.portal_cooldown = 0.0

        if kind == "gravity_bomb":
            self.lifetime = 1.0
            self.radius = 4
        if kind == "hyperspace":
            self.lifetime = 2.5
            self.radius = 3
            self._hyperspace_jumped = False
            self._hyperspace_timer = 0.3

        # Modul: ile razy pocisk juz przebil
        self.module_pierce_count = 0
        # Modul: backfire
        self.is_backfire = False

    def update(self, dt):
        self.portal_cooldown = max(0, self.portal_cooldown - dt)

        # Homing
        if self.kind == "homing" and self.homing_targets:
            best_dist = float('inf')
            best_dx, best_dy = 0, 0
            for t in self.homing_targets:
                if not getattr(t, 'alive', True):
                    continue
                dx, dy = torus_direction(self.x, self.y, t.x, t.y)
                d = math.hypot(dx, dy)
                if d < best_dist:
                    best_dist = d
                    best_dx, best_dy = dx, dy
            if best_dist < 400:
                target_angle = math.atan2(best_dx, -best_dy)
                diff = target_angle - self.angle
                diff = (diff + math.pi) % math.tau - math.pi
                turn = HOMING_TURN_RATE * dt
                if abs(diff) < turn:
                    self.angle = target_angle
                else:
                    self.angle += math.copysign(turn, diff)
                speed = math.hypot(self.vx, self.vy)
                self.vx = math.sin(self.angle) * speed
                self.vy = -math.cos(self.angle) * speed

        self.x += self.vx * dt
        self.y += self.vy * dt

        # Bouncing: odbicie zamiast wrap
        if self.kind == "bouncing" and self.bounces_left > 0:
            bounced = False
            if self.x < 0 or self.x > SCREEN_W:
                self.vx = -self.vx
                self.x = max(0, min(SCREEN_W, self.x))
                bounced = True
            if self.y < 0 or self.y > SCREEN_H:
                self.vy = -self.vy
                self.y = max(0, min(SCREEN_H, self.y))
                bounced = True
            if bounced:
                self.bounces_left -= 1
                self.angle = math.atan2(self.vx, -self.vy)
        else:
            apply_wrap(self)

        # Hyperspace skok
        if self.kind == "hyperspace" and not self._hyperspace_jumped:
            self._hyperspace_timer -= dt
            if self._hyperspace_timer <= 0:
                self.x = (self.x + SCREEN_W / 2) % SCREEN_W
                self.y = (self.y + SCREEN_H / 2) % SCREEN_H
                self._hyperspace_jumped = True

        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self):
        col_map = {
            "normal":       color(255, 255, 255),
            "bouncing":     color(0, 255, 200),
            "homing":       color(255, 200, 0),
            "gravity_bomb": color(200, 50, 255),
            "hyperspace":   color(100, 150, 255),
        }
        c = col_map.get(self.kind, color(255, 255, 255))
        r = self.radius
        if self.kind == "gravity_bomb":
            r = 4
        elif self.kind == "hyperspace" and not self._hyperspace_jumped:
            r = 3 if int(self._hyperspace_timer * 20) % 2 == 0 else 1

        for gx, gy in ghost_positions(self.x, self.y, r):
            rl.DrawCircleV(vec2(gx, gy), r, c)
            if self.kind == "homing":
                tx = gx - self.vx * 0.02
                ty = gy - self.vy * 0.02
                rl.DrawLineV(vec2(tx, ty), vec2(gx, gy), color(255, 200, 0, 100))
