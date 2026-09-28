extends Node3D

const HERO_SCENE: String = "res://assets/models/hero_scene_v5.glb"
const HERO_ROTATION_Y: float = 124.0
const HERO_SCALE: float = 1.035

@onready var player: CharacterBody3D = $Player

func _ready() -> void:
	# Review-only scene: freeze character movement/gravity so the captured frame
	# measures silhouette and environment scale from the authored spawn position.
	player.set_physics_process(false)
	player.velocity = Vector3.ZERO
	_build_environment()
	_load_hero_scene()
	_configure_review_camera()
	_capture_review()

func _build_environment() -> void:
	var sky_material: ProceduralSkyMaterial = ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color("7ea8b5")
	sky_material.sky_horizon_color = Color("c8d5ca")
	sky_material.ground_bottom_color = Color("566a4f")
	sky_material.ground_horizon_color = Color("c7caa9")
	sky_material.sun_angle_max = 18.0
	var sky: Sky = Sky.new()
	sky.sky_material = sky_material

	var env: Environment = Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_color = Color("ead4ae")
	env.ambient_light_energy = 0.26
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.adjustment_enabled = true
	env.adjustment_brightness = 0.88
	env.adjustment_contrast = 1.05
	env.adjustment_saturation = 1.10

	var world: WorldEnvironment = WorldEnvironment.new()
	world.environment = env
	add_child(world)

	var sun: DirectionalLight3D = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-38.0, -39.0, 0.0)
	sun.light_color = Color("ffdaa4")
	sun.light_energy = 0.64
	sun.shadow_enabled = true
	add_child(sun)

	var fill: DirectionalLight3D = DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-58.0, 132.0, 0.0)
	fill.light_color = Color("b8cecb")
	fill.light_energy = 0.075
	fill.shadow_enabled = false
	add_child(fill)

func _load_hero_scene() -> void:
	if not ResourceLoader.exists(HERO_SCENE):
		push_error("Character scale review is missing hero_scene_v5.glb")
		return
	var packed: PackedScene = load(HERO_SCENE) as PackedScene
	if packed == null:
		push_error("Character scale review could not load hero scene")
		return
	var hero: Node3D = packed.instantiate() as Node3D
	if hero == null:
		push_error("Character scale review hero root is not Node3D")
		return
	hero.rotation_degrees.y = HERO_ROTATION_Y
	hero.scale = Vector3.ONE * HERO_SCALE
	add_child(hero)

func _configure_review_camera() -> void:
	var camera: Camera3D = player.get_node_or_null("CameraRig/Camera3D") as Camera3D
	if camera == null:
		push_error("Character scale review could not find player camera")
		return
	camera.position = Vector3(5.8, 5.0, 5.8)
	camera.fov = 35.0
	camera.far = 160.0
	camera.current = true
	camera.look_at(player.global_position + Vector3(0.0, 0.82, 0.0), Vector3.UP)

func _capture_review() -> void:
	for _frame in range(18):
		await get_tree().process_frame
	var image: Image = get_viewport().get_texture().get_image()
	var result: Error = image.save_png("character_scale_review.png")
	if result != OK:
		push_error("Failed to save character scale review: %s" % result)
	get_tree().quit()
