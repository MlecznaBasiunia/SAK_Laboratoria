import math
import random
from raylib import rl, colors
from config import (SCREEN_W, SCREEN_H, ASTEROID_SIZES,
                    ASTEROID_JITTER, ASTEROID_ROT_MIN, ASTEROID_ROT_MAX)
from utils import vec2, rotate, wrap, ghost_positions


class Asteroid:
    def __init__(self, x, y, size="large"):
        self.x = x
        self.y = y
        self.angle = 0.0
        self.alive = True

        radius, spd_min, spd_max, num_verts = ASTEROID_SIZES[size]
        self.radius = radius
        self.size = size

        speed = random.uniform(spd_min, spd_max)
        direction = random.uniform(0, math.tau)
        self.vx = math.cos(direction) * speed
        self.vy = math.sin(direction) * speed

        self.rot_speed = random.uniform(ASTEROID_ROT_MIN, ASTEROID_ROT_MAX)
        if random.random() < 0.5:
            self.rot_speed = -self.rot_speed

        self.verts = []
        for i in range(num_verts):
            a = math.tau * i / num_verts
            r = radius * (1.0 + random.uniform(-ASTEROID_JITTER, ASTEROID_JITTER))
            self.verts.append((math.cos(a) * r, math.sin(a) * r))

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.rot_speed * dt

    def do_wrap(self):
        self.x, self.y = wrap(self.x, self.y)

    def _draw_at(self, cx, cy):
        n = len(self.verts)
        for i in range(n):
            x1, y1 = rotate(self.verts[i][0], self.verts[i][1], self.angle)
            x2, y2 = rotate(self.verts[(i + 1) % n][0], self.verts[(i + 1) % n][1], self.angle)
            rl.DrawLineV(
                vec2(cx + x1, cy + y1),
                vec2(cx + x2, cy + y2),
                colors.RAYWHITE,
            )

    def draw(self):
        for gx, gy in ghost_positions(self.x, self.y, self.radius):
            self._draw_at(gx, gy)


def spawn_asteroids(count):
    asteroids = []
    sizes = ["large", "medium", "small"]
    for _ in range(count):
        x = random.uniform(0, SCREEN_W)
        y = random.uniform(0, SCREEN_H)
        size = random.choice(sizes)
        asteroids.append(Asteroid(x, y, size))
    return asteroids
