extends SceneTree

var failed: bool = false

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var scene: PackedScene = load(str(ProjectSettings.get_setting("application/run/main_scene"))) as PackedScene
	var world: Node = scene.instantiate()
	root.add_child(world)
	current_scene = world
	await _frames(45)
	var player: CharacterBody3D = world.get_node("Player") as CharacterBody3D
	var model: Node = player.get_node("Visual/CharacterLembahSari")
	var animator: AnimationPlayer = player.get("character_animation_player") as AnimationPlayer
	var skeletons: Array[Node] = model.find_children("*", "Skeleton3D", true, false)
	if animator == null or skeletons.is_empty():
		push_error("The imported rig or AnimationPlayer is missing.")
		quit(1)
		return
	var skeleton: Skeleton3D = skeletons[0] as Skeleton3D
	_check(skeleton.get_bone_count() >= 20, "Stylized boy rig must keep a usable humanoid skeleton.")
	_check(String(player.get("walk_source_animation")).to_lower().find("walk") >= 0, "Stylized boy walk.001 source must be mapped at runtime.")
	var textured: bool = false
	for node: Node in model.find_children("*", "MeshInstance3D", true, false):
		var mesh: MeshInstance3D = node as MeshInstance3D
		if mesh.mesh == null or mesh.skin == null:
			continue
		for surface: int in range(mesh.mesh.get_surface_count()):
			var material: StandardMaterial3D = mesh.get_active_material(surface) as StandardMaterial3D
			if material != null and material.albedo_texture != null:
				textured = true
	_check(textured, "Skinned player texture must load.")
	for clip_name: StringName in [&"Idle", &"Walk", &"Run"]:
		if not animator.has_animation(clip_name):
			_check(false, "Missing clip: %s" % clip_name)
			continue
		var clip: Animation = animator.get_animation(clip_name)
		_check(clip.length > 0.0 and clip.loop_mode == Animation.LOOP_LINEAR, "%s must loop." % clip_name)
		var animation_root: Node = animator.get_node(animator.root_node)
		for track: int in range(clip.get_track_count()):
			var path: NodePath = clip.track_get_path(track)
			var target: Node = animation_root.get_node_or_null(NodePath(path.get_concatenated_names()))
			_check(target != null, "Unresolved track: %s" % path)
			if target is Skeleton3D and path.get_subname_count() > 0:
				_check((target as Skeleton3D).find_bone(path.get_subname(0)) >= 0, "Missing bone: %s" % path)
		animator.play(clip_name)
		animator.seek(clip.length * 0.1, true)
		var poses: Array[Transform3D] = []
		for bone: int in range(skeleton.get_bone_count()):
			poses.append(skeleton.get_bone_pose(bone))
		animator.seek(clip.length * 0.35, true)
		var changed: int = 0
		for bone: int in range(skeleton.get_bone_count()):
			if not poses[bone].is_equal_approx(skeleton.get_bone_pose(bone)):
				changed += 1
		if clip_name == &"Idle":
			_check(changed == 0, "Idle fallback must hold a neutral pose.")
		else:
			_check(changed > 0, "%s must move the skeleton." % clip_name)
		print("CHARACTER_CLIP_OK %s changed_bones=%d" % [clip_name, changed])
	animator.play(&"Idle")
	_check(player.is_on_floor(), "The player must stand on the playable floor.")
	var start: Vector3 = player.global_position
	Input.action_press(&"move_right")
	await _frames(30)
	var walked: float = player.global_position.distance_to(start)
	var walk_direction: Vector3 = (player.global_position - start).normalized()
	if bool(player.get("camera_relative_movement")):
		var camera: Camera3D = player.get_node("CameraRig/Camera3D") as Camera3D
		var screen_right: Vector3 = camera.global_basis.x
		screen_right.y = 0.0
		_check(walk_direction.dot(screen_right.normalized()) > .98, "Right input must move toward screen right with the rotated camera.")
	_check(animator.current_animation == &"Walk" and walked > 0.4, "Walking input must move the player and play Walk.")
	var walking_rate: float = animator.speed_scale
	Input.action_release(&"move_right")
	# This project's 0.3 dead zone maps raw strength 0.65 to half output.
	Input.action_press(&"move_right", 0.65)
	await _frames(20)
	_check(animator.current_animation == &"Walk", "Partial joystick input must remain a walk.")
	print("CADENCE_CHECK full=%.3f partial=%.3f input=%s" % [walking_rate, animator.speed_scale, Input.get_vector("move_left", "move_right", "move_up", "move_down")])
	_check(absf(animator.speed_scale / walking_rate - 0.5) < 0.08, "Half-speed movement must also halve the step cadence.")
	Input.action_release(&"move_right")
	Input.action_press(&"move_right")
	await _frames(10)
	start = player.global_position
	Input.action_press(&"run")
	await _frames(30)
	var ran: float = player.global_position.distance_to(start)
	_check(animator.current_animation == &"Run" and ran > walked, "Run must play and move faster than Walk.")
	Input.action_release(&"run")
	Input.action_release(&"move_right")
	await _frames(30)
	_check(animator.current_animation == &"Idle" and Vector2(player.velocity.x, player.velocity.z).length() < 0.01, "Releasing input must stop movement and play Idle.")
	_check(player.is_on_floor(), "The player must remain on the floor.")
	# A collision reduces actual motion to zero even while input is still held.
	var wall: StaticBody3D = StaticBody3D.new()
	var collision: CollisionShape3D = CollisionShape3D.new()
	var shape: BoxShape3D = BoxShape3D.new()
	shape.size = Vector3(0.1, 3.0, 3.0)
	collision.shape = shape
	wall.add_child(collision)
	world.add_child(wall)
	walk_direction.y = 0.0
	walk_direction = walk_direction.normalized()
	wall.global_position = player.global_position + walk_direction * 0.65 + Vector3.UP
	wall.rotation.y = atan2(-walk_direction.z, walk_direction.x)
	Input.action_press(&"move_right")
	await _frames(60)
	_check(animator.current_animation == &"Idle", "Holding input against a wall must stop the walking animation.")
	Input.action_release(&"move_right")
	wall.queue_free()
	await _frames(2)
	Input.action_press(&"move_left")
	await _frames(15)
	player.call("set_input_locked", true)
	await _frames(20)
	_check(animator.current_animation == &"Idle", "Locking input for dialogue must settle back into Idle.")
	Input.action_release(&"move_left")
	player.call("set_input_locked", false)
	if not failed:
		print("PLAYABLE_RUNTIME_VALIDATED Idle -> Walk -> Run -> Idle walk=%.3f run=%.3f textured=true bones=%d cadence=ok blocked=Idle dialogue=Idle" % [walked, ran, skeleton.get_bone_count()])
	world.queue_free()
	await process_frame
	quit(1 if failed else 0)

func _frames(count: int) -> void:
	for frame: int in range(count):
		await physics_frame
	await process_frame

func _check(condition: bool, message: String) -> void:
	if not condition:
		failed = true
		push_error(message)
