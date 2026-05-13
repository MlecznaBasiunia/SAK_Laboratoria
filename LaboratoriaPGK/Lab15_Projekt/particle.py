import math
import random
from raylib import rl
from config import PARTICLE_FRICTION
from utils import vec2, color


class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'lifetime', 'max_lifetime',
                 'r', 'g', 'b', 'size', 'is_line', 'x2', 'y2')

    def __init__(self, x, y, vx, vy, lifetime, col=(255, 255, 255), size=2.0, is_line=False):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.r, self.g, self.b = col
        self.size = size
        self.is_line = is_line
        self.x2 = x
        self.y2 = y

    def update(self, dt):
        old_x, old_y = self.x, self.y
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= PARTICLE_FRICTION
        self.vy *= PARTICLE_FRICTION
        self.lifetime -= dt
        if self.is_line:
            self.x2 = old_x
            self.y2 = old_y

    def draw(self):
        t = max(0, self.lifetime / self.max_lifetime)
        alpha = int(255 * t)
        c = color(self.r, self.g, self.b, alpha)
        if self.is_line:
            rl.DrawLineV(vec2(self.x, self.y), vec2(self.x2, self.y2), c)
        else:
            sz = max(0.5, self.size * t)
            rl.DrawCircleV(vec2(self.x, self.y), sz, c)

    @property
    def alive(self):
        return self.lifetime > 0


def explosion(x, y, count=20, speed=150, col=(255, 200, 50), lifetime=0.6, size=2.5):
    particles = []
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        spd = random.uniform(speed * 0.3, speed)
        vx = math.cos(angle) * spd
        vy = math.sin(angle) * spd
        lt = random.uniform(lifetime * 0.5, lifetime)
        is_line = random.random() < 0.3
        particles.append(Particle(x, y, vx, vy, lt, col, size, is_line))
    return particles


def thrust_particles(x, y, angle, ship_vx, ship_vy):
    ex = x - math.sin(angle) * 16
    ey = y + math.cos(angle) * 16
    particles = []
    for _ in range(2):
        spread = random.uniform(-0.4, 0.4)
        spd = random.uniform(80, 160)
        vx = -math.sin(angle + spread) * spd + ship_vx * 0.3
        vy = math.cos(angle + spread) * spd + ship_vy * 0.3
        lt = random.uniform(0.2, 0.5)
        c = random.choice([(255, 150, 0), (255, 100, 0), (255, 200, 50)])
        particles.append(Particle(ex, ey, vx, vy, lt, c, 2.0))
    return particles


def portal_particles(x, y, radius, col, count=3):
    particles = []
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        dist = radius * random.uniform(0.8, 1.2)
        px = x + math.cos(angle) * dist
        py = y + math.sin(angle) * dist
        vx = -math.sin(angle) * 30
        vy = math.cos(angle) * 30
        particles.append(Particle(px, py, vx, vy, 0.4, col, 1.5))
    return particles


def gravity_well_particles(x, y, radius, count=2):
    particles = []
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        dist = radius * random.uniform(0.6, 1.0)
        px = x + math.cos(angle) * dist
        py = y + math.sin(angle) * dist
        vx = -math.cos(angle) * 40
        vy = -math.sin(angle) * 40
        particles.append(Particle(px, py, vx, vy, 0.5, (150, 100, 255), 1.5))
    return particles


def chain_explosion(x, y):
    return explosion(x, y, 35, 200, (255, 150, 0), 0.9, 3.5)


def warp_flash(x, y, col=(100, 200, 255)):
    particles = []
    for _ in range(15):
        angle = random.uniform(0, math.tau)
        spd = random.uniform(100, 250)
        vx = math.cos(angle) * spd
        vy = math.sin(angle) * spd
        particles.append(Particle(x, y, vx, vy, 0.3, col, 2.0))
    return particles


def heat_trail(x, y, ship_vx, ship_vy, heat):
    """Ogon ognia przy overheacie."""
    particles = []
    intensity = max(0, (heat - 0.5) * 2)  # 0-1 od 50% heat
    count = int(3 * intensity)
    for _ in range(count):
        vx = -ship_vx * 0.3 + random.uniform(-30, 30)
        vy = -ship_vy * 0.3 + random.uniform(-30, 30)
        lt = random.uniform(0.2, 0.5) * intensity
        r = int(255)
        g = int(150 * (1 - intensity))
        b = 0
        particles.append(Particle(x, y, vx, vy, lt, (r, g, b), 2.5 * intensity))
    return particles


def smear_particles(x, y, vx, vy, col=(200, 200, 255)):
    """Efekt relatywistyczny - smugi przy duzej predkosci."""
    particles = []
    for i in range(3):
        t = (i + 1) * 0.01
        px = x - vx * t
        py = y - vy * t
        alpha_frac = 1.0 - i * 0.3
        particles.append(Particle(px, py, 0, 0, 0.05, col, 1.0 * alpha_frac))
    return particles


def topology_border_particle(x, y, col):
    """Particle na granicy topologii."""
    vx = random.uniform(-20, 20)
    vy = random.uniform(-20, 20)
    return Particle(x, y, vx, vy, 0.3, col, 1.5)
