extends Node3D

signal died
signal hp_changed(new_hp: int)

enum State { IDLE, ATTACK, RETREAT, DEATH }

const BULLET_SCENE    = preload("res://bullet.tscn")
const EXPLOSION_SCENE = preload("res://explosion.tscn")

const IDLE_DURATION    := 2.0
const ATTACK_DURATION  := 4.0
const RETREAT_DURATION := 1.5
const SHOOT_INTERVAL   := 0.7
const SWAY_AMPLITUDE   := 3.2
const SWAY_PERIOD      := 2.0
const HOVER_AMPLITUDE  := 0.35
const DASH_RANGE       := 4.0

@export var max_hp: int = 20

var hp: int
var current_state: State = State.IDLE
var _phase2: bool = false
var _state_timer: float = 0.0
var _shoot_timer: float = 0.0
var _shoot_remaining: int = 0
var _tween: Tween = null
var _origin_x: float = 0.0
var _origin_y: float = 0.0

func _ready() -> void:
	hp = max_hp
	_origin_x = position.x
	_origin_y = position.y
	add_to_group("boss")
	$HitboxPhase1.area_entered.connect(func(_a: Area3D) -> void: take_hit(1))
	$HitboxPhase2.area_entered.connect(func(_a: Area3D) -> void: take_hit(2))
	$HitboxPhase2/CollisionShape3D.disabled = true
	var ring_spin := create_tween().set_loops()
	ring_spin.tween_property($BossModel/Ring, "rotation:y", TAU, 4.0)
	enter_state(State.IDLE)

func _process(delta: float) -> void:
	_state_timer -= delta
	match current_state:
		State.IDLE:
			if _state_timer <= 0.0:
				enter_state(State.ATTACK)
		State.ATTACK:
			_shoot_timer -= delta
			if _shoot_remaining > 0 and _shoot_timer <= 0.0:
				_fire_bullet()
				_shoot_remaining -= 1
				_shoot_timer = SHOOT_INTERVAL
			if _shoot_remaining <= 0 and _state_timer <= 0.0:
				enter_state(State.RETREAT)
		State.RETREAT:
			if _state_timer <= 0.0:
				enter_state(State.ATTACK)
		State.DEATH:
			pass

func enter_state(new_state: State) -> void:
	if _tween != null:
		_tween.kill()
		_tween = null
	current_state = new_state
	match new_state:
		State.IDLE:    _start_idle()
		State.ATTACK:  _start_attack()
		State.RETREAT: _start_retreat()
		State.DEATH:   _start_death()

func _start_idle() -> void:
	_state_timer = IDLE_DURATION
	_tween = create_tween().set_loops()
	_tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_tween.tween_property(self, "position:y", _origin_y + HOVER_AMPLITUDE, 1.0)
	_tween.tween_property(self, "position:y", _origin_y - HOVER_AMPLITUDE, 1.0)

func _start_attack() -> void:
	_state_timer = ATTACK_DURATION
	_shoot_remaining = 3 if not _phase2 else 5
	_shoot_timer = 0.25
	_tween = create_tween().set_loops()
	_tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_tween.tween_property(self, "position:x", _origin_x + SWAY_AMPLITUDE, SWAY_PERIOD * 0.5)
	_tween.tween_property(self, "position:x", _origin_x - SWAY_AMPLITUDE, SWAY_PERIOD)
	_tween.tween_property(self, "position:x", _origin_x,                  SWAY_PERIOD * 0.5)

func _start_retreat() -> void:
	_state_timer = RETREAT_DURATION
	var target_x := randf_range(-DASH_RANGE, DASH_RANGE)
	_origin_x = target_x
	_tween = create_tween()
	_tween.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_tween.tween_property(self, "position:x", target_x, RETREAT_DURATION * 0.6)

func _start_death() -> void:
	for i in 2:
		var exp := EXPLOSION_SCENE.instantiate() as Node3D
		get_tree().root.add_child(exp)
		exp.global_position = global_position + Vector3(
			randf_range(-0.8, 0.8), randf_range(-0.8, 0.8), 0.0)
		if i == 1:
			exp.scale = Vector3(2.5, 2.5, 2.5)
	died.emit()
	queue_free()

func take_hit(damage: int) -> void:
	if current_state == State.DEATH:
		return
	hp -= damage
	hp_changed.emit(hp)
	if not _phase2 and hp <= max_hp / 2:
		_phase2 = true
		$HitboxPhase1/CollisionShape3D.disabled = true
		$HitboxPhase2/CollisionShape3D.disabled = false
		_pulse_phase_change()
	if hp <= 0:
		enter_state(State.DEATH)

func _pulse_phase_change() -> void:
	var flash := create_tween()
	flash.set_loops(3)
	flash.tween_property(self, "scale", Vector3(1.35, 1.35, 1.35), 0.12)
	flash.tween_property(self, "scale", Vector3(1.0,  1.0,  1.0),  0.12)

func _fire_bullet() -> void:
	var players := get_tree().get_nodes_in_group("player")
	if players.is_empty():
		return
	var player := players[0] as Node3D
	var dir := (player.global_position - global_position).normalized()
	_spawn_bullet(dir)

func _spawn_bullet(dir: Vector3) -> void:
	var bullet := BULLET_SCENE.instantiate() as Area3D
	get_tree().root.add_child(bullet)
	bullet.global_position = global_position
	bullet.set("direction", dir)
	bullet.collision_layer = 8
	bullet.collision_mask  = 1
