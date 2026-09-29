extends Node3D

const APPROVED_SCENE: String = "res://assets/models/player_character_v2.glb"
const CANDIDATE_SCENE: String = "res://assets/review/player_character_candidate.glb"
const GAMEPLAY_SCALE: float = 0.82

func _ready() -> void:
	_build_environment()
	_add_ground()
	# Symmetric placement and zero yaw make the height/width comparison unbiased.
	_add_character(APPROVED_SCENE, Vector3(-0.78, 0.0, 0.0))
	_add_character(CANDIDATE_SCENE, Vector3(0.78, 0.0, 0.0))
	_add_camera()
	await _capture()

func _build_environment() -> void:
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color("91b7c1")
	sky_mat.sky_horizon_color = Color("d9ddcd")
	sky_mat.ground_bottom_color = Color("6d7a5e")
	sky_mat.ground_horizon_color = Color("d0c9a8")
	var sky := Sky.new()
	sky.sky_material = sky_mat
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.42
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var world := WorldEnvironment.new()
	world.environment = env
	add_child(world)

	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-42.0, -35.0, 0.0)
	key.light_color = Color("ffd7a1")
	key.light_energy = 0.78
	key.shadow_enabled = true
	add_child(key)

	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-55.0, 135.0, 0.0)
	fill.light_color = Color("c4d5d2")
	fill.light_energy = 0.16
	add_child(fill)

func _add_ground() -> void:
	var mesh := PlaneMesh.new()
	mesh.size = Vector2(5.0, 3.0)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color("d8c99a")
	mat.roughness = 1.0
	mesh.material = mat
	var ground := MeshInstance3D.new()
	ground.mesh = mesh
	add_child(ground)

func _add_character(path: String, position_: Vector3) -> void:
	if not ResourceLoader.exists(path):
		push_error("Missing scale-review character: %s" % path)
		return
	var packed := load(path) as PackedScene
	if packed == null:
		push_error("Could not load scale-review character: %s" % path)
		return
	var character := packed.instantiate() as Node3D
	if character == null:
		push_error("Character root is not Node3D: %s" % path)
		return
	character.position = position_
	character.rotation_degrees.y = 0.0
	character.scale = Vector3.ONE * GAMEPLAY_SCALE
	add_child(character)

func _add_camera() -> void:
	var camera := Camera3D.new()
	# Orthographic projection removes distance/perspective bias between left/right.
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 2.35
	camera.position = Vector3(0.0, 1.18, 5.0)
	camera.current = true
	add_child(camera)
	camera.look_at(Vector3(0.0, 0.90, 0.0), Vector3.UP)

func _capture() -> void:
	for _frame in range(20):
		await get_tree().process_frame
	var image := get_viewport().get_texture().get_image()
	var result := image.save_png("character_candidate_scale_review.png")
	if result != OK:
		push_error("Failed to save candidate scale review: %s" % result)
	get_tree().quit()
