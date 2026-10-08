extends RefCounted
## Retarget the MOTION curves of donor run.001 onto our existing Mixamo boy.
## Never instantiate donor model, bind pose, skin, mesh or materials.
## WARNING: copying donor local quaternions directly (even conjugated through
## the target rest pose) made the hero's arms/legs twist and torso collapse.
## Here, donor angles/timing drive ONLY each bone's natural rotation axis,
## derived from the recipient's own healthy Walk. This is an anatomical
## 1-DOF retarget, rather than an unsafe arbitrary 3D joint-space copy.
const RUN_SOURCE = preload("res://scripts/animation/run_source_only.gd")
const SAMPLES: int = 16

func install(player: AnimationPlayer) -> int:
	if not player.has_animation(&"Walk"):
		push_error("[LembahSari] Extracted Run requires the original healthy Walk.")
		return 0
	var donor: Dictionary = RUN_SOURCE.read_motion()
	var records: Array = donor.get("bones",[]) as Array
	if records.size() != 65 or bool(donor.get("source_mesh_included",true)):
		push_error("[LembahSari] Expected animation-only source with 65 Mixamo joints.")
		return 0
	var source_by_bone: Dictionary = {}
	for record: Variant in records:
		if record is Array and (record as Array).size() == 3:
			var item: Array = record as Array
			source_by_bone[_canonical(String(item[0]))] = item

	var walk: Animation = player.get_animation(&"Walk")
	var motion := Animation.new()
	motion.resource_name = "Run_Extracted_Only"
	motion.length = float(donor.get("duration",1.25))
	motion.loop_mode = Animation.LOOP_LINEAR
	var matched: int = 0
	var animated_limbs: int = 0
	for source_track: int in range(walk.get_track_count()):
		var path: NodePath = walk.track_get_path(source_track)
		var track_type: Animation.TrackType = walk.track_get_type(source_track)
		if walk.track_get_key_count(source_track) < 1:
			continue
		if track_type == Animation.TYPE_ROTATION_3D and path.get_subname_count() > 0:
			var bone: String = _canonical(String(path.get_subname(0)))
			if not source_by_bone.has(bone):
				continue
			var record: Array = source_by_bone[bone] as Array
			var donor_frames: Array = record[2] as Array
			if donor_frames.size() != SAMPLES:
				continue
			var donor_quats: Array[Quaternion] = []
			var original_quats: Array[Quaternion] = []
			for i: int in range(SAMPLES):
				donor_quats.append(_source_quaternion(donor_frames[i] as Array))
				var walk_time: float = walk.length*float(i)/float(SAMPLES)
				original_quats.append(walk.rotation_track_interpolate(source_track,walk_time))
			# Train the safe movement axis on the recipient's own valid gait.
			var walk_axis: Vector3 = _principal_motion_axis(original_quats)
			var donor_axis: Vector3 = _principal_motion_axis(donor_quats)
			var walk_range: float = _max_axis_excursion(original_quats,walk_axis)
			var donor_range: float = _max_axis_excursion(donor_quats,donor_axis)
			var new_track: int = motion.add_track(Animation.TYPE_ROTATION_3D)
			motion.track_set_path(new_track,path)
			var frame0: Quaternion = original_quats[0]
			var strength: float = _anatomical_gain(bone)
			var limit: float = _anatomical_angle_cap(bone)
			for i: int in range(SAMPLES):
				var imported_swing: float = _axis_excursion(donor_quats[0],donor_quats[i],donor_axis)
				var stride_angle: float = 0.0
				if donor_range > 0.04 and walk_range > 0.025:
					# Donor supplies its true joint timing/signature; recipient
					# Walk sets the anatomically safe axis and range.
					stride_angle = imported_swing/donor_range*minf(limit,walk_range*strength)
				var safe_pose: Quaternion = (frame0*Quaternion(walk_axis,stride_angle)).normalized()
				motion.rotation_track_insert_key(new_track,motion.length*float(i)/float(SAMPLES),safe_pose)
			# One extra loop seam, exactly equal to the initial pose.
			motion.rotation_track_insert_key(new_track,motion.length,frame0)
			matched += 1
			if "leg" in bone or "arm" in bone or "foot" in bone:
				if walk_range > 0.025 and donor_range > 0.04:
					animated_limbs += 1
		elif track_type == Animation.TYPE_POSITION_3D or track_type == Animation.TYPE_SCALE_3D:
			# Preserve the original model's pelvis height and bind dimensions.
			# The donor cannot move the world root or body twice.
			var preserved: int = motion.add_track(track_type)
			motion.track_set_path(preserved,path)
			var fixed_value: Vector3 = walk.track_get_key_value(source_track,0) as Vector3
			if track_type == Animation.TYPE_POSITION_3D:
				motion.position_track_insert_key(preserved,0.0,fixed_value)
				motion.position_track_insert_key(preserved,motion.length,fixed_value)
			else:
				motion.scale_track_insert_key(preserved,0.0,fixed_value)
				motion.scale_track_insert_key(preserved,motion.length,fixed_value)
	if matched < 50 or animated_limbs < 8:
		push_error("[LembahSari] Run motion incompatible: bones=%d animating_limbs=%d." % [matched,animated_limbs])
		return 0
	var library: AnimationLibrary = player.get_animation_library(&"")
	if library == null:
		push_error("[LembahSari] Missing original character AnimationLibrary")
		return 0
	if library.has_animation(&"Run"):
		library.remove_animation(&"Run")
	library.add_animation(&"Run",motion)
	print("[LembahSari] RUN_ONLY_RETARGETED donor=run.001 bones=%d/65 motion_limbs=%d duration=%.3f donor_model=false anatomical_axis=true" % [matched,animated_limbs,motion.length])
	return matched

func _source_quaternion(values: Array) -> Quaternion:
	return Quaternion(float(values[0]),float(values[1]),float(values[2]),float(values[3])).normalized()

func _short_rotation_vector(delta: Quaternion) -> Vector3:
	var q: Quaternion = delta.normalized()
	var angle: float = q.get_angle()
	if angle > PI:
		angle -= TAU
	if absf(angle) < 0.00001:
		return Vector3.ZERO
	return q.get_axis()*angle

func _principal_motion_axis(frames: Array[Quaternion]) -> Vector3:
	var start: Quaternion = frames[0]
	var strongest: Vector3 = Vector3.ZERO
	for q: Quaternion in frames:
		var swing: Vector3 = _short_rotation_vector(start.inverse()*q)
		if swing.length_squared() > strongest.length_squared():
			strongest = swing
	if strongest.length_squared() < 0.000001:
		return Vector3.RIGHT
	return strongest.normalized()

func _axis_excursion(start: Quaternion,pose: Quaternion,axis: Vector3) -> float:
	return _short_rotation_vector(start.inverse()*pose).dot(axis)

func _max_axis_excursion(frames: Array[Quaternion],axis: Vector3) -> float:
	var largest: float = 0.0
	for pose: Quaternion in frames:
		largest = maxf(largest,absf(_axis_excursion(frames[0],pose,axis)))
	return largest

func _anatomical_gain(bone: String) -> float:
	if bone == "hips" or bone == "head" or bone == "neck":
		return 0.15
	if bone.begins_with("spine"):
		return 0.20
	if "shoulder" in bone:
		return 0.55
	if "upleg" in bone:
		return 1.16
	if bone.ends_with("leg"):
		return 1.20
	if "foot" in bone:
		return 0.90
	if "arm" in bone:
		return 1.20
	if "hand" in bone or "finger" in bone or "thumb" in bone:
		return 0.45
	return 0.55

func _anatomical_angle_cap(bone: String) -> float:
	if bone == "hips":
		return deg_to_rad(5.0)
	if bone == "head" or bone == "neck":
		return deg_to_rad(7.0)
	if bone.begins_with("spine"):
		return deg_to_rad(7.0)
	if "shoulder" in bone:
		return deg_to_rad(20.0)
	if "upleg" in bone:
		return deg_to_rad(58.0)
	if bone.ends_with("leg"):
		return deg_to_rad(66.0)
	if "foot" in bone:
		return deg_to_rad(28.0)
	if "arm" in bone:
		return deg_to_rad(55.0)
	return deg_to_rad(25.0)

func _canonical(value: String) -> String:
	return value.to_lower().replace("mixamorig","").replace("_","").replace(":","").replace("-","").replace(" ","")
