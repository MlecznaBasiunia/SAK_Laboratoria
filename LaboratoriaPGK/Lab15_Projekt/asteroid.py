import math
import random
from raylib import rl
from config import (SCREEN_W, SCREEN_H, ASTEROID_SIZES,
                    ASTEROID_JITTER, ASTEROID_ROT_MIN, ASTEROID_ROT_MAX,
                    ASTEROID_SPECIAL_CHANCE, SAFE_SPAWN_RADIUS,
                    SWARM_RADIUS, SWARM_SPEED, CRYSTAL_HP)
from utils import (vec2, color, rotate, ghost_positions, ghost_positions_topo,
                   dist_wrapped, torus_direction, apply_wrap)

SPECIAL_COLORS = {
    "normal":    (255, 255, 255),
    "explosive": (255, 100, 50),
    "fast":      (200, 200, 255),
    "spiky":     (255, 50, 50),
    "ice":       (100, 220, 255),
    "splitter":  (255, 200, 0),
    "magnetic":  (200, 0, 255),
    "ghost":     (100, 100, 150),
    "growing":   (100, 255, 100),
    "chain":     (255, 120, 0),
    "crystal":   (0, 255, 255),
    "parasite":  (180, 255, 0),
    "virus":     (255, 0, 100),
}

ALL_SPECIALS = list(SPECIAL_COLORS.keys())
ALL_SPECIALS.remove("normal")

# Fakcje: kolory asteroid, ktore sie przyciagaja/odpychaja
FACTION_ATTRACT = {"ice", "magnetic", "crystal"}    # blue team - przyciaganie
FACTION_REPEL = {"explosive", "chain", "spiky", "virus"}  # red team - odpychanie

# Visual effect toggle (set from options)
SPEED_COLOR_ENABLED = True


class Asteroid:
    def __init__(self, x, y, size="large", special="normal", vx=None, vy=None):
        self.x = x
        self.y = y
        self.angle = 0.0
        self.special = special
        self.alive = True

        radius, spd_min, spd_max, num_verts = ASTEROID_SIZES[size]
        self.radius = radius
        self.size = size

        # Modyfikatory specjalnych typow
        if special == "fast":
            spd_min *= 2.0
            spd_max *= 2.0
            num_verts = max(5, num_verts - 3)
        elif special == "spiky":
            num_verts += 4
        elif special == "growing":
            if vx is None:
                self.size = "small"
                radius, spd_min, spd_max, num_verts = ASTEROID_SIZES["small"]
                self.radius = radius
        elif special == "magnetic":
            num_verts += 2
        elif special == "crystal":
            num_verts = 6  # hexagon
        elif special == "parasite":
            num_verts = 5
        elif special == "virus":
            num_verts += 3

        if vx is not None and vy is not None:
            self.vx = vx
            self.vy = vy
        else:
            speed = random.uniform(spd_min, spd_max)
            direction = random.uniform(0, math.tau)
            self.vx = math.cos(direction) * speed
            self.vy = math.sin(direction) * speed

        self.rot_speed = random.uniform(ASTEROID_ROT_MIN, ASTEROID_ROT_MAX)
        if random.random() < 0.5:
            self.rot_speed = -self.rot_speed

        jitter = ASTEROID_JITTER
        if special == "spiky": jitter = 0.7
        elif special == "ice": jitter = 0.15
        elif special == "ghost": jitter = 0.2
        elif special == "chain": jitter = 0.5
        elif special == "crystal": jitter = 0.05
        elif special == "virus": jitter = 0.6

        self.verts = []
        for i in range(num_verts):
            a = math.tau * i / num_verts
            r = radius * (1.0 + random.uniform(-jitter, jitter))
            self.verts.append((math.cos(a) * r, math.sin(a) * r))

        self.ice_timer = 0.0
        self.grow_timer = 0.0
        self.grow_interval = random.uniform(6.0, 10.0)
        self.portal_cooldown = 0.0
        self.time_alive = 0.0

        # Crystal: HP
        self.hp = CRYSTAL_HP if special == "crystal" else 1

        # Parasite: target
        self.parasite_target = None
        self.parasite_eat_timer = 0.0

        # Virus: infected timer
        self.infected = False
        self.infected_timer = 0.0

    def update(self, dt, time_scale=1.0):
        scaled_dt = dt * time_scale
        self.time_alive += dt
        self.portal_cooldown = max(0, self.portal_cooldown - dt)

        # Parasite: podaza za celem i go zjada
        if self.special == "parasite" and self.parasite_target and self.parasite_target.alive:
            target = self.parasite_target
            dx, dy = torus_direction(self.x, self.y, target.x, target.y)
            dist = math.hypot(dx, dy)
            if dist > 5:
                nx, ny = dx / dist, dy / dist
                self.vx += nx * 200 * scaled_dt
                self.vy += ny * 200 * scaled_dt
                spd = math.hypot(self.vx, self.vy)
                if spd > 150:
                    self.vx = self.vx / spd * 150
                    self.vy = self.vy / spd * 150
            if dist < target.radius + self.radius:
                self.parasite_eat_timer += scaled_dt
                if self.parasite_eat_timer > 2.0:
                    self.parasite_eat_timer = 0.0
                    # Zmniejsz cel
                    shrink = {"large": "medium", "medium": "small"}.get(target.size)
                    if shrink:
                        target.size = shrink
                        r, _, _, nv = ASTEROID_SIZES[shrink]
                        target.radius = r
                        target.verts = []
                        for i in range(nv):
                            a = math.tau * i / nv
                            rv = r * (1.0 + random.uniform(-0.3, 0.3))
                            target.verts.append((math.cos(a) * rv, math.sin(a) * rv))
                    else:
                        target.alive = False
                        # Parasite mutuje - rosnie
                        self._grow_parasite()

        # Virus: infected asteroidy staja sie agresywniejsze
        if self.infected:
            self.infected_timer += dt
            speed = math.hypot(self.vx, self.vy)
            if speed > 0:
                boost = 1.0 + 0.5 * min(1, self.infected_timer / 3)
                target_speed = speed * boost
                if target_speed > speed:
                    factor = min(target_speed / speed, 1.0 + dt)
                    self.vx *= factor
                    self.vy *= factor

        self.x += self.vx * scaled_dt
        self.y += self.vy * scaled_dt
        self.angle += self.rot_speed * scaled_dt

        if self.special == "ice":
            self.ice_timer += scaled_dt
            if self.ice_timer > 1.5:
                self.ice_timer = 0.0
                speed = math.hypot(self.vx, self.vy)
                new_dir = math.atan2(self.vy, self.vx) + random.uniform(-0.8, 0.8)
                self.vx = math.cos(new_dir) * speed
                self.vy = math.sin(new_dir) * speed

        if self.special == "growing":
            self.grow_timer += dt
            if self.grow_timer >= self.grow_interval:
                self.grow_timer = 0.0
                self._grow()

    def _grow(self):
        next_size = {"small": "medium", "medium": "large"}.get(self.size)
        if next_size is None:
            return
        self.size = next_size
        radius, _, _, num_verts = ASTEROID_SIZES[next_size]
        self.radius = radius
        self.verts = []
        for i in range(num_verts):
            a = math.tau * i / num_verts
            r = radius * (1.0 + random.uniform(-0.3, 0.3))
            self.verts.append((math.cos(a) * r, math.sin(a) * r))

    def _grow_parasite(self):
        """Parasite mutuje po zjedzeniu celu."""
        next_size = {"small": "medium", "medium": "large"}.get(self.size)
        if next_size:
            self.size = next_size
            radius, _, _, nv = ASTEROID_SIZES[next_size]
            self.radius = radius
            self.verts = []
            for i in range(nv):
                a = math.tau * i / nv
                r = radius * (1.0 + random.uniform(-0.4, 0.4))
                self.verts.append((math.cos(a) * r, math.sin(a) * r))

    def apply_faction_force(self, other, dt):
        """Symbioza: przyciaganie/odpychanie miedzy fakcjami."""
        my_faction = None
        if self.special in FACTION_ATTRACT:
            my_faction = "attract"
        elif self.special in FACTION_REPEL:
            my_faction = "repel"
        if my_faction is None:
            return

        other_faction = None
        if other.special in FACTION_ATTRACT:
            other_faction = "attract"
        elif other.special in FACTION_REPEL:
            other_faction = "repel"
        if other_faction is None:
            return

        dx, dy = torus_direction(self.x, self.y, other.x, other.y)
        dist = math.hypot(dx, dy)
        if dist < 10 or dist > 200:
            return

        # Sama fakcja: przyciaganie; rozne: odpychanie
        force_dir = 1.0 if my_faction == other_faction else -1.0
        strength = 3000 * force_dir / (dist * dist)
        nx, ny = dx / dist, dy / dist
        self.vx += nx * strength * dt
        self.vy += ny * strength * dt

    def apply_magnetic_force(self, objects, dt):
        if self.special != "magnetic":
            return
        strength = 8000
        for obj in objects:
            if obj is self:
                continue
            dx, dy = torus_direction(obj.x, obj.y, self.x, self.y)
            dist = math.hypot(dx, dy)
            if dist < 150 and dist > 5:
                force = strength / (dist * dist)
                nx, ny = dx / dist, dy / dist
                obj.vx += nx * force * dt
                obj.vy += ny * force * dt

    def do_wrap(self):
        apply_wrap(self)

    def take_hit(self):
        """Zwraca True jesli asteroida zniszczona."""
        self.hp -= 1
        return self.hp <= 0

    def split(self):
        if self.special == "splitter":
            count = random.randint(4, 6)
            children = []
            for i in range(count):
                kick_angle = math.tau * i / count + random.uniform(-0.3, 0.3)
                kick_speed = random.uniform(100, 180)
                nvx = math.cos(kick_angle) * kick_speed
                nvy = math.sin(kick_angle) * kick_speed
                children.append(Asteroid(self.x, self.y, "small", "normal", nvx, nvy))
            return children

        # Crystal nie splituje - po prostu znika
        if self.special == "crystal":
            return []

        next_size = {"large": "medium", "medium": "small"}.get(self.size)
        if next_size is None:
            return []

        children = []
        for _ in range(2):
            kick_angle = random.uniform(0, math.tau)
            kick_speed = random.uniform(30, 80)
            nvx = self.vx + math.cos(kick_angle) * kick_speed
            nvy = self.vy + math.sin(kick_angle) * kick_speed
            no_inherit = {"explosive", "chain", "splitter", "crystal", "parasite", "virus"}
            child_special = "normal" if self.special in no_inherit else self.special
            children.append(Asteroid(self.x, self.y, next_size, child_special, nvx, nvy))
        return children

    def _draw_at(self, cx, cy, mirror=False):
        n = len(self.verts)
        r, g, b = SPECIAL_COLORS.get(self.special, (255, 255, 255))
        alpha = 255

        if self.special == "ghost":
            pulse = 0.3 + 0.2 * math.sin(self.time_alive * 3)
            alpha = int(255 * pulse)
        if self.special == "growing" and self.grow_timer > self.grow_interval * 0.8:
            pulse = 0.5 + 0.5 * math.sin(self.time_alive * 10)
            alpha = int(200 * pulse + 55)
        if self.infected:
            r = int(r * 0.5 + 255 * 0.5)
            g = int(g * 0.3)
            b = int(b * 0.3)

        # Proceduralne kolory od predkosci
        if SPEED_COLOR_ENABLED:
            speed = math.hypot(self.vx, self.vy)
            if speed > 120:
                intensity = min(1, (speed - 120) / 200)
                r = int(r * (1 - intensity * 0.3) + 255 * intensity * 0.3)

        col = color(r, g, b, alpha)
        draw_angle = -self.angle if mirror else self.angle

        for i in range(n):
            x1, y1 = rotate(self.verts[i][0], self.verts[i][1], draw_angle)
            x2, y2 = rotate(self.verts[(i + 1) % n][0], self.verts[(i + 1) % n][1], draw_angle)
            rl.DrawLineV(vec2(cx + x1, cy + y1), vec2(cx + x2, cy + y2), col)

        if self.special == "magnetic":
            rl.DrawCircleLines(int(cx), int(cy), 150, color(200, 0, 255, 30))
        if self.special == "crystal":
            # Wewnetrzny blask
            inner = self.radius * 0.4
            rl.DrawCircleV(vec2(cx, cy), inner, color(0, 255, 255, 40 + int(20 * math.sin(self.time_alive * 4))))
            # HP indicator
            for i in range(self.hp):
                rl.DrawCircleV(vec2(cx - 8 + i * 6, cy + self.radius + 6), 2, color(0, 255, 255))
        if self.special == "parasite" and self.parasite_target and self.parasite_target.alive:
            # Linia do celu
            rl.DrawLineV(vec2(cx, cy), vec2(self.parasite_target.x, self.parasite_target.y),
                         color(180, 255, 0, 40))

    def draw(self):
        for gx, gy, mirror in ghost_positions_topo(self.x, self.y, self.radius):
            self._draw_at(gx, gy, mirror)


def spawn_asteroids(count, safe_x=None, safe_y=None, allowed_specials=None):
    if allowed_specials is None:
        allowed_specials = ALL_SPECIALS
    asteroids = []
    for _ in range(count):
        for _attempt in range(20):
            x = random.uniform(0, SCREEN_W)
            y = random.uniform(0, SCREEN_H)
            if safe_x is not None:
                dx = min(abs(x - safe_x), SCREEN_W - abs(x - safe_x))
                dy = min(abs(y - safe_y), SCREEN_H - abs(y - safe_y))
                if math.hypot(dx, dy) < SAFE_SPAWN_RADIUS:
                    continue
            break
        special = "normal"
        if random.random() < ASTEROID_SPECIAL_CHANCE and allowed_specials:
            special = random.choice(allowed_specials)
        asteroids.append(Asteroid(x, y, "large", special))

    # Podlacz pasożyty do losowych celów
    parasites = [a for a in asteroids if a.special == "parasite"]
    non_parasites = [a for a in asteroids if a.special != "parasite" and a.size == "large"]
    for p in parasites:
        if non_parasites:
            p.parasite_target = random.choice(non_parasites)

    return asteroids


def spawn_swarm(count, target_x, target_y):
    side = random.randint(0, 3)
    asteroids = []
    for i in range(count):
        if side == 0:
            x = random.uniform(SCREEN_W * 0.2, SCREEN_W * 0.8)
            y = -20 - i * 8
        elif side == 1:
            x = random.uniform(SCREEN_W * 0.2, SCREEN_W * 0.8)
            y = SCREEN_H + 20 + i * 8
        elif side == 2:
            x = -20 - i * 8
            y = random.uniform(SCREEN_H * 0.2, SCREEN_H * 0.8)
        else:
            x = SCREEN_W + 20 + i * 8
            y = random.uniform(SCREEN_H * 0.2, SCREEN_H * 0.8)

        dx, dy = torus_direction(x, y, target_x, target_y)
        dist = math.hypot(dx, dy)
        if dist > 0:
            dx, dy = dx / dist, dy / dist
        spread = random.uniform(-0.3, 0.3)
        ang = math.atan2(dy, dx) + spread
        spd = SWARM_SPEED * random.uniform(0.8, 1.2)
        vx = math.cos(ang) * spd
        vy = math.sin(ang) * spd

        a = Asteroid(x, y, "small", "fast", vx, vy)
        a.radius = SWARM_RADIUS
        a.verts = []
        for j in range(5):
            ang2 = math.tau * j / 5
            r = SWARM_RADIUS * (1.0 + random.uniform(-0.3, 0.3))
            a.verts.append((math.cos(ang2) * r, math.sin(ang2) * r))
        asteroids.append(a)
    return asteroids
