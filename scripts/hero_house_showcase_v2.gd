extends Node3D

const HOUSE_SCENE := "res://assets/models/house_main_01.glb"

var mats: Dictionary = {}

func _ready() -> void:
	_build_environment()
	_build_ground()
	_load_house()
	_build_context()
	_build_camera()
	_capture()

func _mat(key: String, color_value: Color, roughness: float = 0.9) -> StandardMaterial3D:
	if mats.has(key):
		return mats[key] as StandardMaterial3D
	var material := StandardMaterial3D.new()
	material.albedo_color = color_value
	material.roughness = roughness
	mats[key] = material
	return material

func _box(name_value: String, pos: Vector3, size_value: Vector3, material_value: Material, rot: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size_value
	var item := MeshInstance3D.new()
	item.name = name_value
	item.mesh = mesh
	item.material_override = material_value
	item.position = pos
	item.rotation_degrees = rot
	add_child(item)
	return item

func _cyl(name_value: String, pos: Vector3, radius_value: float, height_value: float, material_value: Material, sides: int = 10, rot: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius_value * 0.94
	mesh.bottom_radius = radius_value
	mesh.height = height_value
	mesh.radial_segments = sides
	var item := MeshInstance3D.new()
	item.name = name_value
	item.mesh = mesh
	item.material_override = material_value
	item.position = pos
	item.rotation_degrees = rot
	add_child(item)
	return item

func _sphere(name_value: String, pos: Vector3, radius_value: float, material_value: Material, scale_value: Vector3 = Vector3.ONE) -> MeshInstance3D:
	var mesh := SphereMesh.new()
	mesh.radius = radius_value
	mesh.height = radius_value * 2.0
	mesh.radial_segments = 12
	mesh.rings = 6
	var item := MeshInstance3D.new()
	item.name = name_value
	item.mesh = mesh
	item.material_override = material_value
	item.position = pos
	item.scale = scale_value
	add_child(item)
	return item

func _build_environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("b9dce5")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("dce6d0")
	env.ambient_light_energy = 0.48
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var world := WorldEnvironment.new()
	world.environment = env
	add_child(world)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-46.0, -28.0, 0.0)
	sun.light_color = Color("fff0d2")
	sun.light_energy = 0.88
	sun.shadow_enabled = true
	add_child(sun)

func _build_ground() -> void:
	var grass := _mat("grass", Color("6f9f54"))
	var grass_dark := _mat("grass_dark", Color("567f45"))
	var soil := _mat("soil", Color("76563d"))
	var water := _mat("water", Color("62a9ba"), 0.35)
	var stone := _mat("stone", Color("8b8a7e"))

	_box("Ground", Vector3(0.0, -0.32, 1.2), Vector3(28.0, 0.58, 23.0), grass)
	_box("SoftForeground", Vector3(-6.5, -0.22, -6.4), Vector3(12.0, 0.20, 5.0), grass_dark, Vector3(0.0, -8.0, 0.0))
	_box("Stream", Vector3(8.0, -0.13, -5.8), Vector3(8.0, 0.07, 1.75), water, Vector3(0.0, -10.0, 0.0))
	_box("GardenBedA", Vector3(5.6, -0.01, -1.4), Vector3(3.5, 0.22, 1.55), soil, Vector3(0.0, -8.0, 0.0))
	_box("GardenBedB", Vector3(5.1, -0.01, 0.6), Vector3(3.1, 0.22, 1.35), soil, Vector3(0.0, 7.0, 0.0))

	var path_positions: Array[Vector3] = [
		Vector3(-0.5, 0.05, -4.3), Vector3(-0.8, 0.05, -5.2), Vector3(-0.35, 0.05, -6.2),
		Vector3(0.25, 0.05, -7.1), Vector3(0.8, 0.05, -8.0), Vector3(1.3, 0.05, -8.9)
	]
	for index: int in range(path_positions.size()):
		var path_stone := _sphere("PathStone", path_positions[index], 0.40, stone, Vector3(1.30, 0.22, 0.90))
		path_stone.rotation_degrees.y = float(index * 19 - 30)

func _load_house() -> void:
	if not ResourceLoader.exists(HOUSE_SCENE):
		push_error("Missing Blender hero house GLB")
		return
	var packed := load(HOUSE_SCENE) as PackedScene
	if packed == null:
		push_error("Unable to load Blender hero house GLB")
		return
	var house := packed.instantiate()
	house.name = "HouseMain01"
	house.position = Vector3(-0.8, 0.0, 1.5)
	# Blender front imported toward Godot -X; rotate it toward the hero camera.
	house.rotation_degrees.y = -90.0
	house.scale = Vector3.ONE * 1.10
	add_child(house)

func _build_context() -> void:
	var bamboo := _mat("bamboo", Color("96854f"))
	var leaf := _mat("leaf", Color("437f43"))
	var leaf_light := _mat("leaf_light", Color("67a052"))
	var trunk := _mat("trunk", Color("6f4933"))
	var flower_a := _mat("flower_a", Color("edbd62"))
	var flower_b := _mat("flower_b", Color("e69cab"))

	# Kitchen garden crops.
	for row: int in range(2):
		for col: int in range(5):
			var px: float = 4.45 + float(col) * 0.62
			var pz: float = -1.78 + float(row) * 0.70
			_cyl("CropStem", Vector3(px, 0.26, pz), 0.025, 0.44, leaf, 7)
			_sphere("CropLeafA", Vector3(px - 0.12, 0.43, pz), 0.17, leaf_light, Vector3(1.25, 0.52, 0.76))
			_sphere("CropLeafB", Vector3(px + 0.13, 0.40, pz + 0.04), 0.15, leaf, Vector3(1.10, 0.52, 0.82))

	# Bamboo fence, intentionally uneven.
	for z_value: float in [-3.0, -1.6, -0.2, 1.2, 2.6]:
		_cyl("BambooPost", Vector3(7.4, 0.56, z_value), 0.055, 1.15, bamboo, 8)
	for z_value: float in [-2.3, -0.9, 0.5, 1.9]:
		_cyl("BambooRail", Vector3(7.4, 0.67, z_value), 0.042, 1.50, bamboo, 8, Vector3(90.0, 0.0, 0.0))

	# Flower rhythm around the front garden.
	for flower_data: Dictionary in [
		{"p": Vector3(3.4, 0.0, -2.8), "m": flower_a},
		{"p": Vector3(4.0, 0.0, -2.95), "m": flower_b},
		{"p": Vector3(6.4, 0.0, 1.55), "m": flower_a},
		{"p": Vector3(6.9, 0.0, 1.35), "m": flower_b}
	]:
		var fp := flower_data["p"] as Vector3
		var fm := flower_data["m"] as Material
		_cyl("FlowerStem", fp + Vector3(0.0, 0.20, 0.0), 0.018, 0.40, leaf, 6)
		_sphere("Flower", fp + Vector3(0.0, 0.45, 0.0), 0.09, fm, Vector3(1.1, 0.58, 1.1))

	# Minimal framing vegetation. Imported nature assets replace these next.
	for tree_data: Dictionary in [
		{"p": Vector3(-8.2, 0.0, 3.4), "s": 1.00},
		{"p": Vector3(9.7, 0.0, 2.8), "s": 0.88},
		{"p": Vector3(-9.3, 0.0, -4.8), "s": 0.72}
	]:
		var p := tree_data["p"] as Vector3
		var s := float(tree_data["s"])
		_cyl("TreeTrunk", p + Vector3(0.0, 1.30 * s, 0.0), 0.22 * s, 2.60 * s, trunk, 9)
		_sphere("TreeCanopyA", p + Vector3(0.0, 3.02 * s, 0.0), 1.10 * s, leaf, Vector3(1.15, 0.84, 1.02))
		_sphere("TreeCanopyB", p + Vector3(-0.60 * s, 2.86 * s, 0.08), 0.68 * s, leaf_light, Vector3(1.0, 0.82, 0.92))

func _build_camera() -> void:
	var camera := Camera3D.new()
	camera.name = "HeroCamera"
	camera.position = Vector3(10.8, 6.5, -12.4)
	camera.fov = 32.0
	camera.current = true
	add_child(camera)
	camera.look_at(Vector3(-0.5, 2.0, 0.4), Vector3.UP)

func _capture() -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().process_frame
	var image := get_viewport().get_texture().get_image()
	var result := image.save_png("hero_house_preview.png")
	if result != OK:
		push_error("Failed to save hero house preview: %s" % result)
	get_tree().quit()
