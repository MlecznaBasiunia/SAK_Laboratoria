extends Node3D

signal died(points: int)

const BULLET_SCENE    = preload("res://bullet.tscn")
const EXPLOSION_SCENE = preload("res://explosion.tscn")

const SPIN_DURATION   := 0.9
const EXPLOSION_SCALE := Vector3(0.4, 0.4, 0.4)
const BULLET_LAYER    := 8
const BULLET_MASK     := 1

@export var hp: int               = 2
@export var score_value: int      = 100
@export var sway_amplitude: float = 2.0
@export var sway_period: float    = 2.0
@export var shoot_interval: float = 2.5

var _shoot_timer: float = 0.0
var _start_x: float     = 0.0

func _ready() -> void:
	_start_x = position.x
	add_to_group("enemies")
	$Area3D.area_entered.connect(_on_area_entered)
	var tween := create_tween()
	tween.set_loops()
	tween.set_trans(Tween.TRANS_SINE)
	tween.set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(self, "position:x", _start_x + sway_amplitude, sway_period * 0.5)
	tween.tween_property(self, "position:x", _start_x - sway_amplitude, sway_period * 0.5)

func _process(delta: float) -> void:
	_shoot_timer += delta
	if _shoot_timer >= shoot_interval:
		_shoot_timer = 0.0
		_shoot_at_player()

func _shoot_at_player() -> void:
	var players := get_tree().get_nodes_in_group("player")
	if players.is_empty():
		return
	var player := players[0] as Node3D
	var dir := (player.global_position - global_position).normalized()
	var spin := create_tween()
	spin.set_trans(Tween.TRANS_SINE)
	spin.set_ease(Tween.EASE_IN_OUT)
	spin.tween_property($EnemyModel, "rotation:x",
		$EnemyModel.rotation.x + TAU, SPIN_DURATION)
	_spawn_bullet(dir)

func _spawn_bullet(dir: Vector3) -> void:
	var bullet := BULLET_SCENE.instantiate() as Area3D
	get_tree().root.add_child(bullet)
	bullet.global_position = global_position
	bullet.set("direction", dir)
	bullet.collision_layer = BULLET_LAYER
	bullet.collision_mask  = BULLET_MASK

func _on_area_entered(_area: Area3D) -> void:
	if is_queued_for_deletion():
		return
	hp -= 1
	if hp <= 0:
		_spawn_explosion()
		died.emit(score_value)
		queue_free()

func _spawn_explosion() -> void:
	var exp := EXPLOSION_SCENE.instantiate() as Node3D
	get_tree().root.add_child(exp)
	exp.global_position = global_position
	exp.scale = EXPLOSION_SCALE
