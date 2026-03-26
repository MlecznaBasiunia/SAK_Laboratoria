"""
Laboratorium 05 – Generator Lasu z Typami Roślin i Biomami
Blender 5.1 – uruchom w Text Editor (Alt+P)

Typy: drzewo, stokrotka, chaber, grzyb, trawa/mech,
      kamien, pniak, krzew jagodowy, motyl, opadle liscie
Bonus: źródełko (3 elipsy), oświetlenie nastrojowe
"""

import bpy
import math
import os
import random


# ── Słownik typów roślin ──────────────────────────────────────────────

TYPY_ROSLIN = {
    "drzewo": {
        "wysokosc": (3.0, 5.0),
        "promien_pnia": (0.08, 0.14),
        "korona_promien": (0.8, 1.4),
        "korona_kule": (4, 7),
        "liczba_korzeni": (3, 5),
        "kolor_pnia": (0.15, 0.08, 0.02, 1),
        "kolor_korony": (0.04, 0.28, 0.06, 1),
    },
    "stokrotka": {
        "wysokosc_lodygi": (0.3, 0.7),
        "liczba_platkow": (8, 14),
        "promien_platka": (0.06, 0.10),
        "promien_srodka": (0.05, 0.08),
        "kolor_lodygi": (0.15, 0.45, 0.08, 1),
        "kolor_platki": (0.95, 0.95, 0.92, 1),
        "kolor_srodek": (0.95, 0.80, 0.10, 1),
    },
    "chaber": {
        "wysokosc_lodygi": (0.35, 0.65),
        "liczba_platkow": (6, 10),
        "promien_platka": (0.05, 0.08),
        "promien_srodka": (0.03, 0.06),
        "kolor_lodygi": (0.12, 0.40, 0.06, 1),
        "kolor_platki": (0.20, 0.25, 0.85, 1),
        "kolor_srodek": (0.30, 0.15, 0.60, 1),
    },
    "grzyb": {
        "wysokosc_nozki": (0.15, 0.35),
        "promien_nozki": (0.03, 0.06),
        "promien_kapelusza": (0.10, 0.22),
        "kolor_nozki": (0.90, 0.88, 0.80, 1),
        "kolor_kapelusz": (0.55, 0.12, 0.05, 1),
    },
    "trawa": {
        "liczba_zdzibel": (5, 12),
        "wysokosc_zdzibla": (0.10, 0.35),
        "promien_rozrzutu": (0.15, 0.30),
        "kolor_trawa": (0.08, 0.40, 0.05, 1),
        "kolor_mech": (0.12, 0.30, 0.02, 1),
    },
    "kamien": {
        "promien": (0.12, 0.40),
        "splaszczenie_z": (0.3, 0.6),
        "kolor": (0.45, 0.44, 0.42, 1),
    },
    "pniak": {
        "wysokosc": (0.15, 0.40),
        "promien": (0.12, 0.25),
        "kolor": (0.22, 0.13, 0.05, 1),
    },
    "krzew_jagodowy": {
        "promien_krzewu": (0.3, 0.6),
        "liczba_jagod": (4, 10),
        "promien_jagody": (0.025, 0.045),
        "kolor_krzew": (0.06, 0.32, 0.08, 1),
        "kolor_jagody": (0.75, 0.05, 0.05, 1),
    },
    "motyl": {
        "wysokosc_lotu": (0.6, 1.8),
        "rozmiar_skrzydla": (0.06, 0.12),
        "kolory_skrzydel": [
            (0.90, 0.60, 0.10, 1),
            (0.85, 0.20, 0.15, 1),
            (0.20, 0.50, 0.90, 1),
            (0.95, 0.95, 0.50, 1),
        ],
    },
    "lisc_opadly": {
        "promien": (0.03, 0.07),
        "rozrzut": (0.8, 1.8),
        "kolory": [
            (0.70, 0.55, 0.10, 1),
            (0.80, 0.40, 0.08, 1),
            (0.55, 0.30, 0.05, 1),
            (0.65, 0.20, 0.05, 1),
        ],
    },
}

# Rozmiar podłoża i strefy spawnu (ten sam!)
ROZMIAR_MAPY = 35.0
POLOWA = ROZMIAR_MAPY / 2


# ── Czyszczenie sceny ─────────────────────────────────────────────────

def wyczysc_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    if "Las" in bpy.data.collections:
        col = bpy.data.collections["Las"]
        for child in list(col.children):
            bpy.data.collections.remove(child)
        bpy.data.collections.remove(col)


# ── Materiały ─────────────────────────────────────────────────────────

def get_bsdf(mat):
    mat.use_nodes = True
    return next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def stworz_material(nazwa, kolor, metallic=0.0, roughness=0.7, emission=None):
    mat = bpy.data.materials.new(name=nazwa)
    bsdf = get_bsdf(mat)
    bsdf.inputs["Base Color"].default_value = kolor
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = 0.3
    return mat


def przenies_do_kolekcji(obiekty, kolekcja):
    for obj in obiekty:
        for col in obj.users_collection:
            col.objects.unlink(obj)
        kolekcja.objects.link(obj)


def losowa_pozycja():
    """Losowa pozycja na całej mapie."""
    return (random.uniform(-POLOWA * 0.95, POLOWA * 0.95),
            random.uniform(-POLOWA * 0.95, POLOWA * 0.95))


# ── DRZEWO ────────────────────────────────────────────────────────────

def stworz_drzewo(px, pz, params):
    p = params
    obiekty = []
    wys = random.uniform(*p["wysokosc"])
    r_pnia = random.uniform(*p["promien_pnia"])
    r_korony = random.uniform(*p["korona_promien"])
    n_kul = random.randint(*p["korona_kule"])

    mat_pien = stworz_material("Pien", p["kolor_pnia"], metallic=0.1, roughness=0.85)
    bk = p["kolor_korony"]
    shift = random.uniform(-0.03, 0.03)
    kolor_k = (bk[0]+shift, bk[1]+random.uniform(-0.05, 0.05), bk[2]+shift, 1)
    mat_korona = stworz_material("Korona", kolor_k, roughness=0.9)

    bpy.ops.mesh.primitive_cylinder_add(radius=r_pnia, depth=wys,
                                        location=(px, pz, wys / 2))
    pien = bpy.context.active_object
    pien.name = "Pien"
    pien.data.materials.append(mat_pien)
    obiekty.append(pien)

    mat_galaz = stworz_material("Galaz", p["kolor_pnia"], metallic=0.1, roughness=0.85)
    for i in range(n_kul):
        kat = random.uniform(0, 2 * math.pi)
        odl = random.uniform(r_pnia * 2, r_korony * 0.6)
        kx = px + math.cos(kat) * odl
        ky = pz + math.sin(kat) * odl
        kz = wys * random.uniform(0.55, 0.90)
        start_z = wys * random.uniform(0.4, 0.7)

        mid_x, mid_y, mid_z = (px+kx)/2, (pz+ky)/2, (start_z+kz)/2
        dx, dy, dz = kx-px, ky-pz, kz-start_z
        dl = math.sqrt(dx*dx + dy*dy + dz*dz)

        bpy.ops.mesh.primitive_cylinder_add(radius=r_pnia*0.4, depth=dl,
                                            location=(mid_x, mid_y, mid_z))
        galaz = bpy.context.active_object
        galaz.name = f"Galaz_{i}"
        galaz.rotation_euler = (math.acos(max(-1, min(1, dz/dl))), 0,
                                math.atan2(dy, dx) + math.pi/2)
        galaz.data.materials.append(mat_galaz)
        obiekty.append(galaz)

        r = r_korony * random.uniform(0.55, 1.0)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=12, ring_count=8,
                                             location=(kx, ky, kz))
        kula = bpy.context.active_object
        kula.scale.z = random.uniform(0.55, 0.85)
        kula.name = f"Korona_{i}"
        kula.data.materials.append(mat_korona)
        bpy.ops.object.shade_smooth()
        obiekty.append(kula)

    mat_korzen = stworz_material("Korzen", (0.25, 0.14, 0.04, 1), roughness=0.9)
    n_korz = random.randint(*p["liczba_korzeni"])
    for i in range(n_korz):
        kat = (2*math.pi/n_korz)*i + random.uniform(-0.3, 0.3)
        kx = px + math.cos(kat) * r_pnia * 2.5
        ky = pz + math.sin(kat) * r_pnia * 2.5
        bpy.ops.mesh.primitive_cube_add(size=0.12, location=(kx, ky, 0.04))
        obj = bpy.context.active_object
        obj.scale = (1.8, 0.4, 0.25)
        obj.rotation_euler = (math.radians(10), 0, kat)
        obj.name = f"Korzen_{i}"
        obj.data.materials.append(mat_korzen)
        obiekty.append(obj)
    return obiekty


# ── KWIAT (stokrotka / chaber) ────────────────────────────────────────

def stworz_kwiat(px, pz, params):
    p = params
    obiekty = []
    wys = random.uniform(*p["wysokosc_lodygi"])
    n_plat = random.randint(*p["liczba_platkow"])
    r_plat = random.uniform(*p["promien_platka"])
    r_sr = random.uniform(*p["promien_srodka"])

    mat_lod = stworz_material("Lodyga_K", p["kolor_lodygi"], roughness=0.6)
    mat_plat = stworz_material("Platek", p["kolor_platki"], roughness=0.4)
    mat_sr = stworz_material("Srodek", p["kolor_srodek"], metallic=0.1, roughness=0.3)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=wys,
                                        location=(px, pz, wys / 2))
    lod = bpy.context.active_object
    lod.name = "Lodyga_Kwiat"
    lod.data.materials.append(mat_lod)
    obiekty.append(lod)

    sz = wys + r_sr * 0.3
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r_sr, segments=10, ring_count=6,
                                         location=(px, pz, sz))
    srodek = bpy.context.active_object
    srodek.scale.z = 0.45
    srodek.name = "Srodek_Kwiat"
    srodek.data.materials.append(mat_sr)
    bpy.ops.object.shade_smooth()
    obiekty.append(srodek)

    for i in range(n_plat):
        kat = (2*math.pi/n_plat) * i
        dist = r_sr + r_plat * 1.3
        lx = px + math.cos(kat) * dist
        ly = pz + math.sin(kat) * dist
        lz = wys
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r_plat, segments=8, ring_count=6,
                                             location=(lx, ly, lz))
        plat = bpy.context.active_object
        plat.scale = (2.4, 0.7, 0.12)
        plat.rotation_euler = (math.radians(-8), 0, kat)
        plat.name = f"Platek_{i}"
        plat.data.materials.append(mat_plat)
        bpy.ops.object.shade_smooth()
        obiekty.append(plat)
    return obiekty


# ── GRZYB ─────────────────────────────────────────────────────────────

def stworz_grzyba(px, pz, params):
    p = params
    obiekty = []
    wys = random.uniform(*p["wysokosc_nozki"])
    r_noz = random.uniform(*p["promien_nozki"])
    r_kap = random.uniform(*p["promien_kapelusza"])

    mat_noz = stworz_material("Nozka_G", p["kolor_nozki"], roughness=0.5)
    mat_kap = stworz_material("Kapelusz", p["kolor_kapelusz"], roughness=0.6)

    bpy.ops.mesh.primitive_cylinder_add(radius=r_noz, depth=wys,
                                        location=(px, pz, wys / 2))
    nozka = bpy.context.active_object
    nozka.name = "Nozka_Grzyb"
    nozka.data.materials.append(mat_noz)
    obiekty.append(nozka)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=r_kap, segments=14, ring_count=8,
                                         location=(px, pz, wys + r_kap * 0.15))
    kap = bpy.context.active_object
    kap.scale.z = 0.4
    kap.name = "Kapelusz_Grzyb"
    kap.data.materials.append(mat_kap)
    bpy.ops.object.shade_smooth()
    obiekty.append(kap)
    return obiekty


# ── TRAWA / MECH ──────────────────────────────────────────────────────

def stworz_trawe(px, pz, params):
    p = params
    obiekty = []
    n = random.randint(*p["liczba_zdzibel"])
    rozrzut = random.uniform(*p["promien_rozrzutu"])

    jest_mech = random.random() < 0.4
    kolor = p["kolor_mech"] if jest_mech else p["kolor_trawa"]
    mat = stworz_material("Trawa", kolor, roughness=0.85)

    for i in range(n):
        ox = px + random.uniform(-rozrzut, rozrzut)
        oy = pz + random.uniform(-rozrzut, rozrzut)
        wys = random.uniform(*p["wysokosc_zdzibla"])
        if jest_mech:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=wys*0.5, segments=6,
                                                 ring_count=4, location=(ox, oy, wys*0.2))
            obj = bpy.context.active_object
            obj.scale.z = 0.35
        else:
            bpy.ops.mesh.primitive_cone_add(radius1=0.012, radius2=0.0,
                                            depth=wys, location=(ox, oy, wys/2))
            obj = bpy.context.active_object
            obj.rotation_euler = (random.uniform(-0.25, 0.25),
                                  random.uniform(-0.25, 0.25), 0)
        obj.name = f"Trawa_{i}"
        obj.data.materials.append(mat)
        obiekty.append(obj)
    return obiekty


# ── KAMIEŃ ────────────────────────────────────────────────────────────

def stworz_kamien(px, pz, params):
    p = params
    obiekty = []
    r = random.uniform(*p["promien"])
    splasz = random.uniform(*p["splaszczenie_z"])
    bk = p["kolor"]
    s = random.uniform(-0.08, 0.08)
    kolor = (bk[0]+s, bk[1]+s, bk[2]+s, 1)
    mat = stworz_material("Kamien", kolor, roughness=0.95)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=8, ring_count=6,
                                         location=(px, pz, r * splasz * 0.5))
    obj = bpy.context.active_object
    obj.scale.z = splasz
    obj.rotation_euler = (random.uniform(0, 0.3), random.uniform(0, 0.3),
                          random.uniform(0, math.pi*2))
    obj.name = "Kamien"
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    obiekty.append(obj)
    return obiekty


# ── PNIAK ─────────────────────────────────────────────────────────────

def stworz_pniak(px, pz, params):
    p = params
    obiekty = []
    wys = random.uniform(*p["wysokosc"])
    r = random.uniform(*p["promien"])
    mat = stworz_material("Pniak", p["kolor"], roughness=0.9)

    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=wys,
                                        location=(px, pz, wys / 2))
    obj = bpy.context.active_object
    obj.name = "Pniak"
    obj.data.materials.append(mat)
    obiekty.append(obj)

    mat_sloj = stworz_material("Sloje", (0.35, 0.22, 0.10, 1), roughness=0.8)
    bpy.ops.mesh.primitive_cylinder_add(radius=r*0.85, depth=0.01,
                                        location=(px, pz, wys + 0.005))
    sloj = bpy.context.active_object
    sloj.name = "Sloje_Pniak"
    sloj.data.materials.append(mat_sloj)
    obiekty.append(sloj)
    return obiekty


# ── KRZEW JAGODOWY ────────────────────────────────────────────────────

def stworz_krzew_jagodowy(px, pz, params):
    p = params
    obiekty = []
    r_krzewu = random.uniform(*p["promien_krzewu"])
    n_jagod = random.randint(*p["liczba_jagod"])

    mat_krzew = stworz_material("Krzew_J", p["kolor_krzew"], roughness=0.85)
    mat_jagoda = stworz_material("Jagoda", p["kolor_jagody"], metallic=0.15, roughness=0.3)

    for i in range(random.randint(2, 3)):
        kat = random.uniform(0, 2*math.pi)
        odl = random.uniform(0, r_krzewu * 0.3)
        kx = px + math.cos(kat) * odl
        ky = pz + math.sin(kat) * odl
        r = r_krzewu * random.uniform(0.6, 1.0)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=10, ring_count=6,
                                             location=(kx, ky, r * 0.7))
        obj = bpy.context.active_object
        obj.scale.z = random.uniform(0.6, 0.85)
        obj.name = f"Krzew_{i}"
        obj.data.materials.append(mat_krzew)
        bpy.ops.object.shade_smooth()
        obiekty.append(obj)

    for i in range(n_jagod):
        kat = random.uniform(0, 2*math.pi)
        odl = random.uniform(r_krzewu*0.3, r_krzewu*0.9)
        jx = px + math.cos(kat) * odl
        jy = pz + math.sin(kat) * odl
        jz = random.uniform(r_krzewu*0.3, r_krzewu*0.9)
        r_j = random.uniform(*p["promien_jagody"])
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r_j, segments=6, ring_count=4,
                                             location=(jx, jy, jz))
        obj = bpy.context.active_object
        obj.name = f"Jagoda_{i}"
        obj.data.materials.append(mat_jagoda)
        bpy.ops.object.shade_smooth()
        obiekty.append(obj)
    return obiekty


# ── MOTYL ─────────────────────────────────────────────────────────────

def stworz_motyla(px, pz, params):
    p = params
    obiekty = []
    wys_lotu = random.uniform(*p["wysokosc_lotu"])
    r_skrz = random.uniform(*p["rozmiar_skrzydla"])
    kolor = random.choice(p["kolory_skrzydel"])

    mat_skrz = stworz_material("Skrzydlo", kolor, metallic=0.2, roughness=0.3)
    mat_cialo = stworz_material("Cialo_Motyl", (0.1, 0.1, 0.1, 1), roughness=0.5)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=r_skrz*1.5,
                                        location=(px, pz, wys_lotu))
    cialo = bpy.context.active_object
    cialo.rotation_euler = (math.radians(90), 0, random.uniform(0, math.pi*2))
    cialo.name = "Cialo_Motyl"
    cialo.data.materials.append(mat_cialo)
    obiekty.append(cialo)

    rot_z = random.uniform(0, math.pi*2)
    for strona, nazwa in [(1, "L"), (-1, "P")]:
        bpy.ops.mesh.primitive_cone_add(
            vertices=3, radius1=r_skrz, depth=0.005,
            location=(px + strona*math.cos(rot_z)*r_skrz*0.5,
                      pz + strona*math.sin(rot_z)*r_skrz*0.5,
                      wys_lotu))
        sk = bpy.context.active_object
        sk.rotation_euler = (0, 0, rot_z + strona*math.radians(30))
        sk.scale = (1.0, 0.6, 1.0)
        sk.name = f"Skrzydlo_{nazwa}"
        sk.data.materials.append(mat_skrz)
        obiekty.append(sk)
    return obiekty


# ── OPADŁE LIŚCIE ────────────────────────────────────────────────────

def stworz_opadle_liscie(px, pz, params):
    p = params
    obiekty = []
    rozrzut = random.uniform(*p["rozrzut"])

    for i in range(random.randint(4, 10)):
        kolor = random.choice(p["kolory"])
        mat = stworz_material(f"Lisc_Op_{i}", kolor, roughness=0.8)
        r = random.uniform(*p["promien"])
        ox = px + random.uniform(-rozrzut, rozrzut)
        oy = pz + random.uniform(-rozrzut, rozrzut)
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=0.005,
                                            location=(ox, oy, 0.005))
        obj = bpy.context.active_object
        obj.scale = (1.0, random.uniform(0.5, 0.8), 1.0)
        obj.rotation_euler = (random.uniform(-0.1, 0.1),
                              random.uniform(-0.1, 0.1),
                              random.uniform(0, math.pi*2))
        obj.name = f"Lisc_Opadly_{i}"
        obj.data.materials.append(mat)
        obiekty.append(obj)
    return obiekty


# ── ŹRÓDEŁKO – 3 elipsy + kamyki ─────────────────────────────────────

def stworz_zrodelko(cx, cy):
    obiekty = []
    mat_woda = stworz_material("Woda", (0.12, 0.32, 0.60, 1), metallic=0.4,
                               roughness=0.05, emission=(0.08, 0.20, 0.45, 1))

    elipsy = [
        (cx, cy, 1.4, 1.0, 0.0),
        (cx + 0.7, cy - 0.5, 1.0, 0.7, math.radians(25)),
        (cx - 0.6, cy + 0.6, 0.8, 0.55, math.radians(-15)),
    ]

    for i, (ex, ey, sx, sy, rot) in enumerate(elipsy):
        bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=0.02,
                                            location=(ex, ey, 0.008))
        elipsa = bpy.context.active_object
        elipsa.scale = (sx, sy, 1.0)
        elipsa.rotation_euler = (0, 0, rot)
        elipsa.name = f"Zrodelko_{i}"
        elipsa.data.materials.append(mat_woda)
        bpy.ops.object.shade_smooth()
        obiekty.append(elipsa)

    mat_kam = stworz_material("Kamyk_Z", (0.48, 0.46, 0.43, 1), roughness=0.9)
    for _ in range(20):
        kat = random.uniform(0, 2*math.pi)
        odl = random.uniform(1.2, 2.5)
        kx = cx + math.cos(kat) * odl
        ky = cy + math.sin(kat) * odl
        r = random.uniform(0.04, 0.14)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=6, ring_count=4,
                                             location=(kx, ky, r * 0.3))
        obj = bpy.context.active_object
        obj.scale.z = random.uniform(0.3, 0.5)
        obj.name = "Kamyk_Zrodelko"
        obj.data.materials.append(mat_kam)
        obiekty.append(obj)

    return obiekty, (cx, cy)


# ── Dispatcher ────────────────────────────────────────────────────────

TWORZENIE = {
    "drzewo": stworz_drzewo,
    "stokrotka": stworz_kwiat,
    "chaber": stworz_kwiat,
    "grzyb": stworz_grzyba,
    "trawa": stworz_trawe,
    "kamien": stworz_kamien,
    "pniak": stworz_pniak,
    "krzew_jagodowy": stworz_krzew_jagodowy,
    "motyl": stworz_motyla,
    "lisc_opadly": stworz_opadle_liscie,
}


def stworz_rosline_typ(x, z, typ):
    return TWORZENIE[typ](x, z, TYPY_ROSLIN[typ])


# ── System biomów ─────────────────────────────────────────────────────

def wybierz_typ_biomu(x, z):
    """Równomierny rozkład po całej mapie z lekkim zagęszczeniem drzew w centrum."""
    odleglosc = max(abs(x), abs(z)) / POLOWA

    if odleglosc < 0.35:
        # Centrum – więcej drzew
        r = random.random()
        if r < 0.55:
            return "drzewo"
        elif r < 0.70:
            return "krzew_jagodowy"
        elif r < 0.80:
            return "stokrotka"
        elif r < 0.90:
            return "chaber"
        else:
            return "pniak"
    elif odleglosc < 0.70:
        # Strefa środkowa – mix
        r = random.random()
        if r < 0.30:
            return "drzewo"
        elif r < 0.45:
            return "stokrotka"
        elif r < 0.58:
            return "chaber"
        elif r < 0.70:
            return "krzew_jagodowy"
        elif r < 0.82:
            return "kamien"
        elif r < 0.92:
            return "pniak"
        else:
            return "grzyb"
    else:
        # Peryferia – kwiaty, trawa, kamienie, pojedyncze drzewa
        r = random.random()
        if r < 0.20:
            return "drzewo"
        elif r < 0.35:
            return "stokrotka"
        elif r < 0.50:
            return "chaber"
        elif r < 0.65:
            return "kamien"
        elif r < 0.78:
            return "pniak"
        elif r < 0.90:
            return "krzew_jagodowy"
        else:
            return "grzyb"


# ── Generator lasu ────────────────────────────────────────────────────

def generuj_las(liczba_roslin=80, seed=42):
    random.seed(seed)
    wyczysc_scene()

    # Kolekcja główna + podkolekcje
    kol_las = bpy.data.collections.new("Las")
    bpy.context.scene.collection.children.link(kol_las)

    nazwy_sub = {
        "drzewo": "Drzewa", "stokrotka": "Stokrotki", "chaber": "Chabry",
        "grzyb": "Grzyby", "trawa": "Trawa_Mech", "kamien": "Kamienie",
        "pniak": "Pniaki", "krzew_jagodowy": "Krzewy_Jagodowe",
        "motyl": "Motyle", "lisc_opadly": "Opadle_Liscie",
        "zrodelko": "Zrodelko",
    }
    podkol = {}
    for klucz, nazwa in nazwy_sub.items():
        sub = bpy.data.collections.new(nazwa)
        kol_las.children.link(sub)
        podkol[klucz] = sub

    # ── Źródełko – przesunięte od centrum ──
    zrodlo_x = random.uniform(3, 7)
    zrodlo_y = random.uniform(-5, -2)
    obiekty_zrodlo, poz_zrodlo = stworz_zrodelko(zrodlo_x, zrodlo_y)
    przenies_do_kolekcji(obiekty_zrodlo, podkol["zrodelko"])

    # ── Faza 1 – główne rośliny rozrzucone po CAŁEJ mapie ──
    pozycje_drzew = []
    pozycje_kwiatow = []

    for _ in range(liczba_roslin):
        x, z = losowa_pozycja()

        # Omijaj źródełko
        if math.sqrt((x - zrodlo_x)**2 + (z - zrodlo_y)**2) < 2.5:
            continue

        typ = wybierz_typ_biomu(x, z)
        obiekty = stworz_rosline_typ(x, z, typ)

        if typ == "drzewo":
            pozycje_drzew.append((x, z))
        if typ in ("stokrotka", "chaber"):
            pozycje_kwiatow.append((x, z))

        przenies_do_kolekcji(obiekty, podkol[typ])

    # ── Faza 2 – grzyby, trawa, opadłe liście pod drzewami ──
    for dx, dz in pozycje_drzew:
        for _ in range(random.randint(1, 3)):
            gx = dx + random.uniform(-2.0, 2.0)
            gz = dz + random.uniform(-2.0, 2.0)
            obiekty = stworz_rosline_typ(gx, gz, "grzyb")
            przenies_do_kolekcji(obiekty, podkol["grzyb"])

        for _ in range(random.randint(3, 5)):
            tx = dx + random.uniform(-2.5, 2.5)
            tz = dz + random.uniform(-2.5, 2.5)
            obiekty = stworz_rosline_typ(tx, tz, "trawa")
            przenies_do_kolekcji(obiekty, podkol["trawa"])

        obiekty = stworz_opadle_liscie(dx, dz, TYPY_ROSLIN["lisc_opadly"])
        przenies_do_kolekcji(obiekty, podkol["lisc_opadly"])

    # ── Faza 3 – DUŻO trawy po całej mapie ──
    for _ in range(120):
        x, z = losowa_pozycja()
        obiekty = stworz_rosline_typ(x, z, "trawa")
        przenies_do_kolekcji(obiekty, podkol["trawa"])

    # ── Faza 4 – gęsta trawa przy źródełku ──
    for _ in range(30):
        kat = random.uniform(0, 2*math.pi)
        odl = random.uniform(2.0, 4.0)
        tx = zrodlo_x + math.cos(kat) * odl
        tz = zrodlo_y + math.sin(kat) * odl
        obiekty = stworz_rosline_typ(tx, tz, "trawa")
        przenies_do_kolekcji(obiekty, podkol["trawa"])

    # ── Faza 5 – motyle nad kwiatami ──
    for fx, fz in pozycje_kwiatow:
        if random.random() < 0.4:
            mx = fx + random.uniform(-0.3, 0.3)
            mz = fz + random.uniform(-0.3, 0.3)
            obiekty = stworz_motyla(mx, mz, TYPY_ROSLIN["motyl"])
            przenies_do_kolekcji(obiekty, podkol["motyl"])

    # ── Podłoże (dokładnie = ROZMIAR_MAPY) ──
    bpy.ops.mesh.primitive_plane_add(size=ROZMIAR_MAPY, location=(0, 0, 0))
    podloze = bpy.context.active_object
    podloze.name = "Podloze"
    mat_pod = stworz_material("Podloze_Mat", (0.06, 0.22, 0.04, 1), roughness=0.95)
    podloze.data.materials.append(mat_pod)
    przenies_do_kolekcji([podloze], kol_las)

    # ── Kamera – oddalona by łapać większość mapy ──
    bpy.ops.object.camera_add(location=(28, -30, 25))
    kamera = bpy.context.active_object
    kamera.rotation_euler = (math.radians(50), 0, math.radians(42))
    bpy.context.scene.camera = kamera

    # ── Światło główne ──
    bpy.ops.object.light_add(type='SUN', location=(10, -10, 20))
    sun = bpy.context.active_object
    sun.rotation_euler = (math.radians(40), 0, math.radians(25))
    sun.data.energy = 4.0

    # ── Oświetlenie nastrojowe ──
    for dx, dz in pozycje_drzew[:5]:
        bpy.ops.object.light_add(type='POINT',
                                 location=(dx + random.uniform(-0.5, 0.5),
                                           dz + random.uniform(-0.5, 0.5),
                                           random.uniform(1.5, 3.0)))
        light = bpy.context.active_object
        light.data.energy = random.uniform(10, 25)
        light.data.color = (1.0, 0.85, 0.55)
        light.data.shadow_soft_size = 2.0
        light.name = "Swiatlo_Nastrojowe"

    # ── Tło ──
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.55, 0.75, 0.95, 1)
        bg.inputs["Strength"].default_value = 1.0

    # ── Render ──
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 800
    scene.render.image_settings.file_format = 'PNG'

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()

    scene.render.filepath = os.path.join(script_dir, "las_05.png")
    bpy.ops.render.render(write_still=True)
    print(f"Render zapisany: {scene.render.filepath}")


# ── Main ──────────────────────────────────────────────────────────────

generuj_las()
