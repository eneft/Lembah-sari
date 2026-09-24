extends Node3D

# Lembah Sari concept-art visual layer.
# Decoration only: no gameplay collision and no state changes.

func _ready() -> void:
	_build_background_homes()
	_build_grass_density()
	_build_bamboo_groves()
	_build_path_details()
	_build_river_details()
	_build_farm_details()
	_build_clouds()

func _material(color_value: Color, roughness_value: float = 0.95) -> StandardMaterial3D:
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = color_value
	material.roughness = roughness_value
	return material

func _box_visual(node_name: String, position_value: Vector3, size_value: Vector3, color_value: Color, rotation_value: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var instance: MeshInstance3D = MeshInstance3D.new()
	instance.name = node_name
	var mesh: BoxMesh = BoxMesh.new()
	mesh.size = size_value
	instance.mesh = mesh
	instance.material_override = _material(color_value)
	instance.position = position_value
	instance.rotation_degrees = rotation_value
	add_child(instance)
	return instance

func _cylinder_visual(node_name: String, position_value: Vector3, radius_value: float, height_value: float, color_value: Color, sides: int = 8, rotation_value: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var instance: MeshInstance3D = MeshInstance3D.new()
	instance.name = node_name
	var mesh: CylinderMesh = CylinderMesh.new()
	mesh.top_radius = radius_value * 0.92
	mesh.bottom_radius = radius_value
	mesh.height = height_value
	mesh.radial_segments = sides
	mesh.rings = 1
	instance.mesh = mesh
	instance.material_override = _material(color_value)
	instance.position = position_value
	instance.rotation_degrees = rotation_value
	add_child(instance)
	return instance

func _sphere_visual(node_name: String, position_value: Vector3, radius_value: float, color_value: Color, scale_value: Vector3 = Vector3.ONE) -> MeshInstance3D:
	var instance: MeshInstance3D = MeshInstance3D.new()
	instance.name = node_name
	var mesh: SphereMesh = SphereMesh.new()
	mesh.radius = radius_value
	mesh.height = radius_value * 2.0
	mesh.radial_segments = 10
	mesh.rings = 5
	instance.mesh = mesh
	instance.material_override = _material(color_value)
	instance.position = position_value
	instance.scale = scale_value
	add_child(instance)
	return instance

func _cone_visual(node_name: String, position_value: Vector3, radius_value: float, height_value: float, color_value: Color, sides: int = 7) -> MeshInstance3D:
	var instance: MeshInstance3D = MeshInstance3D.new()
	instance.name = node_name
	var mesh: CylinderMesh = CylinderMesh.new()
	mesh.top_radius = 0.03
	mesh.bottom_radius = radius_value
	mesh.height = height_value
	mesh.radial_segments = sides
	mesh.rings = 1
	instance.mesh = mesh
	instance.material_override = _material(color_value)
	instance.position = position_value
	add_child(instance)
	return instance

func _grass_clump(position_value: Vector3, scale_value: float = 1.0, color_value: Color = Color("6f9650")) -> void:
	for blade_index: int in range(5):
		var angle: float = float(blade_index) * 72.0
		var radians_value: float = deg_to_rad(angle)
		var offset: Vector3 = Vector3(cos(radians_value) * 0.10, 0.0, sin(radians_value) * 0.10)
		var blade: MeshInstance3D = _cone_visual("GrassBlade", position_value + offset + Vector3(0.0, 0.24 * scale_value, 0.0), 0.055 * scale_value, 0.48 * scale_value, color_value, 5)
		blade.rotation_degrees.z = sin(radians_value) * 12.0
		blade.rotation_degrees.x = cos(radians_value) * 10.0

func _flower_clump(position_value: Vector3, petal_color: Color) -> void:
	_grass_clump(position_value, 0.82, Color("648f4a"))
	for offset: Vector3 in [Vector3(-0.18,0.38,-0.10), Vector3(0.12,0.42,0.06), Vector3(0.02,0.36,0.20)]:
		_sphere_visual("WildFlower", position_value + offset, 0.07, petal_color, Vector3(1.15, 0.62, 1.15))

func _bamboo_cluster(position_value: Vector3, scale_value: float = 1.0) -> void:
	for stem_index: int in range(5):
		var x_offset: float = -0.42 + float(stem_index) * 0.20
		var z_offset: float = sin(float(stem_index) * 1.8) * 0.24
		var height_value: float = (3.0 + float(stem_index % 3) * 0.38) * scale_value
		_cylinder_visual("BambooStem", position_value + Vector3(x_offset, height_value * 0.5, z_offset), 0.075 * scale_value, height_value, Color("6f9850"), 7)
		for leaf_index: int in range(3):
			var leaf_y: float = height_value * (0.48 + float(leaf_index) * 0.16)
			var leaf: MeshInstance3D = _box_visual("BambooLeaf", position_value + Vector3(x_offset + 0.22, leaf_y, z_offset), Vector3(0.42, 0.045, 0.14) * scale_value, Color("4f8748"), Vector3(0.0, float(leaf_index) * 48.0 + float(stem_index) * 20.0, -18.0))
			leaf.scale.z = 0.7

func _village_house(position_value: Vector3, body_color: Color, roof_color: Color, scale_value: float = 1.0, rotation_y: float = 0.0) -> void:
	var root: Node3D = Node3D.new()
	root.position = position_value
	root.rotation_degrees.y = rotation_y
	root.scale = Vector3.ONE * scale_value
	add_child(root)

	var body: MeshInstance3D = MeshInstance3D.new()
	var body_mesh: BoxMesh = BoxMesh.new()
	body_mesh.size = Vector3(4.4, 2.35, 3.2)
	body.mesh = body_mesh
	body.material_override = _material(body_color)
	body.position = Vector3(0.0, 1.25, 0.0)
	root.add_child(body)

	var roof_left: MeshInstance3D = MeshInstance3D.new()
	var roof_mesh_left: BoxMesh = BoxMesh.new()
	roof_mesh_left.size = Vector3(5.2, 0.20, 2.6)
	roof_left.mesh = roof_mesh_left
	roof_left.material_override = _material(roof_color)
	roof_left.position = Vector3(0.0, 2.65, -0.72)
	roof_left.rotation_degrees.x = 24.0
	root.add_child(roof_left)

	var roof_right: MeshInstance3D = MeshInstance3D.new()
	var roof_mesh_right: BoxMesh = BoxMesh.new()
	roof_mesh_right.size = Vector3(5.2, 0.20, 2.6)
	roof_right.mesh = roof_mesh_right
	roof_right.material_override = _material(roof_color.darkened(0.07))
	roof_right.position = Vector3(0.0, 2.65, 0.72)
	roof_right.rotation_degrees.x = -24.0
	root.add_child(roof_right)

	var door: MeshInstance3D = MeshInstance3D.new()
	var door_mesh: BoxMesh = BoxMesh.new()
	door_mesh.size = Vector3(0.75, 1.55, 0.08)
	door.mesh = door_mesh
	door.material_override = _material(Color("6e4932"))
	door.position = Vector3(0.35, 0.85, -1.64)
	root.add_child(door)

	for window_x: float in [-1.25, 1.35]:
		var window: MeshInstance3D = MeshInstance3D.new()
		var window_mesh: BoxMesh = BoxMesh.new()
		window_mesh.size = Vector3(0.72, 0.72, 0.06)
		window.mesh = window_mesh
		window.material_override = _material(Color("83b7c0"))
		window.position = Vector3(window_x, 1.35, -1.65)
		root.add_child(window)

func _build_background_homes() -> void:
	_village_house(Vector3(-18.5, 0.0, 12.7), Color("d6b982"), Color("825043"), 0.92, -8.0)
	_village_house(Vector3(-10.5, 0.0, 15.6), Color("e0c999"), Color("8b5344"), 0.82, 8.0)
	_village_house(Vector3(4.0, 0.0, 17.7), Color("d7bd88"), Color("74453b"), 0.78, -5.0)
	_village_house(Vector3(21.0, 0.0, -2.3), Color("dec391"), Color("7d4a3d"), 0.88, 14.0)

func _build_grass_density() -> void:
	var grass_positions: Array[Vector3] = [
		Vector3(-20.0,0.0,8.0),Vector3(-18.5,0.0,6.3),Vector3(-16.0,0.0,5.5),Vector3(-13.5,0.0,6.2),
		Vector3(-9.0,0.0,5.0),Vector3(-6.5,0.0,5.5),Vector3(-3.5,0.0,5.1),Vector3(0.0,0.0,5.4),
		Vector3(4.3,0.0,5.1),Vector3(7.0,0.0,5.0),Vector3(10.0,0.0,5.4),Vector3(13.0,0.0,5.0),
		Vector3(17.0,0.0,5.5),Vector3(20.0,0.0,5.2),Vector3(-20.5,0.0,-4.5),Vector3(-17.0,0.0,-4.3),
		Vector3(-12.5,0.0,-4.6),Vector3(-7.0,0.0,-4.4),Vector3(7.5,0.0,-4.5),Vector3(11.0,0.0,-4.3),
		Vector3(15.0,0.0,-4.6),Vector3(19.0,0.0,-4.4),Vector3(20.5,0.0,10.5),Vector3(19.5,0.0,13.0)
	]
	for grass_index: int in range(grass_positions.size()):
		var tint: Color = Color("719851") if grass_index % 3 != 0 else Color("789f57")
		_grass_clump(grass_positions[grass_index], 0.85 + float(grass_index % 4) * 0.08, tint)
	_flower_clump(Vector3(-15.5,0.0,5.1), Color("e8a0b9"))
	_flower_clump(Vector3(-2.5,0.0,5.3), Color("f0cf68"))
	_flower_clump(Vector3(12.8,0.0,5.1), Color("d9b0ef"))
	_flower_clump(Vector3(19.5,0.0,8.0), Color("ed9a79"))

func _build_bamboo_groves() -> void:
	_bamboo_cluster(Vector3(-23.0,0.0,1.0), 1.05)
	_bamboo_cluster(Vector3(-21.8,0.0,2.2), 0.92)
	_bamboo_cluster(Vector3(23.0,0.0,10.0), 1.0)
	_bamboo_cluster(Vector3(21.7,0.0,11.3), 0.88)

func _build_path_details() -> void:
	var stepping_stones: Array[Vector3] = [
		Vector3(-15.0,0.13,1.4),Vector3(-11.2,0.13,1.6),Vector3(-7.5,0.13,1.35),Vector3(-3.8,0.13,1.65),
		Vector3(0.0,0.13,1.4),Vector3(4.0,0.13,1.6),Vector3(8.0,0.13,1.35),Vector3(12.0,0.13,1.65),Vector3(16.0,0.13,1.4)
	]
	for stone_index: int in range(stepping_stones.size()):
		_sphere_visual("RoadStone", stepping_stones[stone_index], 0.34 + float(stone_index % 3) * 0.04, Color("9d9276"), Vector3(1.35,0.30,0.85))

func _build_river_details() -> void:
	for x_value: float in [-21.0,-17.0,-13.0,-9.0,-5.0,7.0,11.0,15.0,19.0,23.0]:
		_grass_clump(Vector3(x_value,0.0,-5.0), 0.75, Color("5f8e4d"))
		if int(absf(x_value)) % 2 == 1:
			_sphere_visual("RiverStone", Vector3(x_value + 0.45,0.12,-5.55), 0.42, Color("888a82"), Vector3(1.15,0.55,0.88))

func _build_farm_details() -> void:
	# A few sacks, baskets and pots make the home/farm area feel inhabited.
	_cylinder_visual("WovenBasket", Vector3(12.1,0.30,9.4), 0.34, 0.48, Color("a77a4f"), 10)
	_cylinder_visual("ClayPot", Vector3(19.0,0.28,10.2), 0.27, 0.45, Color("b86846"), 10)
	_sphere_visual("ProduceSack", Vector3(11.5,0.30,9.8), 0.38, Color("c4ad7d"), Vector3(0.9,0.72,0.9))

func _build_clouds() -> void:
	# Static soft cloud silhouettes add depth to the empty sky without textures.
	for cloud_position: Vector3 in [Vector3(-13.0,9.5,-24.0), Vector3(7.0,10.5,-26.0), Vector3(20.0,9.0,-23.0)]:
		_sphere_visual("Cloud", cloud_position, 1.8, Color("eef1df"), Vector3(1.8,0.55,0.75))
		_sphere_visual("Cloud", cloud_position + Vector3(1.6,0.15,0.2), 1.4, Color("f3f4e7"), Vector3(1.5,0.52,0.70))
