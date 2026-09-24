extends Node3D

signal day_changed(day: int)
signal harvest_changed(total: int)

const COLS: int = 5
const ROWS: int = 4
const SPACING: float = 1.6
const GRID_ORIGIN: Vector3 = Vector3(4.8, 0.12, 7.7)
const MAX_GROWTH: int = 3

var day: int = 1
var chili_harvested: int = 0
var tiles: Array[Dictionary] = []
var highlight: Node3D

func _ready() -> void:
	add_to_group("farm_manager")
	_build_grid()
	_build_highlight()

func _process(_delta: float) -> void:
	_update_highlight()

func _mat(color: Color) -> StandardMaterial3D:
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 0.95
	return material

func _soil_mesh(color: Color) -> MeshInstance3D:
	var mesh_instance: MeshInstance3D = MeshInstance3D.new()
	var mesh: CylinderMesh = CylinderMesh.new()
	mesh.top_radius = 0.70
	mesh.bottom_radius = 0.74
	mesh.height = 0.11
	mesh.radial_segments = 8
	mesh_instance.mesh = mesh
	mesh_instance.scale = Vector3(1.0, 1.0, 1.0)
	mesh_instance.material_override = _mat(color)
	return mesh_instance

func _box_mesh(size: Vector3, color: Color) -> MeshInstance3D:
	var mesh_instance: MeshInstance3D = MeshInstance3D.new()
	var mesh: BoxMesh = BoxMesh.new()
	mesh.size = size
	mesh_instance.mesh = mesh
	mesh_instance.material_override = _mat(color)
	return mesh_instance

func _stem_mesh(height_value: float, radius_value: float, color: Color) -> MeshInstance3D:
	var mesh_instance: MeshInstance3D = MeshInstance3D.new()
	var mesh: CylinderMesh = CylinderMesh.new()
	mesh.top_radius = radius_value * 0.85
	mesh.bottom_radius = radius_value
	mesh.height = height_value
	mesh.radial_segments = 7
	mesh_instance.mesh = mesh
	mesh_instance.material_override = _mat(color)
	return mesh_instance

func _leaf_mesh(length_value: float, width_value: float, color: Color) -> MeshInstance3D:
	var vertices: PackedVector3Array = PackedVector3Array([
		Vector3(-width_value * 0.5, 0.0, 0.0),
		Vector3(width_value * 0.5, 0.0, 0.0),
		Vector3(0.0, 0.05, length_value),
		Vector3(-width_value * 0.5, 0.0, 0.0),
		Vector3(0.0, 0.05, length_value),
		Vector3(0.0, -0.02, length_value * 0.50)
	])
	var surface: SurfaceTool = SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for vertex: Vector3 in vertices:
		surface.add_vertex(vertex)
	surface.generate_normals()
	var mesh: ArrayMesh = surface.commit()
	var mesh_instance: MeshInstance3D = MeshInstance3D.new()
	mesh_instance.mesh = mesh
	mesh_instance.material_override = _mat(color)
	return mesh_instance

func _fruit_mesh(color: Color) -> MeshInstance3D:
	var fruit: MeshInstance3D = MeshInstance3D.new()
	var sphere: SphereMesh = SphereMesh.new()
	sphere.radius = 0.075
	sphere.height = 0.20
	sphere.radial_segments = 8
	sphere.rings = 4
	fruit.mesh = sphere
	fruit.scale = Vector3(0.75, 1.15, 0.75)
	fruit.material_override = _mat(color)
	return fruit

func _build_grid() -> void:
	for row: int in range(ROWS):
		for col: int in range(COLS):
			var root: Node3D = Node3D.new()
			root.name = "FarmTile_%d_%d" % [col, row]
			root.position = GRID_ORIGIN + Vector3(float(col) * SPACING, 0.0, float(row) * SPACING)
			add_child(root)
			var soil: MeshInstance3D = _soil_mesh(Color("98714f"))
			root.add_child(soil)
			var plant_root: Node3D = Node3D.new()
			plant_root.name = "Plant"
			plant_root.position.y = 0.08
			root.add_child(plant_root)
			tiles.append({
				"root": root,
				"soil": soil,
				"plant": plant_root,
				"tilled": false,
				"seed": "",
				"growth": 0,
				"watered": false,
				"ready": false
			})

func _build_highlight() -> void:
	highlight = Node3D.new()
	highlight.name = "FarmTarget"
	add_child(highlight)
	var yellow: Color = Color("f5cf57")
	var edge: float = 1.42
	var thick: float = 0.055
	var bar_data: Array[Array] = [
		[Vector3(0.0, 0.0, -edge * 0.5), Vector3(edge, 0.025, thick)],
		[Vector3(0.0, 0.0, edge * 0.5), Vector3(edge, 0.025, thick)],
		[Vector3(-edge * 0.5, 0.0, 0.0), Vector3(thick, 0.025, edge)],
		[Vector3(edge * 0.5, 0.0, 0.0), Vector3(thick, 0.025, edge)]
	]
	for data: Array in bar_data:
		var bar_position: Vector3 = data[0]
		var bar_size: Vector3 = data[1]
		var bar: MeshInstance3D = _box_mesh(bar_size, yellow)
		bar.position = bar_position
		highlight.add_child(bar)
	highlight.visible = false

func _update_highlight() -> void:
	var players: Array[Node] = get_tree().get_nodes_in_group("player")
	if players.is_empty():
		highlight.visible = false
		return
	var player: Node = players[0]
	var target: Vector3 = player.global_position + Vector3(player.get("facing")) * 1.55
	var index: int = _nearest_tile_index(target)
	if index < 0:
		highlight.visible = false
		return
	var root: Node3D = tiles[index]["root"]
	highlight.position = root.position + Vector3(0.0, 0.17, 0.0)
	highlight.visible = true

func _nearest_tile_index(world_pos: Vector3) -> int:
	var best_index: int = -1
	var best_distance: float = 999.0
	var point: Vector2 = Vector2(world_pos.x, world_pos.z)
	for index: int in range(tiles.size()):
		var root: Node3D = tiles[index]["root"]
		var tile_point: Vector2 = Vector2(root.global_position.x, root.global_position.z)
		var distance: float = point.distance_to(tile_point)
		if distance < best_distance:
			best_distance = distance
			best_index = index
	if best_distance <= 1.0:
		return best_index
	return -1

func use_tool(world_pos: Vector3, tool: String) -> Dictionary:
	var index: int = _nearest_tile_index(world_pos)
	if index < 0:
		return {"ok": false, "message": "Arahkan ke petak kebun."}
	var tile: Dictionary = tiles[index]
	match tool:
		"hoe":
			if tile["seed"] != "":
				return {"ok": false, "message": "Petak ini sudah ditanami."}
			if tile["tilled"]:
				return {"ok": false, "message": "Tanah sudah dicangkul."}
			if not _spend_stamina(5.0):
				return {"ok": false, "message": "Stamina tidak cukup untuk mencangkul. Pulang dan tidur dulu."}
			tile["tilled"] = true
			_refresh_tile(tile)
			return {"ok": true, "message": "Tanah dicangkul. -5 stamina."}
		"seed":
			if not tile["tilled"]:
				return {"ok": false, "message": "Cangkul tanah terlebih dahulu."}
			if tile["seed"] != "":
				return {"ok": false, "message": "Sudah ada tanaman di sini."}
			if not _spend_stamina(2.0):
				return {"ok": false, "message": "Stamina tidak cukup untuk menanam."}
			tile["seed"] = "chili"
			tile["growth"] = 0
			tile["watered"] = false
			tile["ready"] = false
			_refresh_tile(tile)
			return {"ok": true, "message": "Benih cabai ditanam. -2 stamina."}
		"water":
			if tile["seed"] == "":
				return {"ok": false, "message": "Belum ada tanaman untuk disiram."}
			if tile["ready"]:
				return {"ok": false, "message": "Cabai sudah siap dipanen."}
			if tile["watered"]:
				return {"ok": false, "message": "Tanaman sudah disiram hari ini."}
			if not _spend_stamina(3.0):
				return {"ok": false, "message": "Stamina tidak cukup untuk menyiram."}
			tile["watered"] = true
			_refresh_tile(tile)
			return {"ok": true, "message": "Tanaman disiram. -3 stamina."}
		"hand":
			if not tile["ready"]:
				return {"ok": false, "message": "Belum ada hasil panen."}
			if not _spend_stamina(2.0):
				return {"ok": false, "message": "Stamina tidak cukup untuk memanen."}
			chili_harvested += 1
			tile["seed"] = ""
			tile["growth"] = 0
			tile["watered"] = false
			tile["ready"] = false
			tile["tilled"] = true
			_refresh_tile(tile)
			harvest_changed.emit(chili_harvested)
			return {"ok": true, "message": "Cabai dipanen! Total: %d. -2 stamina." % chili_harvested}
	return {"ok": false, "message": "Alat tidak dikenal."}

func next_day() -> Dictionary:
	day += 1
	var grew: int = 0
	for tile: Dictionary in tiles:
		if tile["seed"] != "" and not tile["ready"]:
			if tile["watered"]:
				tile["growth"] = mini(int(tile["growth"]) + 1, MAX_GROWTH)
				grew += 1
				if int(tile["growth"]) >= MAX_GROWTH:
					tile["ready"] = true
			tile["watered"] = false
			_refresh_tile(tile)
	day_changed.emit(day)
	if grew > 0:
		return {"message": "Hari %d dimulai. %d tanaman bertumbuh." % [day, grew]}
	return {"message": "Hari %d dimulai. Tanaman yang tidak disiram belum tumbuh." % day}

func water_all_planted() -> int:
	var watered_count: int = 0
	for tile: Dictionary in tiles:
		if tile["seed"] != "" and not tile["ready"]:
			tile["watered"] = true
			watered_count += 1
			_refresh_tile(tile)
	return watered_count

func get_status_text() -> String:
	return "Hari %d  •  Cabai %d" % [day, chili_harvested]

func _spend_stamina(cost: float) -> bool:
	var stats_nodes: Array[Node] = get_tree().get_nodes_in_group("player_stats")
	if stats_nodes.is_empty():
		return true
	var stats: Node = stats_nodes[0]
	if not stats.has_method("spend_stamina"):
		return true
	var result: Variant = stats.call("spend_stamina", cost)
	return bool(result)

func _refresh_tile(tile: Dictionary) -> void:
	var soil: MeshInstance3D = tile["soil"]
	if tile["watered"]:
		soil.material_override = _mat(Color("493d36"))
	elif tile["tilled"]:
		soil.material_override = _mat(Color("654733"))
	else:
		soil.material_override = _mat(Color("98714f"))

	var plant_root: Node3D = tile["plant"]
	for child: Node in plant_root.get_children():
		child.queue_free()
	if tile["seed"] == "":
		return

	var stage: int = int(tile["growth"])
	var height_value: float = 0.25 + float(stage) * 0.18
	var stem: MeshInstance3D = _stem_mesh(height_value, 0.045 + float(stage) * 0.008, Color("418b45"))
	stem.position.y = height_value * 0.5
	plant_root.add_child(stem)

	var leaf_count: int = 2 + stage * 2
	var leaf_length: float = 0.26 + float(stage) * 0.07
	for leaf_index: int in range(leaf_count):
		var leaf: MeshInstance3D = _leaf_mesh(leaf_length, 0.15 + float(stage) * 0.025, Color("55a052").lightened(float(leaf_index % 2) * 0.05))
		leaf.position = Vector3(0.0, height_value * (0.45 + 0.08 * float(leaf_index % 3)), 0.0)
		leaf.rotation_degrees = Vector3(-58.0 + float(stage) * 4.0, float(leaf_index) * (360.0 / float(leaf_count)), 0.0)
		plant_root.add_child(leaf)

	if stage >= 2:
		var crown: MeshInstance3D = _leaf_mesh(0.38 + float(stage) * 0.04, 0.22, Color("4c984c"))
		crown.position.y = height_value * 0.92
		crown.rotation_degrees = Vector3(-70.0, 35.0, 0.0)
		plant_root.add_child(crown)

	if tile["ready"]:
		var fruit_positions: Array[Vector3] = [
			Vector3(-0.17, height_value + 0.05, 0.12),
			Vector3(0.19, height_value - 0.01, -0.10),
			Vector3(0.05, height_value + 0.10, 0.20)
		]
		for fruit_position: Vector3 in fruit_positions:
			var fruit: MeshInstance3D = _fruit_mesh(Color("d73b31"))
			fruit.position = fruit_position
			plant_root.add_child(fruit)
