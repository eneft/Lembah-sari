extends Node3D

@onready var player: CharacterBody3D = $Player

func _ready() -> void:
	player.set_physics_process(false)
	player.velocity = Vector3.ZERO
	player.position = Vector3.ZERO
	_build_character_stage()
	_configure_review_camera()
	await _validate_character_visual()
	await _capture_review()

func _build_character_stage() -> void:
	var sky_material := ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color("78909c")
	sky_material.sky_horizon_color = Color("dbe3df")
	sky_material.ground_bottom_color = Color("596b56")
	sky_material.ground_horizon_color = Color("c8c8aa")
	var sky := Sky.new()
	sky.sky_material = sky_material

	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.7
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var world := WorldEnvironment.new()
	world.environment = env
	add_child(world)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-35.0, -35.0, 0.0)
	sun.light_energy = 1.1
	sun.shadow_enabled = true
	add_child(sun)

	var floor := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(6.0, 6.0)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color("8fa77a")
	plane.material = mat
	floor.mesh = plane
	add_child(floor)

func _configure_review_camera() -> void:
	var old_camera := player.get_node_or_null("CameraRig/Camera3D") as Camera3D
	if old_camera != null:
		old_camera.current = false

	var camera := Camera3D.new()
	camera.name = "CharacterProofCamera"
	camera.position = Vector3(2.4, 1.65, 3.3)
	camera.fov = 34.0
	camera.near = 0.05
	camera.far = 30.0
	add_child(camera)
	camera.current = true
	camera.look_at(Vector3(0.0, 0.78, 0.0), Vector3.UP)

func _validate_character_visual() -> void:
	for _frame in range(20):
		await get_tree().process_frame

	var model := player.get_node_or_null("Visual/CharacterLembahSari") as Node3D
	if model == null:
		push_error("CHARACTER_VISUAL_GATE missing CharacterLembahSari")
		get_tree().quit(2)
		return

	var meshes := model.find_children("*", "MeshInstance3D", true, false)
	var skeletons := model.find_children("*", "Skeleton3D", true, false)
	var animators := model.find_children("*", "AnimationPlayer", true, false)
	print("CHARACTER_VISUAL_GATE meshes=%d skeletons=%d animators=%d model_global=%s visual_scale=%s" % [
		meshes.size(), skeletons.size(), animators.size(), str(model.global_position), str(player.get_node("Visual").scale)
	])
	if meshes.is_empty() or skeletons.is_empty():
		push_error("CHARACTER_VISUAL_GATE rig/mesh missing")
		get_tree().quit(3)
		return

	var combined := AABB()
	var has_bounds := false
	for node: Node in meshes:
		var mesh := node as MeshInstance3D
		if mesh.mesh == null or not mesh.visible:
			continue
		var local_aabb := mesh.get_aabb()
		var world_aabb := mesh.global_transform * local_aabb
		print("CHARACTER_MESH_BOUNDS name=%s local=%s world=%s global=%s" % [
			mesh.name, str(local_aabb), str(world_aabb), str(mesh.global_position)
		])
		if not has_bounds:
			combined = world_aabb
			has_bounds = true
		else:
			combined = combined.merge(world_aabb)

	if not has_bounds:
		push_error("CHARACTER_VISUAL_GATE no visible mesh bounds")
		get_tree().quit(4)
		return

	print("CHARACTER_COMBINED_BOUNDS %s" % str(combined))
	if combined.size.y < 0.5 or combined.size.y > 4.0:
		push_error("CHARACTER_VISUAL_GATE unreasonable height %.3f" % combined.size.y)
		get_tree().quit(5)
		return
	if absf(combined.get_center().x) > 2.0 or absf(combined.get_center().z) > 2.0:
		push_error("CHARACTER_VISUAL_GATE mesh center too far from player: %s" % str(combined.get_center()))
		get_tree().quit(6)
		return

func _capture_review() -> void:
	for _frame in range(8):
		await get_tree().process_frame
	var image := get_viewport().get_texture().get_image()
	var result := image.save_png("character_scale_review.png")
	if result != OK:
		push_error("Failed to save character-only proof: %s" % result)
		get_tree().quit(7)
		return
	print("CHARACTER_ONLY_PROOF_SAVED")
	get_tree().quit()
