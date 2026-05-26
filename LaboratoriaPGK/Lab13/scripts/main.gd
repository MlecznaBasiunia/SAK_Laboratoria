extends Node3D

func _ready() -> void:
	GameManager.game_over.connect(func() -> void:
		get_tree().change_scene_to_file("res://game_over.tscn"))
	GameManager.level_complete.connect(func() -> void:
		get_tree().change_scene_to_file("res://level_complete.tscn"))
