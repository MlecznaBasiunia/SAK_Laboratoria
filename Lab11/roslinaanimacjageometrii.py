import bpy
import math
import os

SCIEZKA_LAB07 = r"X:\Studia UWS Informatyka\semestr 6\systemy animacji komputerowej/Lab08.blend"
NAZWA_KOLEKCJI = "Roslina_Hero"

KLATKA_START = 1
KLATKA_KONIEC = 125
FPS = 25

PREFIX_LISC = "Roslina_Lisc"
NAZWA_PAK = "Roslina_Pak"
NAZWA_LODYGA = "Roslina_Lodyga"

def importuj_rosline(sciezka_blend, nazwa_kolekcji):
    if not os.path.exists(sciezka_blend):
        print(f"[BŁĄD] Plik nie istnieje: {sciezka_blend}")
        print("       Ustaw poprawną SCIEZKA_LAB07 na górze skryptu.")
        return False

    directory = os.path.join(sciezka_blend, "Collection") + os.sep
    try:
        bpy.ops.wm.append(
            filepath=os.path.join(directory, nazwa_kolekcji),
            directory=directory,
            filename=nazwa_kolekcji,
        )
        print(f"[OK] Zaimportowano kolekcję '{nazwa_kolekcji}'")
        return True
    except Exception as e:
        print(f"[BŁĄD] Import nie powiódł się: {e}")
        return False

def wyczysc_animacje(obj):
    if obj and obj.animation_data and obj.animation_data.action:
        obj.animation_data.action = None

def animuj_lisc(obj, faza, czestosc=0.05, amplituda=0.3,
                klatka_start=1, klatka_koniec=125):
    wyczysc_animacje(obj)
    rotacja_bazowa_y = obj.rotation_euler[1]

    for klatka in range(klatka_start, klatka_koniec + 1):
        kat = rotacja_bazowa_y + amplituda * math.sin(klatka * czestosc + faza)
        obj.rotation_euler[1] = kat
        obj.keyframe_insert(data_path="rotation_euler", frame=klatka, index=1)

def animuj_wszystkie_liscie(prefix_nazwy=PREFIX_LISC,
                            czestosc=0.05, amplituda=0.3):
    liscie = [obj for obj in bpy.data.objects
              if obj.name.startswith(prefix_nazwy)]

    if not liscie:
        print(f"[UWAGA] Nie znaleziono liści z prefiksem '{prefix_nazwy}'")
        print(f"        Dostępne obiekty: {[o.name for o in bpy.data.objects]}")
        return

    for i, lisc in enumerate(liscie):
        faza_lisc = i * (2 * math.pi / max(len(liscie), 1))
        animuj_lisc(lisc, faza=faza_lisc, czestosc=czestosc,
                    amplituda=amplituda,
                    klatka_start=KLATKA_START, klatka_koniec=KLATKA_KONIEC)

    print(f"[OK] Zaanimowano {len(liscie)} liści (różne fazy).")

def animuj_pak(nazwa_obj=NAZWA_PAK, klatka_start=30, klatka_koniec=90,
               skala_min=0.1, skala_max=1.0):
    obj = bpy.data.objects.get(nazwa_obj)
    if obj is None:
        print(f"[UWAGA] Obiekt '{nazwa_obj}' nie istnieje. Pomijam pąk.")
        print(f"        Dostępne obiekty: {[o.name for o in bpy.data.objects]}")
        return

    wyczysc_animacje(obj)

    baza = obj.scale.copy()

    obj.scale = (baza.x * skala_min, baza.y * skala_min, baza.z * skala_min)
    obj.keyframe_insert(data_path="scale", frame=KLATKA_START)
    obj.keyframe_insert(data_path="scale", frame=klatka_start)

    obj.scale = (baza.x * skala_max, baza.y * skala_max, baza.z * skala_max)
    obj.keyframe_insert(data_path="scale", frame=klatka_koniec)
    obj.keyframe_insert(data_path="scale", frame=KLATKA_KONIEC)

    print(f"[OK] Pąk '{nazwa_obj}': skala {skala_min} -> {skala_max} "
          f"(kl. {klatka_start}-{klatka_koniec})")

def sparentuj_rosline_do_lodygi(nazwa_lodyga=NAZWA_LODYGA):
    lodyga = bpy.data.objects.get(nazwa_lodyga)
    if lodyga is None:
        print(f"[UWAGA] Łodyga '{nazwa_lodyga}' nie istnieje — pomijam parentowanie")
        return

    czesci = []
    for obj in bpy.data.objects:
        if obj == lodyga:
            continue
        if obj.name.startswith("Roslina_") or obj.name.startswith("Biolum_"):
            czesci.append(obj)

    sparentowane = 0
    for czesc in czesci:
        if czesc.parent == lodyga:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        czesc.select_set(True)
        lodyga.select_set(True)
        bpy.context.view_layer.objects.active = lodyga
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
        sparentowane += 1

    print(f"[OK] Sparentowano {sparentowane} części rośliny do łodygi "
          f"(razem {len(czesci)} dzieci)")

def animuj_lodyge(nazwa_obj=NAZWA_LODYGA, czestosc=0.03, amplituda=0.05):
    obj = bpy.data.objects.get(nazwa_obj)
    if obj is None:
        print(f"[UWAGA] Łodyga '{nazwa_obj}' nie istnieje. Pomijam.")
        return

    wyczysc_animacje(obj)
    bazowa_x = obj.rotation_euler[0]
    bazowa_y = obj.rotation_euler[1]

    for klatka in range(KLATKA_START, KLATKA_KONIEC + 1):
        obj.rotation_euler[0] = bazowa_x + amplituda * math.sin(klatka * czestosc)
        obj.rotation_euler[1] = bazowa_y + amplituda * math.cos(klatka * czestosc * 0.7)
        obj.keyframe_insert(data_path="rotation_euler", frame=klatka, index=0)
        obj.keyframe_insert(data_path="rotation_euler", frame=klatka, index=1)

    print(f"[OK] Łodyga '{nazwa_obj}' kołysze się (amplituda {amplituda})")

def animuj_kamere(pozycja_start=(8, -8, 4), pozycja_koniec=(3, -3, 2),
                  klatka_start=KLATKA_START, klatka_koniec=KLATKA_KONIEC):
    cam = bpy.context.scene.camera
    if cam is None:
        for obj in bpy.data.objects:
            if obj.type == 'CAMERA':
                cam = obj
                bpy.context.scene.camera = cam
                break

    if cam is None:
        print("[UWAGA] Brak kamery w scenie — pomijam animację kamery.")
        return

    wyczysc_animacje(cam)

    from mathutils import Vector
    cel = Vector((0, 0, 1.3))

    for klatka, poz in [(klatka_start, pozycja_start),
                        (klatka_koniec, pozycja_koniec)]:
        cam.location = poz
        kierunek = cel - Vector(poz)
        cam.rotation_euler = kierunek.to_track_quat('-Z', 'Y').to_euler()
        cam.keyframe_insert(data_path="location", frame=klatka)
        cam.keyframe_insert(data_path="rotation_euler", frame=klatka)

    print(f"[OK] Kamera: przelot {pozycja_start} -> {pozycja_koniec}")

def ustaw_oswietlenie():
    istniejace = [o for o in bpy.data.objects if o.type == 'LIGHT']
    if istniejace:
        print(f"[OK] Scena ma już {len(istniejace)} świateł — pomijam.")
        return

    key_data = bpy.data.lights.new("Key_Light_data", 'AREA')
    key_data.energy = 150
    key_data.size = 3.0
    key_data.color = (1.0, 0.95, 0.85)
    key_obj = bpy.data.objects.new("Key_Light", key_data)
    bpy.context.scene.collection.objects.link(key_obj)
    key_obj.location = (4, -4, 5)
    key_obj.rotation_euler = (math.radians(55), 0, math.radians(45))

    fill_data = bpy.data.lights.new("Fill_Light_data", 'AREA')
    fill_data.energy = 50
    fill_data.size = 4.0
    fill_data.color = (0.75, 0.85, 1.0)
    fill_obj = bpy.data.objects.new("Fill_Light", fill_data)
    bpy.context.scene.collection.objects.link(fill_obj)
    fill_obj.location = (-4, 2, 3)
    fill_obj.rotation_euler = (math.radians(60), 0, math.radians(-135))

    rim_data = bpy.data.lights.new("Rim_Light_data", 'SPOT')
    rim_data.energy = 250
    rim_data.color = (0.4, 0.8, 1.0)
    rim_data.spot_size = math.radians(60)
    rim_obj = bpy.data.objects.new("Rim_Light", rim_data)
    bpy.context.scene.collection.objects.link(rim_obj)
    rim_obj.location = (-2, 5, 3.5)
    from mathutils import Vector
    rim_dir = Vector((0, 0, 1.3)) - rim_obj.location
    rim_obj.rotation_euler = rim_dir.to_track_quat('-Z', 'Y').to_euler()

    print("[OK] Dodano Three-Point lighting")

def ustaw_kamere_jesli_brak():
    if bpy.context.scene.camera:
        return
    for obj in bpy.data.objects:
        if obj.type == 'CAMERA':
            bpy.context.scene.camera = obj
            return
    cam_data = bpy.data.cameras.new("Kamera_data")
    cam_data.lens = 50
    cam_obj = bpy.data.objects.new("Kamera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    cam_obj.location = (6, -6, 2.5)
    bpy.context.scene.camera = cam_obj
    print("[OK] Dodano kamerę")

def ustaw_scene():
    scene = bpy.context.scene
    scene.frame_start = KLATKA_START
    scene.frame_end = KLATKA_KONIEC
    scene.render.fps = FPS
    print(f"[OK] Scena: klatki {KLATKA_START}-{KLATKA_KONIEC} @ {FPS}fps")

def ustaw_render():
    scene = bpy.context.scene

    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        try:
            scene.render.engine = 'BLENDER_EEVEE'
        except TypeError:
            pass

    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100

    eevee = scene.eevee
    if hasattr(eevee, 'taa_render_samples'):
        eevee.taa_render_samples = 64
    if hasattr(eevee, 'use_raytracing'):
        eevee.use_raytracing = True
    if hasattr(eevee, 'use_bloom'):
        eevee.use_bloom = True
        eevee.bloom_threshold = 0.5
        eevee.bloom_intensity = 0.1

    blend_path = bpy.data.filepath
    out_dir = os.path.dirname(blend_path) if blend_path else os.path.expanduser("~")

    if bpy.app.version < (5, 0, 0):
        scene.render.image_settings.file_format = 'FFMPEG'
        scene.render.ffmpeg.format = 'MPEG4'
        scene.render.ffmpeg.codec = 'H264'
        scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
        scene.render.ffmpeg.audio_codec = 'NONE'
        scene.render.filepath = os.path.join(out_dir, "roslina_ozywiona_11.mp4")
        return True, out_dir
    else:
        png_dir = os.path.join(out_dir, "roslina_ozywiona_11_frames", "")
        os.makedirs(png_dir, exist_ok=True)
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = png_dir
        return False, out_dir

def renderuj(use_ffmpeg, out_dir):
    bpy.context.scene.frame_set(KLATKA_START)
    print(f"\n[Lab 11] Render animacji ({KLATKA_KONIEC} klatek)...")
    bpy.ops.render.render(animation=True)

    if not use_ffmpeg:
        mp4_path = os.path.join(out_dir, "roslina_ozywiona_11.mp4")
        png_pattern = os.path.join(out_dir, "roslina_ozywiona_11_frames", "%04d.png")
        import subprocess
        try:
            subprocess.run([
                "ffmpeg", "-y", "-framerate", str(FPS),
                "-i", png_pattern,
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-crf", "18", mp4_path
            ], check=True, capture_output=True)
            print(f"[OK] MP4 gotowy: {mp4_path}")
        except (FileNotFoundError, subprocess.CalledProcessError):
            print(f"[UWAGA] ffmpeg niedostepny — skompiluj recznie:")
            print(f'  ffmpeg -framerate {FPS} -i "{png_pattern}" '
                  f'-c:v libx264 -pix_fmt yuv420p "{mp4_path}"')

if __name__ == "__main__" or True:
    print("=" * 55)
    print("  Lab 11 — Animacja Geometrii Rośliny przez bpy")
    print("=" * 55)

    ustaw_scene()

    if NAZWA_KOLEKCJI not in bpy.data.collections:
        importuj_rosline(SCIEZKA_LAB07, NAZWA_KOLEKCJI)
    else:
        print(f"[OK] Kolekcja '{NAZWA_KOLEKCJI}' już w scenie — pomijam import")

    sparentuj_rosline_do_lodygi()

    animuj_wszystkie_liscie()
    animuj_pak()
    animuj_lodyge()
    ustaw_kamere_jesli_brak()
    animuj_kamere()
    ustaw_oswietlenie()

    use_ffmpeg, out_dir = ustaw_render()
    renderuj(use_ffmpeg, out_dir)

    print("\n" + "=" * 55)
    print("  Skrypt zakończony.")
    print("=" * 55)