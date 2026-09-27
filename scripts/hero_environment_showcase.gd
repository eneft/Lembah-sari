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
	env.background_color = Color("b6d4d6")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("dfd4bb")
	env.ambient_light_energy = 0.28
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.adjustment_enabled = true
	env.adjustment_brightness = 0.84
	env.adjustment_contrast = 1.04
	env.adjustment_saturation = 1.04
	var world := WorldEnvironment.new()
	world.environment = env
	add_child(world)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-45.0, -31.0, 0.0)
	sun.light_color = Color("ffe5ba")
	sun.light_energy = 0.70
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 52.0
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
	# Lower and slightly wider than v3: reads as a village composition, not a house showcase.
	camera.position = Vector3(16.8, 7.25, -18.4)
	camera.fov = 38.0
	camera.current = true
	add_child(camera)
	camera.look_at(Vector3(-0.25, 1.35, 0.65), Vector3.UP)

func _capture() -> void:
	for _frame in range(10):
		await get_tree().process_frame
	var image := get_viewport().get_texture().get_image()
	var result := image.save_png("hero_environment_preview.png")
	if result != OK:
		push_error("Failed to save hero environment preview: %s" % result)
	get_tree().quit()
