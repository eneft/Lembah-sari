extends Node3D

const REVIEW_BACKGROUND: Color = Color("10161d")
const MIN_FOREGROUND_PIXELS: int = 500
const MIN_SILHOUETTE_HEIGHT: int = 80
const MIN_SILHOUETTE_WIDTH: int = 24

@onready var player: CharacterBody3D = $Player

func _ready() -> void:
	player.set_physics_process(false)
	player.velocity = Vector3.ZERO
	_build_review_environment()
	_configure_review_camera()
	await _capture_and_validate()

func _build_review_environment() -> void:
	var env: Environment = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = REVIEW_BACKGROUND
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("f1e5d1")
	env.ambient_light_energy = 0.62
	env.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	var world: WorldEnvironment = WorldEnvironment.new()
	world.environment = env
	add_child(world)

	var key: DirectionalLight3D = DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-38.0, -34.0, 0.0)
	key.light_color = Color("ffd9ad")
	key.light_energy = 1.15
	add_child(key)

	var fill: DirectionalLight3D = DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-25.0, 145.0, 0.0)
	fill.light_color = Color("bcd7e4")
	fill.light_energy = 0.48
	add_child(fill)

func _configure_review_camera() -> void:
	var camera: Camera3D = player.get_node_or_null("CameraRig/Camera3D") as Camera3D
	if camera == null:
		push_error("Character-only review could not find player camera.")
		get_tree().quit(1)
		return
	camera.set_as_top_level(true)
	camera.global_position = player.global_position + Vector3(2.25, 1.50, 3.05)
	camera.fov = 31.0
	camera.near = 0.05
	camera.far = 20.0
	camera.current = true
	camera.look_at(player.global_position + Vector3(0.0, 0.78, 0.0), Vector3.UP)

func _capture_and_validate() -> void:
	for _frame: int in range(24):
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image: Image = get_viewport().get_texture().get_image()
	var save_result: Error = image.save_png("character_scale_review.png")
	if save_result != OK:
		push_error("Failed to save character-only review: %s" % save_result)
		get_tree().quit(1)
		return

	var background: Color = image.get_pixel(0, 0)
	var foreground_pixels: int = 0
	var min_x: int = image.get_width()
	var min_y: int = image.get_height()
	var max_x: int = -1
	var max_y: int = -1
	const SAMPLE_STEP: int = 2

	for y: int in range(0, image.get_height(), SAMPLE_STEP):
		for x: int in range(0, image.get_width(), SAMPLE_STEP):
			var pixel: Color = image.get_pixel(x, y)
			var difference: float = absf(pixel.r - background.r) + absf(pixel.g - background.g) + absf(pixel.b - background.b)
			if difference <= 0.10:
				continue
			foreground_pixels += 1
			min_x = mini(min_x, x)
			min_y = mini(min_y, y)
			max_x = maxi(max_x, x)
			max_y = maxi(max_y, y)

	var silhouette_width: int = 0 if max_x < 0 else max_x - min_x + 1
	var silhouette_height: int = 0 if max_y < 0 else max_y - min_y + 1
	var visible: bool = foreground_pixels >= MIN_FOREGROUND_PIXELS and silhouette_width >= MIN_SILHOUETTE_WIDTH and silhouette_height >= MIN_SILHOUETTE_HEIGHT
	print("CHARACTER_VISUAL_REVIEW pixels=%d bbox=%dx%d" % [foreground_pixels, silhouette_width, silhouette_height])
	if not visible:
		push_error("Character visual validation failed: player mesh is missing, off-camera, or collapsed.")
		get_tree().quit(1)
		return
	print("CHARACTER_VISUAL_REVIEW_VALIDATED pixels=%d bbox=%dx%d" % [foreground_pixels, silhouette_width, silhouette_height])
	get_tree().quit(0)
