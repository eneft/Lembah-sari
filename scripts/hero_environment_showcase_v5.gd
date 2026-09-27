extends Node3D

const HERO_SCENE := "res://assets/models/hero_scene_v5.glb"

func _ready() -> void:
	_build_environment()
	_load_hero_scene()
	_build_camera()
	_capture()

func _build_environment() -> void:
	var sky_material := ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color("91b9c6")
	sky_material.sky_horizon_color = Color("d8ddd0")
	sky_material.ground_bottom_color = Color("8a9075")
	sky_material.ground_horizon_color = Color("d7d5bd")
	sky_material.sun_angle_max = 20.0
	var sky := Sky.new()
	sky.sky_material = sky_material

	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_color = Color("ecd9b8")
	env.ambient_light_energy = 0.34
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.adjustment_enabled = true
	env.adjustment_brightness = 0.93
	env.adjustment_contrast = 0.96
	env.adjustment_saturation = 1.05
	env.fog_enabled = true
	env.fog_light_color = Color("d9ddd0")
	env.fog_light_energy = 0.62
	env.fog_density = 0.0065
	env.fog_sky_affect = 0.42
	var world := WorldEnvironment.new()
	world.environment = env
	add_child(world)

	var sun := DirectionalLight3D.new()
	sun.name = "WarmMorningSun"
	sun.rotation_degrees = Vector3(-39.0, -36.0, 0.0)
	sun.light_color = Color("ffe5b6")
	sun.light_energy = 0.56
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 58.0
	add_child(sun)

	var fill := DirectionalLight3D.new()
	fill.name = "SoftSkyFill"
	fill.rotation_degrees = Vector3(-58.0, 132.0, 0.0)
	fill.light_color = Color("bfd5d0")
	fill.light_energy = 0.10
	fill.shadow_enabled = false
	add_child(fill)

func _load_hero_scene() -> void:
	if not ResourceLoader.exists(HERO_SCENE):
		push_error("Missing V5 Blender hero scene GLB")
		return
	var packed := load(HERO_SCENE) as PackedScene
	if packed == null:
		push_error("Unable to load V5 Blender hero scene GLB")
		return
	var hero := packed.instantiate()
	hero.name = "HeroSceneV5"
	# A slightly less frontal angle exposes the house side wall and gives the
	# diagonal river/paddy composition more depth.
	hero.rotation_degrees.y = 132.0
	hero.scale = Vector3.ONE * 1.035
	add_child(hero)

func _build_camera() -> void:
	var camera := Camera3D.new()
	camera.name = "HeroCameraV5"
	camera.position = Vector3(15.2, 6.15, -16.1)
	camera.fov = 34.0
	camera.current = true
	add_child(camera)
	camera.look_at(Vector3(-0.55, 1.28, 0.95), Vector3.UP)

func _capture() -> void:
	for _frame in range(14):
		await get_tree().process_frame
	var image := get_viewport().get_texture().get_image()
	var result := image.save_png("hero_environment_v5_preview.png")
	if result != OK:
		push_error("Failed to save V5 hero environment preview: %s" % result)
	get_tree().quit()
