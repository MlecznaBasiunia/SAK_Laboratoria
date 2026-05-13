extends Node

const ENEMY_SCENE = preload("res://enemy.tscn")

@onready var _path_follow: Node3D = $"../Path3D/PathFollow3D"
@onready var _hud_label: Label = $"../CanvasLayer/HUDLabel"

var _waves: Array = [
	{ "count": 3, "x_positions": [-3.0, 0.0, 3.0], "z_offset": -30.0, "delay": 2.0 },
	{ "count": 2, "x_positions": [-2.0, 2.0], "z_offset": -35.0, "delay": 7.0 },
	{ "count": 4, "x_positions": [-4.0, -1.5, 1.5, 4.0], "z_offset": -30.0, "delay": 13.0 },
]
var _spawned: Array = []
var _time: float = 0.0
var _score: int = 0
var _current_wave: int = 0
var _enemy_count: int = 0

func _ready() -> void:
	_spawned.resize(_waves.size())
	_spawned.fill(false)
	if _path_follow == null:
		printerr("WaveSpawner: PathFollow3D not found!")
	_update_hud()

func _process(delta: float) -> void:
	if _path_follow == null:
		return
	_time += delta
	for i in _waves.size():
		if not _spawned[i] and _time >= _waves[i]["delay"]:
			_spawn_wave(i)
			_spawned[i] = true

func _spawn_wave(index: int) -> void:
	_current_wave = index + 1
	var wave = _waves[index]
	for j in wave["count"]:
		var enemy = ENEMY_SCENE.instantiate()
		get_tree().root.add_child(enemy)
		var x: float = wave["x_positions"][j] if j < wave["x_positions"].size() else 0.0
		enemy.global_position = _path_follow.global_position + Vector3(x, 0.0, wave["z_offset"])
		enemy.died.connect(_on_enemy_died)
		_enemy_count += 1
	_update_hud()

func _on_enemy_died(points: int) -> void:
	_score += points
	_enemy_count = maxi(_enemy_count - 1, 0)
	print("Score: ", _score)
	_update_hud()

func _update_hud() -> void:
	if not is_instance_valid(_hud_label):
		return
	_hud_label.text = "Fala: %d / %d\nWrogowie: %d" % [_current_wave, _waves.size(), _enemy_count]
