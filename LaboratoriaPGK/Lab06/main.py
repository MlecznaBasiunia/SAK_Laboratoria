from raylib import rl, colors
from config import SCREEN_W, SCREEN_H, ASTEROID_COUNT
from ship import Ship
from asteroid import spawn_asteroids

rl.InitWindow(SCREEN_W, SCREEN_H, b"Lab 06 - Asteroids: Topologia Swiata")
rl.SetTargetFPS(60)

ship = Ship(SCREEN_W // 2, SCREEN_H // 2)
asteroids = spawn_asteroids(ASTEROID_COUNT)

while not rl.WindowShouldClose():
    dt = rl.GetFrameTime()

    ship.update(dt)
    ship.do_wrap()

    for a in asteroids:
        a.update(dt)
        a.do_wrap()

    rl.BeginDrawing()
    rl.ClearBackground(colors.BLACK)

    ship.draw()
    for a in asteroids:
        a.draw()

    rl.EndDrawing()

rl.CloseWindow()
