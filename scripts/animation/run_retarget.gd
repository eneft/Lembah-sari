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
			var dest_track: int = motion.add_track(Animation.TYPE_ROTATION_3D)
			motion.track_set_path(dest_track,path)
			for i: int in range(keyframes.size()):
				var values: Array = keyframes[i] as Array
				var q: Quaternion = Quaternion(float(values[0]),float(values[1]),float(values[2]),float(values[3])).normalized()
				# glTF key is a local absolute quaternion. Godot's Skeleton
				# animation track stores bone-pose rotation RELATIVE TO rest.
				# This delta works across matching Mixamo bone names even when
				# the donor's character is a different proportion or design.
				var pose_delta: Quaternion = (rest.inverse()*q).normalized()
				motion.rotation_track_insert_key(dest_track,float(i)/fps,pose_delta)
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
