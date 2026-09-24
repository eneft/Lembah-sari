extends Node3D

# Visual Shape Overhaul 0.0.7b
# Gameplay collision stays simple and reliable, while the visible world uses
# curved ribbons, custom triangle meshes, low-poly foliage and gable roofs.

func _ready() -> void:
	_build_world()

func _mat(color: Color, roughness: float = 0.92, metallic: float = 0.0) -> StandardMaterial3D:
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = roughness
	material.metallic = metallic
	return material

func _mesh_instance(node_name: String, mesh: Mesh, color: Color, pos: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var instance: MeshInstance3D = MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.material_override = _mat(color)
	instance.position = pos
	add_child(instance)
	return instance

func _tri_mesh(node_name: String, vertices: PackedVector3Array, color: Color, pos: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var surface: SurfaceTool = SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for vertex: Vector3 in vertices:
		surface.add_vertex(vertex)
	surface.generate_normals()
	var array_mesh: ArrayMesh = surface.commit()
	return _mesh_instance(node_name, array_mesh, color, pos)

func _box_collision(node_name: String, pos: Vector3, size: Vector3) -> StaticBody3D:
	var body: StaticBody3D = StaticBody3D.new()
	body.name = node_name
	body.position = pos
	var collision: CollisionShape3D = CollisionShape3D.new()
	var shape: BoxShape3D = BoxShape3D.new()
	shape.size = size
	collision.shape = shape
	body.add_child(collision)
	add_child(body)
	return body

func _visual_box(node_name: String, pos: Vector3, size: Vector3, color: Color, rotation: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var mesh: BoxMesh = BoxMesh.new()
	mesh.size = size
	var instance: MeshInstance3D = _mesh_instance(node_name, mesh, color, pos)
	instance.rotation_degrees = rotation
	return instance

func _low_cylinder(node_name: String, pos: Vector3, radius: float, height: float, color: Color, sides: int = 8, rotation: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var mesh: CylinderMesh = CylinderMesh.new()
	mesh.top_radius = radius * 0.92
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = sides
	mesh.rings = 1
	var instance: MeshInstance3D = _mesh_instance(node_name, mesh, color, pos)
	instance.rotation_degrees = rotation
	return instance

func _cone(node_name: String, pos: Vector3, radius: float, height: float, color: Color, sides: int = 7) -> MeshInstance3D:
	var mesh: CylinderMesh = CylinderMesh.new()
	mesh.top_radius = 0.05
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = sides
	mesh.rings = 1
	return _mesh_instance(node_name, mesh, color, pos)

func _low_sphere(node_name: String, pos: Vector3, radius: float, color: Color, scale_value: Vector3 = Vector3.ONE) -> MeshInstance3D:
	var mesh: SphereMesh = SphereMesh.new()
	mesh.radius = radius
	mesh.height = radius * 2.0
	mesh.radial_segments = 10
	mesh.rings = 5
	var instance: MeshInstance3D = _mesh_instance(node_name, mesh, color, pos)
	instance.scale = scale_value
	return instance

func _terrain_height(x_value: float, z_value: float) -> float:
	var broad: float = sin(x_value * 0.11) * 0.07 + cos(z_value * 0.15) * 0.05
	var edge_lift: float = maxf(0.0, (absf(x_value) - 18.0) * 0.018) + maxf(0.0, (absf(z_value) - 15.0) * 0.025)
	return broad + edge_lift

func _build_terrain_mesh() -> void:
	var vertices: PackedVector3Array = PackedVector3Array()
	var cols: int = 14
	var rows: int = 12
	var width: float = 52.0
	var depth: float = 42.0
	for row: int in range(rows - 1):
		for col: int in range(cols - 1):
			var x0: float = -width * 0.5 + width * float(col) / float(cols - 1)
			var x1: float = -width * 0.5 + width * float(col + 1) / float(cols - 1)
			var z0: float = -depth * 0.5 + depth * float(row) / float(rows - 1)
			var z1: float = -depth * 0.5 + depth * float(row + 1) / float(rows - 1)
			var a: Vector3 = Vector3(x0, _terrain_height(x0, z0), z0)
			var b: Vector3 = Vector3(x1, _terrain_height(x1, z0), z0)
			var c: Vector3 = Vector3(x1, _terrain_height(x1, z1), z1)
			var d: Vector3 = Vector3(x0, _terrain_height(x0, z1), z1)
			vertices.append_array(PackedVector3Array([a, b, c, a, c, d]))
	_tri_mesh("RollingValleyGround", vertices, Color("759857"))
	# Stable flat collision beneath the very shallow visual terrain undulation.
	_box_collision("GroundCollision", Vector3(0.0, -0.20, 0.0), Vector3(52.0, 0.40, 42.0))

func _ribbon(node_name: String, points: Array[Vector3], width: float, color: Color, y_offset: float = 0.0) -> MeshInstance3D:
	var vertices: PackedVector3Array = PackedVector3Array()
	if points.size() < 2:
		return _tri_mesh(node_name, vertices, color)
	for index: int in range(points.size() - 1):
		var p0: Vector3 = points[index]
		var p1: Vector3 = points[index + 1]
		var direction: Vector3 = p1 - p0
		direction.y = 0.0
		if direction.length_squared() < 0.001:
			continue
		direction = direction.normalized()
		var side: Vector3 = Vector3(-direction.z, 0.0, direction.x) * width * 0.5
		var a: Vector3 = Vector3(p0.x, p0.y + y_offset, p0.z) - side
		var b: Vector3 = Vector3(p0.x, p0.y + y_offset, p0.z) + side
		var c: Vector3 = Vector3(p1.x, p1.y + y_offset, p1.z) + side
		var d: Vector3 = Vector3(p1.x, p1.y + y_offset, p1.z) - side
		vertices.append_array(PackedVector3Array([a, b, c, a, c, d]))
	return _tri_mesh(node_name, vertices, color)

func _gable_roof(node_name: String, center: Vector3, width: float, depth: float, rise: float, color: Color) -> MeshInstance3D:
	var half_w: float = width * 0.5
	var half_d: float = depth * 0.5
	var vertices: PackedVector3Array = PackedVector3Array([
		# front slope
		Vector3(-half_w, 0.0, -half_d), Vector3(half_w, 0.0, -half_d), Vector3(half_w, 0.0, half_d),
		Vector3(-half_w, 0.0, -half_d), Vector3(half_w, 0.0, half_d), Vector3(-half_w, 0.0, half_d),
		# left roof slope to ridge
		Vector3(-half_w, 0.0, -half_d), Vector3(-half_w, 0.0, half_d), Vector3(0.0, rise, half_d),
		Vector3(-half_w, 0.0, -half_d), Vector3(0.0, rise, half_d), Vector3(0.0, rise, -half_d),
		# right roof slope to ridge
		Vector3(half_w, 0.0, -half_d), Vector3(0.0, rise, -half_d), Vector3(0.0, rise, half_d),
		Vector3(half_w, 0.0, -half_d), Vector3(0.0, rise, half_d), Vector3(half_w, 0.0, half_d),
		# gable ends
		Vector3(-half_w, 0.0, -half_d), Vector3(0.0, rise, -half_d), Vector3(half_w, 0.0, -half_d),
		Vector3(-half_w, 0.0, half_d), Vector3(half_w, 0.0, half_d), Vector3(0.0, rise, half_d)
	])
	var roof: MeshInstance3D = _tri_mesh(node_name, vertices, color, center)
	roof.rotation_degrees.y = 90.0
	return roof

func _leaf_blade(node_name: String, pos: Vector3, length_value: float, width_value: float, color: Color, yaw: float, pitch: float = -10.0) -> MeshInstance3D:
	var vertices: PackedVector3Array = PackedVector3Array([
		Vector3(-width_value * 0.5, 0.0, 0.0), Vector3(width_value * 0.5, 0.0, 0.0), Vector3(0.0, 0.08, length_value),
		Vector3(-width_value * 0.5, 0.0, 0.0), Vector3(0.0, 0.08, length_value), Vector3(0.0, -0.04, length_value * 0.55)
	])
	var leaf: MeshInstance3D = _tri_mesh(node_name, vertices, color, pos)
	leaf.rotation_degrees = Vector3(pitch, yaw, 0.0)
	return leaf

func _tree(pos: Vector3, scale_mul: float = 1.0, foliage: Color = Color("4f8848")) -> void:
	_low_cylinder("TreeTrunk", pos + Vector3(0.0, 1.25 * scale_mul, 0.0), 0.28 * scale_mul, 2.5 * scale_mul, Color("755139"), 7)
	_low_sphere("TreeCrown", pos + Vector3(0.0, 2.95 * scale_mul, 0.0), 1.15 * scale_mul, foliage, Vector3(1.15, 0.9, 1.05))
	_low_sphere("TreeCrown", pos + Vector3(-0.72 * scale_mul, 2.75 * scale_mul, 0.08), 0.78 * scale_mul, foliage.lightened(0.08), Vector3(1.0, 0.85, 0.95))
	_low_sphere("TreeCrown", pos + Vector3(0.68 * scale_mul, 2.78 * scale_mul, -0.15), 0.82 * scale_mul, foliage.darkened(0.05), Vector3(0.95, 0.88, 1.0))

func _palm(pos: Vector3, scale_mul: float = 1.0) -> void:
	_low_cylinder("PalmTrunk", pos + Vector3(0.0, 2.1 * scale_mul, 0.0), 0.18 * scale_mul, 4.2 * scale_mul, Color("89644a"), 7, Vector3(0.0, 0.0, 4.0))
	for angle_value: float in [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]:
		_leaf_blade("PalmFrond", pos + Vector3(0.0, 4.2 * scale_mul, 0.0), 2.2 * scale_mul, 0.58 * scale_mul, Color("3f8748"), angle_value, -18.0)

func _banana(pos: Vector3, scale_mul: float = 1.0) -> void:
	for offset: Vector3 in [Vector3(-0.22, 0.0, 0.0), Vector3(0.20, 0.0, 0.18), Vector3(0.0, 0.0, -0.22)]:
		_low_cylinder("BananaStem", pos + offset + Vector3(0.0, 0.82 * scale_mul, 0.0), 0.10 * scale_mul, 1.65 * scale_mul, Color("78994d"), 6)
	for angle_value: float in [0.0, 60.0, 120.0, 180.0, 240.0, 300.0]:
		_leaf_blade("BananaLeaf", pos + Vector3(0.0, 1.72 * scale_mul, 0.0), 1.65 * scale_mul, 0.62 * scale_mul, Color("66a650"), angle_value, -16.0)

func _bush(pos: Vector3, scale_mul: float = 1.0, color_value: Color = Color("4e914a")) -> void:
	_low_sphere("Bush", pos + Vector3(0.0, 0.45 * scale_mul, 0.0), 0.58 * scale_mul, color_value, Vector3(1.25, 0.72, 1.0))
	_low_sphere("Bush", pos + Vector3(0.38 * scale_mul, 0.40 * scale_mul, 0.08), 0.42 * scale_mul, color_value.lightened(0.06), Vector3.ONE)

func _rock(pos: Vector3, scale_mul: float = 1.0) -> void:
	var rock: MeshInstance3D = _low_sphere("RiverRock", pos + Vector3(0.0, 0.26 * scale_mul, 0.0), 0.48 * scale_mul, Color("7e817b"), Vector3(1.35, 0.58, 0.92))
	rock.rotation_degrees = Vector3(8.0, pos.x * 7.0, 4.0)

func _flower_patch(pos: Vector3, flower_color: Color) -> void:
	for offset: Vector3 in [Vector3(-0.25,0.0,-0.16), Vector3(0.16,0.0,-0.10), Vector3(0.03,0.0,0.24), Vector3(0.31,0.0,0.18)]:
		_low_cylinder("FlowerStem", pos + offset + Vector3(0.0,0.17,0.0), 0.022, 0.34, Color("4e8843"), 5)
		_low_sphere("Flower", pos + offset + Vector3(0.0,0.39,0.0), 0.085, flower_color, Vector3(1.2,0.55,1.0))

func _build_paths() -> void:
	var road_points: Array[Vector3] = [
		Vector3(-25.0, 0.08, 1.7), Vector3(-18.0, 0.08, 1.3), Vector3(-10.0, 0.08, 1.5),
		Vector3(-2.0, 0.08, 1.2), Vector3(6.0, 0.08, 1.8), Vector3(14.0, 0.08, 1.4), Vector3(24.0, 0.08, 1.8)
	]
	_ribbon("VillageRoad", road_points, 3.6, Color("b89a68"), 0.02)
	var home_path: Array[Vector3] = [Vector3(2.0,0.09,1.4), Vector3(2.3,0.09,6.0), Vector3(5.0,0.09,9.0), Vector3(11.0,0.09,10.0), Vector3(15.5,0.09,9.5)]
	_ribbon("HomePath", home_path, 2.25, Color("bca174"), 0.02)

func _build_river() -> void:
	var water_points: Array[Vector3] = [
		Vector3(-27.0,-0.07,-8.7), Vector3(-20.0,-0.08,-8.1), Vector3(-13.0,-0.07,-8.5),
		Vector3(-6.0,-0.08,-7.8), Vector3(2.0,-0.07,-8.2), Vector3(9.0,-0.08,-8.8),
		Vector3(17.0,-0.07,-8.1), Vector3(27.0,-0.08,-8.5)
	]
	_ribbon("RiverWater", water_points, 4.8, Color("4c9bb7"), 0.0)
	# Irregular earthy banks follow the same curved river.
	var south_bank: Array[Vector3] = []
	var north_bank: Array[Vector3] = []
	for point: Vector3 in water_points:
		south_bank.append(point + Vector3(0.0, 0.08, 2.75))
		north_bank.append(point + Vector3(0.0, 0.08, -2.75))
	_ribbon("RiverSouthBank", south_bank, 0.9, Color("8d7d59"), 0.0)
	_ribbon("RiverNorthBank", north_bank, 0.9, Color("8d7d59"), 0.0)
	for rock_pos: Vector3 in [Vector3(-20.0,0.0,-8.0), Vector3(-8.2,0.0,-8.8), Vector3(11.0,0.0,-8.4), Vector3(20.0,0.0,-8.7), Vector3(-14.0,0.0,-7.6)]:
		_rock(rock_pos, 0.9)

func _build_bridge() -> void:
	# Planks form a small arched-looking timber bridge instead of one rectangular slab.
	for index: int in range(8):
		var z_value: float = -10.6 + float(index) * 0.70
		var height_value: float = 0.48 + sin(float(index) / 7.0 * PI) * 0.28
		_visual_box("BridgePlank", Vector3(2.0, height_value, z_value), Vector3(3.25, 0.14, 0.62), Color("a8754d"))
	for x_value: float in [0.35, 3.65]:
		for z_value: float in [-10.5, -8.2, -5.9]:
			_low_cylinder("BridgePost", Vector3(x_value, 1.08, z_value), 0.09, 1.45, Color("6d4933"), 7)
		var rail_points: Array[Vector3] = [Vector3(x_value,1.48,-10.5), Vector3(x_value,1.72,-8.2), Vector3(x_value,1.48,-5.9)]
		# Rail rendered as short cylinders for an organic timber silhouette.
		for rail_index: int in range(rail_points.size() - 1):
			var start: Vector3 = rail_points[rail_index]
			var finish: Vector3 = rail_points[rail_index + 1]
			var middle: Vector3 = (start + finish) * 0.5
			var distance: float = start.distance_to(finish)
			var rail: MeshInstance3D = _low_cylinder("BridgeRail", middle, 0.07, distance, Color("765139"), 6)
			rail.rotation_degrees.x = 90.0
	_box_collision("BridgeCollision", Vector3(2.0,0.42,-8.2), Vector3(3.5,0.55,6.2))

func _build_house() -> void:
	# Rectangular walls are natural architecture; roof/profile/details are no longer box placeholders.
	_visual_box("HouseWalls", Vector3(15.7,1.65,13.2), Vector3(6.0,3.0,4.8), Color("e5d0a7"))
	_box_collision("HouseCollision", Vector3(15.7,1.55,13.4), Vector3(6.0,3.1,4.4))
	_gable_roof("HouseGableRoof", Vector3(15.7,3.15,13.2), 5.8, 7.1, 1.7, Color("88483a"))
	_visual_box("HouseDoor", Vector3(15.7,1.22,10.75), Vector3(1.05,2.18,0.10), Color("68452e"))
	for x_value: float in [13.75,17.65]:
		_visual_box("WindowGlass", Vector3(x_value,1.75,10.72), Vector3(1.15,1.05,0.08), Color("7cabb5"))
		_low_cylinder("WindowAwning", Vector3(x_value,2.35,10.54), 0.08, 1.38, Color("f0dfbd"), 6, Vector3(0.0,0.0,90.0))
	# Rounded timber porch and stairs.
	_visual_box("PorchFloor", Vector3(15.7,0.38,9.9), Vector3(4.4,0.26,1.35), Color("9a704c"))
	for x_value: float in [13.8,17.6]:
		_low_cylinder("PorchPost", Vector3(x_value,1.46,9.75), 0.10, 2.15, Color("78523a"), 7)
	_gable_roof("PorchRoof", Vector3(15.7,2.55,9.65), 2.0, 4.8, 0.65, Color("985142"))
	for stair_index: int in range(3):
		var step_y: float = 0.10 + float(stair_index) * 0.10
		var step_z: float = 8.85 + float(stair_index) * 0.23
		_visual_box("HouseStep", Vector3(15.7,step_y,step_z), Vector3(1.8 - float(stair_index) * 0.15,0.16,0.48), Color("a47a57"))
	_flower_patch(Vector3(12.5,0.0,9.9), Color("ef9faf"))
	_flower_patch(Vector3(18.8,0.0,10.0), Color("f1cd68"))

func _build_warung() -> void:
	_visual_box("WarungWalls", Vector3(-11.5,1.42,3.0), Vector3(5.8,2.65,4.1), Color("d4ad70"))
	_box_collision("WarungCollision", Vector3(-11.5,1.35,3.2), Vector3(5.8,2.7,3.7))
	_gable_roof("WarungRoof", Vector3(-11.5,2.75,3.0), 4.9, 6.6, 1.25, Color("713d31"))
	# Open front with round timber posts and counter.
	for x_value: float in [-13.5,-9.5]:
		_low_cylinder("WarungPost", Vector3(x_value,1.45,0.65), 0.10, 2.65, Color("704d36"), 7)
	_visual_box("WarungCounter", Vector3(-11.5,0.90,0.65), Vector3(3.8,0.95,0.46), Color("7b563b"))
	_gable_roof("WarungAwning", Vector3(-11.5,2.55,0.35), 1.55, 4.8, 0.45, Color("914b39"))
	# Round stools instead of box benches.
	for x_value: float in [-8.6,-7.8,-7.0]:
		_low_cylinder("WarungStool", Vector3(x_value,0.38,1.5), 0.28, 0.62, Color("866044"), 8)
	_flower_patch(Vector3(-14.4,0.0,0.7), Color("ee8b72"))

func _build_rice_fields() -> void:
	# Curved/soft-looking paddy plots with low-poly rice bunches.
	for field_index: int in range(3):
		var center_x: float = -9.2 + float(field_index) * 5.3
		var paddy: MeshInstance3D = _low_sphere("PaddyWater", Vector3(center_x,-0.03,-14.5), 1.0, Color("789c7b"), Vector3(2.35,0.035,2.75))
		paddy.rotation_degrees.y = float(field_index - 1) * 2.5
		for row_index: int in range(5):
			for col_index: int in range(5):
				var rice_x: float = center_x - 1.55 + float(col_index) * 0.78
				var rice_z: float = -16.0 + float(row_index) * 0.78
				var base: Vector3 = Vector3(rice_x,0.18,rice_z)
				for blade_index: int in range(3):
					_leaf_blade("RiceLeaf", base, 0.42, 0.07, Color("68a94d"), float(blade_index) * 120.0, -72.0)
	# Earth bunds are rounded cylinders laid horizontally.
	for x_value: float in [-11.85,-6.55,-1.25,4.05]:
		var bund: MeshInstance3D = _low_cylinder("PaddyBund", Vector3(x_value,0.18,-14.5), 0.16, 5.8, Color("8a7550"), 8)
		bund.rotation_degrees.x = 90.0
	var channel: Array[Vector3] = [Vector3(6.2,0.02,-17.7), Vector3(6.3,0.02,-14.6), Vector3(6.1,0.02,-11.6)]
	_ribbon("IrrigationWater", channel, 0.92, Color("58a8be"), 0.0)
	_low_cylinder("IrrigationGatePost", Vector3(5.65,0.72,-11.8), 0.10, 1.35, Color("7a573e"), 7)
	_low_cylinder("IrrigationGatePost", Vector3(6.75,0.72,-11.8), 0.10, 1.35, Color("7a573e"), 7)
	_visual_box("IrrigationGate", Vector3(6.2,0.70,-11.8), Vector3(1.15,0.8,0.14), Color("866044"))

func _build_nature() -> void:
	for tree_pos: Vector3 in [Vector3(-21.0,0.0,11.0),Vector3(-18.5,0.0,15.5),Vector3(-5.0,0.0,14.8),Vector3(-1.0,0.0,17.2),Vector3(21.0,0.0,7.0),Vector3(22.0,0.0,14.0),Vector3(-18.0,0.0,-14.0),Vector3(13.5,0.0,-15.5)]:
		_tree(tree_pos,0.92)
	for palm_pos: Vector3 in [Vector3(-22.0,0.0,-3.2),Vector3(20.8,0.0,-3.0),Vector3(-15.2,0.0,-4.6),Vector3(18.8,0.0,18.0)]:
		_palm(palm_pos,0.88)
	for banana_pos: Vector3 in [Vector3(19.0,0.0,9.0),Vector3(-16.4,0.0,7.2),Vector3(-14.8,0.0,8.2),Vector3(20.5,0.0,11.0)]:
		_banana(banana_pos,0.85)
	for bush_pos: Vector3 in [Vector3(-20.0,0.0,-4.5),Vector3(-12.5,0.0,-4.5),Vector3(8.0,0.0,-4.6),Vector3(15.0,0.0,-4.7),Vector3(-18.0,0.0,5.2),Vector3(20.0,0.0,5.0)]:
		_bush(bush_pos,0.8)
	_flower_patch(Vector3(-4.0,0.0,4.8),Color("f3d16b"))
	_flower_patch(Vector3(5.6,0.0,4.7),Color("e8a0bc"))

func _build_hills() -> void:
	for hill_data: Dictionary in [
		{"p":Vector3(-23.0,1.5,-19.0),"s":Vector3(6.5,3.8,3.5),"c":Color("52734c")},
		{"p":Vector3(-11.0,1.8,-20.0),"s":Vector3(7.2,4.2,3.4),"c":Color("4e714b")},
		{"p":Vector3(3.0,1.7,-20.4),"s":Vector3(8.0,4.0,3.5),"c":Color("567950")},
		{"p":Vector3(18.0,1.6,-19.2),"s":Vector3(7.0,3.8,3.8),"c":Color("51744d")}
	]:
		var hill_pos: Vector3 = hill_data["p"] as Vector3
		var hill_scale: Vector3 = hill_data["s"] as Vector3
		var hill_color: Color = hill_data["c"] as Color
		_low_sphere("ValleyHill",hill_pos,1.0,hill_color,hill_scale)
	# Layer a few cone silhouettes to feel like distant tropical ridges.
	_cone("DistantPeak",Vector3(-8.0,3.0,-21.0),4.5,6.0,Color("4a6c48"),9)
	_cone("DistantPeak",Vector3(11.0,2.6,-21.0),4.0,5.2,Color("50744d"),9)

func _build_village_details() -> void:
	# Round fence posts + rails.
	for x_value: float in [7.0,9.0,11.0,13.0]:
		_low_cylinder("FencePost",Vector3(x_value,0.55,16.8),0.08,1.1,Color("835f43"),6)
		if x_value < 13.0:
			var rail: MeshInstance3D = _low_cylinder("FenceRail",Vector3(x_value + 1.0,0.68,16.8),0.055,2.05,Color("936a49"),6)
			rail.rotation_degrees.z = 90.0
	for lamp_pos: Vector3 in [Vector3(-17.0,0.0,4.3),Vector3(-5.0,0.0,4.2),Vector3(7.0,0.0,4.3),Vector3(18.0,0.0,4.2)]:
		_low_cylinder("LampPost",lamp_pos + Vector3(0.0,1.25,0.0),0.07,2.5,Color("4d4b47"),7)
		_low_sphere("LampGlass",lamp_pos + Vector3(0.0,2.58,0.0),0.16,Color("f2d28d"),Vector3(1.0,1.25,1.0))

func _build_world() -> void:
	_build_terrain_mesh()
	_build_hills()
	_build_paths()
	_build_river()
	_build_bridge()
	_build_house()
	_build_warung()
	_build_rice_fields()
	_build_nature()
	_build_village_details()

	# World limits stay invisible and gameplay-safe.
	_box_collision("NorthBoundary",Vector3(0.0,1.5,-20.8),Vector3(52.0,3.0,0.5))
	_box_collision("SouthBoundary",Vector3(0.0,1.5,20.8),Vector3(52.0,3.0,0.5))
	_box_collision("WestBoundary",Vector3(-25.8,1.5,0.0),Vector3(0.5,3.0,42.0))
	_box_collision("EastBoundary",Vector3(25.8,1.5,0.0),Vector3(0.5,3.0,42.0))
