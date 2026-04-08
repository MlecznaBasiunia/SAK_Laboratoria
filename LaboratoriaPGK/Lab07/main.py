import os
import random
from raylib import rl, colors

from config import (SCREEN_W, SCREEN_H, ASTEROID_COUNT,
                    BULLET_LIMIT, EXPLOSION_SCALE, STARS_COUNT,
                    SOUND_SHOOT, SOUND_EXPLODE, TEXTURE_STARS)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOUND_SHOOT = os.path.join(SCRIPT_DIR, SOUND_SHOOT)
SOUND_EXPLODE = os.path.join(SCRIPT_DIR, SOUND_EXPLODE)
TEXTURE_STARS = os.path.join(SCRIPT_DIR, TEXTURE_STARS)
from ship import Ship
from asteroid import spawn_asteroids
from bullet import Bullet
from explosion import Explosion
from utils import circles_collide

KEY_SPACE = 32

rl.InitWindow(SCREEN_W, SCREEN_H, b"Lab 07 - Asteroids: Pociski i Kolizje")
rl.SetTargetFPS(150)
rl.InitAudioDevice()

shoot_snd = None
explode_snd = None
if os.path.exists(SOUND_SHOOT):
    shoot_snd = rl.LoadSound(SOUND_SHOOT.encode())
if os.path.exists(SOUND_EXPLODE):
    explode_snd = rl.LoadSound(SOUND_EXPLODE.encode())

stars_tex = None
if os.path.exists(TEXTURE_STARS):
    stars_tex = rl.LoadTexture(TEXTURE_STARS.encode())

star_points = []
if stars_tex is None:
    for _ in range(STARS_COUNT):
        star_points.append((
            random.randint(0, SCREEN_W),
            random.randint(0, SCREEN_H),
            random.randint(1, 2),
        ))

ship = Ship(SCREEN_W // 2, SCREEN_H // 2)
asteroids = spawn_asteroids(ASTEROID_COUNT)
bullets = []
explosions = []

while not rl.WindowShouldClose():
    dt = rl.GetFrameTime()

    if rl.IsKeyPressed(KEY_SPACE) and len(bullets) < BULLET_LIMIT:
        nx, ny = ship.nose_position()
        bullets.append(Bullet(nx, ny, ship.angle))
        if shoot_snd is not None:
            rl.PlaySound(shoot_snd)

    ship.update(dt)
    ship.do_wrap()

    for a in asteroids:
        a.update(dt)
        a.do_wrap()

    for b in bullets:
        b.update(dt)

    for e in explosions:
        e.update(dt)

    for b in bullets:
        if not b.alive:
            continue
        for a in asteroids:
            if not a.alive:
                continue
            if circles_collide(b.x, b.y, b.radius, a.x, a.y, a.radius):
                b.alive = False
                a.alive = False
                explosions.append(Explosion(a.x, a.y, a.radius * EXPLOSION_SCALE))
                if explode_snd is not None:
                    rl.PlaySound(explode_snd)
                break

    for a in asteroids:
        if not a.alive:
            continue
        if circles_collide(ship.x, ship.y, ship.radius, a.x, a.y, a.radius):
            explosions.append(Explosion(ship.x, ship.y, 40))
            if explode_snd is not None:
                rl.PlaySound(explode_snd)
            ship.reset()
            break

    bullets = [b for b in bullets if b.alive]
    asteroids = [a for a in asteroids if a.alive]
    explosions = [e for e in explosions if e.alive]

    rl.BeginDrawing()
    rl.ClearBackground(colors.BLACK)

    if stars_tex is not None:
        rl.DrawTexture(stars_tex, 0, 0, colors.WHITE)
    else:
        for sx, sy, sr in star_points:
            rl.DrawCircle(sx, sy, sr, colors.DARKGRAY)

    for a in asteroids:
        a.draw()

    for b in bullets:
        b.draw()

    ship.draw()

    for e in explosions:
        e.draw()

    rl.EndDrawing()

if stars_tex is not None:
    rl.UnloadTexture(stars_tex)
if shoot_snd is not None:
    rl.UnloadSound(shoot_snd)
if explode_snd is not None:
    rl.UnloadSound(explode_snd)

rl.CloseAudioDevice()
rl.CloseWindow()
