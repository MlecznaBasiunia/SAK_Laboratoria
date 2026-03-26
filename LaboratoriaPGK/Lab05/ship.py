import math
from raylib import ffi, rl, colors

# Stałe fizyczne
THRUST = 300.0       # siła ciągu – daje wyraźne przyspieszenie, ale nie natychmiastowe
FRICTION = 80.0      # tarcie addytywne – statek zatrzymuje się po ~2-3 s dryfu
ROT_SPEED = 4.0      # prędkość kątowa – pełny obrót w ~1.5 s, responsywne sterowanie
MAX_SPEED = 350.0    # limit prędkości – wystarczająco szybko, żeby było dynamicznie
BRAKE_FORCE = 600.0  # hamulec awaryjny – ~4x silniejszy od tarcia, gwałtowne zatrzymanie

# Wierzchołki statku w układzie lokalnym (nos ku górze ekranu = -Y)
SHIP_VERTS = [(0, -18), (-12, 12), (12, 12)]

# Wierzchołki płomienia w układzie lokalnym
FLAME_VERTS = [(-7, 12), (0, 28), (7, 12)]

DEBUG = False

KEY_LEFT = 263
KEY_RIGHT = 262
KEY_UP = 265
KEY_Z = 90


def _vec2(x, y):
    v = ffi.new("Vector2 *")
    v.x = x
    v.y = y
    return v[0]


def _rotate(px, py, angle):
    #Obrót punktu (px, py) o kąt angle wokół (0,0)
    c = math.cos(angle)
    s = math.sin(angle)
    return px * c - py * s, px * s + py * c


class Ship:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.thrusting = False

    # logika

    def update(self, dt):
        # Obrót
        if rl.IsKeyDown(KEY_LEFT):
            self.angle -= ROT_SPEED * dt
        if rl.IsKeyDown(KEY_RIGHT):
            self.angle += ROT_SPEED * dt

        # Ciąg
        self.thrusting = rl.IsKeyDown(KEY_UP)
        if self.thrusting:
            dir_x = math.sin(self.angle)
            dir_y = -math.cos(self.angle)
            self.vx += THRUST * dir_x * dt
            self.vy += THRUST * dir_y * dt

        # Hamulec awaryjny (Z)
        braking = rl.IsKeyDown(KEY_Z)

        # Tarcie / hamulec
        speed = math.hypot(self.vx, self.vy)
        if speed > 0:
            fric = BRAKE_FORCE if braking else FRICTION
            decel = fric * dt
            if decel >= speed:
                self.vx = 0.0
                self.vy = 0.0
            else:
                factor = (speed - decel) / speed
                self.vx *= factor
                self.vy *= factor

        # Clamp prędkości
        speed = math.hypot(self.vx, self.vy)
        if speed > MAX_SPEED:
            factor = MAX_SPEED / speed
            self.vx *= factor
            self.vy *= factor

        # Pozycja
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Odbijanie od krawędzi
        if self.x < 0:
            self.x = 0
            self.vx = -self.vx
        elif self.x > 800:
            self.x = 800
            self.vx = -self.vx
        if self.y < 0:
            self.y = 0
            self.vy = -self.vy
        elif self.y > 600:
            self.y = 600
            self.vy = -self.vy

    # rysowanie

    def _transformed(self, verts):
        result = []
        for px, py in verts:
            rx, ry = _rotate(px, py, self.angle)
            result.append((self.x + rx, self.y + ry))
        return result

    def draw(self):
        pts = self._transformed(SHIP_VERTS)
        rl.DrawTriangleLines(
            _vec2(pts[0][0], pts[0][1]),
            _vec2(pts[1][0], pts[1][1]),
            _vec2(pts[2][0], pts[2][1]),
            colors.RAYWHITE,
        )

        # Płomień
        if self.thrusting:
            fp = self._transformed(FLAME_VERTS)
            rl.DrawTriangleLines(
                _vec2(fp[0][0], fp[0][1]),
                _vec2(fp[1][0], fp[1][1]),
                _vec2(fp[2][0], fp[2][1]),
                colors.ORANGE,
            )

        # Diagnostyka
        if DEBUG:
            speed = math.hypot(self.vx, self.vy)
            scale = 0.3
            ex = self.x + self.vx * scale
            ey = self.y + self.vy * scale
            rl.DrawLine(int(self.x), int(self.y), int(ex), int(ey), colors.GREEN)
            rl.DrawText(f"v={speed:.1f}".encode(), 10, 10, 18, colors.GRAY)