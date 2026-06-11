extends CanvasLayer

@onready var _score_label: Label       = $ScoreLabel
@onready var _lives_label: Label       = $LivesLabel
@onready var _hp_bar: ProgressBar      = $HPBar
@onready var _boss_hp_bar: ProgressBar = $BossHPBar
@onready var _boss_hp_label: Label     = $BossHPLabel
@onready var _lock_on: Panel           = $LockOnIndicator

var _boss: Node3D     = null
var _camera: Camera3D = null

func _ready() -> void:
	_hp_bar.max_value = GameManager.player_max_hp
	_hp_bar.value     = GameManager.player_hp
	_score_label.text = "Wynik: %d" % GameManager.score
	_lives_label.text = "Życia: %d"  % GameManager.lives
	GameManager.score_changed.connect(func(v: int) -> void: _score_label.text = "Wynik: %d" % v)
	GameManager.lives_changed.connect(func(v: int) -> void: _lives_label.text = "Życia: %d"  % v)
	GameManager.hp_changed.connect(   func(v: int) -> void: _hp_bar.value = v)
	_boss_hp_bar.visible   = false
	_boss_hp_label.visible = false
	_lock_on.visible       = false
	call_deferred("_find_boss_and_camera")

func _find_boss_and_camera() -> void:
	var bosses := get_tree().get_nodes_in_group("boss")
	if not bosses.is_empty():
		_boss = bosses[0]
		_boss_hp_bar.max_value = _boss.max_hp
		_boss_hp_bar.value     = _boss.max_hp
		_boss_hp_bar.visible   = true
		_boss_hp_label.visible = true
		_boss.died.connect(_on_boss_died)
	_camera = get_viewport().get_camera_3d()

func _process(_delta: float) -> void:
	if not is_instance_valid(_boss):
		return
	_boss_hp_bar.value = _boss.hp
	_tint_boss_hp_bar()
	_update_lock_on()

func _tint_boss_hp_bar() -> void:
	var ratio := float(_boss.hp) / float(_boss.max_hp)
	var color: Color
	if ratio > 0.5:
		color = Color(0.18, 0.9, 0.18).lerp(Color(1.0, 0.85, 0.1), 1.0 - (ratio - 0.5) * 2.0)
	else:
		color = Color(1.0, 0.85, 0.1).lerp(Color(0.95, 0.1, 0.08), 1.0 - ratio * 2.0)
	_boss_hp_bar.modulate = color

func _update_lock_on() -> void:
	if _camera == null or not is_instance_valid(_boss):
		_lock_on.visible = false
		return
	var cam_fwd := -_camera.global_transform.basis.z
	var to_boss := _boss.global_position - _camera.global_position
	if to_boss.dot(cam_fwd) <= 0.0:
		_lock_on.visible = false
		return
	var screen_pos := _camera.unproject_position(_boss.global_position)
	var vp := get_viewport().get_visible_rect().size
	if screen_pos.x < 0.0 or screen_pos.x > vp.x or screen_pos.y < 0.0 or screen_pos.y > vp.y:
		_lock_on.visible = false
		return
	_lock_on.visible  = true
	_lock_on.position = screen_pos - _lock_on.size * 0.5

func _on_boss_died() -> void:
	_boss_hp_bar.visible   = false
	_boss_hp_label.visible = false
	_lock_on.visible       = false
	_boss = null
