extends Node3D

const HERO_SCENE := "res://assets/models/hero_scene_01.glb"

func _ready() -> void:
	_build_environment()
	_load_hero_scene()
	_build_camera()
	_capture()

func _build_environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("b9dce5")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("e9dfc2")
	env.ambient_light_energy = 0.52
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var world := WorldEnvironment.new()
	world.environment = env
	add_child(world)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-46.0, -32.0, 0.0)
	sun.light_color = Color("fff0ce")
	sun.light_energy = 0.96
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 50.0
	add_child(sun)

func _load_hero_scene() -> void:
	if not ResourceLoader.exists(HERO_SCENE):
		push_error("Missing Blender hero scene GLB")
		return
	var packed := load(HERO_SCENE) as PackedScene
	if packed == null:
		push_error("Unable to load Blender hero scene GLB")
		return
	var hero := packed.instantiate()
	hero.name = "HeroScene01"
	# Same import orientation used by the approved house facade render.
	hero.rotation_degrees.y = 140.0
	hero.scale = Vector3.ONE * 1.05
	add_child(hero)

func _build_camera() -> void:
	var camera := Camera3D.new()
	camera.name = "HeroCamera"
	camera.position = Vector3(15.8, 9.0, -18.2)
	camera.fov = 34.0
	camera.current = true
	add_child(camera)
	camera.look_at(Vector3(-0.8, 1.65, 0.1), Vector3.UP)

func _capture() -> void:
	for _frame in range(8):
		await get_tree().process_frame
	var image := get_viewport().get_texture().get_image()
	var result := image.save_png("hero_environment_preview.png")
	if result != OK:
		push_error("Failed to save hero environment preview: %s" % result)
	get_tree().quit()
