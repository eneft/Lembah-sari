extends Node3D

func _ready() -> void:
	_build_world()

func _mat(color: Color, roughness: float = 0.9, metallic: float = 0.0) -> StandardMaterial3D:
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = roughness
	material.metallic = metallic
	return material

func _box(node_name: String, pos: Vector3, size: Vector3, color: Color, collision: bool = false, rotation: Vector3 = Vector3.ZERO) -> Node3D:
	var root: Node3D
	if collision:
		var body: StaticBody3D = StaticBody3D.new()
		root = body
		var shape: CollisionShape3D = CollisionShape3D.new()
		var box_shape: BoxShape3D = BoxShape3D.new()
		box_shape.size = size
		shape.shape = box_shape
		body.add_child(shape)
	else:
		root = Node3D.new()

	root.name = node_name
	root.position = pos
	root.rotation_degrees = rotation
	add_child(root)

	var mesh_instance: MeshInstance3D = MeshInstance3D.new()
	var mesh: BoxMesh = BoxMesh.new()
	mesh.size = size
	mesh_instance.mesh = mesh
	mesh_instance.material_override = _mat(color)
	root.add_child(mesh_instance)
	return root

func _cylinder(node_name: String, pos: Vector3, radius: float, height: float, color: Color, collision: bool = false, rotation: Vector3 = Vector3.ZERO) -> Node3D:
	var root: Node3D
	if collision:
		var body: StaticBody3D = StaticBody3D.new()
		root = body
		var shape: CollisionShape3D = CollisionShape3D.new()
		var cylinder_shape: CylinderShape3D = CylinderShape3D.new()
		cylinder_shape.radius = radius
		cylinder_shape.height = height
		shape.shape = cylinder_shape
		body.add_child(shape)
	else:
		root = Node3D.new()

	root.name = node_name
	root.position = pos
	root.rotation_degrees = rotation
	add_child(root)

	var mesh_instance: MeshInstance3D = MeshInstance3D.new()
	var mesh: CylinderMesh = CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh_instance.mesh = mesh
	mesh_instance.material_override = _mat(color)
	root.add_child(mesh_instance)
	return root

func _sphere(node_name: String, pos: Vector3, radius: float, color: Color, scale_value: Vector3 = Vector3.ONE) -> MeshInstance3D:
	var mesh_instance: MeshInstance3D = MeshInstance3D.new()
	mesh_instance.name = node_name
	var mesh: SphereMesh = SphereMesh.new()
	mesh.radius = radius
	mesh.height = radius * 2.0
	mesh_instance.mesh = mesh
	mesh_instance.material_override = _mat(color)
	mesh_instance.position = pos
	mesh_instance.scale = scale_value
	add_child(mesh_instance)
	return mesh_instance

func _label(text_value: String, pos: Vector3, font_size_value: int = 28) -> void:
	var label: Label3D = Label3D.new()
	label.text = text_value
	label.position = pos
	label.font_size = font_size_value
	label.outline_size = 6
	label.modulate = Color("fff4d6")
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	add_child(label)

func _tree_canopy(pos: Vector3, scale_mul: float, foliage: Color) -> void:
	_cylinder("TreeTrunk", pos + Vector3(0.0, 1.25 * scale_mul, 0.0), 0.25 * scale_mul, 2.5 * scale_mul, Color("76513a"), true)
	_sphere("TreeCrown", pos + Vector3(0.0, 2.85 * scale_mul, 0.0), 1.0 * scale_mul, foliage, Vector3(1.25, 0.85, 1.15))
	_sphere("TreeCrown", pos + Vector3(-0.65 * scale_mul, 2.7 * scale_mul, 0.1), 0.75 * scale_mul, foliage.lightened(0.07), Vector3(1.1, 0.8, 1.0))
	_sphere("TreeCrown", pos + Vector3(0.65 * scale_mul, 2.72 * scale_mul, -0.1), 0.72 * scale_mul, foliage.darkened(0.04), Vector3(1.0, 0.85, 1.0))

func _palm(pos: Vector3, scale_mul: float = 1.0) -> void:
	_cylinder("PalmTrunk", pos + Vector3(0.0, 2.1 * scale_mul, 0.0), 0.18 * scale_mul, 4.2 * scale_mul, Color("8b684b"), true, Vector3(0.0, 0.0, 4.0))
	for angle_value: float in [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]:
		_box("PalmLeaf", pos + Vector3(0.0, 4.3 * scale_mul, 0.0), Vector3(0.28, 0.08, 2.4) * scale_mul, Color("3c8a4c"), false, Vector3(-12.0, angle_value, 0.0))

func _banana_cluster(pos: Vector3, scale_mul: float = 1.0) -> void:
	for offset: Vector3 in [Vector3(-0.28, 0.0, 0.0), Vector3(0.22, 0.0, 0.18), Vector3(0.0, 0.0, -0.22)]:
		_cylinder("BananaStem", pos + offset + Vector3(0.0, 0.8 * scale_mul, 0.0), 0.10 * scale_mul, 1.6 * scale_mul, Color("71964a"), false)
	for rotation_y: float in [0.0, 60.0, 120.0, 180.0, 240.0, 300.0]:
		_box("BananaLeaf", pos + Vector3(0.0, 1.75 * scale_mul, 0.0), Vector3(0.55, 0.08, 1.9) * scale_mul, Color("66a852"), false, Vector3(-18.0, rotation_y, 0.0))

func _bush(pos: Vector3, scale_mul: float = 1.0, color_value: Color = Color("4e994d")) -> void:
	_sphere("Bush", pos + Vector3(0.0, 0.45 * scale_mul, 0.0), 0.55 * scale_mul, color_value, Vector3(1.3, 0.75, 1.0))

func _rock(pos: Vector3, scale_mul: float = 1.0) -> void:
	_sphere("Rock", pos + Vector3(0.0, 0.22 * scale_mul, 0.0), 0.45 * scale_mul, Color("7f827c"), Vector3(1.25, 0.55, 0.9))

func _flower_patch(pos: Vector3, flower_color: Color) -> void:
	for offset: Vector3 in [Vector3(-0.25, 0.0, -0.18), Vector3(0.18, 0.0, -0.08), Vector3(0.0, 0.0, 0.24), Vector3(0.32, 0.0, 0.2)]:
		_cylinder("FlowerStem", pos + offset + Vector3(0.0, 0.18, 0.0), 0.025, 0.36, Color("4f8d43"), false)
		_sphere("Flower", pos + offset + Vector3(0.0, 0.4, 0.0), 0.09, flower_color)

func _lamp_post(pos: Vector3) -> void:
	_cylinder("LampPost", pos + Vector3(0.0, 1.25, 0.0), 0.08, 2.5, Color("4d4b47"), false)
	_sphere("LampGlow", pos + Vector3(0.0, 2.55, 0.0), 0.18, Color("ffd892"))

func _fence_segment(pos: Vector3, length_value: float, rotation_y: float = 0.0) -> void:
	_box("FenceRail", pos + Vector3(0.0, 0.55, 0.0), Vector3(length_value, 0.12, 0.12), Color("8c6848"), false, Vector3(0.0, rotation_y, 0.0))
	_box("FenceRail", pos + Vector3(0.0, 0.95, 0.0), Vector3(length_value, 0.10, 0.10), Color("9c7652"), false, Vector3(0.0, rotation_y, 0.0))

func _build_house() -> void:
	# Raised tropical village house with warm plaster, timber trim and deep roof.
	_box("HouseBody", Vector3(15.7, 1.65, 13.2), Vector3(6.2, 3.0, 5.0), Color("e7d2a9"), true)
	_box("HouseFoundation", Vector3(15.7, 0.28, 13.2), Vector3(6.5, 0.45, 5.3), Color("8b745f"), true)
	_box("HouseRoofA", Vector3(15.7, 3.65, 12.35), Vector3(7.2, 0.28, 3.8), Color("8d4939"), true, Vector3(18.0, 0.0, 0.0))
	_box("HouseRoofB", Vector3(15.7, 3.65, 14.05), Vector3(7.2, 0.28, 3.8), Color("7d4034"), true, Vector3(-18.0, 0.0, 0.0))
	_box("HouseDoor", Vector3(15.7, 1.25, 10.66), Vector3(1.15, 2.25, 0.10), Color("69472f"), false)
	_box("DoorFrameTop", Vector3(15.7, 2.43, 10.58), Vector3(1.55, 0.16, 0.16), Color("f0dfbe"), false)
	for x_value: float in [13.7, 17.7]:
		_box("HouseWindow", Vector3(x_value, 1.75, 10.63), Vector3(1.35, 1.15, 0.09), Color("72a7b8"), false)
		_box("WindowFrame", Vector3(x_value, 1.75, 10.56), Vector3(1.52, 0.10, 0.13), Color("f4e4c4"), false)
		_box("WindowFrame", Vector3(x_value, 1.75, 10.55), Vector3(0.10, 1.30, 0.13), Color("f4e4c4"), false)
	_box("Porch", Vector3(15.7, 0.42, 9.9), Vector3(4.5, 0.35, 1.45), Color("9b704c"), true)
	for x_value: float in [13.7, 17.7]:
		_cylinder("PorchPost", Vector3(x_value, 1.45, 9.75), 0.10, 2.0, Color("7b573d"), false)
	_box("PorchAwning", Vector3(15.7, 2.55, 9.65), Vector3(4.8, 0.18, 1.9), Color("965040"), false, Vector3(8.0, 0.0, 0.0))
	_box("HouseStep", Vector3(15.7, 0.18, 9.05), Vector3(2.3, 0.18, 0.7), Color("a67a55"), true)
	_flower_patch(Vector3(12.6, 0.0, 10.0), Color("f1a6b8"))
	_flower_patch(Vector3(18.7, 0.0, 10.0), Color("f2d06f"))
	_label("Rumah", Vector3(15.7, 4.65, 13.0), 25)

func _build_warung() -> void:
	_box("WarungBody", Vector3(-11.5, 1.45, 3.0), Vector3(6.2, 2.7, 4.4), Color("d6ae70"), true)
	_box("WarungRoof", Vector3(-11.5, 3.15, 3.0), Vector3(7.0, 0.35, 5.2), Color("6f3c31"), true, Vector3(0.0, 0.0, 0.0))
	_box("WarungFrontShade", Vector3(-11.5, 2.72, 0.55), Vector3(6.2, 0.18, 1.6), Color("8b4a36"), false, Vector3(8.0, 0.0, 0.0))
	_box("WarungCounter", Vector3(-11.5, 0.95, 0.82), Vector3(4.0, 1.15, 0.55), Color("77543b"), true)
	_box("WarungOpening", Vector3(-11.5, 1.95, 0.78), Vector3(3.9, 1.0, 0.08), Color("4b382e"), false)
	for x_value: float in [-13.2, -9.8]:
		_cylinder("WarungPost", Vector3(x_value, 1.5, 0.2), 0.09, 2.7, Color("704d36"), false)
	_box("Bench", Vector3(-7.7, 0.38, 1.4), Vector3(2.3, 0.25, 0.7), Color("8a6244"), true)
	_box("BenchBack", Vector3(-7.7, 0.95, 1.7), Vector3(2.3, 0.85, 0.16), Color("7a553b"), false)
	_bush(Vector3(-14.7, 0.0, 4.9), 0.9)
	_flower_patch(Vector3(-14.0, 0.0, 0.6), Color("ef8b72"))
	_label("Warung Bu Ratih", Vector3(-11.5, 3.95, 2.7), 27)

func _build_rice_field() -> void:
	# Mud-water rice paddies separated by raised bunds.
	for field_index: int in range(3):
		var x_center: float = -9.0 + float(field_index) * 5.2
		_box("PaddyWater", Vector3(x_center, 0.03, -14.5), Vector3(4.7, 0.05, 5.5), Color("779e7e"), false)
		_box("PaddyMud", Vector3(x_center, -0.03, -14.5), Vector3(4.7, 0.07, 5.5), Color("75644a"), false)
		for row_index: int in range(6):
			for col_index: int in range(5):
				var rice_pos: Vector3 = Vector3(x_center - 1.7 + float(col_index) * 0.85, 0.12, -16.4 + float(row_index) * 0.75)
				_cylinder("RiceStem", rice_pos, 0.035, 0.45, Color("6cad4e"), false)
				_box("RiceLeaf", rice_pos + Vector3(0.12, 0.24, 0.0), Vector3(0.28, 0.035, 0.06), Color("83bd52"), false, Vector3(0.0, 0.0, -20.0))
	for x_value: float in [-11.6, -6.4, -1.2, 4.0]:
		_box("PaddyBund", Vector3(x_value, 0.16, -14.5), Vector3(0.42, 0.28, 6.2), Color("92724f"), true)
	_box("PaddyBundNorth", Vector3(-3.8, 0.16, -17.55), Vector3(16.2, 0.28, 0.42), Color("92724f"), true)
	_box("PaddyBundSouth", Vector3(-3.8, 0.16, -11.45), Vector3(16.2, 0.28, 0.42), Color("92724f"), true)
	_box("IrrigationChannel", Vector3(6.2, 0.02, -14.55), Vector3(1.3, 0.06, 6.1), Color("5aacc4"), false)
	_box("IrrigationBankL", Vector3(5.42, 0.14, -14.55), Vector3(0.28, 0.26, 6.3), Color("8b6e4b"), true)
	_box("IrrigationBankR", Vector3(6.98, 0.14, -14.55), Vector3(0.28, 0.26, 6.3), Color("8b6e4b"), true)
	_box("IrrigationGate", Vector3(6.2, 0.72, -11.75), Vector3(1.5, 1.35, 0.28), Color("805c3d"), true)
	_label("Sawah Pak Wiryo", Vector3(-3.8, 2.0, -17.4), 26)

func _build_river_and_bridge() -> void:
	# Layered river banks make the water read as a real channel instead of a blue stripe.
	_box("RiverBed", Vector3(0.0, -0.22, -8.2), Vector3(52.0, 0.35, 6.3), Color("617f73"), false)
	_box("RiverWater", Vector3(0.0, 0.01, -8.2), Vector3(52.0, 0.08, 5.0), Color("4f9fbd"), false)
	_box("RiverBankSouth", Vector3(0.0, 0.20, -5.45), Vector3(52.0, 0.38, 0.70), Color("8b7d59"), true)
	_box("RiverBankNorth", Vector3(0.0, 0.20, -10.95), Vector3(52.0, 0.38, 0.70), Color("8b7d59"), true)
	_box("RiverGrassSouth", Vector3(0.0, 0.38, -5.05), Vector3(52.0, 0.12, 0.65), Color("6f9d58"), false)
	_box("RiverGrassNorth", Vector3(0.0, 0.38, -11.35), Vector3(52.0, 0.12, 0.65), Color("6f9d58"), false)
	# Wooden bridge deck and rails.
	_box("BridgeDeck", Vector3(2.0, 0.48, -8.2), Vector3(3.8, 0.38, 6.4), Color("9b6b47"), true)
	for z_value: float in [-10.7, -9.6, -8.5, -7.4, -6.3]:
		_box("BridgePlank", Vector3(2.0, 0.71, z_value), Vector3(3.55, 0.09, 0.78), Color("b07b52"), false)
	for x_value: float in [0.35, 3.65]:
		for z_value: float in [-10.8, -8.2, -5.6]:
			_cylinder("BridgePost", Vector3(x_value, 1.15, z_value), 0.08, 1.35, Color("684832"), false)
		_box("BridgeRail", Vector3(x_value, 1.48, -8.2), Vector3(0.12, 0.12, 5.8), Color("765039"), false)
	for rock_pos: Vector3 in [Vector3(-20.0, 0.12, -7.9), Vector3(-8.0, 0.10, -8.9), Vector3(11.0, 0.12, -7.3), Vector3(20.5, 0.1, -8.6), Vector3(-14.0, 0.1, -9.1)]:
		_rock(rock_pos, 0.85)

func _build_landscape() -> void:
	# Layered ground zones and distant hills provide depth while keeping collision simple.
	_box("Ground", Vector3(0.0, -0.18, 0.0), Vector3(52.0, 0.36, 42.0), Color("769c59"), true)
	_box("VillageGreen", Vector3(-7.0, 0.02, 5.0), Vector3(25.0, 0.08, 12.0), Color("7fa45c"), false)
	_box("FarmYard", Vector3(11.0, 0.025, 11.0), Vector3(20.0, 0.08, 13.0), Color("84a760"), false)
	_box("VillageRoad", Vector3(0.0, 0.08, 1.5), Vector3(44.0, 0.13, 3.7), Color("b99b6a"), false)
	_box("RoadEdgeNorth", Vector3(0.0, 0.13, -0.55), Vector3(44.0, 0.10, 0.30), Color("947d59"), false)
	_box("RoadEdgeSouth", Vector3(0.0, 0.13, 3.55), Vector3(44.0, 0.10, 0.30), Color("947d59"), false)
	_box("SouthPath", Vector3(2.0, 0.09, 10.2), Vector3(2.7, 0.12, 14.0), Color("b99b6a"), false)
	_box("FarmPlot", Vector3(8.5, 0.04, 10.5), Vector3(14.0, 0.08, 11.0), Color("9b7958"), false)

	# Distant stylized hills around the valley rim.
	for hill_data: Dictionary in [
		{"p": Vector3(-22.0, 3.0, -18.8), "s": Vector3(11.0, 3.5, 5.5), "c": Color("587b50")},
		{"p": Vector3(-9.0, 3.5, -20.0), "s": Vector3(12.0, 4.2, 5.0), "c": Color("52764e")},
		{"p": Vector3(8.0, 3.2, -20.0), "s": Vector3(13.0, 3.9, 5.0), "c": Color("5a8054")},
		{"p": Vector3(22.0, 3.0, -18.5), "s": Vector3(10.0, 3.5, 5.5), "c": Color("557a50")}
	]:
		var hill_pos: Vector3 = hill_data["p"] as Vector3
		var hill_scale: Vector3 = hill_data["s"] as Vector3
		var hill_color: Color = hill_data["c"] as Color
		_sphere("ValleyHill", hill_pos, 1.0, hill_color, hill_scale)

func _build_nature() -> void:
	for tree_pos: Vector3 in [Vector3(-21.0,0.0,11.0), Vector3(-18.5,0.0,15.5), Vector3(-5.0,0.0,14.8), Vector3(-1.0,0.0,17.2), Vector3(21.0,0.0,7.0), Vector3(22.0,0.0,14.0), Vector3(-18.0,0.0,-14.0), Vector3(13.5,0.0,-15.2)]:
		_tree_canopy(tree_pos, 0.9, Color("4f8d49"))
	for palm_pos: Vector3 in [Vector3(-22.5,0.0,-3.2), Vector3(20.8,0.0,-3.0), Vector3(-15.5,0.0,-4.7), Vector3(18.5,0.0,18.0)]:
		_palm(palm_pos, 0.86)
	for banana_pos: Vector3 in [Vector3(19.0,0.0,9.0), Vector3(-16.5,0.0,7.2), Vector3(-14.8,0.0,8.2), Vector3(20.5,0.0,11.0)]:
		_banana_cluster(banana_pos, 0.8)
	for bush_pos: Vector3 in [Vector3(-20.0,0.0,-4.7), Vector3(-12.5,0.0,-4.6), Vector3(8.0,0.0,-4.7), Vector3(15.0,0.0,-4.7), Vector3(-18.0,0.0,5.4), Vector3(20.0,0.0,5.0)]:
		_bush(bush_pos, 0.75)
	_flower_patch(Vector3(-4.0,0.0,4.8), Color("f5d36c"))
	_flower_patch(Vector3(5.5,0.0,4.6), Color("e9a0be"))
	_flower_patch(Vector3(-18.5,0.0,4.8), Color("d7b4f2"))

func _build_village_details() -> void:
	_fence_segment(Vector3(10.0, 0.0, 16.8), 8.0, 0.0)
	_fence_segment(Vector3(20.5, 0.0, 14.8), 5.5, 90.0)
	_fence_segment(Vector3(7.0, 0.0, 14.5), 5.0, 90.0)
	for lamp_pos: Vector3 in [Vector3(-17.0,0.0,4.2), Vector3(-5.0,0.0,4.2), Vector3(7.0,0.0,4.2), Vector3(18.0,0.0,4.2)]:
		_lamp_post(lamp_pos)
	_box("VillageSignPost", Vector3(-2.0, 1.0, 4.9), Vector3(0.16, 2.0, 0.16), Color("70503a"), false)
	_box("VillageSign", Vector3(-2.0, 1.75, 4.85), Vector3(2.8, 0.8, 0.16), Color("9b724f"), false)
	_label("LEMBah SARI", Vector3(-2.0, 1.82, 4.72), 22)

func _build_world() -> void:
	_build_landscape()
	_build_river_and_bridge()
	_build_house()
	_build_warung()
	_build_rice_field()
	_build_nature()
	_build_village_details()

	# Invisible world edges.
	var north_boundary: Node3D = _box("NorthBoundary", Vector3(0.0, 1.5, -20.8), Vector3(52.0, 3.0, 0.5), Color(0.0,0.0,0.0,0.0), true)
	var south_boundary: Node3D = _box("SouthBoundary", Vector3(0.0, 1.5, 20.8), Vector3(52.0, 3.0, 0.5), Color(0.0,0.0,0.0,0.0), true)
	var west_boundary: Node3D = _box("WestBoundary", Vector3(-25.8, 1.5, 0.0), Vector3(0.5, 3.0, 42.0), Color(0.0,0.0,0.0,0.0), true)
	var east_boundary: Node3D = _box("EastBoundary", Vector3(25.8, 1.5, 0.0), Vector3(0.5, 3.0, 42.0), Color(0.0,0.0,0.0,0.0), true)
	north_boundary.visible = false
	south_boundary.visible = false
	west_boundary.visible = false
	east_boundary.visible = false
