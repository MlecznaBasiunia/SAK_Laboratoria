extends Camera3D

@export var lag_speed: float = 7.0
@export var camera_target: Node3D

func _process(delta: float) -> void:
	if camera_target == null:
		return
	global_position = global_position.lerp(camera_target.global_position, lag_speed * delta)
