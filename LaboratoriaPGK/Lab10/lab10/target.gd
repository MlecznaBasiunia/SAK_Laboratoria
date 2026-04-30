extends Node3D

static var score: int = 0

func _ready() -> void:
	$Area3D.area_entered.connect(_on_hit)

func _on_hit(_area: Area3D) -> void:
	score += 1
	print("Trafiony! Wynik: ", score)
	queue_free()
