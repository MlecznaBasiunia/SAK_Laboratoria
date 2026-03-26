from raylib import rl, colors
from ship import Ship

SCREEN_W = 800
SCREEN_H = 600

rl.InitWindow(SCREEN_W, SCREEN_H, b"PG_Lab 05 - Asteroids: Statek")
rl.SetTargetFPS(144)

ship = Ship(SCREEN_W // 2, SCREEN_H // 2)

while not rl.WindowShouldClose():
    dt = rl.GetFrameTime()
    ship.update(dt)

    rl.BeginDrawing()
    rl.ClearBackground(colors.BLACK)
    ship.draw()
    rl.EndDrawing()

rl.CloseWindow()