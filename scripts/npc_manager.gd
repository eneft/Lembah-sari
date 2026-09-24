extends Node3D

const TALK_DISTANCE: float = 2.4
const MOVE_SPEED: float = 2.2

var npcs: Array[Dictionary] = []
var spoken_once: Dictionary = {}

func _ready() -> void:
	add_to_group("npc_manager")
	_build_npcs()

func _process(delta: float) -> void:
	var hour: float = _get_hour()
	for npc: Dictionary in npcs:
		var root: Node3D = npc["root"] as Node3D
		var npc_id: String = str(npc["id"])
		var target: Vector3 = _schedule_target(npc_id, hour)
		var old_position: Vector3 = root.position
		root.position = root.position.move_toward(target, MOVE_SPEED * delta)
		var movement: Vector3 = root.position - old_position
		if movement.length_squared() > 0.0001:
			root.rotation.y = lerp_angle(root.rotation.y, atan2(movement.x, movement.z), minf(1.0, delta * 8.0))

func try_interact(player_position: Vector3, player_facing: Vector3) -> Dictionary:
	var best_npc: Dictionary = {}
	var best_distance: float = TALK_DISTANCE + 1.0
	var flat_facing: Vector3 = Vector3(player_facing.x, 0.0, player_facing.z).normalized()

	for npc: Dictionary in npcs:
		var root: Node3D = npc["root"] as Node3D
		var offset: Vector3 = root.global_position - player_position
		offset.y = 0.0
		var distance: float = offset.length()
		if distance > TALK_DISTANCE or distance >= best_distance:
			continue
		if distance > 0.05:
			var direction_to_npc: Vector3 = offset.normalized()
			if flat_facing.dot(direction_to_npc) < -0.15:
				continue
		best_npc = npc
		best_distance = distance

	if best_npc.is_empty():
		return {"ok": false}

	var npc_id: String = str(best_npc["id"])
	var display_name: String = str(best_npc["display_name"])
	var dialogue: String = _dialogue_for(npc_id)
	spoken_once[npc_id] = true
	return {"ok": true, "speaker": display_name, "text": dialogue}

func _build_npcs() -> void:
	npcs.append(_make_npc("pak_wiryo", "Pak Wiryo", Vector3(-4.0, 0.2, -14.0), Color("6f8f4f"), Color("c98f67")))
	npcs.append(_make_npc("bu_ratih", "Bu Ratih", Vector3(-11.0, 0.2, 1.3), Color("b35f66"), Color("d39a71")))
	npcs.append(_make_npc("laras", "Laras", Vector3(2.0, 0.2, -5.0), Color("6d78b8"), Color("d6a07b")))

func _make_npc(npc_id: String, display_name: String, start_position: Vector3, shirt_color: Color, skin_color: Color) -> Dictionary:
	var root: Node3D = Node3D.new()
	root.name = npc_id
	root.position = start_position
	add_child(root)

	_add_box_part(root, "Torso", Vector3(0.0, 1.03, 0.0), Vector3(0.74, 0.78, 0.44), shirt_color)
	_add_box_part(root, "Bottom", Vector3(0.0, 0.62, 0.0), Vector3(0.68, 0.34, 0.42), shirt_color.darkened(0.45))
	_add_box_part(root, "LeftArm", Vector3(-0.46, 1.02, 0.0), Vector3(0.17, 0.60, 0.18), skin_color, Vector3(0.0, 0.0, -7.0))
	_add_box_part(root, "RightArm", Vector3(0.46, 1.02, 0.0), Vector3(0.17, 0.60, 0.18), skin_color, Vector3(0.0, 0.0, 7.0))
	_add_capsule_part(root, "LeftLeg", Vector3(-0.17, 0.30, 0.0), 0.12, 0.58, skin_color.darkened(0.04))
	_add_capsule_part(root, "RightLeg", Vector3(0.17, 0.30, 0.0), 0.12, 0.58, skin_color.darkened(0.04))
	_add_box_part(root, "LeftSandal", Vector3(-0.17, 0.08, 0.08), Vector3(0.27, 0.13, 0.38), Color("4e392c"))
	_add_box_part(root, "RightSandal", Vector3(0.17, 0.08, 0.08), Vector3(0.27, 0.13, 0.38), Color("4e392c"))
	_add_sphere_part(root, "Head", Vector3(0.0, 1.69, 0.0), 0.34, skin_color, Vector3(1.0, 1.04, 1.0))

	match npc_id:
		"pak_wiryo":
			_add_sphere_part(root, "Hair", Vector3(0.0, 1.89, -0.02), 0.34, Color("4a443e"), Vector3(1.0, 0.5, 1.02))
			_add_cylinder_part(root, "FarmerHat", Vector3(0.0, 2.03, 0.0), 0.54, 0.10, Color("c4a363"))
			_add_cylinder_part(root, "HatTop", Vector3(0.0, 2.11, 0.0), 0.30, 0.18, Color("b89455"))
		"bu_ratih":
			_add_sphere_part(root, "Hair", Vector3(0.0, 1.88, -0.03), 0.36, Color("30251f"), Vector3(1.02, 0.55, 1.02))
			_add_sphere_part(root, "HairBun", Vector3(0.0, 1.91, -0.30), 0.18, Color("30251f"), Vector3.ONE)
			_add_box_part(root, "Apron", Vector3(0.0, 0.96, 0.24), Vector3(0.52, 0.66, 0.05), Color("ead6ae"))
		"laras":
			_add_sphere_part(root, "Hair", Vector3(0.0, 1.90, -0.02), 0.36, Color("2f241f"), Vector3(1.03, 0.60, 1.05))
			_add_box_part(root, "HairBack", Vector3(0.0, 1.58, -0.26), Vector3(0.48, 0.66, 0.18), Color("2f241f"))
			_add_box_part(root, "SlingBag", Vector3(0.30, 0.86, -0.25), Vector3(0.32, 0.38, 0.18), Color("8a5f3e"))

	var label: Label3D = Label3D.new()
	label.text = display_name
	label.position = Vector3(0.0, 2.48, 0.0)
	label.font_size = 26
	label.outline_size = 6
	label.modulate = Color("fff5d9")
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	root.add_child(label)

	return {"id": npc_id, "display_name": display_name, "root": root}

func _add_box_part(parent_node: Node3D, part_name: String, part_position: Vector3, size_value: Vector3, color_value: Color, rotation_value: Vector3 = Vector3.ZERO) -> void:
	var part: MeshInstance3D = MeshInstance3D.new()
	part.name = part_name
	var mesh: BoxMesh = BoxMesh.new()
	mesh.size = size_value
	part.mesh = mesh
	part.position = part_position
	part.rotation_degrees = rotation_value
	part.material_override = _make_material(color_value)
	parent_node.add_child(part)

func _add_sphere_part(parent_node: Node3D, part_name: String, part_position: Vector3, radius_value: float, color_value: Color, scale_value: Vector3) -> void:
	var part: MeshInstance3D = MeshInstance3D.new()
	part.name = part_name
	var mesh: SphereMesh = SphereMesh.new()
	mesh.radius = radius_value
	mesh.height = radius_value * 2.0
	part.mesh = mesh
	part.position = part_position
	part.scale = scale_value
	part.material_override = _make_material(color_value)
	parent_node.add_child(part)

func _add_capsule_part(parent_node: Node3D, part_name: String, part_position: Vector3, radius_value: float, height_value: float, color_value: Color) -> void:
	var part: MeshInstance3D = MeshInstance3D.new()
	part.name = part_name
	var mesh: CapsuleMesh = CapsuleMesh.new()
	mesh.radius = radius_value
	mesh.height = height_value
	part.mesh = mesh
	part.position = part_position
	part.material_override = _make_material(color_value)
	parent_node.add_child(part)

func _add_cylinder_part(parent_node: Node3D, part_name: String, part_position: Vector3, radius_value: float, height_value: float, color_value: Color) -> void:
	var part: MeshInstance3D = MeshInstance3D.new()
	part.name = part_name
	var mesh: CylinderMesh = CylinderMesh.new()
	mesh.top_radius = radius_value
	mesh.bottom_radius = radius_value
	mesh.height = height_value
	part.mesh = mesh
	part.position = part_position
	part.material_override = _make_material(color_value)
	parent_node.add_child(part)

func _make_material(color_value: Color) -> StandardMaterial3D:
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = color_value
	material.roughness = 0.9
	return material

func _get_hour() -> float:
	var time_nodes: Array[Node] = get_tree().get_nodes_in_group("game_time")
	if time_nodes.is_empty():
		return 8.0
	var time_manager: Node = time_nodes[0]
	var minutes_value: float = float(time_manager.get("current_minutes"))
	return minutes_value / 60.0

func _schedule_target(npc_id: String, hour: float) -> Vector3:
	match npc_id:
		"pak_wiryo":
			if hour < 10.5:
				return Vector3(-4.0, 0.2, -14.0)
			if hour < 16.5:
				return Vector3(5.0, 0.2, -12.7)
			if hour < 19.0:
				return Vector3(-8.5, 0.2, 1.3)
			return Vector3(-19.0, 0.2, 15.5)
		"bu_ratih":
			if hour < 19.5:
				return Vector3(-11.0, 0.2, 1.3)
			return Vector3(-18.5, 0.2, 15.0)
		"laras":
			if hour < 10.0:
				return Vector3(2.0, 0.2, -5.0)
			if hour < 16.0:
				return Vector3(-2.5, 0.2, 2.6)
			if hour < 19.0:
				return Vector3(-7.2, 0.2, 2.2)
			return Vector3(-17.0, 0.2, 14.0)
	return Vector3.ZERO

func _dialogue_for(npc_id: String) -> String:
	var first_time: bool = not bool(spoken_once.get(npc_id, false))
	if first_time:
		match npc_id:
			"pak_wiryo":
				return "Kamu akhirnya pulang juga. Tanah peninggalan keluargamu masih bagus. Jangan buru-buru—kenali dulu air, tanah, dan orang-orang di sini."
			"bu_ratih":
				return "Selamat datang kembali di Lembah Sari. Kalau butuh kabar desa, mampir saja ke warung. Orang biasanya cerita banyak sambil minum teh."
			"laras":
				return "Jadi benar kamu yang menempati rumah lama itu? Aku Laras. Sudah lama rumah itu tidak punya lampu di malam hari."

	var period: String = _get_period()
	var weather_text: String = _get_weather()
	match npc_id:
		"pak_wiryo":
			if weather_text == "Hujan":
				return "Hujan begini bagus untuk tanah, tapi saluran air tetap harus dijaga. Air berlebih juga bisa merusak tanaman."
			if period == "Pagi":
				return "Pagi adalah waktu terbaik melihat keadaan sawah. Air yang tenang sering memberi tahu masalah lebih cepat daripada manusia."
			if period == "Siang":
				return "Aku sedang memeriksa pintu irigasi. Nanti kamu juga perlu belajar mengatur aliran air ke kebunmu."
			return "Cukup untuk hari ini. Besok pekerjaan tetap ada, jadi jangan habiskan tenaga sampai malam."
		"bu_ratih":
			if period == "Pagi":
				return "Warung buka dari pagi. Petani biasanya mampir sebelum mulai kerja, jadi kabar desa paling cepat lewat sini."
			if period == "Sore":
				return "Menjelang sore warung mulai ramai. Kadang masalah desa selesai hanya karena orang akhirnya duduk dan bicara."
			return "Kalau panenmu sudah banyak, nanti kita pikirkan cara menjualnya tanpa harus keluar desa."
		"laras":
			if weather_text == "Hujan":
				return "Aku suka suara hujan di sungai. Desa terasa lebih kecil saat semua orang mencari tempat berteduh."
			if period == "Pagi":
				return "Aku sering ke sungai pagi-pagi. Airnya paling jernih sebelum aktivitas desa ramai."
			if period == "Siang":
				return "Lembah Sari kelihatan sederhana, tapi tiap sudut punya cerita. Coba jangan hanya sibuk di kebun terus."
			return "Kalau sempat, mampir ke warung sore hari. Biasanya lebih mudah bertemu orang-orang desa di sana."
	return "..."

func _get_period() -> String:
	var time_nodes: Array[Node] = get_tree().get_nodes_in_group("game_time")
	if time_nodes.is_empty():
		return "Pagi"
	var time_manager: Node = time_nodes[0]
	if time_manager.has_method("get_period_text"):
		return str(time_manager.call("get_period_text"))
	return "Pagi"

func _get_weather() -> String:
	var time_nodes: Array[Node] = get_tree().get_nodes_in_group("game_time")
	if time_nodes.is_empty():
		return "Cerah"
	var time_manager: Node = time_nodes[0]
	if time_manager.has_method("get_weather_text"):
		return str(time_manager.call("get_weather_text"))
	return "Cerah"
