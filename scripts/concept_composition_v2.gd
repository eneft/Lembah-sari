extends Node3D

func _ready() -> void:
	_build_home_path()
	_build_foreground_frames()
	_build_hedges()
	_build_village_clusters()

func _material(color_value: Color) -> StandardMaterial3D:
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = color_value
	material.roughness = 0.97
	return material

func _mesh_instance(node_name: String, mesh: Mesh, color_value: Color, position_value: Vector3) -> MeshInstance3D:
	var instance: MeshInstance3D = MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.material_override = _material(color_value)
	instance.position = position_value
	add_child(instance)
	return instance

func _ribbon(node_name: String, points: Array[Vector3], width_value: float, color_value: Color) -> void:
	var surface: SurfaceTool = SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for index: int in range(points.size() - 1):
		var p0: Vector3 = points[index]
		var p1: Vector3 = points[index + 1]
		var direction: Vector3 = p1 - p0
		direction.y = 0.0
		if direction.length_squared() < 0.001:
			continue
		direction = direction.normalized()
		var side: Vector3 = Vector3(-direction.z, 0.0, direction.x) * width_value * 0.5
		var a: Vector3 = p0 - side
		var b: Vector3 = p0 + side
		var c: Vector3 = p1 + side
		var d: Vector3 = p1 - side
		for vertex: Vector3 in [a, b, c, a, c, d]:
			surface.add_vertex(vertex)
	surface.generate_normals()
	var mesh: ArrayMesh = surface.commit()
	_mesh_instance(node_name, mesh, color_value, Vector3.ZERO)

func _cylinder(position_value: Vector3, radius_value: float, height_value: float, color_value: Color, sides: int = 7) -> MeshInstance3D:
	var mesh: CylinderMesh = CylinderMesh.new()
	mesh.top_radius = radius_value * 0.90
	mesh.bottom_radius = radius_value
	mesh.height = height_value
	mesh.radial_segments = sides
	mesh.rings = 1
	return _mesh_instance("OrganicTrunk", mesh, color_value, position_value)

func _sphere(position_value: Vector3, radius_value: float, color_value: Color, scale_value: Vector3 = Vector3.ONE) -> MeshInstance3D:
	var mesh: SphereMesh = SphereMesh.new()
	mesh.radius = radius_value
	mesh.height = radius_value * 2.0
	mesh.radial_segments = 9
	mesh.rings = 5
	var instance: MeshInstance3D = _mesh_instance("OrganicCrown", mesh, color_value, position_value)
	instance.scale = scale_value
	return instance

func _tree(position_value: Vector3, scale_value: float, foliage: Color) -> void:
	_cylinder(position_value + Vector3(0.0, 1.45 * scale_value, 0.0), 0.28 * scale_value, 2.9 * scale_value, Color("725039"), 7)
	_sphere(position_value + Vector3(0.0, 3.25 * scale_value, 0.0), 1.25 * scale_value, foliage, Vector3(1.15,0.88,1.05))
	_sphere(position_value + Vector3(-0.75 * scale_value, 3.0 * scale_value, 0.12), 0.82 * scale_value, foliage.lightened(0.06), Vector3(1.0,0.84,0.95))
	_sphere(position_value + Vector3(0.72 * scale_value, 3.02 * scale_value, -0.10), 0.88 * scale_value, foliage.darkened(0.04), Vector3(0.96,0.86,1.0))

func _bush(position_value: Vector3, scale_value: float, color_value: Color) -> void:
	_sphere(position_value + Vector3(0.0, 0.48 * scale_value, 0.0), 0.62 * scale_value, color_value, Vector3(1.28,0.70,1.0))
	_sphere(position_value + Vector3(0.46 * scale_value, 0.43 * scale_value, 0.10), 0.44 * scale_value, color_value.lightened(0.05), Vector3.ONE)
	_sphere(position_value + Vector3(-0.42 * scale_value, 0.40 * scale_value, -0.08), 0.40 * scale_value, color_value.darkened(0.04), Vector3.ONE)

func _build_home_path() -> void:
	var home_path: Array[Vector3] = [
		Vector3(15.7,0.12,9.0), Vector3(14.0,0.12,8.2), Vector3(12.1,0.12,7.5),
		Vector3(10.0,0.12,6.5), Vector3(7.8,0.12,5.8), Vector3(5.5,0.12,4.9), Vector3(3.1,0.12,3.4)
	]
	_ribbon("HomeFootPath", home_path, 1.30, Color("b08c61"))
	var river_path: Array[Vector3] = [
		Vector3(3.1,0.13,3.4), Vector3(2.7,0.13,0.5), Vector3(2.3,0.13,-2.6), Vector3(2.1,0.13,-5.4), Vector3(2.0,0.13,-7.2)
	]
	_ribbon("BridgeFootPath", river_path, 1.15, Color("ad8a60"))

func _build_foreground_frames() -> void:
	_tree(Vector3(22.0,0.0,17.2), 1.05, Color("4c7f45"))
	_tree(Vector3(18.8,0.0,19.0), 0.90, Color("56884a"))
	_tree(Vector3(-21.5,0.0,17.4), 1.0, Color("527f47"))
	_tree(Vector3(-23.0,0.0,10.2), 0.88, Color("4f8248"))
	_tree(Vector3(22.5,0.0,7.0), 0.92, Color("557f48"))
	_bush(Vector3(20.2,0.0,15.4), 1.15, Color("4f8248"))
	_bush(Vector3(16.7,0.0,18.4), 0.95, Color("5a8b4e"))
	_bush(Vector3(-19.8,0.0,14.4), 1.05, Color("4e8248"))

func _build_hedges() -> void:
	for index: int in range(8):
		var x_value: float = -19.0 + float(index) * 2.0
		_bush(Vector3(x_value,0.0,7.0 + sin(float(index)) * 0.3), 0.62, Color("537f49"))
	for index: int in range(6):
		var z_value: float = 8.0 + float(index) * 1.7
		_bush(Vector3(21.8,0.0,z_value), 0.66, Color("56864c"))

func _build_village_clusters() -> void:
	for position_value: Vector3 in [Vector3(-16.0,0.0,10.0),Vector3(-12.5,0.0,11.2),Vector3(-8.5,0.0,9.6),Vector3(-4.5,0.0,10.8)]:
		_bush(position_value,0.70,Color("5b8b4f"))
	for position_value: Vector3 in [Vector3(8.5,0.0,8.2),Vector3(10.5,0.0,8.6),Vector3(17.8,0.0,7.6)]:
		_bush(position_value,0.60,Color("648f50"))
