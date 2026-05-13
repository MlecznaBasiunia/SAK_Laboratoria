import math
from raylib import rl, colors
from config import (THRUST, FRICTION, ROT_SPEED, MAX_SPEED, BRAKE_FORCE,
                    SHIP_VERTS, SHIP_SIZE, FLAME_VERTS, SHIP_RADIUS,
                    MAX_BULLETS, SHOOT_COOLDOWN, STRAFE_SPEED,
                    RESPAWN_INVULN_TIME, POWERUP_EFFECT_DURATION,
                    HEAT_THRUST_RATE, HEAT_SHOOT_RATE, HEAT_DECAY_RATE,
                    HEAT_OVERDRIVE, HEAT_OVERHEAT, HEAT_COOLDOWN_TIME,
                    MAX_MODULE_SLOTS, DEBUG)
from utils import (vec2, color, rotate, ghost_positions_topo, apply_wrap)
from bullet import Bullet

KEY_LEFT = 263
KEY_RIGHT = 262
KEY_UP = 265
KEY_DOWN = 264
KEY_Z = 90
KEY_SPACE = 32
KEY_X = 88
KEY_C = 67
KEY_A = 65
KEY_D = 68

# ── Ship Skins ──────────────────────────────────────────────────
# Each skin: (name, hull_verts, flame_verts, size)
# hull_verts — polygon vertices (0,-Y = nose direction)
# flame_verts — triangle behind the ship for thrust
SHIP_SKINS = [
    ("Classic",
     [(0, -18), (-12, 12), (12, 12)],
     [(-7, 12), (0, 28), (7, 12)],
     18),
    ("Arrow",
     [(0, -22), (-6, -6), (-14, 10), (0, 4), (14, 10), (6, -6)],
     [(-6, 10), (0, 24), (6, 10)],
     22),
    ("Diamond",
     [(0, -20), (-16, 0), (-6, 14), (6, 14), (16, 0)],
     [(-5, 14), (0, 28), (5, 14)],
     20),
    ("Falcon",
     [(0, -20), (-5, -10), (-16, 8), (-10, 14), (0, 8), (10, 14), (16, 8), (5, -10)],
     [(-8, 12), (0, 26), (8, 12)],
     20),
]

SKIN_NAMES = [s[0] for s in SHIP_SKINS]


class Ship:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.thrusting = False
        self.radius = SHIP_RADIUS
        self.ship_color = (255, 255, 255)  # RGB tuple, customizable per player
        self.ship_skin = 0  # index into SHIP_SKINS

        self.bullets = []
        self.shoot_cooldown = 0.0

        self.alive = True
        self.invuln_time = RESPAWN_INVULN_TIME
        self.invulnerable = True
        self.portal_cooldown = 0.0

        # Timed powerups
        self.multishot_time = 0.0
        self.rapidfire_time = 0.0
        self.speedboost_time = 0.0
        self.shield_hits = 0
        self.bouncing_time = 0.0
        self.homing_time = 0.0

        self.thrust_shield_timer = 0.0
        self.perks = set()
        self.alt_cooldown = 0.0

        # ---- Weapon modules ----
        self.modules = []  # list of module IDs, max MAX_MODULE_SLOTS

        # ---- Heat system ----
        self.heat = 0.0
        self.overheated = False
        self.overheat_cooldown = 0.0

        # ---- Mutations ----
        self.mutations = set()  # "strafe", "backfire", "evolved", "afterburner"

        # ---- Ship visual evolution ----
        self._apply_skin()  # sets ship_verts, ship_size, _flame_verts from skin

        # ---- Wrap counter (for score bonus) ----
        self.wrap_count = 0

    def _apply_skin(self):
        """Set ship_verts, ship_size and _flame_verts from current skin index."""
        idx = max(0, min(self.ship_skin, len(SHIP_SKINS) - 1))
        _, verts, flame, size = SHIP_SKINS[idx]
        self.ship_verts = list(verts)
        self.ship_size = size
        self._flame_verts = list(flame)

    def set_skin(self, idx):
        """Change ship skin (0..len(SHIP_SKINS)-1). Re-applies vertices."""
        self.ship_skin = max(0, min(idx, len(SHIP_SKINS) - 1))
        # If evolved mutation is active, don't override verts
        if "evolved" not in self.mutations:
            self._apply_skin()

    def reset(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.alive = True
        self.invuln_time = RESPAWN_INVULN_TIME
        self.invulnerable = True
        self.portal_cooldown = 0.0
        self.multishot_time = 0.0
        self.rapidfire_time = 0.0
        self.speedboost_time = 0.0
        self.shield_hits = 0
        self.bouncing_time = 0.0
        self.homing_time = 0.0
        self.thrust_shield_timer = 0.0
        self.alt_cooldown = 0.0
        self.heat = 0.0
        self.overheated = False
        self.overheat_cooldown = 0.0

    def add_module(self, mod_id):
        if mod_id in self.modules:
            return
        if len(self.modules) >= MAX_MODULE_SLOTS:
            self.modules.pop(0)
        self.modules.append(mod_id)

    def has_module(self, mod_id):
        return mod_id in self.modules

    def apply_powerup(self, kind):
        if kind == "multishot":
            self.multishot_time = POWERUP_EFFECT_DURATION
        elif kind == "shield":
            self.shield_hits = 2
        elif kind == "rapidfire":
            self.rapidfire_time = POWERUP_EFFECT_DURATION
        elif kind == "speedboost":
            self.speedboost_time = POWERUP_EFFECT_DURATION
        elif kind == "bouncing":
            self.bouncing_time = POWERUP_EFFECT_DURATION
        elif kind == "homing":
            self.homing_time = POWERUP_EFFECT_DURATION

    def apply_mutation(self, mut):
        self.mutations.add(mut)
        if mut == "evolved":
            # Wiecej wierzcholkow
            self.ship_verts = [(0, -20), (-8, -5), (-14, 12), (0, 6), (14, 12), (8, -5)]
            self.ship_size = 20
            self.shield_hits = max(self.shield_hits, 1)

    def take_hit(self):
        if self.invulnerable:
            return False
        if self.thrust_shield_timer > 0:
            return False
        if self.shield_hits > 0:
            self.shield_hits -= 1
            return False
        self.alive = False
        return True

    def _get_bullet_kind(self):
        if self.bouncing_time > 0 or "bouncing_perk" in self.perks or self.has_module("bounce"):
            return "bouncing"
        if self.homing_time > 0 or "homing_perk" in self.perks or self.has_module("homing"):
            return "homing"
        return "normal"

    def _make_bullet(self, angle, kind=None):
        if kind is None:
            kind = self._get_bullet_kind()
        b = Bullet(self.x, self.y, angle, kind=kind)
        # Apply module/perk pierce
        if "pierce" in self.perks or self.has_module("pierce"):
            b.pierce = True
        # Overdrive: bullets faster
        if self.heat >= HEAT_OVERDRIVE and not self.overheated:
            speed = math.hypot(b.vx, b.vy) * 1.3
            b.vx = math.sin(angle) * speed
            b.vy = -math.cos(angle) * speed
        return b

    def _key_down(self, key, inp=None):
        """Check if a key is held. Uses input_map dict if provided, else raylib."""
        if inp is not None:
            return inp.get(key, False)
        return bool(rl.IsKeyDown(key))

    def _key_pressed(self, key, inp=None):
        """Check if a key was just pressed this frame. Uses input_map if provided."""
        if inp is not None:
            return inp.get(('p', key), False)  # pressed keys stored as ('p', key)
        return bool(rl.IsKeyPressed(key))

    def update(self, dt, input_map=None):
        """Update ship. input_map: optional dict overriding keyboard reads (for co-op P2 / gamepad)."""
        if not self.alive:
            return []

        inp = input_map  # None = read keyboard directly

        # Invulnerability
        if self.invuln_time > 0:
            self.invuln_time -= dt
            self.invulnerable = self.invuln_time > 0
        else:
            self.invulnerable = False

        self.portal_cooldown = max(0, self.portal_cooldown - dt)

        # Timed powerups
        self.multishot_time = max(0, self.multishot_time - dt)
        self.rapidfire_time = max(0, self.rapidfire_time - dt)
        self.speedboost_time = max(0, self.speedboost_time - dt)
        self.bouncing_time = max(0, self.bouncing_time - dt)
        self.homing_time = max(0, self.homing_time - dt)
        self.alt_cooldown = max(0, self.alt_cooldown - dt)

        # ---- Heat decay ----
        if self.overheated:
            self.overheat_cooldown -= dt
            if self.overheat_cooldown <= 0:
                self.overheated = False
                self.heat = 0.3
        else:
            self.heat = max(0, self.heat - HEAT_DECAY_RATE * dt)

        # ---- Rotation ----
        if self._key_down(KEY_LEFT, inp):
            self.angle -= ROT_SPEED * dt
        if self._key_down(KEY_RIGHT, inp):
            self.angle += ROT_SPEED * dt

        # ---- Thrust ----
        thrust = THRUST
        max_spd = MAX_SPEED
        if self.speedboost_time > 0:
            thrust *= 1.5
            max_spd *= 1.4
        if self.heat >= HEAT_OVERDRIVE and not self.overheated:
            thrust *= 1.3
            max_spd *= 1.2

        can_thrust = not self.overheated
        self.thrusting = self._key_down(KEY_UP, inp) and can_thrust
        if self.thrusting:
            dir_x = math.sin(self.angle)
            dir_y = -math.cos(self.angle)
            self.vx += thrust * dir_x * dt
            self.vy += thrust * dir_y * dt
            self.heat = min(1.0, self.heat + HEAT_THRUST_RATE * dt)
            if "thrust_shield" in self.perks:
                self.thrust_shield_timer = 0.3
        else:
            if self.thrust_shield_timer > 0:
                self.thrust_shield_timer -= dt

        # Strafe (mutation)
        if "strafe" in self.mutations:
            strafe_dir = 0
            if self._key_down(KEY_A, inp):
                strafe_dir = -1
            elif self._key_down(KEY_D, inp):
                strafe_dir = 1
            if strafe_dir != 0 and can_thrust:
                sx = math.cos(self.angle) * strafe_dir
                sy = math.sin(self.angle) * strafe_dir
                self.vx += sx * STRAFE_SPEED * dt
                self.vy += sy * STRAFE_SPEED * dt
                self.heat = min(1.0, self.heat + HEAT_THRUST_RATE * 0.5 * dt)

        # Brake (Z)
        braking = self._key_down(KEY_Z, inp)
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

        speed = math.hypot(self.vx, self.vy)
        if speed > max_spd:
            factor = max_spd / speed
            self.vx *= factor
            self.vy *= factor

        self.x += self.vx * dt
        self.y += self.vy * dt

        # ---- Overheat check ----
        if self.heat >= HEAT_OVERHEAT and not self.overheated:
            self.overheated = True
            self.overheat_cooldown = HEAT_COOLDOWN_TIME

        # ---- Shooting ----
        new_bullets = []
        can_shoot = not self.overheated
        self.shoot_cooldown = max(0, self.shoot_cooldown - dt)

        rapid = self.rapidfire_time > 0 or self.has_module("rapid")
        cooldown = SHOOT_COOLDOWN * (0.4 if rapid else 1.0)
        max_b = MAX_BULLETS * (2 if rapid else 1)

        split = self.multishot_time > 0 or self.has_module("split")

        if (self._key_down(KEY_SPACE, inp) and self.shoot_cooldown <= 0
                and len(self.bullets) < max_b and can_shoot):
            self.shoot_cooldown = cooldown
            self.heat = min(1.0, self.heat + HEAT_SHOOT_RATE)

            if split:
                for offset in [-0.15, 0.0, 0.15]:
                    b = self._make_bullet(self.angle + offset)
                    new_bullets.append(b)
                    self.bullets.append(b)
            else:
                b = self._make_bullet(self.angle)
                new_bullets.append(b)
                self.bullets.append(b)

            # Backfire mutation
            if "backfire" in self.mutations:
                b = self._make_bullet(self.angle + math.pi)
                b.is_backfire = True
                new_bullets.append(b)
                self.bullets.append(b)

        # Alt-fire: Gravity bomb (X)
        if (("gravity_shot" in self.perks or self.has_module("gravity"))
                and self._key_pressed(KEY_X, inp) and self.alt_cooldown <= 0 and can_shoot):
            self.alt_cooldown = 2.0
            b = self._make_bullet(self.angle, kind="gravity_bomb")
            new_bullets.append(b)
            self.bullets.append(b)

        # Alt-fire: Hyperspace (C)
        if (("hyperspace_shot" in self.perks or self.has_module("hyper"))
                and self._key_pressed(KEY_C, inp) and self.alt_cooldown <= 0 and can_shoot):
            self.alt_cooldown = 1.5
            b = self._make_bullet(self.angle, kind="hyperspace")
            new_bullets.append(b)
            self.bullets.append(b)

        # Update bullets
        for b in self.bullets:
            b.update(dt)
        self.bullets = [b for b in self.bullets if b.alive]

        return new_bullets

    def do_wrap(self):
        if self.alive:
            crossed = apply_wrap(self)
            if crossed:
                self.wrap_count += 1

    # ---- Drawing ----

    def _draw_at(self, cx, cy, mirror=False):
        cr, cg, cb = self.ship_color
        if self.invulnerable and int(self.invuln_time * 10) % 2 == 0:
            col = color(min(255, cr // 2 + 50), min(255, cg // 2 + 50), 255, 120)
        else:
            col = color(cr, cg, cb)

        # Heat color — blend toward red/orange
        if self.heat > 0.3:
            intensity = (self.heat - 0.3) / 0.7
            col = color(255, int(cg * (1 - intensity * 0.6)), int(cb * (1 - intensity)))

        # Overheated: flash red
        if self.overheated:
            flash = int(self.overheat_cooldown * 8) % 2
            col = color(255, 50, 50) if flash else color(150, 30, 30)

        # Speed distortion
        speed = math.hypot(self.vx, self.vy)
        if speed > MAX_SPEED * 0.8:
            intensity = (speed - MAX_SPEED * 0.8) / (MAX_SPEED * 0.4)
            col = color(int(cr - 50 * intensity), int(max(0, cg - 100 * intensity)), min(255, cb + int(50 * intensity)))

        draw_angle = -self.angle if mirror else self.angle
        verts = self.ship_verts

        pts = []
        for px, py in verts:
            rx, ry = rotate(px, py, draw_angle)
            pts.append((cx + rx, cy + ry))

        n = len(pts)
        for i in range(n):
            rl.DrawLineV(vec2(pts[i][0], pts[i][1]),
                         vec2(pts[(i + 1) % n][0], pts[(i + 1) % n][1]), col)

        if self.thrusting:
            fp = []
            flame = getattr(self, '_flame_verts', FLAME_VERTS)
            for px, py in flame:
                rx, ry = rotate(px, py, draw_angle)
                fp.append((cx + rx, cy + ry))
            flame_col = color(255, 150, 0)
            if self.heat > 0.5:
                flame_col = color(255, int(80 + 170 * (1 - self.heat)), 0)
            rl.DrawTriangleLines(
                vec2(fp[0][0], fp[0][1]),
                vec2(fp[1][0], fp[1][1]),
                vec2(fp[2][0], fp[2][1]),
                flame_col,
            )

        # Shield
        if self.shield_hits > 0:
            alpha = 150 if self.shield_hits >= 2 else 80
            rl.DrawCircleLines(int(cx), int(cy), 22, color(0, 255, 100, alpha))
        if self.thrust_shield_timer > 0:
            a = int(100 * (self.thrust_shield_timer / 0.3))
            rl.DrawCircleLines(int(cx), int(cy), 20, color(0, 255, 150, a))

    def draw(self):
        if not self.alive:
            return

        # Relativistic smear at high speed
        speed = math.hypot(self.vx, self.vy)
        if speed > MAX_SPEED * 0.7:
            intensity = min(1, (speed - MAX_SPEED * 0.7) / (MAX_SPEED * 0.5))
            for i in range(1, 3):
                t = i * 0.008
                sx = self.x - self.vx * t
                sy = self.y - self.vy * t
                a = int(40 * intensity * (1 - i * 0.3))
                for gx, gy, m in ghost_positions_topo(sx, sy, self.ship_size):
                    # Ghost smear
                    draw_angle = -self.angle if m else self.angle
                    pts = []
                    for px, py in self.ship_verts:
                        rx, ry = rotate(px, py, draw_angle)
                        pts.append((gx + rx, gy + ry))
                    smear_col = color(200, 200, 255, a)
                    np = len(pts)
                    for j in range(np):
                        rl.DrawLineV(vec2(pts[j][0], pts[j][1]),
                                     vec2(pts[(j + 1) % np][0], pts[(j + 1) % np][1]),
                                     smear_col)

        for gx, gy, mirror in ghost_positions_topo(self.x, self.y, self.ship_size):
            self._draw_at(gx, gy, mirror)

        for b in self.bullets:
            b.draw()

        if DEBUG:
            speed = math.hypot(self.vx, self.vy)
            rl.DrawText(f"v={speed:.1f}".encode(), 10, 10, 18, colors.GRAY)
