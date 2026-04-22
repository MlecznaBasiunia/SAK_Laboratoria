extends Node3D

## jednostek/sekundę
@export var move_speed: float = 8.0

## margines
@export var limit_x: float = 6.0
@export var limit_y: float = 3.5

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
