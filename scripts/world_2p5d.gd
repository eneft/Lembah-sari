extends Node3D

# Lembah Sari 2.5D proof of concept.
# Gameplay remains in a real 3D world, while hero scenery is rendered as
# illustrated Sprite3D assets facing one fixed orthographic camera.

const HOUSE_TEX: Texture2D = preload("res://assets/2p5d/house_main_render.png")
const TREE_TEX: Texture2D = preload("res://assets/2p5d/tree_tropical.svg")
const CROP_TEX: Texture2D = preload("res://assets/2p5d/crop_chili.svg")

func _ready() -> void:
	_build_ground()
	_build_path()
	_build_stream()
	_build_house()
	_build_trees()
	_build_farm_dressing()

func _mat(color_value: Color, roughness_value: float = 0.95) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color_value
	material.roughness = roughness_value
	return material

func _box_visual(name_value: String, pos: Vector3, size_value: Vector3, color_value: Color, yaw_degrees: float = 0.0) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size_value
	var node := MeshInstance3D.new()
	node.name = name_value
	node.mesh = mesh
	node.material_override = _mat(color_value)
	node.position = pos
	node.rotation_degrees.y = yaw_degrees
	add_child(node)
	return node

func _box_collision(name_value: String, pos: Vector3, size_value: Vector3) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.name = name_value
	body.position = pos
	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size_value
	collision.shape = shape
	body.add_child(collision)
	add_child(body)
	return body

func _sprite(name_value: String, texture_value: Texture2D, pos: Vector3, pixel_size_value: float) -> Sprite3D:
	var sprite := Sprite3D.new()
	sprite.name = name_value
	sprite.texture = texture_value
	sprite.position = pos
	sprite.pixel_size = pixel_size_value
	sprite.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	sprite.shaded = false
	sprite.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
	add_child(sprite)
	return sprite

func _build_ground() -> void:
	_box_visual("Meadow", Vector3(0.0, -0.22, 0.0), Vector3(46.0, 0.40, 38.0), Color("7ea765"))
	_box_collision("GroundCollision", Vector3(0.0, -0.18, 0.0), Vector3(46.0, 0.36, 38.0))
	_box_visual("MeadowShadeLeft", Vector3(-13.0, 0.015, 7.0), Vector3(14.0, 0.025, 9.0), Color("70965b"), -6.0)
	_box_visual("MeadowShadeBack", Vector3(8.0, 0.012, -11.0), Vector3(17.0, 0.024, 8.0), Color("88ad6d"), 4.0)
	_box_visual("HouseYard", Vector3(-6.0, 0.025, -1.0), Vector3(10.0, 0.05, 7.0), Color("8eaa68"), -3.0)

func _build_path() -> void:
	var path_color := Color("c8a271")
	var pieces: Array[Dictionary] = [
		{"p": Vector3(-14.0, 0.045, 7.2), "s": Vector3(9.0, 0.05, 2.7), "r": -8.0},
		{"p": Vector3(-7.0, 0.045, 5.0), "s": Vector3(7.0, 0.05, 2.7), "r": -19.0},
		{"p": Vector3(-1.7, 0.045, 2.5), "s": Vector3(6.3, 0.05, 2.6), "r": -28.0},
		{"p": Vector3(3.6, 0.045, -0.3), "s": Vector3(6.5, 0.05, 2.5), "r": -24.0},
		{"p": Vector3(9.1, 0.045, -2.5), "s": Vector3(6.0, 0.05, 2.4), "r": -15.0}
	]
	for item: Dictionary in pieces:
		_box_visual("DirtPath", item["p"] as Vector3, item["s"] as Vector3, path_color, float(item["r"]))
	for index: int in range(4):
		var x_value := -4.3 + float(index) * 0.9
		_box_visual("StepStone", Vector3(x_value, 0.09, 1.1 + float(index) * 0.18), Vector3(0.68, 0.12, 0.52), Color("9a927e"), float(index * 13 - 18))

func _build_stream() -> void:
	_box_visual("StreamA", Vector3(12.2, -0.02, 4.0), Vector3(2.6, 0.08, 15.0), Color("68b6bd"), 9.0)
	_box_visual("StreamB", Vector3(10.6, -0.02, 12.3), Vector3(2.3, 0.08, 8.0), Color("75c2c5"), -7.0)
	_box_visual("BridgeDeck", Vector3(11.7, 0.20, 6.0), Vector3(4.0, 0.24, 1.5), Color("8b5c3b"), -10.0)
	for offset: float in [-1.55, -0.78, 0.0, 0.78, 1.55]:
		_box_visual("BridgePlank", Vector3(11.7 + offset * 0.18, 0.34, 6.0 + offset), Vector3(3.7, 0.08, 0.18), Color("b47b4d"), -10.0)

func _build_house() -> void:
	# The hero house is now a real Blender material render baked into a single
	# transparent sprite. Keep its gameplay footprint 3D and invisible.
	_sprite("HouseMain", HOUSE_TEX, Vector3(-6.2, 3.22, -2.0), 0.0102)
	_box_collision("HouseCollision", Vector3(-6.2, 1.55, -1.6), Vector3(6.3, 3.1, 3.8))

func _build_trees() -> void:
	var tree_data: Array[Dictionary] = [
		{"p": Vector3(-13.5, 2.45, -5.7), "s": 0.0120},
		{"p": Vector3(-10.4, 2.10, -8.0), "s": 0.0105},
		{"p": Vector3(2.0, 2.45, -9.0), "s": 0.0120},
		{"p": Vector3(7.2, 2.20, -7.2), "s": 0.0108},
		{"p": Vector3(15.0, 2.45, 0.2), "s": 0.0118},
		{"p": Vector3(-16.5, 2.20, 11.0), "s": 0.0108}
	]
	for item: Dictionary in tree_data:
		var pos := item["p"] as Vector3
		var size_value := float(item["s"])
		_sprite("TropicalTree", TREE_TEX, pos, size_value)
		_box_collision("TreeCollision", Vector3(pos.x, 0.9, pos.z), Vector3(1.15, 1.8, 1.15))

func _build_farm_dressing() -> void:
	for row: int in range(2):
		for col: int in range(4):
			var p := Vector3(5.4 + float(col) * 1.55, 0.82, 7.3 + float(row) * 1.55)
			_sprite("DecorativeChili", CROP_TEX, p, 0.0061)
	for index: int in range(6):
		var x_value := 4.4 + float(index) * 1.65
		_box_visual("FencePost", Vector3(x_value, 0.48, 10.9), Vector3(0.15, 0.96, 0.15), Color("9a6b43"))
	_box_visual("FenceRail", Vector3(8.5, 0.52, 10.9), Vector3(8.5, 0.14, 0.14), Color("b37b4a"))
