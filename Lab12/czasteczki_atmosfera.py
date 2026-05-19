import bpy
import random
import math

NAZWA_KOLEKCJI = "Pyl"
NAZWA_MATERIALU = "Pyl_Mat"

LICZBA_CZASTECZEK = 60
KLATKA_START = 1
KLATKA_KONIEC = 125

CZAS_ZYCIA_MIN = 40
CZAS_ZYCIA_MAX = 80

SREDNICA_CZASTECZKI = 0.04
ZAKRES_EMISJI_XY = (-2.0, 2.0)
WYSOKOSC_EMISJI_Z = (0.0, 2.5)
PREDKOSC_DRIFTU = 0.02
SILA_WIATRU_X = 0.005
AMPLITUDA_UNOSZENIA = 0.3
CZESTOSC_UNOSZENIA = 0.1

KLATEK_NA_FALE = 12
CZASTECZEK_NA_FALE = 10

SEED = 42


class Czasteczka:

    KLATKI_NARODZIN = 10

    def __init__(self, indeks, klatka_narodzin, czas_zycia,
                 pozycja_start, predkosc_drift, faza_unoszenia):
        self.indeks = indeks
        self.klatka_narodzin = klatka_narodzin
        self.czas_zycia = czas_zycia
        self.klatka_smierci = klatka_narodzin + czas_zycia
        self.pozycja_start = pozycja_start
        self.predkosc_drift = predkosc_drift
        self.faza_unoszenia = faza_unoszenia
        self.obj = None

    def stworz(self, kolekcja, material):
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=SREDNICA_CZASTECZKI,
            location=self.pozycja_start,
            segments=8, ring_count=4
        )
        self.obj = bpy.context.active_object
        self.obj.name = f"Czasteczka_{self.indeks:03d}"

        if self.obj.data.materials:
            self.obj.data.materials[0] = material
        else:
            self.obj.data.materials.append(material)

        for c in list(self.obj.users_collection):
            c.objects.unlink(self.obj)
        kolekcja.objects.link(self.obj)

        for poly in self.obj.data.polygons:
            poly.use_smooth = True

    def aktualna_pozycja(self, klatka):
        t = klatka - self.klatka_narodzin
        x = self.pozycja_start[0] + self.predkosc_drift[0] * t + SILA_WIATRU_X * t
        y = self.pozycja_start[1] + self.predkosc_drift[1] * t
        z = self.pozycja_start[2] + AMPLITUDA_UNOSZENIA * math.sin(
            t * CZESTOSC_UNOSZENIA + self.faza_unoszenia
        )
        if z < 0:
            z = -z * 0.3
        return (x, y, z)

    def aktualna_skala(self, klatka):
        wiek = klatka - self.klatka_narodzin
        if wiek < self.KLATKI_NARODZIN:
            return wiek / self.KLATKI_NARODZIN
        elif wiek > self.czas_zycia - self.KLATKI_NARODZIN:
            return max(0.0, (self.czas_zycia - wiek) / self.KLATKI_NARODZIN)
        else:
            return 1.0

    def wstaw_keyframes(self):
        if self.obj is None:
            return

        self.obj.scale = (0.0, 0.0, 0.0)
        self.obj.keyframe_insert("scale", frame=max(self.klatka_narodzin - 1, KLATKA_START))
        self.obj.keyframe_insert("scale", frame=min(self.klatka_smierci + 1, KLATKA_KONIEC))

        for klatka in range(self.klatka_narodzin, self.klatka_smierci + 1):
            if klatka < KLATKA_START or klatka > KLATKA_KONIEC:
                continue
            self.obj.location = self.aktualna_pozycja(klatka)
            s = self.aktualna_skala(klatka)
            self.obj.scale = (s, s, s)
            self.obj.keyframe_insert("location", frame=klatka)
            self.obj.keyframe_insert("scale", frame=klatka)


def przygotuj_material(nazwa=NAZWA_MATERIALU):
    mat = bpy.data.materials.get(nazwa)
    if mat is None:
        mat = bpy.data.materials.new(name=nazwa)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for n in list(nodes):
        nodes.remove(n)

    output = nodes.new(type='ShaderNodeOutputMaterial')
    emission = nodes.new(type='ShaderNodeEmission')
    emission.inputs["Color"].default_value = (1.0, 0.95, 0.7, 1.0)
    emission.inputs["Strength"].default_value = 3.0
    output.location = (200, 0)
    emission.location = (0, 0)
    links.new(emission.outputs[0], output.inputs[0])

    if hasattr(mat, 'blend_method'):
        try:
            mat.blend_method = 'BLEND'
        except (TypeError, AttributeError):
            pass

    return mat


def przygotuj_kolekcje(nazwa=NAZWA_KOLEKCJI):
    kolekcja = bpy.data.collections.get(nazwa)
    if kolekcja:
        for obj in list(kolekcja.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        print(f"[OK] Wyczyszczono istniejącą kolekcję '{nazwa}'")
    else:
        kolekcja = bpy.data.collections.new(nazwa)
        bpy.context.scene.collection.children.link(kolekcja)
        print(f"[OK] Utworzono nową kolekcję '{nazwa}'")
    return kolekcja


def generuj_czasteczki(liczba=LICZBA_CZASTECZEK):
    czasteczki = []
    for indeks in range(liczba):
        fala = indeks // CZASTECZEK_NA_FALE
        klatka_narodzin = KLATKA_START + fala * KLATEK_NA_FALE
        if klatka_narodzin >= KLATKA_KONIEC:
            break
        czas_zycia = random.randint(CZAS_ZYCIA_MIN, CZAS_ZYCIA_MAX)
        pozycja = (
            random.uniform(*ZAKRES_EMISJI_XY),
            random.uniform(*ZAKRES_EMISJI_XY),
            random.uniform(*WYSOKOSC_EMISJI_Z),
        )
        drift = (
            random.uniform(-PREDKOSC_DRIFTU, PREDKOSC_DRIFTU),
            random.uniform(-PREDKOSC_DRIFTU, PREDKOSC_DRIFTU),
        )
        czasteczki.append(Czasteczka(
            indeks=indeks,
            klatka_narodzin=klatka_narodzin,
            czas_zycia=czas_zycia,
            pozycja_start=pozycja,
            predkosc_drift=drift,
            faza_unoszenia=random.uniform(0, 2 * math.pi),
        ))
    return czasteczki


def wymus_object_mode():
    try:
        if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        pass


def main_czasteczki():
    print("=" * 55)
    print("  Lab 12 cz. B — System Cząsteczek Atmosferycznych")
    print("=" * 55)

    random.seed(SEED)
    wymus_object_mode()

    bpy.context.scene.frame_start = KLATKA_START
    bpy.context.scene.frame_end = KLATKA_KONIEC

    material = przygotuj_material()
    kolekcja = przygotuj_kolekcje()
    czasteczki = generuj_czasteczki()

    print(f"[INFO] Generuję {len(czasteczki)} cząsteczek...")
    for i, c in enumerate(czasteczki):
        c.stworz(kolekcja, material)
        c.wstaw_keyframes()
        if (i + 1) % 10 == 0:
            print(f"  ...{i + 1}/{len(czasteczki)}")

    print(f"\n[OK] Wygenerowano {len(czasteczki)} cząsteczek w kolekcji '{NAZWA_KOLEKCJI}'")
    print(f"     Materiał współdzielony: '{material.name}'")
    print(f"     Seed: {SEED} (powtarzalne wyniki)")
    print(f"     Fale: co {KLATEK_NA_FALE} klatek po {CZASTECZEK_NA_FALE} cząsteczek")


main_czasteczki()
