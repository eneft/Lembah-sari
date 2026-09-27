extends Node3D

const HOUSE_SCENE := "res://assets/models/house_main_01.glb"

func _ready() -> void:
	_build_environment()
	_build_ground()
	_load_house()
	_build_camera()
	_capture()

func _mat(color_value: Color, roughness: float = 0.98) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color_value
	material.roughness = roughness
	return material

func _build_environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("c7dbe0")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("eadfc9")
	env.ambient_light_energy = 0.58
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var world := WorldEnvironment.new()
	world.environment = env
	add_child(world)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-40.0, -28.0, 0.0)
	sun.light_color = Color("ffe7c4")
	sun.light_energy = 0.48
	sun.shadow_enabled = true
	sun.shadow_opacity = 0.46
	sun.directional_shadow_max_distance = 24.0
	add_child(sun)

func _build_ground() -> void:
	# Minimal review plate only. Environment stays out of the decision until the
	# house itself is approved.
	var mesh := BoxMesh.new()
	mesh.size = Vector3(18.0, 0.18, 14.0)
	var ground := MeshInstance3D.new()
	ground.name = "HouseReviewGround"
	ground.mesh = mesh
	ground.material_override = _mat(Color("718760"))
	ground.position = Vector3(0.0, -0.13, 0.0)
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
	# About 30 degrees away from face-on: enough side depth to read as 3/4,
	# still flat enough to preserve the concept's semi-2D feel.
	house.rotation_degrees.y = 110.0
	house.scale = Vector3.ONE * 1.08
	add_child(house)

func _build_camera() -> void:
	var camera := Camera3D.new()
	camera.name = "HouseConceptCamera"
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 10.2
	camera.position = Vector3(10.8, 6.4, -12.8)
	camera.current = true
	add_child(camera)
	camera.look_at(Vector3(0.0, 2.12, 0.0), Vector3.UP)

func _capture() -> void:
	for _frame in range(10):
		await get_tree().process_frame
	var image := get_viewport().get_texture().get_image()
	var result := image.save_png("hero_house_focus_preview.png")
	if result != OK:
		push_error("Failed to save house focus preview: %s" % result)
	get_tree().quit()
