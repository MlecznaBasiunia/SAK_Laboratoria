import math
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
    """Zawijanie pozycji na torusie (modulo)."""
    return x % SCREEN_W, y % SCREEN_H


def ghost_positions(x, y, size):
    """Zwraca listę pozycji do narysowania (1-4) dla ghost rendering.

    Gdy obiekt jest bliżej krawędzi niż jego rozmiar, dodaje kopie
    przesunięte o wymiar ekranu, żeby był widoczny po obu stronach.
    """
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
