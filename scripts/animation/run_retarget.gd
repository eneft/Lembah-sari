extends RefCounted
## Apply ONLY run.001 bone motion from the uploaded donor GLB to the existing
## player character Skeleton3D. No source mesh/skin/material is instantiated.
const RUN_SOURCE = preload("res://scripts/animation/run_source_only.gd")

func install(player: AnimationPlayer) -> int:
	if not player.has_animation(&"Walk"):
		push_error("[LembahSari] Run retarget needs the existing player Walk template.")
		return 0
	var donor: Dictionary = RUN_SOURCE.read_motion()
	var records: Array = donor.get("bones",[]) as Array
	if records.size() != 65 or bool(donor.get("source_mesh_included",true)):
		push_error("[LembahSari] Donor must be animation-only data for 65 bones.")
		return 0
	var source_by_bone: Dictionary = {}
	for record: Variant in records:
		if not record is Array or (record as Array).size() != 3:
			continue
		var item: Array = record as Array
		source_by_bone[_canonical(String(item[0]))] = item
	var template: Animation = player.get_animation(&"Walk")
	var motion := Animation.new()
	motion.resource_name = "Run_Extracted_Only"
	motion.length = float(donor.get("duration",1.25))
	motion.loop_mode = Animation.LOOP_LINEAR
	var fps: float = float(donor.get("fps",12))
	var mapped: int = 0
	var animation_root: Node = player.get_node(player.root_node)
	# Reuse the existing character's canonical track paths and rest transforms.
	# This never changes the player GLB, node names, skin or scene hierarchy.
	for source_track: int in range(template.get_track_count()):
		var path: NodePath = template.track_get_path(source_track)
		var track_type: Animation.TrackType = template.track_get_type(source_track)
		var key_count: int = template.track_get_key_count(source_track)
		if key_count == 0:
			continue
		if track_type == Animation.TYPE_ROTATION_3D and path.get_subname_count() > 0:
			var normalized_name: String = _canonical(String(path.get_subname(0)))
			if not source_by_bone.has(normalized_name):
				continue
			var source: Array = source_by_bone[normalized_name] as Array
			var rest_values: Array = source[1] as Array
			var keyframes: Array = source[2] as Array
			if rest_values.size() != 4 or keyframes.size() != 16:
				continue
			var rest: Quaternion = Quaternion(float(rest_values[0]),float(rest_values[1]),float(rest_values[2]),float(rest_values[3])).normalized()
			# The donor and player have matching Mixamo names but NOT
			# necessarily matching local bind orientations. Bone-local delta
			# cannot be copied unchanged between rigs: remap it through both
			# bind frames to preserve the intended parent-space swing.
			var target_skeleton: Skeleton3D = animation_root.get_node_or_null(NodePath(path.get_concatenated_names())) as Skeleton3D
			if target_skeleton == null:
				continue
			var target_bone: int = target_skeleton.find_bone(path.get_subname(0))
			if target_bone < 0:
				continue
			var target_rest: Quaternion = target_skeleton.get_bone_rest(target_bone).basis.get_rotation_quaternion().normalized()
			var source_into_target: Quaternion = (target_rest.inverse()*rest).normalized()
			var influence: float = _anatomical_influence(normalized_name)
			var dest_track: int = motion.add_track(Animation.TYPE_ROTATION_3D)
			motion.track_set_path(dest_track,path)
			for i: int in range(keyframes.size()):
				var values: Array = keyframes[i] as Array
				var q: Quaternion = Quaternion(float(values[0]),float(values[1]),float(values[2]),float(values[3])).normalized()
				# Absolute glTF donor pose -> rest-relative donor rotation,
				# conjugated into the recipient skeleton's bind orientation.
				var donor_delta: Quaternion = (rest.inverse()*q).normalized()
				var target_delta: Quaternion = (source_into_target*donor_delta*source_into_target.inverse()).normalized()
				# The imported clip bends pelvis, spine and head together.
				# Full-strength copies collapse this character sideways when
				# sprint begins (reproducible in the user's screen recording).
				# Retain the limb swing; keep the body's axial pose upright.
				var safe_delta: Quaternion = Quaternion.IDENTITY.slerp(target_delta,influence)
				motion.rotation_track_insert_key(dest_track,float(i)/fps,safe_delta)
			mapped += 1
		elif track_type == Animation.TYPE_POSITION_3D or track_type == Animation.TYPE_SCALE_3D:
			# Preserve the ORIGINAL character's bind offsets and scale.
			# The Run donor supplies rotations only. Never import its pelvis
			# planar displacement (the CharacterBody owns world motion).
			var keep_track: int = motion.add_track(track_type)
			motion.track_set_path(keep_track,path)
			var stationary: Variant = template.track_get_key_value(source_track,0)
			if track_type == Animation.TYPE_POSITION_3D:
				motion.position_track_insert_key(keep_track,0.0,stationary as Vector3)
				motion.position_track_insert_key(keep_track,motion.length,stationary as Vector3)
			else:
				motion.scale_track_insert_key(keep_track,0.0,stationary as Vector3)
				motion.scale_track_insert_key(keep_track,motion.length,stationary as Vector3)
	if mapped < 50:
		push_error("[LembahSari] Run rig incompatible: matched only %d/65 rotation tracks." % mapped)
		return 0
	var library: AnimationLibrary = player.get_animation_library(&"")
	if library == null:
		push_error("[LembahSari] Existing player AnimationLibrary is missing.")
		return 0
	if library.has_animation(&"Run"):
		library.remove_animation(&"Run")
	library.add_animation(&"Run",motion)
	print("[LembahSari] RUN_ONLY_RETARGETED donor=run.001 bones=%d/65 duration=%.3f source_character_mesh=false" % [mapped,motion.length])
	return mapped

func _canonical(value: String) -> String:
	return value.to_lower().replace("mixamorig","").replace("_","").replace(":","").replace("-","").replace(" ","")

func _anatomical_influence(bone: String) -> float:
	# This rig differs in rest orientation/proportion from the donor GLB.
	# Preserve the actual donor running stride on limbs while suppressing
	# additive spine/hip/head tipping that made the player fall sideways.
	if bone == "hips":
		return 0.18
	if bone == "spine":
		return 0.24
	if bone == "spine1" or bone == "spine2":
		return 0.28
	if bone == "neck":
		return 0.22
	if bone == "head":
		return 0.18
	if "shoulder" in bone:
		return 0.56
	if "arm" in bone or "forearm" in bone:
		return 0.86
	if "upleg" in bone or bone.ends_with("leg"):
		return 0.88
	if "foot" in bone or "toe" in bone:
		return 0.77
	return 0.68
