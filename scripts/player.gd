extends CharacterBody3D

@export var walk_speed: float = 4.2
@export var run_speed: float = 6.4
@export var acceleration: float = 18.0
@export var gravity: float = 18.0

@onready var visual: Node3D = $Visual
@onready var camera: Camera3D = $CameraRig/Camera3D

var mobile_input := Vector2.ZERO
var facing := Vector3(0, 0, 1)

func _ready() -> void:
	camera.look_at(global_position + Vector3(0, 1.0, 0), Vector3.UP)

func _physics_process(delta: float) -> void:
	var desktop := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	mobile_input = _read_mobile_joystick()
	var input_vec := mobile_input if mobile_input.length() > 0.05 else desktop

	var dir := Vector3(input_vec.x, 0.0, input_vec.y)
	if dir.length() > 1.0:
		dir = dir.normalized()

	var target_speed := run_speed if Input.is_action_pressed("run") else walk_speed
	var target_velocity := dir * target_speed
	velocity.x = move_toward(velocity.x, target_velocity.x, acceleration * delta)
	velocity.z = move_toward(velocity.z, target_velocity.z, acceleration * delta)

	if not is_on_floor():
		velocity.y -= gravity * delta
	else:
		velocity.y = 0.0

	if dir.length() > 0.1:
		facing = dir.normalized()
		visual.rotation.y = lerp_angle(visual.rotation.y, atan2(facing.x, facing.z), 10.0 * delta)

	move_and_slide()

	if Input.is_action_just_pressed("interact"):
		print("[LembahSari] interact at ", global_position)

func _read_mobile_joystick() -> Vector2:
	var nodes := get_tree().get_nodes_in_group("mobile_joystick")
	if nodes.is_empty():
		return Vector2.ZERO
	var joystick = nodes[0]
	if joystick.has_method("get_output"):
		return joystick.get_output()
	return Vector2.ZERO
