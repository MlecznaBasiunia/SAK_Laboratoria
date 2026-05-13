import math
import random
from raylib import rl
from config import (SCREEN_W, SCREEN_H, BOSS_BEHEMOTH_HP, BOSS_BEHEMOTH_RADIUS,
                    BOSS_QUEEN_HP, BOSS_QUEEN_RADIUS, BOSS_QUEEN_SPAWN_INTERVAL,
                    BOSS_MIRROR_HP, SHIP_VERTS)
from utils import (vec2, color, rotate, ghost_positions_topo, torus_direction,
                   apply_wrap)
from bullet import Bullet


class Boss:
    """Bazowa klasa bossa."""
    def __init__(self, boss_type, wave_num):
        self.boss_type = boss_type
        self.alive = True
        self.time = 0.0
        self.portal_cooldown = 0.0

    def update(self, dt, ship_x, ship_y):
        pass

    def draw(self):
        pass

    def take_hit(self):
        self.hp -= 1
        return self.hp <= 0


class Behemoth(Boss):
    """Gigantyczna asteroida z warstwami HP."""
    def __init__(self, wave_num):
        super().__init__("behemoth", wave_num)
        self.hp = BOSS_BEHEMOTH_HP + wave_num * 2
        self.max_hp = self.hp
        self.radius = BOSS_BEHEMOTH_RADIUS
        self.x = random.choice([100, SCREEN_W - 100])
        self.y = random.uniform(200, SCREEN_H - 200)
        self.vx = random.uniform(-20, 20)
        self.vy = random.uniform(-20, 20)
        self.angle = 0.0
        self.rot_speed = 0.3
        self.points = 2000

        # Warstwy: co utrata 30% HP zrzuca asteroidy
        self.layer_thresholds = [0.7, 0.4, 0.15]
        self.layers_shed = 0

        # Proceduralne wierzcholki
        self.verts = []
        num = 14
        for i in range(num):
            a = math.tau * i / num
            r = self.radius * (1.0 + random.uniform(-0.3, 0.3))
            self.verts.append((math.cos(a) * r, math.sin(a) * r))

    def update(self, dt, ship_x, ship_y):
        self.time += dt
        self.portal_cooldown = max(0, self.portal_cooldown - dt)
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.rot_speed * dt
        apply_wrap(self)

        # Lekkie podazanie za graczem
        dx, dy = torus_direction(self.x, self.y, ship_x, ship_y)
        dist = math.hypot(dx, dy)
        if dist > 10:
            self.vx += (dx / dist) * 15 * dt
            self.vy += (dy / dist) * 15 * dt

        speed = math.hypot(self.vx, self.vy)
        if speed > 50:
            self.vx = self.vx / speed * 50
            self.vy = self.vy / speed * 50

    def should_shed_layer(self):
        """Sprawdza czy nalezy zrzucic warstwe. Zwraca True jesli tak."""
        hp_frac = self.hp / self.max_hp
        if self.layers_shed < len(self.layer_thresholds):
            if hp_frac <= self.layer_thresholds[self.layers_shed]:
                self.layers_shed += 1
                self.radius = max(40, self.radius - 10)
                return True
        return False

    def draw(self):
        hp_frac = self.hp / self.max_hp
        for gx, gy, mirror in ghost_positions_topo(self.x, self.y, self.radius):
            draw_angle = -self.angle if mirror else self.angle
            # Kolory zmieniaja sie z HP
            r = int(255 * (1 - hp_frac) + 150 * hp_frac)
            g = int(80 * hp_frac)
            b = int(50)
            n = len(self.verts)
            col = color(r, g, b)
            for i in range(n):
                x1, y1 = rotate(self.verts[i][0], self.verts[i][1], draw_angle)
                x2, y2 = rotate(self.verts[(i + 1) % n][0], self.verts[(i + 1) % n][1], draw_angle)
                rl.DrawLineV(vec2(gx + x1, gy + y1), vec2(gx + x2, gy + y2), col)

            # Wewnetrzne warstwy
            for layer in range(self.layers_shed, 3):
                lr = self.radius * (0.4 + layer * 0.15)
                a = int(60 - layer * 15)
                rl.DrawCircleLines(int(gx), int(gy), lr, color(r, g, b, a))

            # "Jadro"
            core_r = 10 + 3 * math.sin(self.time * 4)
            rl.DrawCircleV(vec2(gx, gy), core_r, color(255, 50, 0, 80))


class SwarmQueen(Boss):
    """Spawnuje male asteroidy non-stop."""
    def __init__(self, wave_num):
        super().__init__("queen", wave_num)
        self.hp = BOSS_QUEEN_HP + wave_num
        self.max_hp = self.hp
        self.radius = BOSS_QUEEN_RADIUS
        self.x = SCREEN_W / 2
        self.y = 100
        self.vx = random.uniform(-40, 40)
        self.vy = random.uniform(-40, 40)
        self.angle = 0.0
        self.rot_speed = 1.0
        self.points = 2500
        self.spawn_timer = BOSS_QUEEN_SPAWN_INTERVAL
        self.portal_cooldown = 0.0

    def update(self, dt, ship_x, ship_y):
        self.time += dt
        self.portal_cooldown = max(0, self.portal_cooldown - dt)

        # Ruch erratyczny
        self.vx += random.uniform(-80, 80) * dt
        self.vy += random.uniform(-80, 80) * dt
        speed = math.hypot(self.vx, self.vy)
        if speed > 80:
            self.vx = self.vx / speed * 80
            self.vy = self.vy / speed * 80

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.rot_speed * dt
        apply_wrap(self)
        self.spawn_timer -= dt

    def should_spawn(self):
        if self.spawn_timer <= 0:
            self.spawn_timer = BOSS_QUEEN_SPAWN_INTERVAL * (0.5 + 0.5 * self.hp / self.max_hp)
            return True
        return False

    def draw(self):
        for gx, gy, mirror in ghost_positions_topo(self.x, self.y, self.radius):
            draw_angle = -self.angle if mirror else self.angle
            # Ksztalt: szesciokatna "krolowa"
            col = color(255, 180, 0)
            segments = 8
            for i in range(segments):
                a1 = draw_angle + math.tau * i / segments
                a2 = draw_angle + math.tau * (i + 1) / segments
                r1 = self.radius * (1.0 + 0.2 * math.sin(self.time * 3 + i))
                r2 = self.radius * (1.0 + 0.2 * math.sin(self.time * 3 + i + 1))
                x1 = gx + math.cos(a1) * r1
                y1 = gy + math.sin(a1) * r1
                x2 = gx + math.cos(a2) * r2
                y2 = gy + math.sin(a2) * r2
                rl.DrawLineV(vec2(x1, y1), vec2(x2, y2), col)

            # Wewnetrzne oko
            rl.DrawCircleV(vec2(gx, gy), 8, color(255, 100, 0, 100))
            rl.DrawCircleV(vec2(gx, gy), 4, color(255, 200, 0))


class MirrorLord(Boss):
    """Duplikat statku gracza z opoznieniem."""
    def __init__(self, wave_num, ship_x, ship_y, ship_angle):
        super().__init__("mirror_lord", wave_num)
        self.hp = BOSS_MIRROR_HP + wave_num
        self.max_hp = self.hp
        self.x = (ship_x + SCREEN_W / 2) % SCREEN_W
        self.y = (ship_y + SCREEN_H / 2) % SCREEN_H
        self.vx = 0.0
        self.vy = 0.0
        self.angle = ship_angle + math.pi
        self.radius = 16
        self.points = 3000
        self.shoot_timer = 2.0
        self.target_history = []
        self.delay = 1.0
        self.portal_cooldown = 0.0
        # Fazy tarczy
        self.shield_active = True
        self.shield_timer = 3.0

    def update(self, dt, ship_x, ship_y):
        self.time += dt
        self.portal_cooldown = max(0, self.portal_cooldown - dt)

        self.target_history.append((self.time, ship_x, ship_y))
        while self.target_history and self.target_history[0][0] < self.time - self.delay - 0.1:
            self.target_history.pop(0)

        delayed_x, delayed_y = ship_x, ship_y
        for t, tx, ty in self.target_history:
            if t >= self.time - self.delay:
                delayed_x, delayed_y = tx, ty
                break

        dx, dy = torus_direction(self.x, self.y, delayed_x, delayed_y)
        dist = math.hypot(dx, dy)
        if dist > 30:
            nx, ny = dx / dist, dy / dist
            self.vx += nx * 250 * dt
            self.vy += ny * 250 * dt

        spd = math.hypot(self.vx, self.vy)
        if spd > 180:
            self.vx = self.vx / spd * 180
            self.vy = self.vy / spd * 180

        self.x += self.vx * dt
        self.y += self.vy * dt
        apply_wrap(self)

        if dist > 5:
            self.angle = math.atan2(dx, -dy)

        self.shoot_timer -= dt

        # Shield cyklicznie
        self.shield_timer -= dt
        if self.shield_timer <= 0:
            self.shield_active = not self.shield_active
            self.shield_timer = 3.0 if self.shield_active else 4.0

    def take_hit(self):
        if self.shield_active:
            return False
        self.hp -= 1
        return self.hp <= 0

    def try_shoot(self, ship_x, ship_y):
        if self.shoot_timer > 0:
            return None
        self.shoot_timer = 1.0
        dx, dy = torus_direction(self.x, self.y, ship_x, ship_y)
        angle = math.atan2(dx, -dy) + random.uniform(-0.15, 0.15)
        b = Bullet(self.x, self.y, angle)
        b.lifetime = 2.0
        return b

    def draw(self):
        for gx, gy, mirror in ghost_positions_topo(self.x, self.y, self.radius):
            draw_angle = -self.angle if mirror else self.angle
            pulse = 0.5 + 0.5 * math.sin(self.time * 6)
            col = color(255, int(50 * pulse), 255, int(200 + 55 * pulse))

            pts = []
            for px, py in SHIP_VERTS:
                rx, ry = rotate(px * 1.3, py * 1.3, draw_angle)
                pts.append((gx + rx, gy + ry))
            rl.DrawTriangleLines(
                vec2(pts[0][0], pts[0][1]),
                vec2(pts[1][0], pts[1][1]),
                vec2(pts[2][0], pts[2][1]),
                col,
            )
            # Glitch
            offset = 4 * math.sin(self.time * 10)
            for i in range(3):
                pts[i] = (pts[i][0] + offset, pts[i][1])
            rl.DrawTriangleLines(
                vec2(pts[0][0], pts[0][1]),
                vec2(pts[1][0], pts[1][1]),
                vec2(pts[2][0], pts[2][1]),
                color(255, 0, 255, 40),
            )
            # Shield
            if self.shield_active:
                rl.DrawCircleLines(int(gx), int(gy), self.radius + 5,
                                   color(255, 100, 255, int(120 * pulse)))


def create_boss(wave_num, ship_x=600, ship_y=400, ship_angle=0):
    """Tworzy bossa na podstawie numeru fali."""
    boss_type = (wave_num // 5) % 3
    if boss_type == 0:
        return Behemoth(wave_num)
    elif boss_type == 1:
        return SwarmQueen(wave_num)
    else:
        return MirrorLord(wave_num, ship_x, ship_y, ship_angle)
