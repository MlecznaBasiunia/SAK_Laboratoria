import math
from raylib import ffi
from config import SCREEN_W, SCREEN_H


def vec2(x, y):
    v = ffi.new("Vector2 *")
    v.x = x
    v.y = y
    return v[0]


def rotate(px, py, angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return px * c - py * s, px * s + py * c


def wrap(x, y):
    return x % SCREEN_W, y % SCREEN_H


def ghost_positions(x, y, size):
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
    return math.hypot(x1 - x2, y1 - y2) < (r1 + r2)
