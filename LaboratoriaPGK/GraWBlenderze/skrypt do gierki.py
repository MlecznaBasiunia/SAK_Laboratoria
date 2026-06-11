import bpy
import math
import random

# ---------------- KONFIGURACJA ----------------
LANES        = (-2.0, 0.0, 2.0)   # pozycje X trzech pasow
TILE_LEN     = 10.0               # dlugosc kafelka podlogi
N_TILES      = 12                 # ile kafelkow w puli (recykling)
BASE_SPEED   = 7.0                # m/s na starcie
SPEED_GAIN   = 0.15               # przyrost predkosci na sekunde
LANE_LERP    = 12.0               # szybkosc zmiany pasa
JUMP_V       = 6.5                # predkosc wybicia
GRAVITY      = -18.0
TICK         = 1.0 / 30.0         # krok symulacji (30 Hz)

COIN_Z       = 0.6
COIN_R       = 0.8                # promien zbierania monety
OBST_DY      = 0.65               # pol-glebokosc kolizji przeszkody
OBST_DX      = 0.95               # pol-szerokosc kolizji
OBST_TOP     = 0.9                # wysokosc przeszkody - nad nia mozna przeskoczyc

ANIM = {
    "Run":   (1, 20,  True),    # (start, koniec, loop?)
    "Idle":  (1, 40,  True),
    "Jump":  (1, 25,  False),
    "Death": (1, 30,  False),
}


def reset_pose(arm):
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)


class CUBERUNNER_OT_game(bpy.types.Operator):
    """Endless runner - modal operator z timerem"""
    bl_idname = "wm.cube_runner"
    bl_label = "Start Cube Runner"

    _timer = None

    # ---------- cykl zycia operatora ----------
    def invoke(self, context, event):
        sc = context.scene
        self.player = bpy.data.objects["Player"]
        self.arm    = bpy.data.objects["Robot_Armature"]
        self.txt    = bpy.data.objects["ScoreText"].data

        # pule obiektow (po prefiksie nazwy)
        self.tiles  = [o for o in sc.objects if o.name.startswith("FloorTile")]
        self.rails  = [o for o in sc.objects if o.name.startswith("Rail.")]
        self.coins  = [o for o in sc.objects if o.name.startswith("Coin.")]
        self.obsts  = [o for o in sc.objects if o.name.startswith("Obstacle")]

        self.reset_game()

        # auto-przelaczenie viewportu na widok z kamery gry
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.region_3d.view_perspective = 'CAMERA'

        wm = context.window_manager
        self._timer = wm.event_timer_add(TICK, window=context.window)
        wm.modal_handler_add(self)
        self.report({'INFO'}, "CUBE RUNNER: A/D pasy, SPACE skok, ESC koniec")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None

    # ---------- stan gry ----------
    def reset_game(self):
        random.seed()
        self.state      = 'RUNNING'
        self.time       = 0.0
        self.coins_got  = 0
        self.lane_idx   = 1            # srodkowy pas
        self.z          = 0.0          # wysokosc skoku
        self.vz         = 0.0
        self.on_ground  = True
        self.anim_name  = None
        self.anim_frame = 1.0

        p = self.player
        p.location = (LANES[1], 0.0, 0.0)
        p.rotation_euler = (0, 0, 0)

        # rozklad kafelkow / barierek od poczatku
        for i, t in enumerate(self.tiles):
            t.location.y = i * TILE_LEN
        for r in self.rails:
            idx = int(r.name.split(".")[1])
            r.location.y = idx * TILE_LEN

        for i, c in enumerate(self.coins):
            c.location = (random.choice(LANES), 15.0 + i * 7.0, COIN_Z)
            c.hide_viewport = False
            c.hide_render = False
        for i, o in enumerate(self.obsts):
            o.location = (random.choice(LANES), 25.0 + i * 13.0, 0.0)

        reset_pose(self.arm)
        self.set_anim("Run")
        self.update_hud()

    # ---------- animacje ----------
    def set_anim(self, name):
        if self.anim_name == name:
            return
        self.anim_name = name
        self.anim_frame = float(ANIM[name][0])
        reset_pose(self.arm)
        self.arm.animation_data.action = bpy.data.actions[name]

    def step_anim(self, speed_scale=1.0):
        start, end, loop = ANIM[self.anim_name]
        self.anim_frame += 30.0 * TICK * speed_scale   # akcje robione w 30 fps
        if self.anim_frame > end:
            self.anim_frame = start if loop else float(end)
        # tylko armatura ma klucze, wiec frame_set jest bezpieczny
        bpy.context.scene.frame_set(int(self.anim_frame))

    # ---------- HUD ----------
    def update_hud(self):
        score = int(self.time * 10) + self.coins_got * 10
        if self.state == 'RUNNING':
            self.txt.body = f"SCORE {score}   COINS {self.coins_got}"
        else:
            self.txt.body = (f"GAME OVER\nSCORE {score}  COINS {self.coins_got}\n"
                             f"[R] restart   [ESC] wyjscie")

    # ---------- logika klatki ----------
    def tick_game(self):
        p = self.player
        dt = TICK
        self.time += dt
        speed = BASE_SPEED + SPEED_GAIN * self.time

        # ruch do przodu
        p.location.y += speed * dt

        # plynna zmiana pasa
        target_x = LANES[self.lane_idx]
        p.location.x += (target_x - p.location.x) * min(1.0, LANE_LERP * dt)

        # skok / grawitacja
        if not self.on_ground:
            self.vz += GRAVITY * dt
            self.z += self.vz * dt
            if self.z <= 0.0:
                self.z = 0.0
                self.vz = 0.0
                self.on_ground = True
                self.set_anim("Run")
        p.location.z = self.z

        # animacja (tempo biegu rosnie z predkoscia)
        self.step_anim(speed / BASE_SPEED if self.anim_name == "Run" else 1.0)

        py = p.location.y

        # recykling kafelkow i barierek
        wrap = N_TILES * TILE_LEN
        for t in self.tiles:
            if t.location.y < py - TILE_LEN * 1.5:
                t.location.y += wrap
        for r in self.rails:
            if r.location.y < py - TILE_LEN * 1.5:
                r.location.y += wrap

        # monety: obrot + zbieranie + recykling
        for c in self.coins:
            c.rotation_euler.z += 4.0 * dt
            dy = c.location.y - py
            if (not c.hide_viewport and abs(dy) < COIN_R
                    and abs(c.location.x - p.location.x) < COIN_R
                    and self.z < 1.2):
                self.coins_got += 1
                c.hide_viewport = True
                c.hide_render = True
            if dy < -5.0:
                c.location = (random.choice(LANES), py + 60.0 + random.uniform(0, 30), COIN_Z)
                c.hide_viewport = False
                c.hide_render = False

        # przeszkody: kolizja + recykling
        for o in self.obsts:
            dy = o.location.y - py
            if (abs(dy) < OBST_DY
                    and abs(o.location.x - p.location.x) < OBST_DX
                    and self.z < OBST_TOP):
                self.game_over()
                return
            if dy < -5.0:
                o.location = (random.choice(LANES), py + 70.0 + random.uniform(0, 40), 0.0)

        self.update_hud()

    def game_over(self):
        self.state = 'GAME_OVER'
        self.set_anim("Death")
        self.update_hud()

    # ---------- modal: input + timer ----------
    def modal(self, context, event):
        if event.type == 'ESC':
            self.cancel(context)
            self.txt.body = "CUBE RUNNER"
            return {'CANCELLED'}

        if event.type == 'TIMER':
            if self.state == 'RUNNING':
                self.tick_game()
            else:
                self.step_anim()   # dogrywa animacje smierci
            # odswiez widok 3D
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
            return {'RUNNING_MODAL'}

        if event.value == 'PRESS':
            if self.state == 'RUNNING':
                if event.type in {'A', 'LEFT_ARROW'}:
                    self.lane_idx = max(0, self.lane_idx - 1)
                    return {'RUNNING_MODAL'}
                if event.type in {'D', 'RIGHT_ARROW'}:
                    self.lane_idx = min(len(LANES) - 1, self.lane_idx + 1)
                    return {'RUNNING_MODAL'}
                if event.type in {'SPACE', 'W', 'UP_ARROW'} and self.on_ground:
                    self.on_ground = False
                    self.vz = JUMP_V
                    self.set_anim("Jump")
                    return {'RUNNING_MODAL'}
            else:
                if event.type == 'R':
                    self.reset_game()
                    return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}


class CUBERUNNER_PT_panel(bpy.types.Panel):
    """Panel startowy gry w pasku bocznym (N) viewportu 3D"""
    bl_label = "Cube Runner"
    bl_idname = "CUBERUNNER_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Cube Runner"

    def draw(self, context):
        col = self.layout.column()
        col.scale_y = 2.0
        col.operator("wm.cube_runner", text="START GRY", icon='PLAY')
        col2 = self.layout.column()
        col2.label(text="A/D lub strzalki - pasy")
        col2.label(text="Space/W - skok")
        col2.label(text="R - restart, ESC - koniec")


_keymaps = []

def register():
    bpy.utils.register_class(CUBERUNNER_OT_game)
    bpy.utils.register_class(CUBERUNNER_PT_panel)
    # P = widok z kamery (zamiennik Numpad 0 dla klawiatur bez bloku numerycznego)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new('view3d.view_camera', 'P', 'PRESS')
        _keymaps.append((km, kmi))

def unregister():
    for km, kmi in _keymaps:
        km.keymap_items.remove(kmi)
    _keymaps.clear()
    bpy.utils.unregister_class(CUBERUNNER_PT_panel)
    bpy.utils.unregister_class(CUBERUNNER_OT_game)

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
    print("Cube Runner zarejestrowany. F3 -> 'Start Cube Runner'")
