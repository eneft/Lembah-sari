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
	# Uploaded donor contributes only motion; the existing player mesh/texture
	# and clean walk.001 remain the game's character identity.
	_check(bool(player.get("run_from_uploaded_source")),"Run must use extracted donor run.001 motion, not duplicated Walk")
	_check(int(player.get("run_source_bones")) >= 50,"Run retarget must animate most matching source bones")
	var actual_run: Animation = animator.get_animation(&"Run")
	_check(actual_run != null and absf(actual_run.length-1.25)<0.015,"Run animation must keep original ~1.25 second cycle")
	_check(actual_run.resource_name == "Run_Extracted_Only","Run resource must be the transferred clip, not original Walk")
	var transferred_rotation_tracks: int = 0
	for idx: int in range(actual_run.get_track_count()):
		if actual_run.track_get_type(idx) == Animation.TYPE_ROTATION_3D and actual_run.track_get_key_count(idx) >= 14:
			transferred_rotation_tracks += 1
	_check(transferred_rotation_tracks >= 50,"Run must contain actual sampled quaternion animation, not procedural fake movement")
	print("RUN_EXTRACTED_SOURCE_VALIDATED bones=%d transferred_rotations=%d donor_mesh_used=false duration=%.3f" % [int(player.get("run_source_bones")),transferred_rotation_tracks,actual_run.length])
	# Regression: the previous retarget passed movement tests but turned
	# the boy horizontal when Shift/Run was pressed. Evaluate upright torso
	# throughout the entire real animation, not just whether tracks exist.
	var hips_bone: int = -1
	var head_bone: int = -1
	for b: int in range(skeleton.get_bone_count()):
		var bone_label: String = String(skeleton.get_bone_name(b)).to_lower()
		if bone_label.ends_with("hips"):
			hips_bone = b
		elif bone_label.ends_with("head"):
			head_bone = b
	_check(hips_bone >= 0 and head_bone >= 0,"Run posture needs head and hips landmarks")
	if hips_bone >= 0 and head_bone >= 0:
		var baseline: Vector3 = skeleton.get_bone_global_rest(head_bone).origin-skeleton.get_bone_global_rest(hips_bone).origin
		_check(baseline.length() > 0.15,"Rest skeleton must have a meaningful torso length")
		var lowest_upright: float = 1.0
		var lowest_height_fraction: float = 100.0
		animator.play(&"Run",0.0)
		for phase_idx: int in range(16):
			var sample_t: float = actual_run.length*float(phase_idx)/16.0
			animator.seek(sample_t,true)
			skeleton.force_update_all_bone_transforms()
			var torso: Vector3 = skeleton.get_bone_global_pose(head_bone).origin-skeleton.get_bone_global_pose(hips_bone).origin
			var upright: float = torso.normalized().dot(baseline.normalized())
			var height_fraction: float = torso.y/maxf(absf(baseline.y),0.001)
			lowest_upright = minf(lowest_upright,upright)
			lowest_height_fraction = minf(lowest_height_fraction,height_fraction)
			_check(upright > 0.72 and height_fraction > 0.58,
				"Run torso collapses / character lies sideways: phase=%.2f upright=%.3f height_fraction=%.3f" % [sample_t,upright,height_fraction])
		print("RUN_UPRIGHT_POSE_VALIDATED frames=16 min_dot=%.3f min_height_fraction=%.3f" % [lowest_upright,lowest_height_fraction])
		_audit_run_limbs(skeleton,animator,actual_run)
		animator.play(&"Idle",0.0)
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
	_check(animator.get_animation(&"Walk").resource_name != "Run_Extracted_Only","Walk must be preserved from the game's existing source")
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

# The previous "upright" test missed fully splayed/hyperextended legs.
# Validate that ankles remain anatomically BELOW hips throughout Run, and
# that alternating foot movement is present rather than a frozen standing pose.
func _audit_run_limbs(skeleton: Skeleton3D,animator: AnimationPlayer,run_clip: Animation) -> void:
	var hips_id: int = -1
	var left_id: int = -1
	var right_id: int = -1
	for idx: int in range(skeleton.get_bone_count()):
		var label: String = String(skeleton.get_bone_name(idx)).to_lower()
		if label.ends_with("hips"):
			hips_id = idx
		elif label.ends_with("leftfoot"):
			left_id = idx
		elif label.ends_with("rightfoot"):
			right_id = idx
	_check(hips_id >= 0 and left_id >= 0 and right_id >= 0,"Run anatomical audit must resolve hip and both feet")
	if hips_id < 0 or left_id < 0 or right_id < 0:
		return
	var rest_hips: Vector3 = skeleton.get_bone_global_rest(hips_id).origin
	var rest_left: Vector3 = skeleton.get_bone_global_rest(left_id).origin
	var rest_right: Vector3 = skeleton.get_bone_global_rest(right_id).origin
	var left_length: float = rest_hips.distance_to(rest_left)
	var right_length: float = rest_hips.distance_to(rest_right)
	_check(left_length > 0.15 and right_length > 0.15,"Foot leg-length references must be nonzero")
	var left_min: float = INF
	var left_max: float = -INF
	var right_min: float = INF
	var right_max: float = -INF
	animator.play(&"Run",0.0)
	for frame: int in range(16):
		var t: float = run_clip.length*float(frame)/16.0
		animator.seek(t,true)
		skeleton.force_update_all_bone_transforms()
		var hip: Vector3 = skeleton.get_bone_global_pose(hips_id).origin
		var left: Vector3 = skeleton.get_bone_global_pose(left_id).origin
		var right: Vector3 = skeleton.get_bone_global_pose(right_id).origin
		var ls: Vector3 = left-hip
		var rs: Vector3 = right-hip
		_check(ls.y < -0.10*left_length and rs.y < -0.10*right_length,
			"Run leg inverted or horizontal at t=%.3f left_y=%.3f right_y=%.3f" % [t,ls.y,rs.y])
		_check(ls.length() < left_length*1.18 and rs.length() < right_length*1.18,
			"Run hyperextends limb beyond original rig dimensions")
		_check(Vector2(ls.x,ls.z).length() < 1.05*left_length and Vector2(rs.x,rs.z).length() < 1.05*right_length,
			"Run legs are splayed sideways instead of striding forward")
		left_min = minf(left_min,ls.z)
		left_max = maxf(left_max,ls.z)
		right_min = minf(right_min,rs.z)
		right_max = maxf(right_max,rs.z)
	_check(left_max-left_min > 0.035*left_length and right_max-right_min > 0.035*right_length,
		"Run must visibly alternate the feet; no static fallback allowed")
	print("RUN_ANATOMY_VALIDATED frames=16 left_swing=%.3f right_swing=%.3f legs=groundward" % [left_max-left_min,right_max-right_min])

func _frames(count: int) -> void:
	for frame: int in range(count):
		await physics_frame
	await process_frame

func _check(condition: bool, message: String) -> void:
	if not condition:
		failed = true
		push_error(message)
