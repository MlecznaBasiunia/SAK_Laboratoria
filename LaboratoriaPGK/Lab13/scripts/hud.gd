extends CanvasLayer

@onready var _score_label: Label = $ScoreLabel
@onready var _lives_label: Label = $LivesLabel
@onready var _hp_bar: ProgressBar = $HPBar

func _ready() -> void:
	_hp_bar.max_value = GameManager.player_max_hp
	_hp_bar.value = GameManager.player_hp
	_score_label.text = "Wynik: %d" % GameManager.score
	_lives_label.text = "Życia: %d" % GameManager.lives
	GameManager.score_changed.connect(func(v: int) -> void: _score_label.text = "Wynik: %d" % v)
	GameManager.lives_changed.connect(func(v: int) -> void: _lives_label.text = "Życia: %d" % v)
	GameManager.hp_changed.connect(func(v: int) -> void: _hp_bar.value = v)
