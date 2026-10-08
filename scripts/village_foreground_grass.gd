extends RefCounted
## Selective polygon grass in the fixed-camera playable foreground.
## No extra textures or draw calls per tuft: 4 MultiMeshInstance3D batches.
## Distant grass/hills are deliberately left image-based.
const GROUND_Y: float = -0.045
const GRASS_SEED: int = 20261008
const TERRAIN_MIN: Vector2 = Vector2(-8.1, -3.85)
const TERRAIN_MAX: Vector2 = Vector2(9.1, 9.65)
const REGIONS: Array[Dictionary] = [
	{"name":"LawnGrass3D", "amount":510, "rect":Rect2(0.06,0.64,0.88,0.135), "min_h":0.12, "max_h":0.23},
	{"name":"LeftGardenGrass3D", "amount":235, "rect":Rect2(0.055,0.49,0.40,0.21), "min_h":0.11, "max_h":0.21},
	{"name":"RightGardenGrass3D", "amount":195, "rect":Rect2(0.66,0.51,0.30,0.20), "min_h":0.12, "max_h":0.21},
	{"name":"RiverBankGrass3D", "amount":205, "rect":Rect2(0.07,0.766,0.86,0.044), "min_h":0.21, "max_h":0.37},
]
func apply(world: Node3D, view: Camera3D, player: CharacterBody3D) -> void:
	var root := Node3D.new()
	root.name = "ForegroundGrass3D"
	world.add_child(root)
	var blade_mesh: ArrayMesh = _build_blade_mesh()
	var grass_material: StandardMaterial3D = _grass_material()
	blade_mesh.surface_set_material(0,grass_material)
	var rng := RandomNumberGenerator.new()
	rng.seed = GRASS_SEED
	var screen_size: Vector2 = view.get_viewport().get_visible_rect().size
	var count: int = 0
	for region: Dictionary in REGIONS:
		var zone: Rect2 = region["rect"]
		var max_amount: int = int(region["amount"])
		var transforms: Array[Transform3D] = []
		var colors: Array[Color] = []
		for attempt: int in range(max_amount):
			var sample: Vector2 = Vector2(
				rng.randf_range(zone.position.x,zone.end.x),
				rng.randf_range(zone.position.y,zone.end.y)
			)
			if _is_clear_zone(sample):
				continue
			var at: Vector3 = _ground_point(view,sample * screen_size)
			if not _is_playable_ground(at,player):
				continue
			if _near_foreground_plant(world,at):
				continue
			var height: float = rng.randf_range(float(region["min_h"]),float(region["max_h"]))
			var width: float = rng.randf_range(0.68,1.14) * height
			var spin: float = rng.randf_range(-PI,PI)
			var tilt: float = rng.randf_range(-0.09,0.09)
			var basis: Basis = Basis.from_euler(Vector3(tilt,spin,0.0)) * Basis.from_scale(Vector3(width,height,width))
			transforms.append(Transform3D(basis,at))
			var variation: float = rng.randf_range(0.89,1.09)
			colors.append(Color(variation,variation*0.99,variation*0.91,1.0))
		if transforms.is_empty():
			push_warning("[LembahSari] Grass region has no playable ground: %s" % region["name"])
			continue
		# Headless/dummy renderers return identity from MultiMesh GPU readback.
		# Keep exact authored height bounds in CPU metadata for regression tests.
		var min_height: float = INF
		var max_height: float = -INF
		for authored: Transform3D in transforms:
			var authored_height: float = authored.basis.get_scale().y
			min_height = minf(min_height,authored_height)
			max_height = maxf(max_height,authored_height)
		var multimesh := MultiMesh.new()
		multimesh.transform_format = MultiMesh.TRANSFORM_3D
		multimesh.use_colors = true
		multimesh.mesh = blade_mesh
		multimesh.instance_count = transforms.size()
		for index: int in range(transforms.size()):
			multimesh.set_instance_transform(index,transforms[index])
			multimesh.set_instance_color(index,colors[index])
		var node := MultiMeshInstance3D.new()
		node.name = String(region["name"])
		node.multimesh = multimesh
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		node.set_meta("authored_min_height",min_height)
		node.set_meta("authored_max_height",max_height)
		root.add_child(node)
		count += transforms.size()
	root.set_meta("tufts",count)
	root.set_meta("batches",root.get_child_count())
	root.set_meta("image_background_preserved",true)
	print("[LembahSari] VOLUMETRIC_GRASS_READY tufts=%d batches=%d foreground=polygon far=image" % [count,root.get_child_count()])

func _build_blade_mesh() -> ArrayMesh:
	# Each tuft is five crossed, tapered blades. Triangles are real geometry;
	# base and tips have natural color gradient. 15 triangles/tuft.
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for blade: int in range(5):
		var angle: float = float(blade)*TAU/5.0
		var radial: Vector3 = Vector3(cos(angle),0.0,sin(angle))
		var tangent: Vector3 = Vector3(-sin(angle),0.0,cos(angle))
		var foot: Vector3 = radial*0.075
		var left: Vector3 = foot-tangent*0.145
		var right: Vector3 = foot+tangent*0.145
		var shoulder: Vector3 = foot+radial*0.045+Vector3.UP*0.55
		var left_mid: Vector3 = shoulder-tangent*0.076
		var right_mid: Vector3 = shoulder+tangent*0.076
		var tip: Vector3 = foot+radial*0.15+Vector3.UP*(0.85+float(blade%3)*0.075)
		_grass_triangle(surface,left,right,left_mid,0.0,0.0,0.55)
		_grass_triangle(surface,right,right_mid,left_mid,0.0,0.55,0.55)
		_grass_triangle(surface,left_mid,right_mid,tip,0.55,0.55,1.0)
	surface.generate_normals()
	return surface.commit() as ArrayMesh

func _grass_triangle(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, ya: float, yb: float, yc: float) -> void:
	for v: Dictionary in [
		{"pos":a,"h":ya},
		{"pos":b,"h":yb},
		{"pos":c,"h":yc},
	]:
		var t: float = float(v["h"])
		# Slightly golden tips match the warm-morning ground and the plant GLBs.
		var color: Color = Color("526a32").lerp(Color("a6b85d"),t)
		st.set_color(color)
		st.set_uv(Vector2(0.5,t))
		st.add_vertex(v["pos"])

func _grass_material() -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.resource_name = "LembahSariWarmGrassBlades"
	mat.vertex_color_use_as_albedo = true
	mat.albedo_color = Color.WHITE
	mat.roughness = 0.98
	mat.metallic = 0.0
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	return mat

func _ground_point(view: Camera3D, pixel: Vector2) -> Vector3:
	var start: Vector3 = view.project_ray_origin(pixel)
	var direction: Vector3 = view.project_ray_normal(pixel)
	if direction.y > -0.001:
		return Vector3(9999.0,GROUND_Y,9999.0)
	var distance: float = (GROUND_Y-start.y)/direction.y
	return start+direction*distance

func _is_playable_ground(at: Vector3, player: CharacterBody3D) -> bool:
	if at.x < TERRAIN_MIN.x or at.x > TERRAIN_MAX.x or at.z < TERRAIN_MIN.y or at.z > TERRAIN_MAX.y:
		return false
	var delta: Vector2 = Vector2(at.x-player.global_position.x,at.z-player.global_position.z)
	# Keep the character's starting footprint clear for readability.
	return delta.length_squared() > 0.68*0.68

func _is_clear_zone(p: Vector2) -> bool:
	# The path sweeps from the house entrance to the screen-right exit.
	var line_start := Vector2(0.49,0.565)
	var line_end := Vector2(1.02,0.685)
	var segment: Vector2 = line_end-line_start
	var u: float = clampf((p-line_start).dot(segment)/segment.length_squared(),0.0,1.0)
	if p.distance_to(line_start+segment*u) < 0.049:
		return true
	# No decorative grass on the stairs, door landing, rice fields or river.
	if p.x > 0.66 and p.y < 0.59:
		return true
	if p.x > 0.37 and p.x < 0.66 and p.y < 0.57:
		return true
	return p.y >= 0.81

func _near_foreground_plant(world: Node3D, point: Vector3) -> bool:
	var hero: Node3D = world.get_node_or_null("HeroSceneV5") as Node3D
	if hero == null:
		return false
	var plants: Node3D = hero.get_node_or_null("ForegroundPlants3D") as Node3D
	if plants == null:
		return false
	for model: Node in plants.get_children():
		if not model is Node3D:
			continue
		var plant: Node3D = model as Node3D
		var kind: int = int(plant.get_meta("plant_type",-1))
		var clearance: float = 0.56 if kind <= 1 else 0.43
		if Vector2(point.x-plant.global_position.x,point.z-plant.global_position.z).length_squared() < clearance*clearance:
			return true
	return false
