import math
from raylib import rl, colors
from config import BULLET_SPEED, BULLET_TTL, BULLET_RADIUS
from utils import vec2, wrap, ghost_positions


class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.vx = math.sin(angle) * BULLET_SPEED
        self.vy = -math.cos(angle) * BULLET_SPEED
        self.radius = BULLET_RADIUS
        self.ttl = BULLET_TTL
        self.alive = True

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.x, self.y = wrap(self.x, self.y)
        self.ttl -= dt
        if self.ttl <= 0:
            self.alive = False

    def draw(self):
        for gx, gy in ghost_positions(self.x, self.y, self.radius):
            rl.DrawCircleV(vec2(gx, gy), self.radius, colors.YELLOW)
