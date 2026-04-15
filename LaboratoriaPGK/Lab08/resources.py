import os
import random
from raylib import rl, colors
from config import (SOUND_SHOOT, SOUND_EXPLODE, TEXTURE_STARS,
                    SCREEN_W, SCREEN_H, STARS_COUNT)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _abs(path):
    return os.path.join(SCRIPT_DIR, path)


class Resources:
    """Kontener na załadowane zasoby. Wszystko opcjonalne – brak pliku
    nie crashuje gry, tylko wyłącza odpowiedni efekt."""

    def __init__(self):
        self.shoot_snd = self._load_sound(SOUND_SHOOT)
        self.explode_snd = self._load_sound(SOUND_EXPLODE)
        self.stars_tex = self._load_texture(TEXTURE_STARS)
        self.star_points = self._gen_stars() if self.stars_tex is None else None

    @staticmethod
    def _load_sound(path):
        full = _abs(path)
        if os.path.exists(full):
            return rl.LoadSound(full.encode())
        return None

    @staticmethod
    def _load_texture(path):
        full = _abs(path)
        if os.path.exists(full):
            return rl.LoadTexture(full.encode())
        return None

    @staticmethod
    def _gen_stars():
        return [
            (random.randint(0, SCREEN_W),
             random.randint(0, SCREEN_H),
             random.randint(1, 2))
            for _ in range(STARS_COUNT)
        ]

    def play_shoot(self):
        if self.shoot_snd is not None:
            rl.PlaySound(self.shoot_snd)

    def play_explode(self):
        if self.explode_snd is not None:
            rl.PlaySound(self.explode_snd)

    def draw_background(self):
        if self.stars_tex is not None:
            rl.DrawTexture(self.stars_tex, 0, 0, colors.WHITE)
        else:
            for sx, sy, sr in self.star_points:
                rl.DrawCircle(sx, sy, sr, colors.DARKGRAY)

    def unload(self):
        """Zwalnianie zasobów w odpowiedniej kolejności."""
        if self.stars_tex is not None:
            rl.UnloadTexture(self.stars_tex)
        if self.shoot_snd is not None:
            rl.UnloadSound(self.shoot_snd)
        if self.explode_snd is not None:
            rl.UnloadSound(self.explode_snd)
