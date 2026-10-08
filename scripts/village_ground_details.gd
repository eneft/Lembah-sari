extends RefCounted
## Six tiny partly-buried rock accents, authored in fixed-camera screen layout.
## No new collisions or random scattering: keep paths, farmland and stairs clear.
const ROCKS: Array[Dictionary] = [
	{"name":"BananaRootStone","uv":Vector2(0.205,0.565),"size":0.30,"tone":0},
	{"name":"LeftBankStoneA","uv":Vector2(0.120,0.777),"size":0.38,"tone":1},
	{"name":"LeftBankStoneB","uv":Vector2(0.278,0.781),"size":0.24,"tone":0},
	{"name":"CenterBankStone","uv":Vector2(0.372,0.796),"size":0.42,"tone":2},
	{"name":"RightBankStoneA","uv":Vector2(0.751,0.775),"size":0.36,"tone":1},
	{"name":"RightBankStoneB","uv":Vector2(0.865,0.792),"size":0.27,"tone":0},
]
func apply(world: Node3D, view: Camera3D) -> void:
	var root := Node3D.new()
	root.name = "LandscapedGroundDetails"
	world.add_child(root)
	var stones: Array[StandardMaterial3D] = []
	for tone: String in ["807f6c","969483","777664"]:
		var material := StandardMaterial3D.new()
		material.albedo_color = Color(tone)
		material.roughness = 0.94
		material.metallic = 0.0
		stones.append(material)
	var size: Vector2 = view.get_viewport().get_visible_rect().size
	var stone_mesh := SphereMesh.new()
	stone_mesh.radial_segments = 8
	stone_mesh.rings = 4
	var planted: int = 0
	for setting: Dictionary in ROCKS:
		var fraction: Vector2 = setting["uv"]
		var ray_origin: Vector3 = view.project_ray_origin(fraction*size)
		var ray: Vector3 = view.project_ray_normal(fraction*size)
		if ray.y >= -0.001:
			continue
		var at: Vector3 = ray_origin+ray*((-0.065-ray_origin.y)/ray.y)
		var stone: MeshInstance3D = MeshInstance3D.new()
		stone.name = String(setting["name"])
		stone.mesh = stone_mesh
		stone.material_override = stones[int(setting["tone"])]
		var scale_m: float = float(setting["size"])
		stone.scale = Vector3(scale_m*1.18,scale_m*0.60,scale_m*0.93)
		stone.rotation_degrees.y = float(abs(String(stone.name).hash())%145)
		root.add_child(stone)
		# bury the bottom 35% and keep the stone small enough to not hide water
		stone.global_position = at-Vector3.UP*scale_m*0.16
		stone.set_meta("partly_buried",true)
		planted += 1
	root.set_meta("rock_count",planted)
	print("[LembahSari] ORGANIC_STONE_LAYOUT count=%d fixed_camera=true paths=clear" % planted)
