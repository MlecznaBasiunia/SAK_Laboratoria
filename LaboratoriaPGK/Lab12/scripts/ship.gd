extends Node3D

const LIMIT_X: float        = 4.0
const LIMIT_Y: float        = 3.0
const MAX_BANK_Z: float     = 0.436332
const MAX_BANK_X: float     = 0.261799
const BANK_SPEED: float     = 8.0
const SHOOT_COOLDOWN: float = 0.3
const BULLET_LAYER: int     = 4
const BULLET_MASK: int      = 2

@export var move_speed: float = 5.0
@export var bullet_scene: PackedScene

var _shoot_cooldown: float = 0.0
var _is_invincible: bool   = false
var hp: int = 3

func _ready() -> void:
	add_to_group("player")
	$Area3D.body_entered.connect(_on_body_entered)
	$Area3D.area_entered.connect(_on_area_entered)

func _process(delta: float) -> void:
	var input_x := Input.get_axis("ui_left", "ui_right")
	var input_y := Input.get_axis("ui_up", "ui_down")
	position.x += input_x * move_speed * delta
	position.y -= input_y * move_speed * delta
	position.x = clamp(position.x, -LIMIT_X, LIMIT_X)
	position.y = clamp(position.y, -LIMIT_Y, LIMIT_Y)
	if not _is_invincible:
		$ShipModel.rotation.z = lerp($ShipModel.rotation.z, -input_x * MAX_BANK_Z, BANK_SPEED * delta)
		$ShipModel.rotation.x = lerp($ShipModel.rotation.x, -input_y * MAX_BANK_X, BANK_SPEED * delta)
	_shoot_cooldown -= delta
	if Input.is_action_just_pressed("ui_accept") and _shoot_cooldown <= 0.0:
		_spawn_bullet()
		_shoot_cooldown = SHOOT_COOLDOWN
	if Input.is_action_just_pressed("barrel_roll") and not _is_invincible:
		_barrel_roll()

func _barrel_roll() -> void:
	_is_invincible = true
	$ShipModel.rotation.z = 0.0
	$ShipModel.rotation.x = 0.0
	$AnimationPlayer.play("barrel_roll")
	await $AnimationPlayer.animation_finished
	_is_invincible = false

func _take_damage(amount: int) -> void:
	if _is_invincible:
		return
	hp -= amount
	print("HP: ", hp)
	GameManager.player_hit(amount)

func _on_body_entered(_body: Node3D) -> void:
	_take_damage(1)

func _on_area_entered(_area: Area3D) -> void:
	_take_damage(1)

func _spawn_bullet() -> void:
	if bullet_scene == null:
		return
	var bullet := bullet_scene.instantiate() as Area3D
	get_tree().root.add_child(bullet)
	bullet.global_position = global_position
	bullet.set("direction", Vector3(0, 0, -1))
	bullet.collision_layer = BULLET_LAYER
	bullet.collision_mask  = BULLET_MASK
