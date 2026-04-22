extends PathFollow3D

@export var max_rail_speed: float = 0.08
@export var ramp_duration: float = 5.0

var _elapsed: float = 0.0

func _process(delta: float) -> void:
	_elapsed += delta

	var t: float = clampf(_elapsed / ramp_duration, 0.0, 1.0)
	var current_speed: float = lerpf(0.0, max_rail_speed, t)

	progress_ratio += current_speed * delta

	if progress_ratio >= 1.0:
		progress_ratio = 1.0
		set_process(false)
