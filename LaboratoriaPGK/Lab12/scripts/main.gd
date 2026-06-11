extends Node3D

@onready var _boss = $Boss

func _ready() -> void:
	GameManager.game_over.connect(func() -> void:
		get_tree().change_scene_to_file("res://game_over.tscn"))
	GameManager.level_complete.connect(func() -> void:
		get_tree().change_scene_to_file("res://level_complete.tscn"))
	_boss.died.connect(func() -> void:
		GameManager.level_complete.emit())
