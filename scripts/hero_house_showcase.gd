extends Node3D

const HOUSE_SCENE := "res://assets/models/house_main_01.glb"

var _materials: Dictionary = {}

func _ready() -> void:
	_build_environment()
	_build_ground_context()
	_load_house_asset()
	_build_garden_context()
	_build_foliage_context()
	_build_camera()
	_capture_when_ready()

func _mat(key: String, color_value: Color, roughness: float = 0.9) -> StandardMaterial3D:
	if _materials.has(key):
		return _materials[key] as StandardMaterial3D
	var material := StandardMaterial3D.new()
	material.albedo_color = color_value
	material.roughness = roughness
	_materials[key] = material
	return material

func _box(node_name: String, position_value: Vector3, size_value: Vector3, material_value: Material, rotation_value: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size_value
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.material_override = material_value
	instance.position = position_value
	instance.rotation_degrees = rotation_value
	add_child(instance)
	return instance

func _cylinder(node_name: String, position_value: Vector3, radius_value: float, height_value: float, material_value: Material, sides: int = 10) -> MeshInstance3D:
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius_value * 0.94
	mesh.bottom_radius = radius_value
	mesh.height = height_value
	mesh.radial_segments = sides
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.material_override = material_value
	instance.position = position_value
	add_child(instance)
	return instance

func _sphere(node_name: String, position_value: Vector3, radius_value: float, material_value: Material, scale_value: Vector3 = Vector3.ONE) -> MeshInstance3D:
	var mesh := SphereMesh.new()
	mesh.radius = radius_value
	mesh.height = radius_value * 2.0
	mesh.radial_segments = 12
	mesh.rings = 6
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.material_override = material_value
	instance.position = position_value
	instance.scale = scale_value
	add_child(instance)
	return instance

func _build_environment() -> void:
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("b9dce2")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("f5e5c7")
	environment.ambient_light_energy = 0.72
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var world := WorldEnvironment.new()
	world.environment = environment
	add_child(world)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-44.0, -34.0, 0.0)
	sun.light_color = Color("ffe0aa")
	sun.light_energy = 1.15
	sun.shadow_enabled = true
	add_child(sun)

func _build_ground_context() -> void:
	var grass := _mat("grass", Color("78a85b"))
	var grass_dark := _mat("grass_dark", Color("5c8a49"))
	var dirt := _mat("dirt", Color("b79062"))
	var soil := _mat("soil", Color("76543a"))
	var stone := _mat("stone", Color("8d8d84"))

	_box("Ground", Vector3(0.0, -0.30, 1.0), Vector3(30.0, 0.55, 24.0), grass)
	_box("FrontMeadow", Vector3(-8.0, -0.20, -7.2), Vector3(13.0, 0.18, 5.0), grass_dark, Vector3(0.0, -6.0, 0.0))

	# Curved-looking stepping path assembled as irregular stones, purely context.
	var path_positions: Array[Vector3] = [
		Vector3(-0.4, 0.05, -4.6), Vector3(-0.8, 0.05, -5.6), Vector3(-0.25, 0.05, -6.6),
		Vector3(0.25, 0.05, -7.6), Vector3(0.8, 0.05, -8.6), Vector3(1.2, 0.05, -9.4)
	]
	for index: int in range(path_positions.size()):
		var stone_instance := _sphere("PathStone", path_positions[index], 0.42, stone, Vector3(1.35, 0.22, 0.95))
		stone_instance.rotation_degrees.y = float(index * 21 - 35)

	# Two garden soil beds at camera-right.
	_box("GardenBedA", Vector3(5.6, -0.02, -1.7), Vector3(3.4, 0.22, 1.55), soil, Vector3(0.0, -8.0, 0.0))
	_box("GardenBedB", Vector3(5.1, -0.02, 0.35), Vector3(3.0, 0.22, 1.35), soil, Vector3(0.0, 7.0, 0.0))

	# A small water ribbon hints at the wider village scene without competing with the house.
	var water := _mat("water", Color("65afbf"), 0.35)
	_box("Irrigation", Vector3(8.4, -0.12, -5.6), Vector3(6.8, 0.08, 1.65), water, Vector3(0.0, -9.0, 0.0))

func _load_house_asset() -> void:
	if not ResourceLoader.exists(HOUSE_SCENE):
		push_error("Hero house GLB is missing: %s" % HOUSE_SCENE)
		return
	var packed := load(HOUSE_SCENE) as PackedScene
	if packed == null:
		push_error("Hero house GLB failed to import")
		return
	var house := packed.instantiate()
	house.name = "HouseMain01"
	# Blender generator faces -Y; glTF import preserves the intended front toward -Z in Godot.
	house.position = Vector3(0.0, 0.0, 1.7)
	house.scale = Vector3.ONE * 1.08
	add_child(house)

func _build_garden_context() -> void:
	var bamboo := _mat("bamboo", Color("9a8a51"))
	var leaf := _mat("leaf", Color("4f8f48"))
	var leaf_light := _mat("leaf_light", Color("6da454"))
	var flower := _mat("flower", Color("e9b25d"))
	var clay := _mat("clay", Color("aa5b3e"))
	var wood := _mat("wood", Color("775036"))

	# Uneven bamboo fence framing the garden.
	for z_value: float in [-3.2, -1.7, -0.2, 1.3, 2.8]:
		_cylinder("BambooPost", Vector3(7.4, 0.55, z_value), 0.055, 1.15, bamboo, 8)
	for z_value: float in [-2.45, -0.95, 0.55, 2.05]:
		var rail := _cylinder("BambooRail", Vector3(7.4, 0.68, z_value), 0.045, 1.52, bamboo, 8)
		rail.rotation_degrees.x = 90.0

	# Crops are deliberately denser than the old prototype grid.
	for row: int in range(2):
		for col: int in range(5):
			var px := 4.45 + float(col) * 0.62
			var pz := -2.08 + float(row) * 0.72
			_cylinder("CropStem", Vector3(px, 0.28, pz), 0.025, 0.48, leaf, 7)
			_sphere("CropLeaf", Vector3(px - 0.12, 0.46, pz), 0.18, leaf_light, Vector3(1.2, 0.55, 0.78))
			_sphere("CropLeaf", Vector3(px + 0.13, 0.42, pz + 0.05), 0.16, leaf, Vector3(1.1, 0.52, 0.82))
	for col: int in range(4):
		var px := 4.35 + float(col) * 0.70
		_cylinder("FlowerStem", Vector3(px, 0.26, 0.45), 0.018, 0.45, leaf, 6)
		_sphere("FlowerHead", Vector3(px, 0.54, 0.45), 0.09, flower, Vector3(1.1, 0.6, 1.1))

	# Props near the porch, sized to be readable from 3/4 view.
	_cylinder("ClayPotA", Vector3(-3.7, 0.24, -2.9), 0.28, 0.46, clay, 12)
	_sphere("PotPlantA", Vector3(-3.7, 0.62, -2.9), 0.38, leaf, Vector3(1.05, 0.78, 0.95))
	_cylinder("Basket", Vector3(3.55, 0.25, -3.15), 0.36, 0.48, wood, 12)

func _build_foliage_context() -> void:
	var trunk := _mat("trunk", Color("765039"))
	var canopy := _mat("canopy", Color("4f8548"))
	var canopy_light := _mat("canopy_light", Color("60974f"))

	# Sparse foreground framing only. These will be replaced by imported nature assets next.
	for tree_data: Dictionary in [
		{"p": Vector3(-8.3, 0.0, 2.8), "s": 1.05},
		{"p": Vector3(9.4, 0.0, 2.2), "s": 0.90},
		{"p": Vector3(-9.5, 0.0, -5.2), "s": 0.78}
	]:
		var p := tree_data["p"] as Vector3
		var s := float(tree_data["s"])
		_cylinder("TreeTrunk", p + Vector3(0.0, 1.35 * s, 0.0), 0.22 * s, 2.70 * s, trunk, 9)
		_sphere("TreeCanopy", p + Vector3(0.0, 3.10 * s, 0.0), 1.15 * s, canopy, Vector3(1.18, 0.84, 1.02))
		_sphere("TreeCanopy", p + Vector3(-0.62 * s, 2.95 * s, 0.06), 0.72 * s, canopy_light, Vector3(1.0, 0.82, 0.92))

func _build_camera() -> void:
	var camera := Camera3D.new()
	camera.name = "HeroCamera"
	camera.position = Vector3(11.8, 7.4, -13.8)
	camera.fov = 34.0
	camera.current = true
	add_child(camera)
	camera.look_at(Vector3(0.3, 2.05, 0.0), Vector3.UP)

func _capture_when_ready() -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().process_frame
	var image := get_viewport().get_texture().get_image()
	var result := image.save_png("hero_house_preview.png")
	if result != OK:
		push_error("Failed to save hero house preview: %s" % result)
	get_tree().quit()
