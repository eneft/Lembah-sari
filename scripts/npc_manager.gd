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
	return {
		"ok": true,
		"speaker": display_name,
		"text": dialogue
	}

func _build_npcs() -> void:
	npcs.append(_make_npc("pak_wiryo", "Pak Wiryo", Vector3(-4.0, 0.2, -14.0), Color("6f8f4f"), Color("c98f67")))
	npcs.append(_make_npc("bu_ratih", "Bu Ratih", Vector3(-11.0, 0.2, 1.3), Color("b35f66"), Color("d39a71")))
	npcs.append(_make_npc("laras", "Laras", Vector3(2.0, 0.2, -5.0), Color("6d78b8"), Color("d6a07b")))

func _make_npc(npc_id: String, display_name: String, start_position: Vector3, shirt_color: Color, skin_color: Color) -> Dictionary:
	var root: Node3D = Node3D.new()
	root.name = npc_id
	root.position = start_position
	add_child(root)

	var body: MeshInstance3D = MeshInstance3D.new()
	var body_mesh: CapsuleMesh = CapsuleMesh.new()
	body_mesh.radius = 0.38
	body_mesh.height = 1.35
	body.mesh = body_mesh
	body.position = Vector3(0.0, 0.72, 0.0)
	body.material_override = _make_material(shirt_color)
	root.add_child(body)

	var head: MeshInstance3D = MeshInstance3D.new()
	var head_mesh: SphereMesh = SphereMesh.new()
	head_mesh.radius = 0.30
	head_mesh.height = 0.60
	head.mesh = head_mesh
	head.position = Vector3(0.0, 1.62, 0.0)
	head.material_override = _make_material(skin_color)
	root.add_child(head)

	var label: Label3D = Label3D.new()
	label.text = display_name
	label.position = Vector3(0.0, 2.25, 0.0)
	label.font_size = 30
	label.outline_size = 5
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	root.add_child(label)

	return {
		"id": npc_id,
		"display_name": display_name,
		"root": root
	}

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
