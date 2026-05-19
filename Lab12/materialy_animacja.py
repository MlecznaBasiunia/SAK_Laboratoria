import bpy
import math

NAZWY_KANDYDACI_MATERIALU = [
    "Roslina_Bioluminescencja",
    "Mat_Bioluminescencja",
    "Bioluminescencja",
]
NAZWA_NODE_EMISSION = "Emission"

KLATKA_START = 1
KLATKA_KONIEC = 125
KLATKA_PAK_START = 30
KLATKA_PAK_KONIEC = 90

MIN_STR = 0.5
MAX_STR_BAZOWY = 2.0
MAX_STR_PIK = 6.0
OKRES = 25

KOLOR_START = (0.0, 0.7, 1.0, 1.0)
KOLOR_KONIEC = (0.2, 1.0, 0.4, 1.0)


def znajdz_material_bioluminescencja():
    for nazwa in NAZWY_KANDYDACI_MATERIALU:
        m = bpy.data.materials.get(nazwa)
        if m:
            return m
    for m in bpy.data.materials:
        if "biolumin" in m.name.lower():
            print(f"[INFO] Fuzzy match: znaleziono materiał '{m.name}'")
            return m
    return None


def znajdz_node(mat, nazwa, typ_zapasowy=None):
    node = mat.node_tree.nodes.get(nazwa)
    if node is None and typ_zapasowy:
        for n in mat.node_tree.nodes:
            if n.type == typ_zapasowy:
                print(f"[INFO] Nie znaleziono '{nazwa}', używam '{n.name}' (typ {typ_zapasowy})")
                return n
    if node is None:
        dostepne = [n.name for n in mat.node_tree.nodes]
        raise KeyError(f"Węzeł '{nazwa}' nie istnieje w '{mat.name}'. Dostępne: {dostepne}")
    return node


def wyczysc_animacje_materialu(mat):
    if mat.node_tree.animation_data and mat.node_tree.animation_data.action:
        mat.node_tree.animation_data.action = None


def smoothstep(edge0, edge1, x):
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def pulsuj_emission(mat, min_str=MIN_STR, max_str_bazowy=MAX_STR_BAZOWY,
                    max_str_pik=MAX_STR_PIK, okres=OKRES):
    emission = znajdz_node(mat, NAZWA_NODE_EMISSION, typ_zapasowy='EMISSION')
    sciezka = f'nodes["{emission.name}"].inputs["Strength"].default_value'

    for klatka in range(KLATKA_START, KLATKA_KONIEC + 1):
        if klatka < KLATKA_PAK_START:
            max_str = max_str_bazowy
        elif klatka > KLATKA_PAK_KONIEC:
            max_str = max_str_pik
        else:
            s = smoothstep(KLATKA_PAK_START, KLATKA_PAK_KONIEC, klatka)
            max_str = max_str_bazowy + (max_str_pik - max_str_bazowy) * s

        srednia = (min_str + max_str) / 2.0
        amplituda = (max_str - min_str) / 2.0
        t = (klatka - KLATKA_START) * (2 * math.pi / okres)
        emission.inputs["Strength"].default_value = srednia + amplituda * math.sin(t)
        mat.node_tree.keyframe_insert(data_path=sciezka, frame=klatka)

    print(f"[OK] Pulsacja Emission Strength: {min_str}-{max_str_bazowy} -> {min_str}-{max_str_pik} (smoothstep)")


def pulsuj_principled_emission_backup(mat):
    princ = mat.node_tree.nodes.get("Principled BSDF")
    if princ is None:
        for n in mat.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                princ = n
                break
    if princ is None:
        return
    strength_input = princ.inputs.get("Emission Strength")
    if strength_input is None:
        return

    sciezka = f'nodes["{princ.name}"].inputs["Emission Strength"].default_value'
    for klatka in range(KLATKA_START, KLATKA_KONIEC + 1):
        if klatka < KLATKA_PAK_START:
            max_str = MAX_STR_BAZOWY
        elif klatka > KLATKA_PAK_KONIEC:
            max_str = MAX_STR_PIK
        else:
            s = smoothstep(KLATKA_PAK_START, KLATKA_PAK_KONIEC, klatka)
            max_str = MAX_STR_BAZOWY + (MAX_STR_PIK - MAX_STR_BAZOWY) * s
        srednia = (MIN_STR + max_str) / 2.0
        amplituda = (max_str - MIN_STR) / 2.0
        t = (klatka - KLATKA_START) * (2 * math.pi / OKRES)
        strength_input.default_value = srednia + amplituda * math.sin(t)
        mat.node_tree.keyframe_insert(data_path=sciezka, frame=klatka)
    print("[OK] Pulsacja Principled BSDF Emission Strength (backup dla Blender 5.x)")


def animuj_kolor_emisji(mat):
    emission = znajdz_node(mat, NAZWA_NODE_EMISSION, typ_zapasowy='EMISSION')
    sciezka = f'nodes["{emission.name}"].inputs["Color"].default_value'

    emission.inputs["Color"].default_value = KOLOR_START
    mat.node_tree.keyframe_insert(data_path=sciezka, frame=KLATKA_START)
    emission.inputs["Color"].default_value = KOLOR_KONIEC
    mat.node_tree.keyframe_insert(data_path=sciezka, frame=KLATKA_KONIEC)

    princ = mat.node_tree.nodes.get("Principled BSDF")
    if princ is None:
        for n in mat.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                princ = n
                break
    if princ is not None:
        emission_color = princ.inputs.get("Emission Color")
        if emission_color is not None:
            sciezka_p = f'nodes["{princ.name}"].inputs["Emission Color"].default_value'
            emission_color.default_value = KOLOR_START
            mat.node_tree.keyframe_insert(data_path=sciezka_p, frame=KLATKA_START)
            emission_color.default_value = KOLOR_KONIEC
            mat.node_tree.keyframe_insert(data_path=sciezka_p, frame=KLATKA_KONIEC)

    print(f"[OK] Animacja koloru: błękit -> zielony")


def animuj_tlo_swiata():
    world = bpy.data.worlds.get("World")
    if world is None or not world.use_nodes:
        return
    bg = world.node_tree.nodes.get("Background")
    if bg is None:
        for n in world.node_tree.nodes:
            if n.type == 'BACKGROUND':
                bg = n
                break
    if bg is None:
        return

    if world.node_tree.animation_data and world.node_tree.animation_data.action:
        world.node_tree.animation_data.action = None

    sciezka_str = f'nodes["{bg.name}"].inputs["Strength"].default_value'

    bg.inputs["Strength"].default_value = 0.5
    world.node_tree.keyframe_insert(data_path=sciezka_str, frame=KLATKA_START)
    bg.inputs["Strength"].default_value = 0.5
    world.node_tree.keyframe_insert(data_path=sciezka_str, frame=KLATKA_PAK_START)
    bg.inputs["Strength"].default_value = 0.15
    world.node_tree.keyframe_insert(data_path=sciezka_str, frame=KLATKA_PAK_KONIEC)
    bg.inputs["Strength"].default_value = 0.15
    world.node_tree.keyframe_insert(data_path=sciezka_str, frame=KLATKA_KONIEC)

    print("[OK] Tło świata przyciemnia się gdy roślina mocniej świeci")


def main_materialy():
    print("=" * 55)
    print("  Lab 12 cz. A — Animacja Materiału Bioluminescencji")
    print("=" * 55)

    mat = znajdz_material_bioluminescencja()
    if mat is None:
        dostepne = [m.name for m in bpy.data.materials]
        print(f"[BŁĄD] Brak materiału bioluminescencji.")
        print(f"       Dostępne materiały: {dostepne}")
        return

    print(f"[OK] Materiał: '{mat.name}'")
    wyczysc_animacje_materialu(mat)
    pulsuj_emission(mat)
    pulsuj_principled_emission_backup(mat)
    animuj_kolor_emisji(mat)
    animuj_tlo_swiata()

    print("\n[OK] Animacja materiałów zakończona")
    print("     Sprawdź: Shader Editor + Graph Editor (filtr Materials)")


main_materialy()
