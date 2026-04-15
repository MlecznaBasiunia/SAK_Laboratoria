from enum import Enum
from raylib import rl, colors

from config import (SCREEN_W, SCREEN_H, BULLET_LIMIT, EXPLOSION_SCALE,
                    WAVE_INITIAL, WAVE_INCREMENT, WAVE_DELAY,
                    HUD_FONT, HUD_MARGIN, TITLE_FONT, SUBTITLE_FONT,
                    KEY_SPACE, KEY_ENTER, KEY_R)
from utils import circles_collide, prune
from ship import Ship
from asteroid import spawn_wave
from bullet import Bullet
from explosion import Explosion


class State(Enum):
    MENU = "menu"
    GAME = "game"
    GAME_OVER = "game_over"


class Game:
    """Stan gry – wszystkie zmienne w jednym miejscu, FSM dispatchuje per stan."""

    def __init__(self, resources, best=0):
        self.resources = resources
        self.best = best
        self.state = State.MENU
        self.victory = False
        self._init_game()

    def _init_game(self):
        self.ship = Ship(SCREEN_W // 2, SCREEN_H // 2)
        self.asteroids = spawn_wave(WAVE_INITIAL)
        self.bullets = []
        self.explosions = []
        self.score = 0
        self.wave = 1
        self.wave_timer = 0.0
        self.victory = False

    # =====================================================
    # MENU
    # =====================================================

    def update_menu(self, dt):
        if rl.IsKeyPressed(KEY_ENTER) or rl.IsKeyPressed(KEY_SPACE):
            self._init_game()
            self.state = State.GAME

    def draw_menu(self):
        self.resources.draw_background()
        _draw_centered("ASTEROIDS", SCREEN_H // 2 - 80, TITLE_FONT, colors.RAYWHITE)
        _draw_centered("ENTER / SPACE - start", SCREEN_H // 2 + 10, SUBTITLE_FONT, colors.GRAY)
        _draw_centered(f"Best: {self.best}", SCREEN_H // 2 + 50, SUBTITLE_FONT, colors.YELLOW)
        _draw_centered("Strzaly: SPACE   Ruch: <- -> ^   Hamulec: Z",
                       SCREEN_H - 40, HUD_FONT, colors.DARKGRAY)

    # =====================================================
    # GAME
    # =====================================================

    def update_game(self, dt):
        # Wejście – strzał
        if rl.IsKeyPressed(KEY_SPACE) and len(self.bullets) < BULLET_LIMIT:
            nx, ny = self.ship.nose_position()
            self.bullets.append(Bullet(nx, ny, self.ship.angle))
            self.resources.play_shoot()

        # Update obiektów
        self.ship.update(dt)
        self.ship.do_wrap()

        for asteroid in self.asteroids:
            asteroid.update(dt)
            asteroid.do_wrap()
        for bullet in self.bullets:
            bullet.update(dt)
        for explosion in self.explosions:
            explosion.update(dt)

        # Kolizje
        self._check_bullet_asteroid_collisions()
        if self._check_ship_asteroid_collision():
            return  # przeszliśmy do GAME_OVER

        # Czyszczenie
        self.bullets = prune(self.bullets)
        self.asteroids = prune(self.asteroids)
        self.explosions = prune(self.explosions)

        # Zwycięstwo / nowa fala (Zad. *)
        if not self.asteroids:
            self.wave_timer += dt
            if self.wave_timer >= WAVE_DELAY:
                self.wave += 1
                self.asteroids = spawn_wave(WAVE_INITIAL + (self.wave - 1) * WAVE_INCREMENT)
                self.wave_timer = 0.0

    def _check_bullet_asteroid_collisions(self):
        """Oznacza trafione obiekty jako alive=False, dodaje punkty i splity."""
        new_asteroids = []
        for bullet in self.bullets:
            if not bullet.alive:
                continue
            for asteroid in self.asteroids:
                if not asteroid.alive:
                    continue
                if circles_collide(bullet.x, bullet.y, bullet.radius,
                                   asteroid.x, asteroid.y, asteroid.radius):
                    bullet.alive = False
                    asteroid.alive = False
                    self.score += asteroid.score_value
                    self.explosions.append(
                        Explosion(asteroid.x, asteroid.y, asteroid.radius * EXPLOSION_SCALE)
                    )
                    new_asteroids.extend(asteroid.split())
                    self.resources.play_explode()
                    break
        self.asteroids.extend(new_asteroids)

    def _check_ship_asteroid_collision(self):
        """Zwraca True i przechodzi do GAME_OVER gdy statek został trafiony."""
        for asteroid in self.asteroids:
            if not asteroid.alive:
                continue
            if circles_collide(self.ship.x, self.ship.y, self.ship.radius,
                               asteroid.x, asteroid.y, asteroid.radius):
                self.explosions.append(Explosion(self.ship.x, self.ship.y, 50))
                self.resources.play_explode()
                self._end_game(victory=False)
                return True
        return False

    def _end_game(self, victory):
        self.victory = victory
        if self.score > self.best:
            self.best = self.score
        self.state = State.GAME_OVER

    def draw_game(self):
        self.resources.draw_background()

        for asteroid in self.asteroids:
            asteroid.draw()
        for bullet in self.bullets:
            bullet.draw()
        self.ship.draw()
        for explosion in self.explosions:
            explosion.draw()

        self._draw_hud()

    def _draw_hud(self):
        rl.DrawText(f"Score: {self.score}".encode(),
                    HUD_MARGIN, HUD_MARGIN, HUD_FONT, colors.RAYWHITE)
        rl.DrawText(f"Best: {self.best}".encode(),
                    HUD_MARGIN, HUD_MARGIN + HUD_FONT + 4, HUD_FONT, colors.YELLOW)

        wave_text = f"Wave: {self.wave}".encode()
        text_w = rl.MeasureText(wave_text, HUD_FONT)
        rl.DrawText(wave_text, SCREEN_W - text_w - HUD_MARGIN, HUD_MARGIN,
                    HUD_FONT, colors.SKYBLUE)

    # =====================================================
    # GAME_OVER
    # =====================================================

    def update_gameover(self, dt):
        if rl.IsKeyPressed(KEY_R) or rl.IsKeyPressed(KEY_ENTER):
            self.state = State.MENU

    def draw_gameover(self):
        self.resources.draw_background()
        # Tło częściowo zaciemnione przez ostatnią klatkę
        if self.victory:
            _draw_centered("VICTORY", SCREEN_H // 2 - 80, TITLE_FONT, colors.GREEN)
        else:
            _draw_centered("GAME OVER", SCREEN_H // 2 - 80, TITLE_FONT, colors.RED)

        _draw_centered(f"Score: {self.score}", SCREEN_H // 2, SUBTITLE_FONT, colors.RAYWHITE)
        _draw_centered(f"Best: {self.best}", SCREEN_H // 2 + 32, SUBTITLE_FONT, colors.YELLOW)
        _draw_centered("R / ENTER - menu", SCREEN_H // 2 + 80, HUD_FONT, colors.GRAY)

    # =====================================================
    # Dispatcher
    # =====================================================

    def update(self, dt):
        if self.state == State.MENU:
            self.update_menu(dt)
        elif self.state == State.GAME:
            self.update_game(dt)
        elif self.state == State.GAME_OVER:
            self.update_gameover(dt)

    def draw(self):
        if self.state == State.MENU:
            self.draw_menu()
        elif self.state == State.GAME:
            self.draw_game()
        elif self.state == State.GAME_OVER:
            self.draw_gameover()


def _draw_centered(text, y, font_size, color):
    text_bytes = text.encode()
    text_w = rl.MeasureText(text_bytes, font_size)
    rl.DrawText(text_bytes, (SCREEN_W - text_w) // 2, y, font_size, color)
