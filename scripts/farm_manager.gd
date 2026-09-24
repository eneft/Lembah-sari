extends Node3D

signal day_changed(day: int)
signal harvest_changed(total: int)

const COLS := 5
const ROWS := 4
const SPACING := 1.6
const GRID_ORIGIN := Vector3(4.8, 0.12, 7.7)
const MAX_GROWTH := 3

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
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 0.95
	return material

func _mesh_box(size: Vector3, color: Color) -> MeshInstance3D:
	var mesh_instance := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	mesh_instance.mesh = mesh
	mesh_instance.material_override = _mat(color)
	return mesh_instance

func _build_grid() -> void:
	for row in range(ROWS):
		for col in range(COLS):
			var root := Node3D.new()
			root.name = "FarmTile_%d_%d" % [col, row]
			root.position = GRID_ORIGIN + Vector3(col * SPACING, 0.0, row * SPACING)
			add_child(root)

			var soil := _mesh_box(Vector3(1.35, 0.12, 1.35), Color("9d744f"))
			root.add_child(soil)

			var plant_root := Node3D.new()
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
	var yellow := Color("ffd95a")
	var edge := 1.42
	var thick := 0.07
	for data in [
		[Vector3(0, 0, -edge * 0.5), Vector3(edge, 0.04, thick)],
		[Vector3(0, 0, edge * 0.5), Vector3(edge, 0.04, thick)],
		[Vector3(-edge * 0.5, 0, 0), Vector3(thick, 0.04, edge)],
		[Vector3(edge * 0.5, 0, 0), Vector3(thick, 0.04, edge)]
	]:
		var bar := _mesh_box(data[1], yellow)
		bar.position = data[0]
		highlight.add_child(bar)
	highlight.visible = false

func _update_highlight() -> void:
	var players := get_tree().get_nodes_in_group("player")
	if players.is_empty():
		highlight.visible = false
		return
	var player = players[0]
	var target: Vector3 = player.global_position + player.facing * 1.55
	var index := _nearest_tile_index(target)
	if index < 0:
		highlight.visible = false
		return
	var root: Node3D = tiles[index]["root"]
	highlight.position = root.position + Vector3(0, 0.17, 0)
	highlight.visible = true

func _nearest_tile_index(world_pos: Vector3) -> int:
	var best_index := -1
	var best_distance := 999.0
	var point := Vector2(world_pos.x, world_pos.z)
	for i in range(tiles.size()):
		var root: Node3D = tiles[i]["root"]
		var tile_point := Vector2(root.global_position.x, root.global_position.z)
		var distance := point.distance_to(tile_point)
		if distance < best_distance:
			best_distance = distance
			best_index = i
	return best_index if best_distance <= 1.0 else -1

func use_tool(world_pos: Vector3, tool: String) -> Dictionary:
	var index := _nearest_tile_index(world_pos)
	if index < 0:
		return {"ok": false, "message": "Arahkan ke petak kebun."}

	var tile: Dictionary = tiles[index]
	match tool:
		"hoe":
			if tile["seed"] != "":
				return {"ok": false, "message": "Petak ini sudah ditanami."}
			if tile["tilled"]:
				return {"ok": false, "message": "Tanah sudah dicangkul."}
			tile["tilled"] = true
			_refresh_tile(tile)
			return {"ok": true, "message": "Tanah dicangkul."}
		"seed":
			if not tile["tilled"]:
				return {"ok": false, "message": "Cangkul tanah terlebih dahulu."}
			if tile["seed"] != "":
				return {"ok": false, "message": "Sudah ada tanaman di sini."}
			tile["seed"] = "chili"
			tile["growth"] = 0
			tile["watered"] = false
			tile["ready"] = false
			_refresh_tile(tile)
			return {"ok": true, "message": "Benih cabai ditanam."}
		"water":
			if tile["seed"] == "":
				return {"ok": false, "message": "Belum ada tanaman untuk disiram."}
			if tile["ready"]:
				return {"ok": false, "message": "Cabai sudah siap dipanen."}
			if tile["watered"]:
				return {"ok": false, "message": "Tanaman sudah disiram hari ini."}
			tile["watered"] = true
			_refresh_tile(tile)
			return {"ok": true, "message": "Tanaman disiram."}
		"hand":
			if not tile["ready"]:
				return {"ok": false, "message": "Belum ada hasil panen."}
			chili_harvested += 1
			tile["seed"] = ""
			tile["growth"] = 0
			tile["watered"] = false
			tile["ready"] = false
			tile["tilled"] = true
			_refresh_tile(tile)
			harvest_changed.emit(chili_harvested)
			return {"ok": true, "message": "Cabai dipanen! Total: %d" % chili_harvested}
	return {"ok": false, "message": "Alat tidak dikenal."}

func next_day() -> Dictionary:
	day += 1
	var grew := 0
	for tile in tiles:
		if tile["seed"] != "" and not tile["ready"]:
			if tile["watered"]:
				tile["growth"] = min(int(tile["growth"]) + 1, MAX_GROWTH)
				grew += 1
				if tile["growth"] >= MAX_GROWTH:
					tile["ready"] = true
			tile["watered"] = false
			_refresh_tile(tile)
	day_changed.emit(day)
	if grew > 0:
		return {"message": "Hari %d dimulai. %d tanaman bertumbuh." % [day, grew]}
	return {"message": "Hari %d dimulai. Tanaman yang tidak disiram belum tumbuh." % day}

func get_status_text() -> String:
	return "Hari %d  •  Cabai %d" % [day, chili_harvested]

func _refresh_tile(tile: Dictionary) -> void:
	var soil: MeshInstance3D = tile["soil"]
	if tile["watered"]:
		soil.material_override = _mat(Color("4d4038"))
	elif tile["tilled"]:
		soil.material_override = _mat(Color("674733"))
	else:
		soil.material_override = _mat(Color("9d744f"))

	var plant_root: Node3D = tile["plant"]
	for child in plant_root.get_children():
		child.queue_free()
	if tile["seed"] == "":
		return

	var stage: int = int(tile["growth"])
	var height := 0.20 + stage * 0.18
	var stem := _mesh_box(Vector3(0.10, height, 0.10), Color("3f8f46"))
	stem.position.y = height * 0.5
	plant_root.add_child(stem)

	var leaf_size := 0.22 + stage * 0.08
	var leaf_a := _mesh_box(Vector3(leaf_size, 0.07, 0.15), Color("55a955"))
	leaf_a.position = Vector3(-leaf_size * 0.35, height * 0.72, 0)
	plant_root.add_child(leaf_a)
	var leaf_b := _mesh_box(Vector3(0.15, 0.07, leaf_size), Color("62b55b"))
	leaf_b.position = Vector3(0, height * 0.85, leaf_size * 0.30)
	plant_root.add_child(leaf_b)

	if stage >= 2:
		var crown := _mesh_box(Vector3(0.48, 0.13, 0.48), Color("4f9f4e"))
		crown.position.y = height
		plant_root.add_child(crown)

	if tile["ready"]:
		for fruit_pos in [Vector3(-0.18, height + 0.05, 0.12), Vector3(0.20, height - 0.02, -0.10), Vector3(0.05, height + 0.10, 0.22)]:
			var fruit := MeshInstance3D.new()
			var sphere := SphereMesh.new()
			sphere.radius = 0.08
			sphere.height = 0.18
			fruit.mesh = sphere
			fruit.material_override = _mat(Color("d83b32"))
			fruit.position = fruit_pos
			plant_root.add_child(fruit)
