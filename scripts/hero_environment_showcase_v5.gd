extends Node3D

const HERO_SCENE := "res://assets/models/hero_scene_v5.glb"

func _ready() -> void:
	_build_environment()
	_load_hero_scene()
	_build_camera()
	_capture()

func _build_environment() -> void:
	var sky_material := ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color("7ea8b5")
	sky_material.sky_horizon_color = Color("c8d5ca")
	sky_material.ground_bottom_color = Color("566a4f")
	sky_material.ground_horizon_color = Color("c7caa9")
	sky_material.sun_angle_max = 18.0
	var sky := Sky.new()
	sky.sky_material = sky_material

	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	# Morning grade: lift shadow-side readability without flattening the scene.
	env.ambient_light_color = Color("e6d9bc")
	env.ambient_light_energy = 0.34
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.adjustment_enabled = true
	env.adjustment_brightness = 0.94
	env.adjustment_contrast = 1.01
	env.adjustment_saturation = 0.99
	env.fog_enabled = true
	env.fog_light_color = Color("d4dbcd")
	env.fog_light_energy = 0.36
	env.fog_density = 0.0018
	env.fog_sky_affect = 0.18
	var world := WorldEnvironment.new()
	world.environment = env
	add_child(world)

	var sun := DirectionalLight3D.new()
	sun.name = "WarmMorningSun"
	sun.rotation_degrees = Vector3(-36.0, -43.0, 0.0)
	sun.light_color = Color("ffd6a1")
	sun.light_energy = 0.56
	sun.light_specular = 0.72
	sun.shadow_enabled = true
	# GL Compatibility cannot use directional PCSS, so soften the blocky house
	# shadow with filtered edges, reduced opacity and blended PSSM splits.
	sun.shadow_opacity = 0.74
	sun.shadow_blur = 1.28
	sun.shadow_bias = 0.075
	sun.shadow_normal_bias = 1.55
	sun.directional_shadow_max_distance = 50.0
	sun.directional_shadow_fade_start = 0.72
	sun.directional_shadow_blend_splits = true
	add_child(sun)

	var fill := DirectionalLight3D.new()
	fill.name = "SoftSkyFill"
	fill.rotation_degrees = Vector3(-54.0, 128.0, 0.0)
	fill.light_color = Color("bfd5d0")
	fill.light_energy = 0.12
	fill.light_specular = 0.35
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
	# Rotate farther from a front elevation: show more house side depth and let the
	# river climb diagonally into the farming/background mass.
	hero.rotation_degrees.y = 124.0
	hero.scale = Vector3.ONE * 1.035
	add_child(hero)

func _build_camera() -> void:
	var camera := Camera3D.new()
	camera.name = "HeroCameraV5"
	# Lower/closer fixed 3/4 framing. It preserves the full vertical slice while
	# reducing the detached diorama feeling of the earlier high camera.
	camera.position = Vector3(14.7, 5.55, -15.3)
	camera.fov = 33.0
	camera.current = true
	add_child(camera)
	camera.look_at(Vector3(-0.70, 1.20, 1.05), Vector3.UP)

func _capture() -> void:
	for _frame in range(14):
		await get_tree().process_frame
	var image := get_viewport().get_texture().get_image()
	var result := image.save_png("hero_environment_v5_preview.png")
	if result != OK:
		push_error("Failed to save V5 hero environment preview: %s" % result)
	get_tree().quit()
