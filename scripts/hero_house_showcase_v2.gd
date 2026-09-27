extends Node3D

const HOUSE_SCENE := "res://assets/models/house_main_01.glb"

func _ready() -> void:
	_build_environment()
	_build_ground()
	_load_house()
	_build_camera()
	_capture()

func _mat(color_value: Color, roughness: float = 0.96) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color_value
	material.roughness = roughness
	return material

func _build_environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("c7dce0")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("f2e5c8")
	env.ambient_light_energy = 0.72
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var world := WorldEnvironment.new()
	world.environment = env
	add_child(world)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-43.0, -34.0, 0.0)
	sun.light_color = Color("fff0d5")
	sun.light_energy = 0.64
	sun.shadow_enabled = true
	sun.shadow_opacity = 0.52
	sun.directional_shadow_max_distance = 24.0
	add_child(sun)

func _build_ground() -> void:
	# Deliberately minimal. This render is for evaluating the house art direction,
	# not the environment. A single soft ground plate is enough to read shadows.
	var mesh := BoxMesh.new()
	mesh.size = Vector3(18.0, 0.20, 14.0)
	var ground := MeshInstance3D.new()
	ground.name = "HouseReviewGround"
	ground.mesh = mesh
	ground.material_override = _mat(Color("8ca676"))
	ground.position = Vector3(0.0, -0.14, 0.0)
	add_child(ground)

func _load_house() -> void:
	if not ResourceLoader.exists(HOUSE_SCENE):
		push_error("Missing Blender hero house GLB")
		return
	var packed := load(HOUSE_SCENE) as PackedScene
	if packed == null:
		push_error("Unable to load Blender hero house GLB")
		return
	var house := packed.instantiate()
	house.name = "HouseMainConcept25D"
	house.position = Vector3(0.0, 0.0, 0.0)
	# Blender -Y facade imports toward Godot +Z. Rotate the graphic facade toward
	# the fixed 3/4 review camera.
	house.rotation_degrees.y = 138.0
	house.scale = Vector3.ONE * 1.08
	add_child(house)

func _build_camera() -> void:
	var camera := Camera3D.new()
	camera.name = "HouseConceptCamera"
	# Orthographic projection is intentional: the concept reads closer to a
	# painted 2.5D farming-game asset than a perspective-heavy 3D model.
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 10.8
	camera.position = Vector3(10.8, 6.6, -12.8)
	camera.current = true
	add_child(camera)
	camera.look_at(Vector3(0.0, 2.15, 0.0), Vector3.UP)

func _capture() -> void:
	for _frame in range(10):
		await get_tree().process_frame
	var image := get_viewport().get_texture().get_image()
	var result := image.save_png("hero_house_focus_preview.png")
	if result != OK:
		push_error("Failed to save house focus preview: %s" % result)
	get_tree().quit()
