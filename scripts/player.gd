extends CharacterBody3D

signal tool_changed(tool: String)
signal farming_feedback(text: String)
signal dialogue_requested(speaker: String, text: String)
signal day_transition_requested(summary: String)

@export var walk_speed: float = 1.25
@export var run_speed: float = 3.2
@export var acceleration: float = 18.0
@export var gravity: float = 18.0

@onready var visual: Node3D = $Visual
@onready var camera: Camera3D = $CameraRig/Camera3D
@onready var character_model: Node = $Visual/CharacterLembahSari

var mobile_input: Vector2 = Vector2.ZERO
var facing: Vector3 = Vector3(0, 0, 1)
var selected_tool: String = "hoe"
var input_locked: bool = false

var character_animation_player: AnimationPlayer
var current_locomotion_animation: StringName = &""

# Distance covered by one complete in-place cycle, in the GLB's model units.
# Keep these aligned with tools/animation/refine_player_locomotion.py.
const WALK_CYCLE_DISTANCE: float = 0.34 / 0.62
const RUN_CYCLE_DISTANCE: float = 0.42 / 0.36

func _ready() -> void:
	add_to_group("player")
	camera.look_at(global_position + Vector3(0, 0.82, 0), Vector3.UP)
	tool_changed.emit(selected_tool)
	_setup_character_animations()
	_play_locomotion_animation(&"Idle")

func _physics_process(delta: float) -> void:
	if input_locked:
		velocity.x = move_toward(velocity.x, 0.0, acceleration * delta)
		velocity.z = move_toward(velocity.z, 0.0, acceleration * delta)
		if not is_on_floor():
			velocity.y -= gravity * delta
		else:
			velocity.y = 0.0
		move_and_slide()
		_update_character_animation()
		return

	var desktop: Vector2 = Input.get_vector("move_left", "move_right", "move_up", "move_down")
	mobile_input = _read_mobile_joystick()
	var input_vec: Vector2 = mobile_input if mobile_input.length() > 0.05 else desktop

	var direction: Vector3 = Vector3(input_vec.x, 0.0, input_vec.y)
	if direction.length() > 1.0:
		direction = direction.normalized()

	var wants_run: bool = Input.is_action_pressed("run") and direction.length() > 0.1
	var running: bool = wants_run and _has_running_stamina()
	var target_speed: float = run_speed if running else walk_speed
	var target_velocity: Vector3 = direction * target_speed
	velocity.x = move_toward(velocity.x, target_velocity.x, acceleration * delta)
	velocity.z = move_toward(velocity.z, target_velocity.z, acceleration * delta)

	if running:
		_drain_running_stamina(delta)

	if not is_on_floor():
		velocity.y -= gravity * delta
	else:
		velocity.y = 0.0

	if direction.length() > 0.1:
		facing = direction.normalized()
		visual.rotation.y = lerp_angle(visual.rotation.y, atan2(facing.x, facing.z), 10.0 * delta)

	move_and_slide()
	_update_character_animation()

	if Input.is_action_just_pressed("interact"):
		_do_interact()

func _setup_character_animations() -> void:
	character_animation_player = _find_animation_player(character_model)
	if character_animation_player == null:
		push_warning("[LembahSari] AnimationPlayer tidak ditemukan pada player_character_lembah_sari.glb")
		return

	for animation_name: StringName in [&"Idle", &"Walk", &"Run"]:
		if not character_animation_player.has_animation(animation_name):
			push_warning("[LembahSari] Animation clip tidak ditemukan: %s" % animation_name)
			continue
		var animation: Animation = character_animation_player.get_animation(animation_name)
		if animation != null:
			animation.loop_mode = Animation.LOOP_LINEAR

func _find_animation_player(root: Node) -> AnimationPlayer:
	if root is AnimationPlayer:
		return root as AnimationPlayer
	for child: Node in root.get_children():
		var found: AnimationPlayer = _find_animation_player(child)
		if found != null:
			return found
	return null

func _update_character_animation() -> void:
	if character_animation_player == null:
		return
	# Actual displacement includes acceleration, braking, and collisions. A held
	# direction against a wall must not keep the feet walking on the spot.
	var real_velocity: Vector3 = get_real_velocity()
	var speed: float = Vector2(real_velocity.x, real_velocity.z).length()
	if speed < 0.08:
		_play_locomotion_animation(&"Idle")
		character_animation_player.speed_scale = 1.0
		return
	var running: bool = speed > walk_speed + 0.20
	var animation_name: StringName = &"Run" if running else &"Walk"
	_play_locomotion_animation(animation_name)
	var cycle_distance: float = RUN_CYCLE_DISTANCE if running else WALK_CYCLE_DISTANCE
	var model_scale: float = absf(visual.global_basis.get_scale().y)
	var clip: Animation = character_animation_player.get_animation(animation_name)
	character_animation_player.speed_scale = clampf(speed * clip.length / (cycle_distance * maxf(model_scale, 0.001)), 0.1, 2.5)

func _play_locomotion_animation(animation_name: StringName) -> void:
	if character_animation_player == null:
		return
	if current_locomotion_animation == animation_name:
		return
	if not character_animation_player.has_animation(animation_name):
		return
	var phase: float = 0.0
	var preserve_phase: bool = current_locomotion_animation in [&"Walk", &"Run"] and animation_name in [&"Walk", &"Run"]
	if preserve_phase and character_animation_player.current_animation_length > 0.0:
		phase = fposmod(character_animation_player.current_animation_position / character_animation_player.current_animation_length, 1.0)
	character_animation_player.play(animation_name, 0.16)
	if preserve_phase:
		character_animation_player.seek(phase * character_animation_player.get_animation(animation_name).length)
	current_locomotion_animation = animation_name

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
					if bool(activity_result.get("sleep", false)):
						var wake_value: Variant = activity_result.get("wake_position", global_position)
						if wake_value is Vector3:
							global_position = wake_value as Vector3
						velocity = Vector3.ZERO
						day_transition_requested.emit(activity_message)
						return
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

func _has_running_stamina() -> bool:
	var stats_nodes: Array[Node] = get_tree().get_nodes_in_group("player_stats")
	if stats_nodes.is_empty():
		return true
	var stats: Node = stats_nodes[0]
	if not stats.has_method("has_stamina"):
		return true
	var result: Variant = stats.call("has_stamina", 0.2)
	return bool(result)

func _drain_running_stamina(delta: float) -> void:
	var stats_nodes: Array[Node] = get_tree().get_nodes_in_group("player_stats")
	if stats_nodes.is_empty():
		return
	var stats: Node = stats_nodes[0]
	if stats.has_method("drain_running"):
		stats.call("drain_running", delta)

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
