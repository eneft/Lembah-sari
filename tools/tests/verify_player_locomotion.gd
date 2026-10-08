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
	# Diagnose any authored translation that moves the mesh forward and snaps it back.
	var source_animation: Animation = animator.get_animation(player.get("walk_source_animation"))
	if source_animation != null:
		print("SOURCE_WALK_DIAGNOSTIC length=%.4f tracks=%d" % [source_animation.length, source_animation.get_track_count()])
		for track: int in range(source_animation.get_track_count()):
			if source_animation.track_get_type(track) != Animation.TYPE_POSITION_3D:
				continue
			var key_count: int = source_animation.track_get_key_count(track)
			if key_count < 1:
				continue
			var first_position: Vector3 = source_animation.track_get_key_value(track, 0)
			var last_position: Vector3 = source_animation.track_get_key_value(track, key_count - 1)
			var furthest: float = 0.0
			var min_x: float = first_position.x
			var max_x: float = first_position.x
			var min_z: float = first_position.z
			var max_z: float = first_position.z
			for key: int in range(key_count):
				var pos: Vector3 = source_animation.track_get_key_value(track, key)
				furthest = maxf(furthest, Vector2(pos.x - first_position.x, pos.z - first_position.z).length())
				min_x = minf(min_x, pos.x)
				max_x = maxf(max_x, pos.x)
				min_z = minf(min_z, pos.z)
				max_z = maxf(max_z, pos.z)
			print("SOURCE_WALK_POSITION path=%s keys=%d first=%s last=%s planar_drift=%.5f planar_range=(%.4f,%.4f) max_displacement=%.5f" % [source_animation.track_get_path(track), key_count, first_position, last_position, Vector2(last_position.x - first_position.x, last_position.z - first_position.z).length(), max_x-min_x, max_z-min_z, furthest])
	# The clean source has ~1.366 units of root travel baked into the walk.
	# Reject any copy that would move the visible mesh forward then snap back.
	var imported_distance: float = float(player.get("source_walk_distance"))
	_check(imported_distance > 1.0, "Source root-travel diagnostic must remain measurable before neutralization.")
	for in_place_clip: StringName in [&"Walk", &"Run"]:
		var clip: Animation = animator.get_animation(in_place_clip)
		var root_tracks: int = 0
		var max_root_excursion: float = 0.0
		for track: int in range(clip.get_track_count()):
			if clip.track_get_type(track) != Animation.TYPE_POSITION_3D:
				continue
			var path: String = String(clip.track_get_path(track)).to_lower()
			if not ("hips" in path or "pelvis" in path or "root" in path):
				continue
			root_tracks += 1
			var origin: Vector3 = clip.track_get_key_value(track, 0)
			for key: int in range(clip.track_get_key_count(track)):
				var sample: Vector3 = clip.track_get_key_value(track, key)
				max_root_excursion = maxf(max_root_excursion, Vector2(sample.x-origin.x, sample.z-origin.z).length())
		_check(root_tracks > 0 and max_root_excursion < 0.0001,
			"%s must play in place: root travel must not jump backwards on loop." % in_place_clip)
		print("IN_PLACE_ROOT_OK clip=%s planar_excursion=%.6f original_root_travel=%.5f" % [in_place_clip, max_root_excursion, imported_distance])
	_check(skeleton.get_bone_count() >= 20, "Stylized boy rig must keep a usable humanoid skeleton.")
	_check(String(player.get("walk_source_animation")).to_lower().find("walk") >= 0, "Stylized boy walk.001 source must be mapped at runtime.")
	var textured: bool = false
	var total_vertices: int = 0
	var largest_texture_width: int = 0
	for node: Node in model.find_children("*", "MeshInstance3D", true, false):
		var mesh: MeshInstance3D = node as MeshInstance3D
		if mesh.mesh == null or mesh.skin == null:
			continue
		for surface: int in range(mesh.mesh.get_surface_count()):
			total_vertices += mesh.mesh.surface_get_array_len(surface)
			var material: StandardMaterial3D = mesh.get_active_material(surface) as StandardMaterial3D
			if material != null and material.albedo_texture != null:
				textured = true
				largest_texture_width = maxi(largest_texture_width, material.albedo_texture.get_width())
	_check(textured, "Skinned player texture must load.")
	_check(total_vertices >= 30000, "Player mesh must retain high-fidelity geometry (>= 30k vertices).")
	_check(largest_texture_width >= 1024, "Player texture must retain at least 1024px source detail.")
	print("CHARACTER_FIDELITY_OK vertices=%d texture_width=%d" % [total_vertices, largest_texture_width])
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
	# Short, observable acceleration gate: a first stride must not snap
	# directly to full speed; braking should not leave the player drifting.
	Input.action_press(&"move_right")
	await _frames(3)
	var launch_speed: float = Vector2(player.velocity.x, player.velocity.z).length()
	_check(launch_speed > 0.08 and launch_speed < float(player.get("walk_speed")) * 0.75,
		"Walking must ramp up smoothly over the first three frames.")
	var visual_node: Node3D = player.get_node("Visual") as Node3D
	var desired_yaw: float = atan2(player.facing.x, player.facing.z)
	var remaining_yaw: float = absf(wrapf(desired_yaw - visual_node.rotation.y, -PI, PI))
	_check(remaining_yaw > 0.20, "Player torso should ease into a turn, not snap to its target angle.")
	Input.action_release(&"move_right")
	await _frames(14)
	_check(Vector2(player.velocity.x, player.velocity.z).length() < 0.035,
		"Stopping a walk must settle cleanly without residual movement.")
	_check(float(player.get("animation_blend_time")) >= 0.20,
		"Idle / Walk transitions need a visible crossfade.")
	print("WALK_SMOOTHNESS_OK launch=%.3f yaw_remaining=%.3f braking=ok blend=%.2f" % [launch_speed, remaining_yaw, player.get("animation_blend_time")])
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
