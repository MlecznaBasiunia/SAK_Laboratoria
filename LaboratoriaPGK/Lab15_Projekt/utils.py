import math
import random
from raylib import ffi
from config import (SCREEN_W, SCREEN_H,
                    TORUS, CYLINDER, MOBIUS, KLEIN, SPHERE)

# ---- Globalna topologia ----
_topology = TORUS


def set_topology(topo):
    global _topology
    _topology = topo


def get_topology():
    return _topology


# ---- Raylib helpers ----

def vec2(x, y):
    v = ffi.new("Vector2 *")
    v.x = x
    v.y = y
    return v[0]


def color(r, g, b, a=255):
    c = ffi.new("Color *")
    c.r = int(max(0, min(255, r)))
    c.g = int(max(0, min(255, g)))
    c.b = int(max(0, min(255, b)))
    c.a = int(max(0, min(255, a)))
    return c[0]


def rotate(px, py, angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return px * c - py * s, px * s + py * c


# ---- Wrapping z topologia ----

def wrap(x, y):
    """Proste zawijanie pozycji (bez efektow predkosci)."""
    topo = _topology
    if topo in (TORUS, SPHERE):
        return x % SCREEN_W, y % SCREEN_H
    elif topo == CYLINDER:
        return x % SCREEN_W, max(0, min(SCREEN_H - 1, y))
    elif topo in (MOBIUS, KLEIN):
        # X wrap obslugiwany w apply_wrap, tu tylko clamp
        nx = x % SCREEN_W
        if topo == KLEIN:
            return nx, y % SCREEN_H
        else:  # Mobius: Y walls
            return nx, max(0, min(SCREEN_H - 1, y))
    return x % SCREEN_W, y % SCREEN_H


def apply_wrap(obj):
    """Topology-aware wrapping z efektami na predkosc i kat.
    Wywolac PO update pozycji. Zwraca True jesli nastapilo przejscie."""
    topo = _topology
    crossed = False

    # ---- X ----
    if obj.x < 0:
        obj.x += SCREEN_W
        crossed = True
        if topo in (MOBIUS, KLEIN):
            obj.y = SCREEN_H - obj.y
            if hasattr(obj, 'vy'):
                obj.vy = -obj.vy
            if hasattr(obj, 'angle'):
                obj.angle = -obj.angle
    elif obj.x >= SCREEN_W:
        obj.x -= SCREEN_W
        crossed = True
        if topo in (MOBIUS, KLEIN):
            obj.y = SCREEN_H - obj.y
            if hasattr(obj, 'vy'):
                obj.vy = -obj.vy
            if hasattr(obj, 'angle'):
                obj.angle = -obj.angle

    # ---- Y ----
    if topo in (TORUS, KLEIN, SPHERE):
        if obj.y < 0:
            obj.y += SCREEN_H
            crossed = True
        elif obj.y >= SCREEN_H:
            obj.y -= SCREEN_H
            crossed = True
    elif topo in (CYLINDER, MOBIUS):
        # Odbicie od scian Y
        if obj.y < 0:
            obj.y = -obj.y
            if hasattr(obj, 'vy'):
                obj.vy = abs(obj.vy)
            crossed = True
        elif obj.y >= SCREEN_H:
            obj.y = 2 * SCREEN_H - obj.y - 1
            if hasattr(obj, 'vy'):
                obj.vy = -abs(obj.vy)
            crossed = True

    # Sphere: lekki jitter kata przy przejsciu
    if topo == SPHERE and crossed and hasattr(obj, 'angle'):
        obj.angle += random.uniform(-0.08, 0.08)

    return crossed


# ---- Ghost positions z topologia ----

def ghost_positions(x, y, size):
    """Proste ghost positions (bez mirror info) - do particle/prostych obiektow."""
    topo = _topology

    if topo in (TORUS, SPHERE):
        xs = [x]
        ys = [y]
        if x - size < 0: xs.append(x + SCREEN_W)
        elif x + size > SCREEN_W: xs.append(x - SCREEN_W)
        if y - size < 0: ys.append(y + SCREEN_H)
        elif y + size > SCREEN_H: ys.append(y - SCREEN_H)
        return [(px, py) for px in xs for py in ys]

    elif topo == CYLINDER:
        xs = [x]
        if x - size < 0: xs.append(x + SCREEN_W)
        elif x + size > SCREEN_W: xs.append(x - SCREEN_W)
        return [(px, y) for px in xs]

    elif topo == MOBIUS:
        result = [(x, y)]
        if x - size < 0:
            result.append((x + SCREEN_W, SCREEN_H - y))
        elif x + size > SCREEN_W:
            result.append((x - SCREEN_W, SCREEN_H - y))
        return result

    elif topo == KLEIN:
        x_ghosts = [(x, False)]
        if x - size < 0: x_ghosts.append((x + SCREEN_W, True))
        elif x + size > SCREEN_W: x_ghosts.append((x - SCREEN_W, True))
        y_ghosts = [y]
        if y - size < 0: y_ghosts.append(y + SCREEN_H)
        elif y + size > SCREEN_H: y_ghosts.append(y - SCREEN_H)
        result = []
        for gx, mirror in x_ghosts:
            for gy in y_ghosts:
                result.append((gx, SCREEN_H - gy if mirror else gy))
        return result

    return [(x, y)]


def ghost_positions_topo(x, y, size):
    """Ghost positions z informacja o mirrorze: [(gx, gy, mirror)]."""
    topo = _topology

    if topo in (TORUS, SPHERE, CYLINDER):
        return [(gx, gy, False) for gx, gy in ghost_positions(x, y, size)]

    elif topo == MOBIUS:
        result = [(x, y, False)]
        if x - size < 0:
            result.append((x + SCREEN_W, SCREEN_H - y, True))
        elif x + size > SCREEN_W:
            result.append((x - SCREEN_W, SCREEN_H - y, True))
        return result

    elif topo == KLEIN:
        x_ghosts = [(x, False)]
        if x - size < 0: x_ghosts.append((x + SCREEN_W, True))
        elif x + size > SCREEN_W: x_ghosts.append((x - SCREEN_W, True))
        y_ghosts = [y]
        if y - size < 0: y_ghosts.append(y + SCREEN_H)
        elif y + size > SCREEN_H: y_ghosts.append(y - SCREEN_H)
        result = []
        for gx, mirror in x_ghosts:
            for gy in y_ghosts:
                result.append((gx, SCREEN_H - gy if mirror else gy, mirror))
        return result

    return [(x, y, False)]


# ---- Odleglosc i kolizje ----

def dist_wrapped(x1, y1, x2, y2):
    topo = _topology
    dx = abs(x1 - x2)
    dy = abs(y1 - y2)
    # X wrap we wszystkich topologiach
    dx = min(dx, SCREEN_W - dx)
    # Y wrap tylko w torus/klein/sphere
    if topo in (TORUS, KLEIN, SPHERE):
        dy = min(dy, SCREEN_H - dy)
    return math.hypot(dx, dy)


def torus_direction(x1, y1, x2, y2):
    topo = _topology
    dx = x2 - x1
    dy = y2 - y1
    if abs(dx) > SCREEN_W / 2:
        dx -= math.copysign(SCREEN_W, dx)
    if topo in (TORUS, KLEIN, SPHERE):
        if abs(dy) > SCREEN_H / 2:
            dy -= math.copysign(SCREEN_H, dy)
    return dx, dy


def circle_collision(x1, y1, r1, x2, y2, r2):
    return dist_wrapped(x1, y1, x2, y2) < r1 + r2
