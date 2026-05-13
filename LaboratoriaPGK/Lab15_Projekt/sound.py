"""Procedural sound effects and dynamic music for Asteroids on Steroids.

All sounds are generated mathematically at startup — no external audio files needed.
Music is synthesized in real-time via an AudioStream, adapting to gameplay intensity.
"""
import array
import math
import struct
import random as _random
from raylib import rl, ffi

SAMPLE_RATE = 22050  # Lower rate for SFX — plenty for retro sounds
MUSIC_RATE = 11025
MUSIC_BUFFER = 512   # Small buffer to avoid overrun

# Separate RNG for sound generation — never touches gameplay randomness
_R = _random.Random(12345)


# ──────────────────────────────────────────────
#  WAV helpers
# ──────────────────────────────────────────────

def _wav_bytes(samples, rate=SAMPLE_RATE):
    """Pack float samples [-1,1] into a mono 16-bit WAV byte string."""
    n = len(samples)
    # Clamp + convert all at once via array module (fast)
    pcm = array.array('h', (int(max(-1.0, min(1.0, s)) * 32767) for s in samples))
    raw = pcm.tobytes()
    hdr = struct.pack('<4sI4s', b'RIFF', 36 + len(raw), b'WAVE')
    fmt = struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, 1, rate, rate * 2, 2, 16)
    dat = struct.pack('<4sI', b'data', len(raw))
    return hdr + fmt + dat + raw


def _load_sound(samples, rate=SAMPLE_RATE):
    wav = _wav_bytes(samples, rate)
    buf = ffi.new('unsigned char[]', len(wav))
    ffi.memmove(buf, wav, len(wav))
    wave_obj = rl.LoadWaveFromMemory(b".wav", buf, len(wav))
    snd = rl.LoadSoundFromWave(wave_obj)
    rl.UnloadWave(wave_obj)
    return snd


# ──────────────────────────────────────────────
#  Sound-effect generators (all at SAMPLE_RATE)
# ──────────────────────────────────────────────

def _gen_shoot():
    n = int(SAMPLE_RATE * 0.06)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = (1 - t / 0.06) ** 2
        freq = 1200 - t * 13000
        s = math.sin(2 * math.pi * freq * t) * env * 0.25
        s += (_R.random() * 2 - 1) * env * 0.05
        out.append(s)
    return out


def _gen_explosion():
    n = int(SAMPLE_RATE * 0.3)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = (1 - t / 0.3) ** 2
        s = math.sin(2 * math.pi * 60 * t) * env * 0.3
        s += (_R.random() * 2 - 1) * env * 0.4
        out.append(s)
    return out


def _gen_big_explosion():
    n = int(SAMPLE_RATE * 0.45)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = (1 - t / 0.45) ** 1.5
        s = math.sin(2 * math.pi * 40 * t) * env * 0.4
        s += math.sin(2 * math.pi * 80 * t) * env * 0.2
        s += (_R.random() * 2 - 1) * env * 0.5
        out.append(s)
    return out


def _gen_powerup():
    n = int(SAMPLE_RATE * 0.15)
    out = []
    notes = [500, 700, 900]
    note_len = n // len(notes)
    for freq in notes:
        for i in range(note_len):
            t = i / SAMPLE_RATE
            env = 1 - (i / note_len) * 0.6
            s = math.sin(2 * math.pi * freq * t) * env * 0.2
            out.append(s)
    return out


def _gen_menu_select():
    n = int(SAMPLE_RATE * 0.04)
    return [math.sin(2 * math.pi * 800 * i / SAMPLE_RATE) * (1 - i / n) * 0.15
            for i in range(n)]


def _gen_menu_confirm():
    n = int(SAMPLE_RATE * 0.08)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 600 + t * 3000
        env = (1 - t / 0.08) ** 0.5
        out.append(math.sin(2 * math.pi * freq * t) * env * 0.2)
    return out


def _gen_boss_hit():
    n = int(SAMPLE_RATE * 0.12)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = (1 - t / 0.12) ** 1.5
        s = math.sin(2 * math.pi * 100 * t) * env * 0.35
        s += (_R.random() * 2 - 1) * env * 0.2
        out.append(s)
    return out


def _gen_ship_die():
    n = int(SAMPLE_RATE * 0.5)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = (1 - t / 0.5) ** 1.5
        freq = max(20, 300 - t * 500)
        s = math.sin(2 * math.pi * freq * t) * env * 0.2
        s += (_R.random() * 2 - 1) * env * 0.5
        out.append(s)
    return out


def _gen_combo():
    n = int(SAMPLE_RATE * 0.06)
    return [math.sin(2 * math.pi * 1000 * i / SAMPLE_RATE) * (1 - i / n) * 0.15
            for i in range(n)]


def _gen_wave_clear():
    notes = [523, 659, 784, 1047]  # C5 E5 G5 C6
    note_len = int(SAMPLE_RATE * 0.08)
    out = []
    for freq in notes:
        for i in range(note_len):
            t = i / SAMPLE_RATE
            env = 1 - (i / note_len) * 0.3
            s = math.sin(2 * math.pi * freq * t) * env * 0.18
            s += math.sin(2 * math.pi * freq * 2 * t) * env * 0.06
            out.append(s)
    return out


def _gen_perk():
    n = int(SAMPLE_RATE * 0.18)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = (1 - t / 0.18) ** 0.8
        lfo = 0.5 + 0.5 * math.sin(2 * math.pi * 12 * t)
        s = math.sin(2 * math.pi * 1200 * t) * env * lfo * 0.15
        s += math.sin(2 * math.pi * 1800 * t) * env * (1 - lfo) * 0.1
        out.append(s)
    return out


def _gen_shield_hit():
    n = int(SAMPLE_RATE * 0.08)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = (1 - t / 0.08) ** 3
        s = math.sin(2 * math.pi * 2000 * t) * env * 0.2
        s += (_R.random() * 2 - 1) * max(0, (0.01 - t) * 100) * 0.3
        out.append(s)
    return out


def _gen_crystal_hit():
    n = int(SAMPLE_RATE * 0.1)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = (1 - t / 0.1) ** 2
        s = math.sin(2 * math.pi * 2500 * t) * env * 0.12
        s += math.sin(2 * math.pi * 3800 * t) * env * 0.08
        out.append(s)
    return out


def _gen_portal():
    n = int(SAMPLE_RATE * 0.15)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = math.sin(math.pi * t / 0.15)
        freq = 200 + t * 1500
        s = math.sin(2 * math.pi * freq * t) * env * 0.12
        s += (_R.random() * 2 - 1) * env * 0.08
        out.append(s)
    return out


def _gen_overheat():
    n = int(SAMPLE_RATE * 0.15)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = 0.8 if t < 0.1 else max(0, 1 - (t - 0.1) / 0.05)
        freq = 800 if (int(t * 20) % 2 == 0) else 1000
        out.append(math.sin(2 * math.pi * freq * t) * env * 0.2)
    return out


# ──────────────────────────────────────────────
#  SoundSystem — main interface
# ──────────────────────────────────────────────

class SoundSystem:
    """Manages all game audio: procedural SFX + dynamic music stream."""

    def __init__(self):
        self.available = True
        self.sfx_enabled = True
        self.music_enabled = True
        self.sfx_volume = 0.7
        self.music_volume = 0.35
        self._sounds = {}
        self._stream = None

        try:
            rl.InitAudioDevice()
            if not rl.IsAudioDeviceReady():
                self.available = False
                return
        except Exception:
            self.available = False
            return

        # ---- load all SFX ----
        self._sounds = {
            'shoot':         _load_sound(_gen_shoot()),
            'explosion':     _load_sound(_gen_explosion()),
            'big_explosion': _load_sound(_gen_big_explosion()),
            'powerup':       _load_sound(_gen_powerup()),
            'menu_select':   _load_sound(_gen_menu_select()),
            'menu_confirm':  _load_sound(_gen_menu_confirm()),
            'boss_hit':      _load_sound(_gen_boss_hit()),
            'ship_die':      _load_sound(_gen_ship_die()),
            'combo':         _load_sound(_gen_combo()),
            'wave_clear':    _load_sound(_gen_wave_clear()),
            'perk':          _load_sound(_gen_perk()),
            'shield_hit':    _load_sound(_gen_shield_hit()),
            'crystal_hit':   _load_sound(_gen_crystal_hit()),
            'portal':        _load_sound(_gen_portal()),
            'overheat':      _load_sound(_gen_overheat()),
        }

        # ---- dynamic music via AudioStream ----
        rl.SetAudioStreamBufferSizeDefault(MUSIC_BUFFER)
        self._stream = rl.LoadAudioStream(MUSIC_RATE, 16, 1)
        rl.SetAudioStreamVolume(self._stream, self.music_volume)
        rl.PlayAudioStream(self._stream)
        self._music_buf = ffi.new(f'short[{MUSIC_BUFFER}]')

        # synthesis state
        self._bass_ph = 0.0
        self._pad_ph = [0.0, 0.0, 0.0]
        self._arp_ph = 0.0
        self._arp_idx = 0
        self._arp_timer = 0.0
        self._noise_lp = 0.0
        self._intensity = 0.0
        self._base_note = 55.0
        self._boss = False

    # ---- SFX ----

    def play(self, name, volume=1.0):
        if not self.available or not self.sfx_enabled:
            return
        snd = self._sounds.get(name)
        if snd:
            rl.SetSoundVolume(snd, self.sfx_volume * min(1.0, volume))
            rl.PlaySound(snd)

    # ---- Music ----

    def set_music_volume(self, vol):
        self.music_volume = vol
        if self.available and self._stream:
            rl.SetAudioStreamVolume(self._stream, vol)

    def update_music(self, intensity=0.0, sector=1, boss=False):
        """Call once per frame. *intensity* 0-1 drives musical complexity."""
        if not self.available or not self.music_enabled or not self._stream:
            return
        self._intensity += (intensity - self._intensity) * 0.02
        self._boss = boss
        notes = [55.0, 58.27, 61.74, 65.41, 69.30, 73.42]
        self._base_note = notes[(sector - 1) % len(notes)]

        if rl.IsAudioStreamProcessed(self._stream):
            self._fill_buffer()

    def _fill_buffer(self):
        n = MUSIC_BUFFER
        buf = self._music_buf
        base = self._base_note
        intensity = max(0.0, min(1.0, self._intensity))
        rate = MUSIC_RATE

        sin = math.sin
        pi2 = 2 * math.pi

        for i in range(n):
            sample = 0.0

            # ---- bass drone ----
            self._bass_ph += base / rate
            sample += sin(pi2 * self._bass_ph) * 0.12
            sample += sin(pi2 * self._bass_ph * 0.5) * 0.08

            # ---- pad chords (medium intensity) ----
            if intensity > 0.2:
                vol = min(1.0, (intensity - 0.2) * 2) * 0.06
                for j, m in enumerate((2.0, 3.0, 4.0)):
                    self._pad_ph[j] += (base * m) / rate
                    sample += sin(pi2 * self._pad_ph[j]) * vol

            # ---- arpeggio (high intensity) ----
            if intensity > 0.4:
                vol = min(1.0, (intensity - 0.4) * 2.5) * 0.05
                arp_notes = [1, 1.25, 1.5, 2.0, 1.5, 1.25]
                speed = 3 + intensity * 10
                self._arp_timer += 1.0 / rate
                if self._arp_timer > 1.0 / speed:
                    self._arp_timer = 0.0
                    self._arp_idx = (self._arp_idx + 1) % len(arp_notes)
                freq = base * 4 * arp_notes[self._arp_idx]
                self._arp_ph += freq / rate
                sq = 1.0 if (self._arp_ph % 1.0) < 0.5 else -1.0
                env = max(0.0, 1 - self._arp_timer * speed * 3)
                sample += sq * vol * env

            # ---- boss tension layer ----
            if self._boss:
                sample += sin(pi2 * self._bass_ph * 1.06) * 0.04
                pulse = 0.7 + 0.3 * max(0, sin(
                    pi2 * self._bass_ph * 3 / max(1, base)))
                sample *= pulse

            # ---- filtered noise ----
            noise = (_R.random() * 2 - 1) * 0.015 * max(0.1, intensity)
            self._noise_lp = self._noise_lp * 0.93 + noise * 0.07
            sample += self._noise_lp

            buf[i] = int(max(-0.95, min(0.95, sample)) * 32767)

        rl.UpdateAudioStream(self._stream, buf, n)

    # ---- cleanup ----

    def cleanup(self):
        if not self.available:
            return
        for snd in self._sounds.values():
            rl.UnloadSound(snd)
        if self._stream:
            rl.UnloadAudioStream(self._stream)
        rl.CloseAudioDevice()
