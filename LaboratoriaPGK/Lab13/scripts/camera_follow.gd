extends Camera3D

@export var lag_speed: float = 7.0

@onready var _target: Node3D = $"../Path3D/PathFollow3D/CameraTarget"

func _process(delta: float) -> void:
	if _target == null:
		return
	global_position = global_position.lerp(_target.global_position, lag_speed * delta)
