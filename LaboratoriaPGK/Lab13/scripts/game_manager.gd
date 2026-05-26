extends Node

var score: int = 0
var lives: int = 3
var player_max_hp: int = 3
var player_hp: int = 3

signal score_changed(new_score: int)
signal lives_changed(new_lives: int)
signal hp_changed(new_hp: int)
signal game_over
signal level_complete
signal enemy_killed
signal player_damaged

var _sfx_kill: AudioStreamPlayer
var _sfx_hit: AudioStreamPlayer
var _sfx_over: AudioStreamPlayer

func _ready() -> void:
	_sfx_kill = _make_player(_beep(880.0, 0.08))
	_sfx_hit  = _make_player(_beep(140.0, 0.22))
	_sfx_over = _make_player(_sweep(440.0, 80.0, 1.0))
	enemy_killed.connect(func(): _sfx_kill.play())
	player_damaged.connect(func(): _sfx_hit.play())
	game_over.connect(func(): _sfx_over.play())

func add_score(points: int) -> void:
	score += points
	score_changed.emit(score)
	enemy_killed.emit()

func player_hit(damage: int = 1) -> void:
	player_hp -= damage
	hp_changed.emit(player_hp)
	player_damaged.emit()
	if player_hp <= 0:
		lives -= 1
		lives_changed.emit(lives)
		player_hp = player_max_hp
		hp_changed.emit(player_hp)
		if lives <= 0:
			game_over.emit()

func reset() -> void:
	score = 0
	lives = 3
	player_hp = player_max_hp
	score_changed.emit(score)
	lives_changed.emit(lives)
	hp_changed.emit(player_hp)

# ── audio helpers ───────────────────────────────────────────────────────────

func _make_player(stream: AudioStreamWAV) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.stream = stream
	add_child(p)
	return p

func _beep(freq: float, dur: float) -> AudioStreamWAV:
	const SR := 22050
	var n := int(SR * dur)
	var data := PackedByteArray()
	data.resize(n)
	for i in n:
		var fade := 1.0 - float(i) / n
		data[i] = clamp(int(127.0 + 110.0 * fade * sin(TAU * freq * float(i) / SR)), 0, 255)
	var s := AudioStreamWAV.new()
	s.format = 0 # FORMAT_8_BIT
	s.mix_rate = SR
	s.stereo = false
	s.data = data
	return s

func _sweep(freq_start: float, freq_end: float, dur: float) -> AudioStreamWAV:
	const SR := 22050
	var n := int(SR * dur)
	var data := PackedByteArray()
	data.resize(n)
	for i in n:
		var t := float(i) / SR
		var fade := 1.0 - t / dur
		var freq := freq_start + (freq_end - freq_start) * (t / dur)
		data[i] = clamp(int(127.0 + 110.0 * fade * sin(TAU * freq * t)), 0, 255)
	var s := AudioStreamWAV.new()
	s.format = 0 # FORMAT_8_BIT
	s.mix_rate = SR
	s.stereo = false
	s.data = data
	return s
