extends Node3D

signal died(points: int)

const BULLET_SCENE = preload("res://bullet.tscn")

@export var hp: int = 2
@export var score_value: int = 100
@export var sway_amplitude: float = 2.0
@export var sway_period: float = 2.0
@export var shoot_interval: float = 2.5

var _shoot_timer: float = 0.0
var _start_x: float = 0.0

func _ready() -> void:
	_start_x = position.x
	add_to_group("enemies")
	$Area3D.area_entered.connect(_on_area_entered)

	var tween = create_tween()
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
	var players = get_tree().get_nodes_in_group("player")
	if players.is_empty():
		return
	var player: Node3D = players[0]
	var dir := (player.global_position - global_position).normalized()

	var spin_tween = create_tween()
	spin_tween.set_trans(Tween.TRANS_SINE)
	spin_tween.set_ease(Tween.EASE_IN_OUT)
	spin_tween.tween_property($EnemyMesh, "rotation:x", $EnemyMesh.rotation.x + TAU, 0.9)

	var bullet = BULLET_SCENE.instantiate()
	get_tree().root.add_child(bullet)
	bullet.global_position = global_position
	bullet.direction = dir
	bullet.collision_layer = 8
	bullet.collision_mask = 1

func _on_area_entered(_area: Area3D) -> void:
	hp -= 1
	if hp <= 0:
		died.emit(score_value)
		queue_free()
