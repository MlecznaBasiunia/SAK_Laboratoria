import math
from raylib import rl, colors
from config import (THRUST, FRICTION, ROT_SPEED, MAX_SPEED, BRAKE_FORCE,
                    SHIP_VERTS, SHIP_SIZE, SHIP_RADIUS, FLAME_VERTS,
                    SCREEN_W, SCREEN_H, DEBUG,
                    KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_Z)
from utils import vec2, rotate, wrap, ghost_positions


class Ship:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.thrusting = False
        self.radius = SHIP_RADIUS

    def reset(self):
        self.x = SCREEN_W / 2
        self.y = SCREEN_H / 2
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0

    def nose_position(self):
        nx, ny = rotate(SHIP_VERTS[0][0], SHIP_VERTS[0][1], self.angle)
        return self.x + nx, self.y + ny

    def update(self, dt):
        if rl.IsKeyDown(KEY_LEFT):
            self.angle -= ROT_SPEED * dt
        if rl.IsKeyDown(KEY_RIGHT):
            self.angle += ROT_SPEED * dt

        self.thrusting = rl.IsKeyDown(KEY_UP)
        if self.thrusting:
            dir_x = math.sin(self.angle)
            dir_y = -math.cos(self.angle)
            self.vx += THRUST * dir_x * dt
            self.vy += THRUST * dir_y * dt

        braking = rl.IsKeyDown(KEY_Z)
        self._apply_friction(BRAKE_FORCE if braking else FRICTION, dt)
        self._clamp_speed()

        self.x += self.vx * dt
        self.y += self.vy * dt

    def _apply_friction(self, fric, dt):
        speed = math.hypot(self.vx, self.vy)
        if speed <= 0:
            return
        decel = fric * dt
        if decel >= speed:
            self.vx = 0.0
            self.vy = 0.0
        else:
            factor = (speed - decel) / speed
            self.vx *= factor
            self.vy *= factor

    def _clamp_speed(self):
        speed = math.hypot(self.vx, self.vy)
        if speed > MAX_SPEED:
            factor = MAX_SPEED / speed
            self.vx *= factor
            self.vy *= factor

    def do_wrap(self):
        self.x, self.y = wrap(self.x, self.y)

    def _draw_at(self, cx, cy):
        pts = []
        for px, py in SHIP_VERTS:
            rx, ry = rotate(px, py, self.angle)
            pts.append((cx + rx, cy + ry))
        rl.DrawTriangleLines(
            vec2(pts[0][0], pts[0][1]),
            vec2(pts[1][0], pts[1][1]),
            vec2(pts[2][0], pts[2][1]),
            colors.RAYWHITE,
        )

        if self.thrusting:
            fp = []
            for px, py in FLAME_VERTS:
                rx, ry = rotate(px, py, self.angle)
                fp.append((cx + rx, cy + ry))
            rl.DrawTriangleLines(
                vec2(fp[0][0], fp[0][1]),
                vec2(fp[1][0], fp[1][1]),
                vec2(fp[2][0], fp[2][1]),
                colors.ORANGE,
            )

    def draw(self):
        for gx, gy in ghost_positions(self.x, self.y, SHIP_SIZE):
            self._draw_at(gx, gy)

        if DEBUG:
            speed = math.hypot(self.vx, self.vy)
            scale = 0.3
            ex = self.x + self.vx * scale
            ey = self.y + self.vy * scale
            rl.DrawLine(int(self.x), int(self.y), int(ex), int(ey), colors.GREEN)
            rl.DrawText(f"v={speed:.1f}".encode(), 10, 10, 18, colors.GRAY)
