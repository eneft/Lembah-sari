extends Node3D

func _ready() -> void:
	_build_world()

func _mat(color: Color, roughness := 0.9) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = roughness
	return m

func _box(name: String, pos: Vector3, size: Vector3, color: Color, collision := false) -> Node3D:
	var root: Node3D
	if collision:
		var body := StaticBody3D.new()
		root = body
		var shape := CollisionShape3D.new()
		var box_shape := BoxShape3D.new()
		box_shape.size = size
		shape.shape = box_shape
		body.add_child(shape)
	else:
		root = Node3D.new()

	root.name = name
	root.position = pos
	add_child(root)

	var mesh_i := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	mesh_i.mesh = mesh
	mesh_i.material_override = _mat(color)
	root.add_child(mesh_i)
	return root

func _cylinder(name: String, pos: Vector3, radius: float, height: float, color: Color, collision := false) -> Node3D:
	var root: Node3D
	if collision:
		var body := StaticBody3D.new()
		root = body
		var shape := CollisionShape3D.new()
		var cyl_shape := CylinderShape3D.new()
		cyl_shape.radius = radius
		cyl_shape.height = height
		shape.shape = cyl_shape
		body.add_child(shape)
	else:
		root = Node3D.new()
	root.name = name
	root.position = pos
	add_child(root)
	var mesh_i := MeshInstance3D.new()
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh_i.mesh = mesh
	mesh_i.material_override = _mat(color)
	root.add_child(mesh_i)
	return root

func _tree(pos: Vector3, scale_mul := 1.0) -> void:
	_cylinder("TreeTrunk", pos + Vector3(0, 1.0 * scale_mul, 0), 0.28 * scale_mul, 2.0 * scale_mul, Color("7b5536"), true)
	var crown := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 1.15 * scale_mul
	sphere.height = 2.0 * scale_mul
	crown.mesh = sphere
	crown.material_override = _mat(Color("4f9c4b"))
	crown.position = pos + Vector3(0, 2.45 * scale_mul, 0)
	add_child(crown)

func _build_world() -> void:
	# Ground and roads
	_box("Ground", Vector3(0, -0.15, 0), Vector3(52, 0.3, 42), Color("7fa85d"), true)
	_box("VillageRoad", Vector3(0, 0.04, 1.5), Vector3(44, 0.08, 4.0), Color("c7aa78"), false)
	_box("SouthPath", Vector3(2, 0.05, 10), Vector3(3.0, 0.09, 14.0), Color("c7aa78"), false)

	# River and bridge
	_box("River", Vector3(0, 0.03, -8.2), Vector3(52, 0.08, 5.2), Color("4fa8c8"), false)
	_box("Bridge", Vector3(2, 0.35, -8.2), Vector3(3.6, 0.55, 6.0), Color("a77248"), true)
	for x in [-20.0, -8.0, 12.0, 21.0]:
		_box("RiverRock", Vector3(x, 0.18, -8.2), Vector3(1.1, 0.35, 0.9), Color("8b8d88"), true)

	# Player farm
	_box("FarmPlot", Vector3(8.5, 0.02, 10.5), Vector3(14.0, 0.06, 11.0), Color("8c5e3c"), false)
	for row in range(4):
		_box("TilledRow%d" % row, Vector3(6.2 + row * 1.7, 0.08, 10.4), Vector3(1.15, 0.08, 7.7), Color("6c432d"), false)

	# House
	_box("HouseBody", Vector3(15.7, 1.55, 13.2), Vector3(6.0, 3.1, 5.0), Color("e9d0a2"), true)
	_box("HouseRoof", Vector3(15.7, 3.45, 13.2), Vector3(6.8, 0.55, 5.8), Color("9d4f3f"), true)
	_box("Door", Vector3(15.7, 1.15, 10.64), Vector3(1.25, 2.3, 0.12), Color("6c422a"), false)
	_box("Porch", Vector3(15.7, 0.25, 10.0), Vector3(4.0, 0.35, 1.3), Color("a8754d"), true)

	# Warung Bu Ratih
	_box("WarungBody", Vector3(-11.5, 1.35, 3.0), Vector3(6.0, 2.7, 4.3), Color("d7b06c"), true)
	_box("WarungRoof", Vector3(-11.5, 3.05, 3.0), Vector3(6.8, 0.45, 5.0), Color("7f3f31"), true)
	_box("WarungCounter", Vector3(-11.5, 1.0, 0.8), Vector3(3.8, 1.2, 0.55), Color("805d3f"), true)

	# Pak Wiryo rice field north
	_box("RiceField", Vector3(-4.0, 0.01, -14.6), Vector3(18.0, 0.04, 6.0), Color("7db766"), false)
	for i in range(8):
		_box("RiceLine%d" % i, Vector3(-11.0 + i * 2.0, 0.08, -14.6), Vector3(0.35, 0.14, 5.2), Color("4d9a48"), false)
	_box("IrrigationChannel", Vector3(6.2, 0.05, -14.6), Vector3(1.25, 0.09, 6.0), Color("5eb2d0"), false)
	_box("IrrigationGate", Vector3(6.2, 0.7, -11.8), Vector3(1.6, 1.4, 0.35), Color("8d6b48"), true)

	# Trees for visual framing
	for p in [Vector3(-20,0,11), Vector3(-18,0,15), Vector3(-5,0,14), Vector3(0,0,16), Vector3(21,0,7), Vector3(22,0,14), Vector3(-18,0,-14), Vector3(14,0,-15)]:
		_tree(p, 0.9)

	# Invisible world edges
	_box("NorthBoundary", Vector3(0, 1.5, -20.8), Vector3(52, 3, 0.5), Color(0,0,0,0), true).visible = false
	_box("SouthBoundary", Vector3(0, 1.5, 20.8), Vector3(52, 3, 0.5), Color(0,0,0,0), true).visible = false
	_box("WestBoundary", Vector3(-25.8, 1.5, 0), Vector3(0.5, 3, 42), Color(0,0,0,0), true).visible = false
	_box("EastBoundary", Vector3(25.8, 1.5, 0), Vector3(0.5, 3, 42), Color(0,0,0,0), true).visible = false
