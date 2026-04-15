import math
import random
from raylib import rl, colors
from config import (SCREEN_W, SCREEN_H, ASTEROID_LEVELS,
                    ASTEROID_JITTER, ASTEROID_ROT_MIN, ASTEROID_ROT_MAX)
from utils import vec2, rotate, wrap, ghost_positions, random_velocity


class Asteroid:
    """Asteroida z proceduralnym kształtem.

    level 3 = duża, 2 = średnia, 1 = mała.
    Parametry (promień, prędkość, liczba wierzchołków, punkty) wyznaczane
    automatycznie z poziomu w config.ASTEROID_LEVELS.
    """

    def __init__(self, x, y, level=3):
        self.x = x
        self.y = y
        self.angle = 0.0
        self.alive = True
        self.level = level

        radius, spd_min, spd_max, num_verts, score = ASTEROID_LEVELS[level]
        self.radius = radius
        self.score_value = score

        self.vx, self.vy = random_velocity(spd_min, spd_max)

        self.rot_speed = random.uniform(ASTEROID_ROT_MIN, ASTEROID_ROT_MAX)
        if random.random() < 0.5:
            self.rot_speed = -self.rot_speed

        self.verts = self._generate_verts(radius, num_verts)

    @staticmethod
    def _generate_verts(radius, num_verts):
        """Wierzchołki rozmieszczone wokół środka z losowym jitterem promienia."""
        verts = []
        for i in range(num_verts):
            angle = math.tau * i / num_verts
            r = radius * (1.0 + random.uniform(-ASTEROID_JITTER, ASTEROID_JITTER))
            verts.append((math.cos(angle) * r, math.sin(angle) * r))
        return verts

    def split(self):
        """Zwraca listę nowych asteroid po trafieniu.

        level 1 → []  (mała znika bezpowrotnie)
        level >1 → 2x asteroida o level-1 z pozycji rodzica
        """
        if self.level == 1:
            return []
        return [
            Asteroid(self.x, self.y, self.level - 1),
            Asteroid(self.x, self.y, self.level - 1),
        ]

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


def spawn_wave(count):
    """Generuje falę dużych asteroid (level 3) w losowych pozycjach."""
    asteroids = []
    for _ in range(count):
        x = random.uniform(0, SCREEN_W)
        y = random.uniform(0, SCREEN_H)
        asteroids.append(Asteroid(x, y, level=3))
    return asteroids
