extends Node3D

## jednostek/sekundę
@export var move_speed: float = 8.0

## margines
@export var limit_x: float = 6.0
@export var limit_y: float = 3.5

@export var bullet_scene: PackedScene

var _shoot_cooldown: float = 0.0

func _process(delta: float) -> void:

	var input_dir := Vector2.ZERO

	if Input.is_action_pressed("ui_left"):
		input_dir.x -= 1.0
	if Input.is_action_pressed("ui_right"):
		input_dir.x += 1.0
	if Input.is_action_pressed("ui_up"):
		input_dir.y += 1.0
	if Input.is_action_pressed("ui_down"):
		input_dir.y -= 1.0

	# żeby przekątna nie była szybsza bo się jebie jak polańska na OFie
	input_dir = input_dir.normalized()

	position.x += input_dir.x * move_speed * delta
	position.y += input_dir.y * move_speed * delta

	position.x = clamp(position.x, -limit_x, limit_x)
	position.y = clamp(position.y, -limit_y, limit_y)

	_shoot_cooldown -= delta
	if Input.is_action_just_pressed("ui_accept") and _shoot_cooldown <= 0.0:
		_shoot()
		_shoot_cooldown = 0.3

func _shoot() -> void:
	if bullet_scene == null:
		return
	var bullet = bullet_scene.instantiate()
	get_tree().root.add_child(bullet)
	bullet.global_position = global_position
