extends Node3D

const SKY: Color = Color("a9d7df")
const GRASS: Color = Color("78a95a")
const GRASS_DARK: Color = Color("5f8e49")
const GRASS_LIGHT: Color = Color("91ba69")
const DIRT: Color = Color("b69261")
const SOIL: Color = Color("7f5c40")
const WATER: Color = Color("62abc0")
const WATER_LIGHT: Color = Color("8bc6cf")
const WOOD: Color = Color("8b5d3b")
const WOOD_DARK: Color = Color("5e3d2a")
const WOOD_LIGHT: Color = Color("b07a4d")
const BAMBOO: Color = Color("a28d53")
const WALL: Color = Color("e6d4aa")
const TERRACOTTA: Color = Color("a8513e")
const TERRACOTTA_DARK: Color = Color("78392f")
const LEAF: Color = Color("4f8a49")
const LEAF_DARK: Color = Color("3f7040")
const LEAF_LIGHT: Color = Color("6fa956")
const STONE: Color = Color("85877e")

var _materials: Dictionary = {}

func _ready() -> void:
	_build_environment()
	_build_ground()
	_build_river()
	_build_house()
	_build_garden()
	_build_bridge()
	_build_rice_fields()
	_build_vegetation()
	_build_story_props()
	_build_camera()
	call_deferred("_capture_preview")

func _mat(color_value: Color, roughness_value: float = 0.94, emission_value: float = 0.0) -> StandardMaterial3D:
	var key: String = "%s|%.2f|%.2f" % [color_value.to_html(), roughness_value, emission_value]
	if _materials.has(key):
		return _materials[key] as StandardMaterial3D
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = color_value
	material.roughness = roughness_value
	if emission_value > 0.0:
		material.emission_enabled = true
		material.emission = color_value
		material.emission_energy_multiplier = emission_value
	_materials[key] = material
	return material

func _mesh(node_name: String, mesh_value: Mesh, material_value: Material, pos: Vector3, rot: Vector3 = Vector3.ZERO, scale_value: Vector3 = Vector3.ONE) -> MeshInstance3D:
	var node: MeshInstance3D = MeshInstance3D.new()
	node.name = node_name
	node.mesh = mesh_value
	node.material_override = material_value
	node.position = pos
	node.rotation_degrees = rot
	node.scale = scale_value
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	add_child(node)
	return node

func _box(node_name: String, pos: Vector3, size_value: Vector3, color_value: Color, rot: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var mesh_value: BoxMesh = BoxMesh.new()
	mesh_value.size = size_value
	return _mesh(node_name, mesh_value, _mat(color_value), pos, rot)

func _cyl(node_name: String, pos: Vector3, radius_value: float, height_value: float, color_value: Color, sides_value: int = 8, rot: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var mesh_value: CylinderMesh = CylinderMesh.new()
	mesh_value.top_radius = radius_value * 0.93
	mesh_value.bottom_radius = radius_value
	mesh_value.height = height_value
	mesh_value.radial_segments = sides_value
	mesh_value.rings = 1
	return _mesh(node_name, mesh_value, _mat(color_value), pos, rot)

func _sphere(node_name: String, pos: Vector3, radius_value: float, color_value: Color, scale_value: Vector3 = Vector3.ONE) -> MeshInstance3D:
	var mesh_value: SphereMesh = SphereMesh.new()
	mesh_value.radius = radius_value
	mesh_value.height = radius_value * 2.0
	mesh_value.radial_segments = 12
	mesh_value.rings = 6
	return _mesh(node_name, mesh_value, _mat(color_value), pos, Vector3.ZERO, scale_value)

func _surface_mesh(node_name: String, vertices: PackedVector3Array, color_value: Color, pos: Vector3 = Vector3.ZERO, rot: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var surface: SurfaceTool = SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for vertex_value: Vector3 in vertices:
		surface.add_vertex(vertex_value)
	surface.generate_normals()
	var result: ArrayMesh = surface.commit()
	return _mesh(node_name, result, _mat(color_value), pos, rot)

func _ribbon(node_name: String, points: Array[Vector3], width_value: float, color_value: Color, y_value: float) -> MeshInstance3D:
	var vertices: PackedVector3Array = PackedVector3Array()
	for index: int in range(points.size() - 1):
		var a: Vector3 = points[index]
		var b: Vector3 = points[index + 1]
		var direction: Vector3 = b - a
		direction.y = 0.0
		if direction.length_squared() < 0.001:
			continue
		direction = direction.normalized()
		var side: Vector3 = Vector3(-direction.z, 0.0, direction.x) * width_value * 0.5
		var p0: Vector3 = Vector3(a.x, y_value, a.z) - side
		var p1: Vector3 = Vector3(a.x, y_value, a.z) + side
		var p2: Vector3 = Vector3(b.x, y_value, b.z) + side
		var p3: Vector3 = Vector3(b.x, y_value, b.z) - side
		vertices.append_array(PackedVector3Array([p0, p1, p2, p0, p2, p3]))
	return _surface_mesh(node_name, vertices, color_value)

func _gable_roof(node_name: String, center: Vector3, width_value: float, depth_value: float, rise_value: float, color_value: Color) -> MeshInstance3D:
	var hw: float = width_value * 0.5
	var hd: float = depth_value * 0.5
	var vertices: PackedVector3Array = PackedVector3Array([
		Vector3(-hw, 0.0, -hd), Vector3(0.0, rise_value, -hd), Vector3(0.0, rise_value, hd),
		Vector3(-hw, 0.0, -hd), Vector3(0.0, rise_value, hd), Vector3(-hw, 0.0, hd),
		Vector3(0.0, rise_value, -hd), Vector3(hw, 0.0, -hd), Vector3(hw, 0.0, hd),
		Vector3(0.0, rise_value, -hd), Vector3(hw, 0.0, hd), Vector3(0.0, rise_value, hd),
		Vector3(-hw, 0.0, -hd), Vector3(hw, 0.0, -hd), Vector3(0.0, rise_value, -hd),
		Vector3(-hw, 0.0, hd), Vector3(0.0, rise_value, hd), Vector3(hw, 0.0, hd)
	])
	return _surface_mesh(node_name, vertices, color_value, center)

func _leaf_blade(node_name: String, pos: Vector3, length_value: float, width_value: float, color_value: Color, yaw_value: float, pitch_value: float = -58.0) -> MeshInstance3D:
	var vertices: PackedVector3Array = PackedVector3Array([
		Vector3(-width_value * 0.5, 0.0, 0.0), Vector3(width_value * 0.5, 0.0, 0.0), Vector3(width_value * 0.14, 0.08, length_value * 0.58),
		Vector3(-width_value * 0.5, 0.0, 0.0), Vector3(width_value * 0.14, 0.08, length_value * 0.58), Vector3(0.0, 0.02, length_value),
		Vector3(-width_value * 0.5, 0.0, 0.0), Vector3(0.0, 0.02, length_value), Vector3(-width_value * 0.12, -0.02, length_value * 0.58)
	])
	return _surface_mesh(node_name, vertices, color_value, pos, Vector3(pitch_value, yaw_value, 0.0))

func _build_environment() -> void:
	var environment: Environment = Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = SKY
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("f2e3c4")
	environment.ambient_light_energy = 0.78
	var world: WorldEnvironment = WorldEnvironment.new()
	world.environment = environment
	add_child(world)

	var sun: DirectionalLight3D = DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48.0, -42.0, 0.0)
	sun.light_color = Color("ffe1ad")
	sun.light_energy = 1.18
	sun.shadow_enabled = true
	add_child(sun)

func _build_ground() -> void:
	_box("Ground", Vector3(0.0, -0.34, 1.0), Vector3(46.0, 0.55, 34.0), GRASS)
	var path_points: Array[Vector3] = [
		Vector3(-10.5, 0.0, 4.2), Vector3(-7.0, 0.0, 2.6), Vector3(-3.2, 0.0, 1.6),
		Vector3(0.0, 0.0, -0.2), Vector3(2.8, 0.0, -2.8), Vector3(4.0, 0.0, -4.4)
	]
	_ribbon("DirtPath", path_points, 2.0, DIRT, 0.02)
	for index: int in range(10):
		var x_value: float = -9.4 + float(index) * 1.25
		var z_value: float = 3.7 - float(index) * 0.78 + sin(float(index) * 1.4) * 0.18
		_sphere("PathStone", Vector3(x_value, 0.12, z_value), 0.32, Color("a69a7d"), Vector3(1.25, 0.30, 0.85))

	for hill_data: Dictionary in [
		{"p":Vector3(-17.0,2.0,-14.5),"s":Vector3(7.0,3.2,3.2),"c":Color("5d8253")},
		{"p":Vector3(-5.0,2.2,-15.5),"s":Vector3(7.5,3.4,3.0),"c":Color("56794d")},
		{"p":Vector3(8.0,2.1,-15.0),"s":Vector3(8.0,3.2,3.2),"c":Color("608555")},
		{"p":Vector3(20.0,1.8,-14.0),"s":Vector3(6.5,2.9,3.1),"c":Color("55794e")}
	]:
		_sphere("DistantHill", hill_data["p"] as Vector3, 1.0, hill_data["c"] as Color, hill_data["s"] as Vector3)

func _build_river() -> void:
	var river_points: Array[Vector3] = [
		Vector3(-23.0,0.0,-6.2), Vector3(-15.0,0.0,-5.4), Vector3(-7.0,0.0,-6.1),
		Vector3(1.0,0.0,-5.4), Vector3(8.0,0.0,-6.2), Vector3(16.0,0.0,-5.5), Vector3(23.0,0.0,-6.2)
	]
	_ribbon("River", river_points, 4.5, WATER, -0.02)
	var near_bank: Array[Vector3] = []
	var far_bank: Array[Vector3] = []
	for point_value: Vector3 in river_points:
		near_bank.append(point_value + Vector3(0.0,0.0,2.55))
		far_bank.append(point_value + Vector3(0.0,0.0,-2.55))
	_ribbon("RiverBankNear", near_bank, 0.55, SOIL, 0.01)
	_ribbon("RiverBankFar", far_bank, 0.55, SOIL, 0.01)
	for x_value: float in [-17.0,-12.0,-8.0,-3.0,8.0,12.0,17.0]:
		_sphere("RiverRock", Vector3(x_value,0.10,-4.0 + sin(x_value)*0.25), 0.46, STONE, Vector3(1.25,0.50,0.85))
	for x_value: float in [-14.0,-5.5,10.5,15.0]:
		_sphere("LilyPad", Vector3(x_value,-0.01,-6.0), 0.28, Color("6aa665"), Vector3(1.25,0.07,1.05))

func _build_house() -> void:
	var base: Vector3 = Vector3(-8.0, 0.0, 5.1)
	_box("HouseFoundation", base + Vector3(0.0,0.24,0.0), Vector3(7.3,0.45,5.4), Color("8e7456"))
	_box("HouseWalls", base + Vector3(0.0,1.75,0.0), Vector3(6.7,3.0,4.9), WALL)
	_gable_roof("MainRoof", base + Vector3(0.0,3.24,0.0), 7.8, 6.0, 2.0, TERRACOTTA)
	_cyl("RoofRidge", base + Vector3(0.0,5.25,0.0), 0.11, 5.85, TERRACOTTA_DARK, 10, Vector3(90.0,0.0,0.0))

	for x_offset: float in [-2.65,-1.35,0.0,1.35,2.65]:
		_box("TimberStud", base + Vector3(x_offset,1.78,-2.49), Vector3(0.12,2.75,0.10), WOOD_DARK)
	_box("TimberBeamTop", base + Vector3(0.0,2.95,-2.50), Vector3(6.55,0.14,0.11), WOOD_DARK)
	_box("TimberBeamLow", base + Vector3(0.0,0.68,-2.50), Vector3(6.55,0.12,0.11), WOOD)

	_box("Door", base + Vector3(0.0,1.35,-2.55), Vector3(1.10,2.35,0.12), WOOD_DARK)
	for window_x: float in [-2.0,2.0]:
		_box("WindowGlass", base + Vector3(window_x,1.75,-2.56), Vector3(1.05,1.05,0.10), Color("82b8c2"))
		_box("ShutterL", base + Vector3(window_x-0.75,1.75,-2.62), Vector3(0.52,1.15,0.09), WOOD, Vector3(0.0,25.0,0.0))
		_box("ShutterR", base + Vector3(window_x+0.75,1.75,-2.62), Vector3(0.52,1.15,0.09), WOOD, Vector3(0.0,-25.0,0.0))

	_box("PorchFloor", base + Vector3(0.0,0.48,-3.30), Vector3(5.4,0.22,1.5), WOOD_LIGHT)
	for x_offset: float in [-2.35,2.35]:
		_cyl("PorchPost", base + Vector3(x_offset,1.62,-3.55), 0.10, 2.55, WOOD_DARK, 8)
	_gable_roof("PorchRoof", base + Vector3(0.0,2.82,-3.45), 5.9, 2.1, 0.75, TERRACOTTA_DARK)
	for x_offset: float in [-2.2,2.2]:
		_cyl("PorchRailPost", base + Vector3(x_offset,0.92,-3.92), 0.05, 1.0, WOOD_DARK, 7)
	for y_value: float in [0.76,1.08]:
		_cyl("PorchRail", base + Vector3(0.0,y_value,-3.92), 0.045, 4.4, WOOD, 7, Vector3(0.0,0.0,90.0))
	_box("BenchSeat", base + Vector3(1.45,0.72,-3.48), Vector3(1.5,0.14,0.50), WOOD_LIGHT)
	_box("BenchBack", base + Vector3(1.45,1.07,-3.25), Vector3(1.5,0.60,0.10), WOOD, Vector3(-8.0,0.0,0.0))
	for step_index: int in range(3):
		_box("Step", base + Vector3(0.0,0.10+float(step_index)*0.10,-4.20-float(step_index)*0.27), Vector3(1.8-float(step_index)*0.12,0.16,0.48), WOOD_LIGHT)

	for pot_x: float in [-2.8,2.8]:
		_cyl("ClayPot", base + Vector3(pot_x,0.30,-3.55), 0.28, 0.48, Color("b56645"), 10)
		for angle_value: float in [0.0,90.0,180.0,270.0]:
			_leaf_blade("PotLeaf", base + Vector3(pot_x,0.55,-3.55), 0.65, 0.16, LEAF_LIGHT, angle_value)

func _build_garden() -> void:
	var beds: Array[Vector3] = [Vector3(-2.6,0.10,6.2),Vector3(-1.5,0.10,9.0)]
	for bed_index: int in range(beds.size()):
		var center_value: Vector3 = beds[bed_index]
		_box("GardenBed", center_value, Vector3(3.6,0.20,1.7), SOIL, Vector3(0.0,-8.0+float(bed_index)*15.0,0.0))
		for row_index: int in range(2):
			for plant_index: int in range(6):
				var px: float = center_value.x - 1.35 + float(plant_index)*0.54
				var pz: float = center_value.z - 0.36 + float(row_index)*0.72
				for angle_value: float in [0.0,72.0,144.0,216.0,288.0]:
					_leaf_blade("GardenLeaf",Vector3(px,0.23,pz),0.48,0.13,LEAF_LIGHT if bed_index==0 else LEAF,angle_value,-62.0)

	var fence_points: Array[Vector3] = [
		Vector3(-4.7,0.0,5.0),Vector3(-4.6,0.0,7.0),Vector3(-4.5,0.0,9.0),Vector3(-4.2,0.0,11.0),
		Vector3(-2.2,0.0,11.7),Vector3(0.0,0.0,11.5),Vector3(1.2,0.0,10.1)
	]
	for point_value: Vector3 in fence_points:
		_cyl("BambooFencePost",point_value+Vector3(0.0,0.62,0.0),0.065,1.25,BAMBOO,7)
	for index: int in range(fence_points.size()-1):
		var a: Vector3 = fence_points[index]+Vector3(0.0,0.72,0.0)
		var b: Vector3 = fence_points[index+1]+Vector3(0.0,0.72,0.0)
		var middle: Vector3 = (a+b)*0.5
		var length_value: float = a.distance_to(b)
		var rail: MeshInstance3D = _cyl("BambooRail",middle,0.045,length_value,BAMBOO,7)
		rail.rotation_degrees = Vector3(90.0,rad_to_deg(atan2(b.x-a.x,b.z-a.z)),0.0)

func _build_bridge() -> void:
	var center_x: float = 3.7
	for index: int in range(10):
		var z_value: float = -7.6 + float(index)*0.55
		var y_value: float = 0.38 + sin(float(index)/9.0*PI)*0.34
		_box("BridgePlank",Vector3(center_x,y_value,z_value),Vector3(3.4,0.14,0.48),WOOD_LIGHT,Vector3(0.0,2.0*sin(float(index)),0.0))
	for x_value: float in [2.05,5.35]:
		for z_value: float in [-7.5,-5.1,-2.8]:
			_cyl("BridgePost",Vector3(x_value,1.08,z_value),0.09,1.55,WOOD_DARK,8)
		for rail_index: int in range(2):
			var start_z: float = -7.45 + float(rail_index)*2.35
			var rail: MeshInstance3D = _cyl("BridgeRail",Vector3(x_value,1.48,start_z+1.18),0.07,2.4,WOOD,7,Vector3(90.0,0.0,0.0))
			rail.rotation_degrees.z = -4.0 if rail_index == 0 else 4.0

func _rice_clump(pos: Vector3, scale_value: float = 1.0) -> void:
	for angle_value: float in [0.0,45.0,90.0,135.0,180.0,225.0,270.0,315.0]:
		_leaf_blade("RiceLeaf",pos,0.52*scale_value,0.055*scale_value,Color("74ad4f"),angle_value,-72.0)

func _build_rice_fields() -> void:
	var field_centers: Array[Vector3] = [Vector3(9.0,0.0,6.7),Vector3(14.6,0.0,7.1),Vector3(11.8,0.0,11.3)]
	for field_index: int in range(field_centers.size()):
		var center_value: Vector3 = field_centers[field_index]
		_box("PaddyWater",center_value+Vector3(0.0,-0.03,0.0),Vector3(4.7,0.08,3.5),Color("86b8a0"),Vector3(0.0,float(field_index-1)*3.0,0.0))
		for row_index: int in range(4):
			for col_index: int in range(6):
				_rice_clump(center_value+Vector3(-1.75+float(col_index)*0.70,0.18,-1.05+float(row_index)*0.70),0.9)
		for side: float in [-1.0,1.0]:
			_box("PaddyBund",center_value+Vector3(side*2.45,0.10,0.0),Vector3(0.22,0.24,3.8),SOIL)
			_box("PaddyBund",center_value+Vector3(0.0,0.10,side*1.85),Vector3(5.1,0.24,0.22),SOIL)

func _tree(pos: Vector3, scale_value: float, tint: Color = LEAF) -> void:
	_cyl("TreeTrunk",pos+Vector3(0.0,1.65*scale_value,0.0),0.25*scale_value,3.3*scale_value,WOOD_DARK,8,Vector3(0.0,0.0,3.0))
	var crown_data: Array[Dictionary] = [
		{"o":Vector3(0.0,3.65,0.0),"r":1.25,"s":Vector3(1.2,0.85,1.0)},
		{"o":Vector3(-0.85,3.40,0.10),"r":0.88,"s":Vector3(1.05,0.80,0.95)},
		{"o":Vector3(0.82,3.42,-0.12),"r":0.92,"s":Vector3(0.95,0.82,1.0)},
		{"o":Vector3(-0.18,4.24,-0.08),"r":0.78,"s":Vector3(1.0,0.78,0.92)}
	]
	for index: int in range(crown_data.size()):
		var data: Dictionary = crown_data[index]
		var shade: Color = tint.lightened(0.06*float(index%2)) if index%2==0 else tint.darkened(0.05)
		_sphere("TreeCrown",pos+(data["o"] as Vector3)*scale_value,float(data["r"])*scale_value,shade,data["s"] as Vector3)

func _banana(pos: Vector3, scale_value: float) -> void:
	for offset: Vector3 in [Vector3(-0.20,0.0,0.0),Vector3(0.18,0.0,0.16),Vector3(0.0,0.0,-0.18)]:
		_cyl("BananaStem",pos+offset+Vector3(0.0,0.85*scale_value,0.0),0.09*scale_value,1.7*scale_value,Color("7f9b50"),7)
	for angle_value: float in [0.0,60.0,120.0,180.0,240.0,300.0]:
		_leaf_blade("BananaLeaf",pos+Vector3(0.0,1.75*scale_value,0.0),1.55*scale_value,0.55*scale_value,Color("69a754"),angle_value,-18.0)

func _grass_clump(pos: Vector3, scale_value: float, tint: Color) -> void:
	for angle_value: float in [0.0,60.0,120.0,180.0,240.0,300.0]:
		_leaf_blade("Grass",pos,0.38*scale_value,0.065*scale_value,tint,angle_value,-74.0)

func _build_vegetation() -> void:
	for tree_data: Dictionary in [
		{"p":Vector3(-16.0,0.0,8.8),"s":1.25,"c":Color("4c7d45")},
		{"p":Vector3(-13.5,0.0,12.0),"s":0.95,"c":Color("56884b")},
		{"p":Vector3(19.0,0.0,11.8),"s":1.05,"c":Color("4f8047")},
		{"p":Vector3(18.5,0.0,2.5),"s":0.86,"c":Color("5a8c4d")},
		{"p":Vector3(-20.0,0.0,-1.8),"s":1.0,"c":Color("527f48")}
	]:
		_tree(tree_data["p"] as Vector3,float(tree_data["s"]),tree_data["c"] as Color)
	for banana_pos: Vector3 in [Vector3(-13.0,0.0,5.8),Vector3(-1.0,0.0,12.0),Vector3(17.0,0.0,5.5)]:
		_banana(banana_pos,0.95)
	for x_value: float in [-18.0,-15.5,-12.0,-5.0,-1.0,7.5,11.0,15.5,19.0]:
		_grass_clump(Vector3(x_value,0.05,-3.4+sin(x_value*0.6)*0.3),0.9,GRASS_DARK)
	for index: int in range(28):
		var px: float = -18.0 + float((index*7)%37)
		var pz: float = -1.0 + float((index*11)%24)*0.55
		if Vector2(px+8.0,pz-5.0).length() < 4.5:
			continue
		_grass_clump(Vector3(px,0.03,pz),0.55+float(index%4)*0.07,GRASS_LIGHT if index%3==0 else GRASS_DARK)

func _build_story_props() -> void:
	# laundry line beside the house
	for x_value: float in [-12.2,-9.5]:
		_cyl("LaundryPost",Vector3(x_value,1.15,10.0),0.055,2.3,WOOD_DARK,7)
	_cyl("LaundryLine",Vector3(-10.85,2.10,10.0),0.018,2.7,Color("d7c9ae"),6,Vector3(0.0,0.0,90.0))
	_box("LaundryClothA",Vector3(-11.5,1.70,9.98),Vector3(0.85,0.72,0.035),Color("e9c56e"),Vector3(0.0,0.0,3.0))
	_box("LaundryClothB",Vector3(-10.2,1.72,9.98),Vector3(0.75,0.68,0.035),Color("d98576"),Vector3(0.0,0.0,-4.0))

	# baskets and crates near porch
	_cyl("Basket",Vector3(-5.3,0.30,1.3),0.34,0.48,Color("b18452"),12)
	_box("Crate",Vector3(-4.6,0.34,1.4),Vector3(0.72,0.62,0.72),WOOD_LIGHT,Vector3(0.0,12.0,0.0))
	for flower_data: Dictionary in [
		{"p":Vector3(-12.0,0.0,1.0),"c":Color("ef9dad")},
		{"p":Vector3(-3.8,0.0,3.3),"c":Color("f0ce65")},
		{"p":Vector3(0.8,0.0,5.0),"c":Color("d8a7ea")},
		{"p":Vector3(6.0,0.0,-2.8),"c":Color("f09c73")}
	]:
		var fp: Vector3 = flower_data["p"] as Vector3
		for offset: Vector3 in [Vector3(-0.18,0.0,0.0),Vector3(0.14,0.0,0.12),Vector3(0.04,0.0,-0.18)]:
			_cyl("FlowerStem",fp+offset+Vector3(0.0,0.18,0.0),0.018,0.36,LEAF_DARK,5)
			_sphere("FlowerHead",fp+offset+Vector3(0.0,0.40,0.0),0.075,flower_data["c"] as Color,Vector3(1.2,0.55,1.2))

func _build_camera() -> void:
	var camera: Camera3D = Camera3D.new()
	camera.position = Vector3(25.0, 18.5, 27.0)
	camera.fov = 31.0
	camera.near = 0.1
	camera.far = 120.0
	camera.current = true
	add_child(camera)
	camera.look_at(Vector3(0.5,1.0,2.2), Vector3.UP)

func _capture_preview() -> void:
	for _frame: int in range(12):
		await get_tree().process_frame
	var image: Image = get_viewport().get_texture().get_image()
	var output_path: String = ProjectSettings.globalize_path("res://hero_preview.png")
	var result: Error = image.save_png(output_path)
	print("[HeroPreview] saved=", output_path, " result=", result)
	await get_tree().process_frame
	get_tree().quit()
