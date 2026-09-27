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
	env.background_color = Color("a9d4dc")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("e4d7bb")
	env.ambient_light_energy = 0.34
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.adjustment_enabled = true
	env.adjustment_brightness = 0.88
	env.adjustment_contrast = 1.08
	env.adjustment_saturation = 1.08
	var world := WorldEnvironment.new()
	world.environment = env
	add_child(world)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48.0, -34.0, 0.0)
	sun.light_color = Color("ffe7bd")
	sun.light_energy = 0.76
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 46.0
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
	hero.rotation_degrees.y = 140.0
	hero.scale = Vector3.ONE * 1.05
	add_child(hero)

func _build_camera() -> void:
	var camera := Camera3D.new()
	camera.name = "HeroCamera"
	camera.position = Vector3(12.7, 6.8, -14.4)
	camera.fov = 35.0
	camera.current = true
	add_child(camera)
	camera.look_at(Vector3(-1.05, 1.55, 0.15), Vector3.UP)

func _capture() -> void:
	for _frame in range(8):
		await get_tree().process_frame
	var image := get_viewport().get_texture().get_image()
	var result := image.save_png("hero_environment_preview.png")
	if result != OK:
		push_error("Failed to save hero environment preview: %s" % result)
	get_tree().quit()
