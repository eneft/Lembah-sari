extends Node3D

const HERO_SCENE: String = "res://assets/models/hero_scene_v5.glb"
const PLAYER_HOUSE_SCENE: String = "res://assets/models/player_house_traditional_v4.glb"
const HERO_ROTATION_Y: float = 124.0
const HERO_SCALE: float = 1.035
# Preserve the embedded house's actual site position when replacing it. This
# fallback matches the currently deployed V5 environment artifact.
const PLAYER_HOUSE_LOCAL_POSITION: Vector3 = Vector3(-4.25, 0.02, -2.85)
# The supplied traditional house faces +Z, as does the original V5 porch.
const PLAYER_HOUSE_LOCAL_ROTATION_Y: float = 0.0
const PLAYER_HOUSE_SCALE: float = 6.6

@onready var player: CharacterBody3D = $Player


func _ready() -> void:
	_build_environment()
	_load_hero_scene()
	_build_test_collision()
	_configure_player_camera()
	_build_test_hud()


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
	env.fog_enabled = true
	env.fog_light_color = Color("cdd7cb")
	env.fog_light_energy = 0.45
	env.fog_density = 0.0025
	env.fog_sky_affect = 0.22

	var world: WorldEnvironment = WorldEnvironment.new()
	world.name = "V5WorldEnvironment"
	world.environment = env
	add_child(world)

	var sun: DirectionalLight3D = DirectionalLight3D.new()
	sun.name = "WarmMorningSun"
	sun.rotation_degrees = Vector3(-38.0, -39.0, 0.0)
	sun.light_color = Color("ffdaa4")
	sun.light_energy = 0.64
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 58.0
	add_child(sun)

	var fill: DirectionalLight3D = DirectionalLight3D.new()
	fill.name = "SoftSkyFill"
	fill.rotation_degrees = Vector3(-58.0, 132.0, 0.0)
	fill.light_color = Color("b8cecb")
	fill.light_energy = 0.075
	fill.shadow_enabled = false
	add_child(fill)


func _load_hero_scene() -> void:
	if not ResourceLoader.exists(HERO_SCENE):
		push_error("Playable V5 test is missing hero_scene_v5.glb")
		return

	var packed: PackedScene = load(HERO_SCENE) as PackedScene
	if packed == null:
		push_error("Playable V5 test could not load hero_scene_v5.glb")
		return

	var hero: Node3D = packed.instantiate() as Node3D
	if hero == null:
		push_error("Playable V5 test hero GLB root is not Node3D")
		return

	hero.name = "HeroSceneV5"
	hero.rotation_degrees.y = HERO_ROTATION_Y
	hero.scale = Vector3.ONE * HERO_SCALE
	add_child(hero)
	_replace_embedded_player_house(hero)


func _replace_embedded_player_house(hero: Node3D) -> void:
	# V5's exported environment still contains the earlier authored house under
	# HeroHouseRoot. Hide/remove that branch before adding the repaired game asset.
	var legacy_house: Node = _find_node_with_prefix(hero, "HeroHouseRoot")
	var house_position: Vector3 = PLAYER_HOUSE_LOCAL_POSITION
	if legacy_house != null:
		if legacy_house is Node3D:
			house_position = hero.to_local((legacy_house as Node3D).global_position)
		_set_node3d_visibility_recursive(legacy_house, false)
		legacy_house.queue_free()
	else:
		push_warning("[LembahSari] Embedded HeroHouseRoot was not found in V5 hero scene.")

	if not ResourceLoader.exists(PLAYER_HOUSE_SCENE):
		push_error("[LembahSari] Repaired player house is missing: %s" % PLAYER_HOUSE_SCENE)
		return

	var house_packed: PackedScene = load(PLAYER_HOUSE_SCENE) as PackedScene
	if house_packed == null:
		push_error("[LembahSari] Repaired player house could not be loaded as PackedScene.")
		return

	var repaired_house: Node3D = house_packed.instantiate() as Node3D
	if repaired_house == null:
		push_error("[LembahSari] Repaired player house GLB root is not Node3D.")
		return

	repaired_house.name = "PlayerHouseTraditionalV4"
	repaired_house.position = house_position
	repaired_house.rotation_degrees.y = PLAYER_HOUSE_LOCAL_ROTATION_Y
	repaired_house.scale = Vector3.ONE * PLAYER_HOUSE_SCALE
	hero.add_child(repaired_house)
	print("[LembahSari] PLAYABLE_HOUSE_V4_ACTIVE")


func _find_node_with_prefix(root: Node, prefix: String) -> Node:
	if String(root.name).begins_with(prefix):
		return root
	for child: Node in root.get_children():
		var found: Node = _find_node_with_prefix(child, prefix)
		if found != null:
			return found
	return null


func _set_node3d_visibility_recursive(root: Node, visible_value: bool) -> void:
	if root is Node3D:
		(root as Node3D).visible = visible_value
	for child: Node in root.get_children():
		_set_node3d_visibility_recursive(child, visible_value)


func _build_test_collision() -> void:
	# First playable pass: a stable walkable floor and hard map bounds. Detailed
	# house/river/bridge collision is intentionally isolated for the next gameplay
	# audit so it can be aligned from actual player movement rather than guessed.
	_add_box_collider(
		"PlayableGround",
		Vector3(0.0, -0.28, 0.0),
		Vector3(34.0, 0.46, 30.0)
	)
	_add_box_collider("NorthBound", Vector3(0.0, 1.1, -15.0), Vector3(34.0, 2.4, 0.5))
	_add_box_collider("SouthBound", Vector3(0.0, 1.1, 15.0), Vector3(34.0, 2.4, 0.5))
	_add_box_collider("WestBound", Vector3(-17.0, 1.1, 0.0), Vector3(0.5, 2.4, 30.0))
	_add_box_collider("EastBound", Vector3(17.0, 1.1, 0.0), Vector3(0.5, 2.4, 30.0))


func _add_box_collider(collider_name: String, center: Vector3, size: Vector3) -> void:
	var body: StaticBody3D = StaticBody3D.new()
	body.name = collider_name
	body.position = center

	var shape_node: CollisionShape3D = CollisionShape3D.new()
	var shape: BoxShape3D = BoxShape3D.new()
	shape.size = size
	shape_node.shape = shape
	body.add_child(shape_node)
	add_child(body)


func _configure_player_camera() -> void:
	var camera: Camera3D = player.get_node_or_null("CameraRig/Camera3D") as Camera3D
	if camera == null:
		push_warning("Playable V5 test could not find the player camera")
		return

	# Low view from the village approach: see the front porch instead of looking
	# down onto the roof. Follow the player with enough room to see the path.
	camera.position = Vector3(9.0, 4.8, -7.0)
	camera.fov = 43.0
	camera.far = 160.0
	camera.look_at(player.global_position + Vector3(0.0, 0.82, 0.0), Vector3.UP)
	player.set("camera_relative_movement", true)


func _build_test_hud() -> void:
	var layer: CanvasLayer = CanvasLayer.new()
	layer.name = "PlayableV5TestHUD"
	add_child(layer)

	var label: Label = Label.new()
	label.name = "TestBadge"
	label.position = Vector2(18.0, 14.0)
	label.text = "V5 PLAYABLE TEST  •  HOUSE V4  •  WASD / joystick  •  Shift: lari"
	label.add_theme_font_size_override("font_size", 16)
	label.modulate = Color(1.0, 1.0, 1.0, 0.88)
	layer.add_child(label)
