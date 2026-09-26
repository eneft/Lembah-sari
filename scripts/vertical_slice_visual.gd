extends Node3D

# Handcrafted art-direction layer for Vertical Slice 01.
# Decorative only: no gameplay state, input, farming logic, or gameplay collision.
# The layer enriches the existing procedural world around the hero house, garden,
# footpath, bridge, stream and rice fields so the scene reads like a cozy stylized
# Indonesian village instead of a blockout.

const WOOD_DARK: Color = Color("5f412f")
const WOOD_MID: Color = Color("825a3d")
const WOOD_LIGHT: Color = Color("aa7a50")
const BAMBOO: Color = Color("9b8b52")
const BAMBOO_GREEN: Color = Color("718d4d")
const TERRACOTTA: Color = Color("a5543f")
const TERRACOTTA_DARK: Color = Color("7e4035")
const SOIL: Color = Color("785b3f")
const SOIL_LIGHT: Color = Color("8f6d48")
const LEAF_DARK: Color = Color("3f7544")
const LEAF_MID: Color = Color("57934c")
const LEAF_LIGHT: Color = Color("72aa55")
const STONE: Color = Color("85867d")
const CREAM: Color = Color("e6d5ad")

func _ready() -> void:
	_build_house_character()
	_build_kitchen_garden()
	_build_yard_storytelling()
	_build_home_foliage()
	_build_path_rhythm()
	_build_stream_life()
	_build_bridge_focus()
	_build_rice_edge_detail()

func _material(color_value: Color, roughness_value: float = 0.93) -> StandardMaterial3D:
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = color_value
	material.roughness = roughness_value
	material.metallic = 0.0
	return material

func _emissive_material(color_value: Color, energy_value: float = 1.25) -> StandardMaterial3D:
	var material: StandardMaterial3D = _material(color_value, 0.82)
	material.emission_enabled = true
	material.emission = color_value
	material.emission_energy_multiplier = energy_value
	return material

func _add_mesh(node_name: String, mesh_value: Mesh, material_value: Material, position_value: Vector3, rotation_value: Vector3 = Vector3.ZERO, scale_value: Vector3 = Vector3.ONE) -> MeshInstance3D:
	var instance: MeshInstance3D = MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh_value
	instance.material_override = material_value
	instance.position = position_value
	instance.rotation_degrees = rotation_value
	instance.scale = scale_value
	add_child(instance)
	return instance

func _box(node_name: String, position_value: Vector3, size_value: Vector3, color_value: Color, rotation_value: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var mesh_value: BoxMesh = BoxMesh.new()
	mesh_value.size = size_value
	return _add_mesh(node_name, mesh_value, _material(color_value), position_value, rotation_value)

func _cylinder(node_name: String, position_value: Vector3, radius_value: float, height_value: float, color_value: Color, sides_value: int = 8, rotation_value: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var mesh_value: CylinderMesh = CylinderMesh.new()
	mesh_value.top_radius = radius_value * 0.94
	mesh_value.bottom_radius = radius_value
	mesh_value.height = height_value
	mesh_value.radial_segments = sides_value
	mesh_value.rings = 1
	return _add_mesh(node_name, mesh_value, _material(color_value), position_value, rotation_value)

func _sphere(node_name: String, position_value: Vector3, radius_value: float, color_value: Color, scale_value: Vector3 = Vector3.ONE) -> MeshInstance3D:
	var mesh_value: SphereMesh = SphereMesh.new()
	mesh_value.radius = radius_value
	mesh_value.height = radius_value * 2.0
	mesh_value.radial_segments = 10
	mesh_value.rings = 5
	return _add_mesh(node_name, mesh_value, _material(color_value), position_value, Vector3.ZERO, scale_value)

func _leaf(node_name: String, position_value: Vector3, length_value: float, width_value: float, color_value: Color, yaw_value: float, pitch_value: float = -16.0) -> MeshInstance3D:
	var surface: SurfaceTool = SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var vertices: PackedVector3Array = PackedVector3Array([
		Vector3(-width_value * 0.50, 0.0, 0.0),
		Vector3(width_value * 0.50, 0.0, 0.0),
		Vector3(width_value * 0.14, 0.06, length_value * 0.58),
		Vector3(-width_value * 0.50, 0.0, 0.0),
		Vector3(width_value * 0.14, 0.06, length_value * 0.58),
		Vector3(0.0, 0.02, length_value),
		Vector3(-width_value * 0.50, 0.0, 0.0),
		Vector3(0.0, 0.02, length_value),
		Vector3(-width_value * 0.10, -0.03, length_value * 0.58)
	])
	for vertex_value: Vector3 in vertices:
		surface.add_vertex(vertex_value)
	surface.generate_normals()
	var array_mesh: ArrayMesh = surface.commit()
	return _add_mesh(node_name, array_mesh, _material(color_value), position_value, Vector3(pitch_value, yaw_value, 0.0))

func _plant_cluster(position_value: Vector3, scale_value: float, color_value: Color = LEAF_MID) -> void:
	for blade_index: int in range(6):
		var angle_value: float = float(blade_index) * 60.0
		_leaf("GardenLeaf", position_value + Vector3(0.0, 0.05, 0.0), 0.52 * scale_value, 0.16 * scale_value, color_value if blade_index % 2 == 0 else color_value.lightened(0.07), angle_value, -55.0)

func _flower(position_value: Vector3, color_value: Color, scale_value: float = 1.0) -> void:
	_cylinder("FlowerStem", position_value + Vector3(0.0, 0.20 * scale_value, 0.0), 0.018 * scale_value, 0.40 * scale_value, LEAF_DARK, 5)
	_sphere("FlowerHead", position_value + Vector3(0.0, 0.43 * scale_value, 0.0), 0.085 * scale_value, color_value, Vector3(1.2, 0.55, 1.2))

func _clay_pot(position_value: Vector3, scale_value: float = 1.0, plant: bool = true) -> void:
	var pot: MeshInstance3D = _cylinder("ClayPot", position_value + Vector3(0.0, 0.24 * scale_value, 0.0), 0.27 * scale_value, 0.44 * scale_value, Color("b76646"), 10)
	pot.scale.x = 1.05
	if plant:
		_plant_cluster(position_value + Vector3(0.0, 0.43 * scale_value, 0.0), 0.70 * scale_value, LEAF_MID)

func _basket(position_value: Vector3, scale_value: float = 1.0) -> void:
	_cylinder("WovenBasket", position_value + Vector3(0.0, 0.24 * scale_value, 0.0), 0.34 * scale_value, 0.46 * scale_value, Color("b18452"), 12)
	var rim: MeshInstance3D = _cylinder("BasketRim", position_value + Vector3(0.0, 0.48 * scale_value, 0.0), 0.38 * scale_value, 0.07 * scale_value, Color("8f633f"), 12)
	rim.scale = Vector3(1.0, 1.0, 1.0)

func _bamboo_post(position_value: Vector3, height_value: float, radius_value: float = 0.055) -> void:
	_cylinder("BambooPost", position_value + Vector3(0.0, height_value * 0.5, 0.0), radius_value, height_value, BAMBOO, 7)

func _build_house_character() -> void:
	# Existing house shell is kept as gameplay-safe foundation. This layer gives it
	# timber rhythm, terracotta ridge detail, shutters and a richer veranda silhouette.
	var beam_x_values: Array[float] = [12.78, 14.25, 15.70, 17.15, 18.62]
	for x_value: float in beam_x_values:
		_box("HouseTimberStud", Vector3(x_value, 1.72, 10.69), Vector3(0.10, 2.70, 0.08), WOOD_DARK)
	_box("HouseFrontBeam", Vector3(15.70, 2.92, 10.68), Vector3(5.90, 0.13, 0.10), WOOD_DARK)
	_box("HouseSillBeam", Vector3(15.70, 0.60, 10.68), Vector3(5.90, 0.11, 0.10), WOOD_MID)

	# A few bamboo wall strips break the large flat facade without making it noisy.
	for strip_index: int in range(8):
		var strip_x: float = 13.05 + float(strip_index) * 0.72
		_cylinder("BambooWallStrip", Vector3(strip_x, 1.75, 10.61), 0.025, 2.20, Color("c6ab73"), 6)

	# Open shutters angle outward from the two front windows.
	for window_x: float in [13.75, 17.65]:
		_box("WindowShutterLeft", Vector3(window_x - 0.69, 1.75, 10.58), Vector3(0.55, 1.08, 0.07), WOOD_MID, Vector3(0.0, 22.0, 0.0))
		_box("WindowShutterRight", Vector3(window_x + 0.69, 1.75, 10.58), Vector3(0.55, 1.08, 0.07), WOOD_MID, Vector3(0.0, -22.0, 0.0))

	# Terracotta ridge and eave accents visually soften the procedural gable roof.
	_cylinder("RoofRidge", Vector3(15.70, 4.82, 13.20), 0.13, 5.85, TERRACOTTA_DARK, 10, Vector3(0.0, 0.0, 90.0))
	for tile_index: int in range(11):
		var tile_x: float = 12.95 + float(tile_index) * 0.55
		_cylinder("EaveTile", Vector3(tile_x, 3.11, 10.25), 0.055, 0.48, TERRACOTTA, 7, Vector3(90.0, 0.0, 0.0))

	# Porch rails, bench and warm hanging lamp create a lived-in focal point.
	for x_value: float in [13.80, 17.60]:
		_cylinder("PorchRailPost", Vector3(x_value, 0.92, 9.20), 0.055, 1.05, WOOD_DARK, 7)
	for rail_y: float in [0.76, 1.12]:
		_cylinder("PorchRail", Vector3(15.70, rail_y, 9.20), 0.045, 3.75, WOOD_MID, 7, Vector3(0.0, 0.0, 90.0))
	_box("PorchBenchSeat", Vector3(17.00, 0.66, 9.58), Vector3(1.35, 0.14, 0.48), WOOD_LIGHT)
	_box("PorchBenchBack", Vector3(17.00, 1.02, 9.78), Vector3(1.35, 0.56, 0.10), WOOD_MID, Vector3(-8.0, 0.0, 0.0))
	_cylinder("PorchLampCord", Vector3(15.70, 2.30, 9.35), 0.015, 0.55, WOOD_DARK, 5)
	var lamp_mesh: SphereMesh = SphereMesh.new()
	lamp_mesh.radius = 0.13
	lamp_mesh.height = 0.26
	lamp_mesh.radial_segments = 8
	lamp_mesh.rings = 4
	_add_mesh("PorchWarmLamp", lamp_mesh, _emissive_material(Color("ffd58b"), 1.10), Vector3(15.70, 1.98, 9.35), Vector3.ZERO, Vector3(1.0, 1.22, 1.0))

func _build_kitchen_garden() -> void:
	var bed_centers: Array[Vector3] = [Vector3(10.65, 0.11, 11.55), Vector3(10.30, 0.11, 14.10)]
	var bed_rotations: Array[float] = [-8.0, 7.0]
	for bed_index: int in range(bed_centers.size()):
		var center_value: Vector3 = bed_centers[bed_index]
		var rotation_value: float = bed_rotations[bed_index]
		_box("GardenSoil", center_value, Vector3(3.30, 0.18, 1.55), SOIL, Vector3(0.0, rotation_value, 0.0))
		# Timber edges keep the beds readable from the 3/4 camera.
		_box("GardenEdge", center_value + Vector3(0.0, 0.12, -0.80), Vector3(3.45, 0.18, 0.12), WOOD_MID, Vector3(0.0, rotation_value, 0.0))
		_box("GardenEdge", center_value + Vector3(0.0, 0.12, 0.80), Vector3(3.45, 0.18, 0.12), WOOD_MID, Vector3(0.0, rotation_value, 0.0))
		for row_index: int in range(2):
			for plant_index: int in range(5):
				var plant_x: float = center_value.x - 1.20 + float(plant_index) * 0.60
				var plant_z: float = center_value.z - 0.34 + float(row_index) * 0.68
				_plant_cluster(Vector3(plant_x, 0.24, plant_z), 0.62 + float((plant_index + row_index) % 2) * 0.08, LEAF_LIGHT if bed_index == 0 else LEAF_MID)
				if bed_index == 1 and plant_index % 2 == 0:
					_sphere("GardenFruit", Vector3(plant_x + 0.10, 0.55, plant_z + 0.05), 0.07, Color("d85c42"), Vector3(1.0, 0.9, 1.0))

	# Organic bamboo fence: intentionally uneven, never a perfectly rigid rectangle.
	var fence_positions: Array[Vector3] = [
		Vector3(8.45,0.0,10.20), Vector3(8.35,0.0,11.55), Vector3(8.45,0.0,12.90),
		Vector3(8.34,0.0,14.25), Vector3(8.48,0.0,15.65), Vector3(9.80,0.0,16.25),
		Vector3(11.20,0.0,16.35), Vector3(12.55,0.0,16.18)
	]
	for fence_index: int in range(fence_positions.size()):
		var post_height: float = 0.92 + float(fence_index % 3) * 0.07
		_bamboo_post(fence_positions[fence_index], post_height, 0.052)
	for rail_z: float in [0.48, 0.76]:
		_cylinder("GardenFenceRail", Vector3(8.40, rail_z, 12.92), 0.035, 5.65, BAMBOO, 6, Vector3(90.0, 0.0, 0.0))

	_flower(Vector3(8.95,0.0,10.65), Color("f2a4b8"), 0.92)
	_flower(Vector3(9.10,0.0,15.60), Color("f0d16e"), 0.88)
	_flower(Vector3(12.35,0.0,15.95), Color("dda7e8"), 0.95)

func _build_yard_storytelling() -> void:
	# Pots and woven baskets around the veranda reinforce the human scale.
	_clay_pot(Vector3(12.65, 0.0, 9.35), 0.92, true)
	_clay_pot(Vector3(18.62, 0.0, 9.48), 0.80, true)
	_clay_pot(Vector3(18.98, 0.0, 10.18), 0.64, false)
	_basket(Vector3(12.05, 0.0, 9.65), 0.90)
	_basket(Vector3(11.48, 0.0, 10.10), 0.68)
	_box("WoodCrate", Vector3(18.55, 0.30, 11.02), Vector3(0.62, 0.60, 0.72), WOOD_LIGHT, Vector3(0.0, -8.0, 0.0))

	# Irregular stepping stones connect the porch to the existing home path.
	var stone_positions: Array[Vector3] = [
		Vector3(15.55,0.15,8.55), Vector3(14.65,0.14,8.10), Vector3(13.62,0.14,7.72),
		Vector3(12.52,0.14,7.35), Vector3(11.35,0.14,7.00), Vector3(10.15,0.14,6.55)
	]
	for stone_index: int in range(stone_positions.size()):
		var stone: MeshInstance3D = _sphere("YardStone", stone_positions[stone_index], 0.36 + float(stone_index % 2) * 0.05, STONE.lightened(0.05 * float(stone_index % 2)), Vector3(1.35, 0.24, 0.90))
		stone.rotation_degrees.y = -18.0 + float(stone_index) * 11.0

	# Clothesline on the quieter right side of the house.
	var line_z: float = 14.50
	_bamboo_post(Vector3(19.65,0.0,line_z), 2.35, 0.065)
	_bamboo_post(Vector3(22.60,0.0,line_z + 0.18), 2.25, 0.065)
	_cylinder("ClothesLine", Vector3(21.12,2.12,line_z + 0.09), 0.012, 2.98, Color("6b5944"), 5, Vector3(0.0,0.0,90.0))
	var cloth_colors: Array[Color] = [Color("efe8d4"), Color("8bb6be"), Color("d79683"), Color("e6c46c")]
	for cloth_index: int in range(cloth_colors.size()):
		var cloth_x: float = 20.08 + float(cloth_index) * 0.68
		_box("HangingCloth", Vector3(cloth_x,1.72,line_z + 0.09), Vector3(0.48,0.72,0.035), cloth_colors[cloth_index], Vector3(0.0,0.0,-3.0 + float(cloth_index) * 2.0))

func _build_home_foliage() -> void:
	# Broad-leaf framing around the hero house mimics the lush reference without
	# blocking the playable path or the front facade.
	var clusters: Array[Vector3] = [
		Vector3(19.65,0.0,8.75), Vector3(20.55,0.0,9.55), Vector3(21.05,0.0,11.25),
		Vector3(12.15,0.0,10.65), Vector3(12.25,0.0,15.70), Vector3(13.30,0.0,16.40)
	]
	for cluster_index: int in range(clusters.size()):
		var center_value: Vector3 = clusters[cluster_index]
		for leaf_index: int in range(7):
			var angle_value: float = float(leaf_index) * 51.4 + float(cluster_index) * 13.0
			_leaf("BroadLeaf", center_value + Vector3(0.0,0.18,0.0), 1.05 + float(leaf_index % 3) * 0.14, 0.38, LEAF_MID if leaf_index % 2 == 0 else LEAF_LIGHT, angle_value, -38.0)
		_cylinder("PlantStem", center_value + Vector3(0.0,0.52,0.0), 0.055, 1.02, BAMBOO_GREEN, 7)

	# Flowering hedge near the garden gives the hero zone a soft color accent.
	var hedge_positions: Array[Vector3] = [Vector3(9.10,0.0,9.45),Vector3(9.72,0.0,9.35),Vector3(10.35,0.0,9.45),Vector3(11.00,0.0,9.35)]
	for hedge_index: int in range(hedge_positions.size()):
		_sphere("FlowerBush", hedge_positions[hedge_index] + Vector3(0.0,0.36,0.0), 0.46, LEAF_DARK if hedge_index % 2 == 0 else LEAF_MID, Vector3(1.18,0.70,1.0))
		_flower(hedge_positions[hedge_index] + Vector3(0.10,0.18,0.02), Color("ee9eb5") if hedge_index % 2 == 0 else Color("f1cf73"), 0.72)

func _build_path_rhythm() -> void:
	# Detail clusters follow the already-curved gameplay path. They deliberately
	# leave breathing room so the path reads clearly at the fixed 3/4 angle.
	var path_clusters: Array[Vector3] = [
		Vector3(8.50,0.0,5.65), Vector3(6.55,0.0,4.95), Vector3(4.50,0.0,4.10),
		Vector3(3.15,0.0,2.10), Vector3(2.72,0.0,-0.65), Vector3(2.42,0.0,-3.15)
	]
	for cluster_index: int in range(path_clusters.size()):
		var base_value: Vector3 = path_clusters[cluster_index]
		_plant_cluster(base_value + Vector3(0.72,0.0,0.18), 0.46, LEAF_DARK)
		if cluster_index % 2 == 0:
			_flower(base_value + Vector3(-0.55,0.0,-0.12), Color("f0c96a") if cluster_index % 4 == 0 else Color("e9a3c0"), 0.74)
		var path_rock: MeshInstance3D = _sphere("PathRock", base_value + Vector3(-0.82,0.14,0.38), 0.27, STONE, Vector3(1.22,0.45,0.82))
		path_rock.rotation_degrees.y = float(cluster_index) * 27.0

func _build_stream_life() -> void:
	# Reeds, lily pads and stones add depth to the otherwise flat water ribbon.
	var reed_positions: Array[Vector3] = [
		Vector3(-1.2,0.0,-5.85),Vector3(0.0,0.0,-5.55),Vector3(4.3,0.0,-5.72),Vector3(5.2,0.0,-6.05),
		Vector3(-0.7,0.0,-10.55),Vector3(4.8,0.0,-10.40)
	]
	for reed_index: int in range(reed_positions.size()):
		var reed_base: Vector3 = reed_positions[reed_index]
		for stem_index: int in range(4):
			var offset_x: float = -0.12 + float(stem_index) * 0.08
			var height_value: float = 0.72 + float((stem_index + reed_index) % 3) * 0.12
			_cylinder("RiverReed", reed_base + Vector3(offset_x, height_value * 0.5, 0.0), 0.018, height_value, Color("688d4c"), 5, Vector3(0.0,0.0,-5.0 + float(stem_index) * 3.0))

	var lily_positions: Array[Vector3] = [Vector3(-3.2,-0.01,-8.15),Vector3(-1.8,-0.01,-8.62),Vector3(5.2,-0.01,-8.55),Vector3(6.1,-0.01,-7.85)]
	for lily_index: int in range(lily_positions.size()):
		var pad: MeshInstance3D = _cylinder("LilyPad", lily_positions[lily_index], 0.28 + float(lily_index % 2) * 0.06, 0.025, Color("5b9654"), 12)
		pad.scale.z = 0.82
		if lily_index % 2 == 0:
			_sphere("LilyFlower", lily_positions[lily_index] + Vector3(0.07,0.07,0.02), 0.07, Color("f4d7df"), Vector3(1.25,0.55,1.25))

	var river_stones: Array[Vector3] = [Vector3(-4.2,0.08,-6.15),Vector3(-2.5,0.08,-10.10),Vector3(6.3,0.08,-6.35),Vector3(7.0,0.08,-9.75)]
	for stone_index: int in range(river_stones.size()):
		var river_stone: MeshInstance3D = _sphere("StreamStone", river_stones[stone_index], 0.42 + float(stone_index % 2) * 0.10, STONE.darkened(0.04), Vector3(1.30,0.50,0.92))
		river_stone.rotation_degrees.y = 14.0 + float(stone_index) * 31.0

func _build_bridge_focus() -> void:
	# Small lanterns mark the bridge as the secondary focal point from the house.
	var lantern_positions: Array[Vector3] = [Vector3(0.20,0.0,-5.50),Vector3(3.80,0.0,-5.50),Vector3(0.20,0.0,-10.85),Vector3(3.80,0.0,-10.85)]
	for lantern_index: int in range(lantern_positions.size()):
		var base_value: Vector3 = lantern_positions[lantern_index]
		_cylinder("BridgeLanternPost", base_value + Vector3(0.0,0.72,0.0), 0.055, 1.44, WOOD_DARK, 7)
		_box("BridgeLanternCap", base_value + Vector3(0.0,1.48,0.0), Vector3(0.34,0.10,0.34), TERRACOTTA_DARK)
		var light_mesh: SphereMesh = SphereMesh.new()
		light_mesh.radius = 0.11
		light_mesh.height = 0.22
		light_mesh.radial_segments = 8
		light_mesh.rings = 4
		_add_mesh("BridgeLanternGlow", light_mesh, _emissive_material(Color("ffd48a"), 0.95), base_value + Vector3(0.0,1.30,0.0), Vector3.ZERO, Vector3(0.92,1.10,0.92))

	# Flower/grass islands frame both bridge entrances without blocking travel.
	for entry_value: Vector3 in [Vector3(-0.65,0.0,-5.25),Vector3(4.65,0.0,-5.35),Vector3(-0.55,0.0,-11.15),Vector3(4.55,0.0,-11.05)]:
		_plant_cluster(entry_value, 0.56, LEAF_DARK)
		_flower(entry_value + Vector3(0.32,0.0,0.12), Color("eda0b8"), 0.74)

func _build_rice_edge_detail() -> void:
	# Keep the paddies visually open; only enrich their near edge and irrigation side.
	var edge_positions: Array[Vector3] = [
		Vector3(-11.8,0.0,-11.55),Vector3(-8.0,0.0,-11.55),Vector3(-4.3,0.0,-11.55),
		Vector3(-0.6,0.0,-11.55),Vector3(3.3,0.0,-11.55),Vector3(6.7,0.0,-11.65)
	]
	for edge_index: int in range(edge_positions.size()):
		_plant_cluster(edge_positions[edge_index], 0.42 + float(edge_index % 2) * 0.07, Color("628f4c"))
		if edge_index in [1, 4]:
			_flower(edge_positions[edge_index] + Vector3(0.35,0.0,0.0), Color("f0d26f"), 0.68)

	# Two field baskets hint at harvesting activity without adding gameplay systems.
	_basket(Vector3(5.15,0.0,-12.25), 0.72)
	_basket(Vector3(5.78,0.0,-12.48), 0.56)
