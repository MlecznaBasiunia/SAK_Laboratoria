import math
import random
from raylib import ffi
from config import SCREEN_W, SCREEN_H


def vec2(x, y):
    """Tworzy Vector2 dla raylib cffi."""
    v = ffi.new("Vector2 *")
    v.x = x
    v.y = y
    return v[0]


def rotate(px, py, angle):
    """Obrót punktu (px, py) o kąt angle wokół (0,0)."""
    c = math.cos(angle)
    s = math.sin(angle)
    return px * c - py * s, px * s + py * c


def wrap(x, y):
    """Zawijanie pozycji na torusie."""
    return x % SCREEN_W, y % SCREEN_H


def ghost_positions(x, y, size):
    """Lista pozycji do narysowania (1-4) dla ghost rendering przy krawędziach."""
    xs = [x]
    ys = [y]

    if x - size < 0:
        xs.append(x + SCREEN_W)
    elif x + size > SCREEN_W:
        xs.append(x - SCREEN_W)

    if y - size < 0:
        ys.append(y + SCREEN_H)
    elif y + size > SCREEN_H:
        ys.append(y - SCREEN_H)

    return [(px, py) for px in xs for py in ys]


def circles_collide(x1, y1, r1, x2, y2, r2):
    """Kolizja dwóch okręgów – odległość euklidesowa vs suma promieni."""
    return math.hypot(x1 - x2, y1 - y2) < (r1 + r2)


def random_velocity(speed_min, speed_max):
    """Losowy wektor prędkości o module z zadanego zakresu."""
    speed = random.uniform(speed_min, speed_max)
    direction = random.uniform(0, math.tau)
    return math.cos(direction) * speed, math.sin(direction) * speed


def prune(items):
    """Zwraca listę zawierającą tylko elementy z flagą alive=True."""
    return [it for it in items if it.alive]
