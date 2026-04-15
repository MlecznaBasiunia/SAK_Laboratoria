from raylib import rl
from config import SCREEN_W, SCREEN_H, TARGET_FPS, SCORES_FILE
from resources import Resources
from scoring import load_best, save_best
from game import Game

# ---- Inicjalizacja ----
rl.InitWindow(SCREEN_W, SCREEN_H, b"Lab 08 - Asteroids")
rl.SetTargetFPS(TARGET_FPS)
rl.InitAudioDevice()

resources = Resources()
game = Game(resources, best=load_best(SCORES_FILE))
last_best = game.best

# ---- Pętla gry ----
while not rl.WindowShouldClose():
    dt = rl.GetFrameTime()

    game.update(dt)

    # Zapis wyniku po pobiciu (Zad. **)
    if game.best > last_best:
        save_best(SCORES_FILE, game.best)
        last_best = game.best

    rl.BeginDrawing()
    game.draw()
    rl.EndDrawing()

# ---- Zwalnianie zasobów ----
resources.unload()
rl.CloseAudioDevice()
rl.CloseWindow()
