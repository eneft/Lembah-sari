extends CharacterBody3D

signal tool_changed(tool: String)
signal farming_feedback(text: String)
signal dialogue_requested(speaker: String, text: String)

@export var walk_speed: float = 4.2
@export var run_speed: float = 6.4
@export var acceleration: float = 18.0
@export var gravity: float = 18.0

@onready var visual: Node3D = $Visual
@onready var camera: Camera3D = $CameraRig/Camera3D

var mobile_input: Vector2 = Vector2.ZERO
var facing: Vector3 = Vector3(0, 0, 1)
var selected_tool: String = "hoe"
var input_locked: bool = false

func _ready() -> void:
	add_to_group("player")
	camera.look_at(global_position + Vector3(0, 1.0, 0), Vector3.UP)
	tool_changed.emit(selected_tool)

func _physics_process(delta: float) -> void:
	if input_locked:
		velocity.x = move_toward(velocity.x, 0.0, acceleration * delta)
		velocity.z = move_toward(velocity.z, 0.0, acceleration * delta)
		if not is_on_floor():
			velocity.y -= gravity * delta
		else:
			velocity.y = 0.0
		move_and_slide()
		return

	var desktop: Vector2 = Input.get_vector("move_left", "move_right", "move_up", "move_down")
	mobile_input = _read_mobile_joystick()
	var input_vec: Vector2 = mobile_input if mobile_input.length() > 0.05 else desktop

	var direction: Vector3 = Vector3(input_vec.x, 0.0, input_vec.y)
	if direction.length() > 1.0:
		direction = direction.normalized()

	var target_speed: float = run_speed if Input.is_action_pressed("run") else walk_speed
	var target_velocity: Vector3 = direction * target_speed
	velocity.x = move_toward(velocity.x, target_velocity.x, acceleration * delta)
	velocity.z = move_toward(velocity.z, target_velocity.z, acceleration * delta)

	if not is_on_floor():
		velocity.y -= gravity * delta
	else:
		velocity.y = 0.0

	if direction.length() > 0.1:
		facing = direction.normalized()
		visual.rotation.y = lerp_angle(visual.rotation.y, atan2(facing.x, facing.z), 10.0 * delta)

	move_and_slide()

	if Input.is_action_just_pressed("interact"):
		_do_interact()

func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey:
		return
	var key_event: InputEventKey = event as InputEventKey
	if not key_event.pressed or key_event.echo or input_locked:
		return
	match key_event.keycode:
		KEY_1:
			set_tool("hoe")
		KEY_2:
			set_tool("seed")
		KEY_3:
			set_tool("water")
		KEY_4:
			set_tool("hand")
		KEY_5:
			set_tool("rod")
		KEY_6:
			set_tool("sell")

func set_tool(tool: String) -> void:
	if tool not in ["hoe", "seed", "water", "hand", "rod", "sell"]:
		return
	selected_tool = tool
	tool_changed.emit(selected_tool)

func get_selected_tool() -> String:
	return selected_tool

func set_input_locked(locked: bool) -> void:
	input_locked = locked

func _do_interact() -> void:
	var activity_managers: Array[Node] = get_tree().get_nodes_in_group("activity_manager")
	if not activity_managers.is_empty():
		var activity_manager: Node = activity_managers[0]
		if activity_manager.has_method("try_interact"):
			var activity_value: Variant = activity_manager.call("try_interact", global_position, facing, selected_tool)
			if activity_value is Dictionary:
				var activity_result: Dictionary = activity_value as Dictionary
				if bool(activity_result.get("ok", false)):
					var activity_message: String = str(activity_result.get("message", ""))
					if activity_message != "":
						farming_feedback.emit(activity_message)
					return

	var npc_managers: Array[Node] = get_tree().get_nodes_in_group("npc_manager")
	if not npc_managers.is_empty():
		var npc_manager: Node = npc_managers[0]
		if npc_manager.has_method("try_interact"):
			var talk_value: Variant = npc_manager.call("try_interact", global_position, facing)
			if talk_value is Dictionary:
				var talk_result: Dictionary = talk_value as Dictionary
				if bool(talk_result.get("ok", false)):
					dialogue_requested.emit(str(talk_result.get("speaker", "")), str(talk_result.get("text", "")))
					return

	var farm_managers: Array[Node] = get_tree().get_nodes_in_group("farm_manager")
	if farm_managers.is_empty():
		farming_feedback.emit("Belum ada objek untuk diinteraksikan.")
		return
	var target_position: Vector3 = global_position + facing * 1.55
	var farm_value: Variant = farm_managers[0].call("use_tool", target_position, selected_tool)
	if not farm_value is Dictionary:
		return
	var result: Dictionary = farm_value as Dictionary
	var message: String = str(result.get("message", ""))
	if message != "":
		farming_feedback.emit(message)
	print("[LembahSari] ", message)

func _read_mobile_joystick() -> Vector2:
	var nodes: Array[Node] = get_tree().get_nodes_in_group("mobile_joystick")
	if nodes.is_empty():
		return Vector2.ZERO
	var joystick: Node = nodes[0]
	if joystick.has_method("get_output"):
		var output_value: Variant = joystick.call("get_output")
		if output_value is Vector2:
			return output_value
	return Vector2.ZERO
