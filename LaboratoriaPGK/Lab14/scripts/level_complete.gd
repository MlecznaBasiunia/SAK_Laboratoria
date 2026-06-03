extends Control

func _ready() -> void:
	$VBoxContainer/ScoreLabel.text = "Wynik końcowy: %d" % GameManager.score
	$VBoxContainer/MenuButton.pressed.connect(func() -> void:
		get_tree().change_scene_to_file("res://main_menu.tscn"))
