extends Control

func _ready() -> void:
	$VBoxContainer/PlayButton.pressed.connect(_on_play)

func _on_play() -> void:
	GameManager.reset()
	get_tree().change_scene_to_file("res://main.tscn")
