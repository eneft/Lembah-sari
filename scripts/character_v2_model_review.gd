extends Node3D

const CHARACTER_SCENE: String = "res://assets/models/player_character_v2.glb"

func _ready() -> void:
	_build_studio()
	_load_views()
	_capture_review()

func _build_studio() -> void:
	var env: Environment = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("e8dfcc")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("fff1d4")
	env.ambient_light_energy = 0.58
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.adjustment_enabled = true
	env.adjustment_brightness = 1.02
	env.adjustment_contrast = 1.04
	env.adjustment_saturation = 1.04

	var world: WorldEnvironment = WorldEnvironment.new()
	world.environment = env
	add_child(world)

	var sun: DirectionalLight3D = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-42.0, -34.0, 0.0)
	sun.light_color = Color("ffd9a0")
	sun.light_energy = 1.05
	sun.shadow_enabled = true
	add_child(sun)

	var fill: DirectionalLight3D = DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-28.0, 145.0, 0.0)
	fill.light_color = Color("bcd5d0")
	fill.light_energy = 0.30
	fill.shadow_enabled = false
	add_child(fill)

	var ground_mesh: PlaneMesh = PlaneMesh.new()
	ground_mesh.size = Vector2(5.2, 2.5)
	var ground_mat: StandardMaterial3D = StandardMaterial3D.new()
	ground_mat.albedo_color = Color("d8cdb6")
	ground_mat.roughness = 1.0
	ground_mesh.material = ground_mat
	var ground: MeshInstance3D = MeshInstance3D.new()
	ground.mesh = ground_mesh
	ground.position = Vector3(0.0, 0.0, 0.0)
	add_child(ground)

	var camera: Camera3D = Camera3D.new()
	camera.position = Vector3(0.0, 1.33, 5.4)
	camera.fov = 31.0
	camera.near = 0.1
	camera.far = 30.0
	camera.current = true
	add_child(camera)
	camera.look_at(Vector3(0.0, 0.86, 0.0), Vector3.UP)

func _load_views() -> void:
	if not ResourceLoader.exists(CHARACTER_SCENE):
		push_error("Character V2 review is missing player_character_v2.glb")
		return
	var packed: PackedScene = load(CHARACTER_SCENE) as PackedScene
	if packed == null:
		push_error("Character V2 review could not load GLB")
		return

	var view_specs: Array[Dictionary] = [
		{"name": "Front", "x": -1.18, "rotation": 0.0},
		{"name": "ThreeQuarter", "x": 0.0, "rotation": -28.0},
		{"name": "Side", "x": 1.18, "rotation": -88.0},
	]
	for spec in view_specs:
		var instance: Node3D = packed.instantiate() as Node3D
		if instance == null:
			push_error("Character V2 GLB root is not Node3D")
			continue
		instance.name = str(spec["name"])
		instance.position = Vector3(float(spec["x"]), 0.0, 0.0)
		instance.rotation_degrees.y = float(spec["rotation"])
		add_child(instance)

func _capture_review() -> void:
	for _frame in range(24):
		await get_tree().process_frame
	var image: Image = get_viewport().get_texture().get_image()
	var result: Error = image.save_png("character_v2_model_review.png")
	if result != OK:
		push_error("Failed to save Character V2 model review: %s" % result)
	get_tree().quit()
