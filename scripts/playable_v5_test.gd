extends Node3D

const HYBRID_ENVIRONMENT = "res://scripts/village_hybrid_environment.gd"
const FOREGROUND_PLANTS = "res://scripts/village_foreground_plants.gd"
const FOREGROUND_GRASS = "res://scripts/village_foreground_grass.gd"

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

# Final fixed-camera composition is independent from player spawn/movement.
# These values preserve the approved framing from the previous passes.
const CAMERA_WORLD_POSITION: Vector3 = Vector3(12.3, 4.88, -3.9)
const CAMERA_WORLD_TARGET: Vector3 = Vector3(3.3, 0.90, 3.1)
const CAMERA_FOV: float = 43.0

@onready var player: CharacterBody3D = $Player


func _ready() -> void:
	_build_environment()
	_load_hero_scene()
	_build_test_collision()
	_configure_player_camera()
	_build_player_readability()
	_apply_hybrid_environment()
	_apply_foreground_plants()
	_apply_foreground_grass()


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

	var world: WorldEnvironment = WorldEnvironment.new()
	world.name = "V5WorldEnvironment"
	world.environment = env
	add_child(world)

	var sun: DirectionalLight3D = DirectionalLight3D.new()
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

	var fill: DirectionalLight3D = DirectionalLight3D.new()
	fill.name = "SoftSkyFill"
	fill.rotation_degrees = Vector3(-54.0, 128.0, 0.0)
	fill.light_color = Color("bfd5d0")
	fill.light_energy = 0.12
	fill.light_specular = 0.35
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
	_polish_player_house_gable(repaired_house)
	print("[LembahSari] PLAYABLE_HOUSE_V4_ACTIVE")


func _polish_player_house_gable(house: Node3D) -> void:
	# The source mesh leaves a visually flat triangle under the front ridge.
	# Overlay a light woven-bamboo infill and a real timber king-post truss.
	# Coordinates are in the normalized repaired-house space; the complete house
	# remains uniformly scaled by PLAYER_HOUSE_SCALE.
	var polish := Node3D.new()
	polish.name = "FrontGablePolish"
	house.add_child(polish)

	var weave_material := _make_gable_weave_material()
	var panel_tool := SurfaceTool.new()
	panel_tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	var left := Vector3(-0.315, 0.382, 0.320)
	var right := Vector3(0.247, 0.382, 0.320)
	var peak := Vector3(-0.034, 0.566, 0.320)
	panel_tool.set_uv(Vector2(0.0, 0.0))
	panel_tool.add_vertex(left)
	panel_tool.set_uv(Vector2(1.0, 0.0))
	panel_tool.add_vertex(right)
	panel_tool.set_uv(Vector2(0.5, 1.0))
	panel_tool.add_vertex(peak)
	var panel := MeshInstance3D.new()
	panel.name = "GableWovenBambooPanel"
	panel.mesh = panel_tool.commit()
	panel.set_surface_override_material(0, weave_material)
	polish.add_child(panel)

	# Existing fitted gable boards get the same finish when visible from other angles.
	for node: Node in house.find_children("*", "MeshInstance3D", true, false):
		var mesh_node := node as MeshInstance3D
		if String(mesh_node.name).begins_with("GableTimberBoards_"):
			for surface: int in range(mesh_node.mesh.get_surface_count()):
				mesh_node.set_surface_override_material(surface, weave_material)

	var timber := StandardMaterial3D.new()
	timber.resource_name = "FrontGableStructuralTimber"
	timber.albedo_color = Color("65452f")
	timber.roughness = 0.90
	timber.metallic = 0.0

	var beam_z := 0.327
	var tie_left := Vector3(-0.315, 0.392, beam_z)
	var tie_right := Vector3(0.247, 0.392, beam_z)
	var ridge := Vector3(-0.034, 0.566, beam_z)
	var center_bottom := Vector3(-0.034, 0.392, beam_z)
	_add_gable_beam(polish, "GableTieBeam", tie_left, tie_right, 0.018, timber)
	_add_gable_beam(polish, "GableLeftRafter", tie_left, ridge, 0.018, timber)
	_add_gable_beam(polish, "GableRightRafter", ridge, tie_right, 0.018, timber)
	_add_gable_beam(polish, "GableKingPost", center_bottom, ridge, 0.016, timber)
	_add_gable_beam(polish, "GableLeftBrace", center_bottom, Vector3(-0.175, 0.480, beam_z), 0.012, timber)
	_add_gable_beam(polish, "GableRightBrace", center_bottom, Vector3(0.107, 0.480, beam_z), 0.012, timber)
	print("[LembahSari] FRONT_GABLE_POLISHED")


func _make_gable_weave_material() -> ShaderMaterial:
	var material := ShaderMaterial.new()
	material.resource_name = "GableWovenBamboo"
	var shader := Shader.new()
	shader.code = """
shader_type spatial;
render_mode cull_disabled, diffuse_burley, specular_schlick_ggx;

float stripe(float value, float frequency) {
	return smoothstep(0.32, 0.48, abs(fract(value * frequency) - 0.5));
}

void fragment() {
	vec2 p = UV;
	float diagonal_a = stripe(p.x + p.y * 0.72, 16.0);
	float diagonal_b = stripe(p.x - p.y * 0.72, 16.0);
	float weave = mix(diagonal_a, diagonal_b, step(0.5, fract(p.y * 18.0)));
	float grain = 0.5 + 0.5 * sin((p.x * 31.0 + p.y * 7.0) * 6.28318);
	vec3 bamboo_light = vec3(0.53, 0.36, 0.20);
	vec3 bamboo_dark = vec3(0.30, 0.19, 0.105);
	vec3 base = mix(bamboo_dark, bamboo_light, 0.46 + weave * 0.34);
	ALBEDO = base * (0.92 + grain * 0.08);
	ROUGHNESS = 0.92;
	METALLIC = 0.0;
}
"""
	material.shader = shader
	return material


func _add_gable_beam(parent: Node3D, beam_name: String, start: Vector3, finish: Vector3, width: float, material: Material) -> void:
	var direction := finish - start
	var length := direction.length()
	if length <= 0.0001:
		return
	var mesh := BoxMesh.new()
	mesh.size = Vector3(width, width, length)
	var beam := MeshInstance3D.new()
	beam.name = beam_name
	beam.mesh = mesh
	beam.position = (start + finish) * 0.5
	beam.quaternion = Quaternion(Vector3(0.0, 0.0, 1.0), direction.normalized())
	beam.set_surface_override_material(0, material)
	parent.add_child(beam)


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
	_add_box_collider("NorthBound", Vector3(0.0, 1.1, -4.2), Vector3(34.0, 2.4, 0.5))
	_add_box_collider("SouthBound", Vector3(0.0, 1.1, 10.0), Vector3(34.0, 2.4, 0.5))
	_add_box_collider("WestBound", Vector3(-8.5, 1.1, 0.0), Vector3(0.5, 2.4, 30.0))
	_add_box_collider("EastBound", Vector3(9.5, 1.1, 0.0), Vector3(0.5, 2.4, 30.0))


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
	var rig: Node3D = player.get_node_or_null("CameraRig") as Node3D
	var camera: Camera3D = player.get_node_or_null("CameraRig/Camera3D") as Camera3D
	if rig == null or camera == null:
		push_warning("Playable V5 test could not find the fixed camera rig")
		return

	# Detach once, then author the camera in world space. Player spawn changes can
	# no longer nudge the whole composition or move the house away from its frame.
	rig.set_as_top_level(true)
	rig.global_transform = Transform3D.IDENTITY
	camera.position = CAMERA_WORLD_POSITION
	camera.fov = CAMERA_FOV
	camera.near = 0.10
	camera.far = 160.0
	camera.look_at(CAMERA_WORLD_TARGET, Vector3.UP)
	player.set("camera_relative_movement", true)


func _build_player_readability() -> void:
	# A restrained contact ellipse keeps the stylized character grounded/readable
	# across grass, dirt and shallow-water values without adding an outline shader.
	var shadow := MeshInstance3D.new()
	shadow.name = "PlayerContactShadow"
	var disc := CylinderMesh.new()
	disc.top_radius = 0.34
	disc.bottom_radius = 0.34
	disc.height = 0.012
	disc.radial_segments = 28
	shadow.mesh = disc
	shadow.scale = Vector3(1.18, 1.0, 0.72)
	shadow.position = Vector3(0.0, 0.012, 0.0)
	shadow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

	var material := StandardMaterial3D.new()
	material.resource_name = "PlayerReadabilityContact"
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = Color(0.055, 0.050, 0.040, 0.17)
	material.roughness = 1.0
	shadow.material_override = material
	player.add_child(shadow)


func _apply_hybrid_environment() -> void:
	var hero: Node3D = get_node_or_null("HeroSceneV5") as Node3D
	var camera: Camera3D = player.get_node("CameraRig/Camera3D") as Camera3D
	if hero != null:
		var environment_script: Script = load(HYBRID_ENVIRONMENT) as Script
		if environment_script != null and environment_script.can_instantiate():
			environment_script.new().apply(hero,camera)
		else:
			push_error("[LembahSari] Could not load image environment")


func _apply_foreground_plants() -> void:
	# Foreground polygons are authored after image cards. Distant vegetation and
	# the backdrop stay sprite/image based; overlapping near cards are culled.
	var hero: Node3D = get_node_or_null("HeroSceneV5") as Node3D
	if hero == null:
		return
	var plant_script: Script = load(FOREGROUND_PLANTS) as Script
	if plant_script == null or not plant_script.can_instantiate():
		push_error("[LembahSari] Foreground plant placement script is missing")
		return
	plant_script.new().apply(hero,player)

func _apply_foreground_grass() -> void:
	# Render-only real polygon grass, after the hero plants are placed, so grass
	# can avoid the tree/palm trunks; fixed camera and movement remain unchanged.
	var grass_script: Script = load(FOREGROUND_GRASS) as Script
	if grass_script == null or not grass_script.can_instantiate():
		push_error("[LembahSari] Missing procedural foreground grass")
		return
	var camera: Camera3D = player.get_node("CameraRig/Camera3D") as Camera3D
	grass_script.new().apply(self,camera,player)
