from raylib import rl, ffi
from config import EXPLOSION_DURATION


class Explosion:
    def __init__(self, x, y, max_radius):
        self.x = x
        self.y = y
        self.max_radius = max_radius
        self.elapsed = 0.0
        self.alive = True

    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= EXPLOSION_DURATION:
            self.alive = False

    def draw(self):
        progress = self.elapsed / EXPLOSION_DURATION
        radius = self.max_radius * progress
        alpha = int(255 * (1 - progress))

        color = ffi.new("Color *")
        color.r = 255
        color.g = 200
        color.b = 80
        color.a = alpha

        rl.DrawCircleLines(int(self.x), int(self.y), radius, color[0])
