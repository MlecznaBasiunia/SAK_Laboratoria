"""
Laboratorium 04 – Proceduralna roślina biomechaniczna (bpy)
Blender 5.1 – uruchom w Text Editor (Alt+P)
"""

import bpy
import math
import os


# Czyszczenie sceny

def wyczysc_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)


# Helper: Principled BSDF (blenderowi nie smakuje)

def get_bsdf(mat):
    mat.use_nodes = True
    return next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


# Materiały

def stworz_material_lodyga():
    mat = bpy.data.materials.new(name="Lodyga")
    bsdf = get_bsdf(mat)
    bsdf.inputs["Base Color"].default_value = (0.45, 0.25, 0.12, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.85
    bsdf.inputs["Roughness"].default_value = 0.25
    return mat


def stworz_material_lisc():
    mat = bpy.data.materials.new(name="Lisc")
    bsdf = get_bsdf(mat)
    bsdf.inputs["Base Color"].default_value = (0.05, 0.75, 0.55, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.6
    bsdf.inputs["Roughness"].default_value = 0.35
    bsdf.inputs["Emission Color"].default_value = (0.0, 0.4, 0.3, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 0.3
    return mat


def stworz_material_korzen():
    mat = bpy.data.materials.new(name="Korzen")
    bsdf = get_bsdf(mat)
    bsdf.inputs["Base Color"].default_value = (0.3, 0.18, 0.08, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.7
    bsdf.inputs["Roughness"].default_value = 0.5
    return mat


# Elementy rośliny 

def stworz_lodyge(pozycja_x, pozycja_y, wysokosc, mat):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.08,
        depth=1.0,
        location=(pozycja_x, pozycja_y, wysokosc / 2)
    )
    obj = bpy.context.active_object
    obj.scale.z = wysokosc
    obj.name = "Lodyga"
    obj.data.materials.append(mat)
    return obj


def stworz_liscie(pozycja_x, pozycja_y, wysokosc, liczba_lisci, promien_lisci, mat):
    for i in range(liczba_lisci):
        kat = (2 * math.pi / liczba_lisci) * i
        odleglosc = 0.25
        lx = pozycja_x + math.cos(kat) * odleglosc
        ly = pozycja_y + math.sin(kat) * odleglosc
        lz = wysokosc * 0.85

        bpy.ops.mesh.primitive_cube_add(
            size=promien_lisci,
            location=(lx, ly, lz)
        )
        lisc = bpy.context.active_object
        lisc.scale = (1.8, 0.5, 0.15)
        lisc.rotation_euler = (
            math.radians(-25),
            0,
            kat
        )
        lisc.name = f"Lisc_{i}"
        lisc.data.materials.append(mat)


def stworz_korzenie(pozycja_x, pozycja_y, liczba_korzeni, mat):
    for i in range(liczba_korzeni):
        kat = (2 * math.pi / liczba_korzeni) * i
        odleglosc = 0.18
        kx = pozycja_x + math.cos(kat) * odleglosc
        ky = pozycja_y + math.sin(kat) * odleglosc
        kz = 0.05

        bpy.ops.mesh.primitive_cube_add(
            size=0.12,
            location=(kx, ky, kz)
        )
        korzen = bpy.context.active_object
        korzen.scale = (1.5, 0.4, 0.3)
        korzen.rotation_euler = (
            math.radians(15),
            0,
            kat + math.radians(45)
        )
        korzen.name = f"Korzen_{i}"
        korzen.data.materials.append(mat)


# Główna funkcja rośliny 

def stworz_rosline(pozycja_x=0.0, pozycja_y=0.0,
                   wysokosc=2.0, liczba_lisci=3,
                   promien_lisci=0.3, liczba_korzeni=4):
    mat_lodyga = stworz_material_lodyga()
    mat_lisc = stworz_material_lisc()
    mat_korzen = stworz_material_korzen()

    stworz_lodyge(pozycja_x, pozycja_y, wysokosc, mat_lodyga)
    stworz_liscie(pozycja_x, pozycja_y, wysokosc, liczba_lisci, promien_lisci, mat_lisc)
    stworz_korzenie(pozycja_x, pozycja_y, liczba_korzeni, mat_korzen)


# Scena (kamera + światło + render) 

def ustaw_scene_i_renderuj():
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 8))
    sun = bpy.context.active_object
    sun.rotation_euler = (math.radians(45), 0, math.radians(30))
    sun.data.energy = 3.0

    bpy.ops.object.camera_add(location=(5, -6, 4))
    kamera = bpy.context.active_object
    kamera.rotation_euler = (math.radians(65), 0, math.radians(40))
    bpy.context.scene.camera = kamera

    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 800
    scene.render.resolution_y = 600
    scene.render.image_settings.file_format = 'PNG'

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()

    scene.render.filepath = os.path.join(script_dir, "rosliny_lab04.png")
    bpy.ops.render.render(write_still=True)
    print(f"Render zapisany: {scene.render.filepath}")


# Main 

wyczysc_scene()

stworz_rosline(pozycja_x=-2.0, wysokosc=1.2, liczba_lisci=3,
               promien_lisci=0.2, liczba_korzeni=3)

stworz_rosline(pozycja_x=0.0, wysokosc=2.0, liczba_lisci=4,
               promien_lisci=0.3, liczba_korzeni=4)

stworz_rosline(pozycja_x=2.0, wysokosc=3.0, liczba_lisci=5,
               promien_lisci=0.4, liczba_korzeni=5)

ustaw_scene_i_renderuj()