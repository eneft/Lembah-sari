extends Node3D

const IRRIGATION_POSITION: Vector3 = Vector3(6.2, 0.2, -11.8)
const FISHING_POSITION: Vector3 = Vector3(-8.0, 0.2, -5.25)
const SELL_POSITION: Vector3 = Vector3(-11.5, 0.2, -0.15)
const SLEEP_POSITION: Vector3 = Vector3(15.7, 0.2, 9.7)
const WAKE_POSITION: Vector3 = Vector3(15.7, 0.25, 9.1)
const IRRIGATION_DISTANCE: float = 2.1
const FISHING_DISTANCE: float = 3.0
const SELL_DISTANCE: float = 2.8
const SLEEP_DISTANCE: float = 2.2
const FISHING_COOLDOWN_MS: int = 1400

var last_irrigation_day: int = -1
var last_fishing_time_ms: int = -100000
var rng: RandomNumberGenerator = RandomNumberGenerator.new()

func _ready() -> void:
	add_to_group("activity_manager")
	rng.randomize()
	_build_markers()

func try_interact(player_position: Vector3, _player_facing: Vector3, selected_tool: String) -> Dictionary:
	if _flat_distance(player_position, SLEEP_POSITION) <= SLEEP_DISTANCE:
		return _try_sleep()
	if _flat_distance(player_position, IRRIGATION_POSITION) <= IRRIGATION_DISTANCE:
		return _use_irrigation()
	if selected_tool == "rod":
		if _flat_distance(player_position, FISHING_POSITION) <= FISHING_DISTANCE:
			return _fish()
		return {"ok": true, "message": "Cari tanda kecil Mancing di tepi sungai."}
	if selected_tool == "sell":
		if _flat_distance(player_position, SELL_POSITION) <= SELL_DISTANCE:
			return _sell_inventory()
		return {"ok": true, "message": "Bawa hasil ke keranjang depan Warung Bu Ratih."}
	return {"ok": false}

func _try_sleep() -> Dictionary:
	var hour: float = _get_hour()
	var stamina: float = _get_stamina()
	if hour < 18.0 and stamina > 15.0:
		return {"ok": true, "message": "Masih terlalu pagi untuk tidur. Pulang lagi setelah pukul 18:00."}
	var time_nodes: Array[Node] = get_tree().get_nodes_in_group("game_time")
	if time_nodes.is_empty():
		return {"ok": true, "message": "Jam dunia belum siap untuk tidur."}
	var time_manager: Node = time_nodes[0]
	if not time_manager.has_method("skip_to_next_day"):
		return {"ok": true, "message": "Belum bisa berganti hari dari rumah."}
	var day_value: Variant = time_manager.call("skip_to_next_day")
	var message: String = "Kamu tidur nyenyak dan bangun pagi dengan tenaga penuh."
	if day_value is Dictionary:
		var day_result: Dictionary = day_value as Dictionary
		message = "%s Stamina pulih penuh." % str(day_result.get("message", "Hari baru dimulai."))
	return {"ok": true, "message": message, "sleep": true, "wake_position": WAKE_POSITION}

func _use_irrigation() -> Dictionary:
	var farm_nodes: Array[Node] = get_tree().get_nodes_in_group("farm_manager")
	if farm_nodes.is_empty():
		return {"ok": true, "message": "Saluran irigasi belum terhubung ke kebun."}
	var farm_manager: Node = farm_nodes[0]
	var current_day: int = int(farm_manager.get("day"))
	if last_irrigation_day == current_day:
		return {"ok": true, "message": "Irigasi sudah digunakan hari ini."}
	if not farm_manager.has_method("water_all_planted"):
		return {"ok": true, "message": "Pintu air bergerak, tetapi saluran belum siap."}
	if not _spend_stamina(8.0):
		return {"ok": true, "message": "Stamina tidak cukup untuk mengoperasikan pintu irigasi."}
	var watered_value: Variant = farm_manager.call("water_all_planted")
	var watered_count: int = int(watered_value)
	if watered_count <= 0:
		return {"ok": true, "message": "Pintu irigasi dibuka, tapi belum ada tanaman yang perlu disiram. -8 stamina."}
	last_irrigation_day = current_day
	return {"ok": true, "message": "Irigasi dibuka. %d tanaman tersiram sekaligus. -8 stamina." % watered_count}

func _fish() -> Dictionary:
	var now_ms: int = Time.get_ticks_msec()
	if now_ms - last_fishing_time_ms < FISHING_COOLDOWN_MS:
		return {"ok": true, "message": "Tunggu pelampung tenang sebentar..."}
	var inventory_nodes: Array[Node] = get_tree().get_nodes_in_group("inventory_manager")
	if inventory_nodes.is_empty():
		return {"ok": true, "message": "Tas belum siap menampung ikan."}
	if not _spend_stamina(6.0):
		return {"ok": true, "message": "Stamina tidak cukup untuk memancing."}
	last_fishing_time_ms = now_ms
	var roll: int = rng.randi_range(0, 2)
	var fish_id: String = "fish_wader"
	var fish_name: String = "Ikan Wader"
	match roll:
		1:
			fish_id = "fish_lele"
			fish_name = "Lele Sungai"
		2:
			fish_id = "fish_nila"
			fish_name = "Ikan Nila"
	var inventory: Node = inventory_nodes[0]
	if inventory.has_method("add_item"):
		inventory.call("add_item", fish_id, 1)
	return {"ok": true, "message": "Dapat %s! Ikan masuk ke tas. -6 stamina." % fish_name}

func _sell_inventory() -> Dictionary:
	var inventory_nodes: Array[Node] = get_tree().get_nodes_in_group("inventory_manager")
	if inventory_nodes.is_empty():
		return {"ok": true, "message": "Sistem penjualan belum siap."}
	var inventory: Node = inventory_nodes[0]
	if not inventory.has_method("sell_all"):
		return {"ok": true, "message": "Warung belum menerima hasil hari ini."}
	var sale_value: Variant = inventory.call("sell_all")
	if sale_value is Dictionary:
		var sale: Dictionary = sale_value as Dictionary
		return {"ok": true, "message": str(sale.get("message", "Penjualan selesai."))}
	return {"ok": true, "message": "Penjualan selesai."}

func _get_hour() -> float:
	var time_nodes: Array[Node] = get_tree().get_nodes_in_group("game_time")
	if time_nodes.is_empty():
		return 12.0
	var time_manager: Node = time_nodes[0]
	return float(time_manager.get("current_minutes")) / 60.0

func _get_stamina() -> float:
	var stats_nodes: Array[Node] = get_tree().get_nodes_in_group("player_stats")
	if stats_nodes.is_empty():
		return 100.0
	var stats: Node = stats_nodes[0]
	if stats.has_method("get_stamina"):
		return float(stats.call("get_stamina"))
	return 100.0

func _spend_stamina(cost: float) -> bool:
	var stats_nodes: Array[Node] = get_tree().get_nodes_in_group("player_stats")
	if stats_nodes.is_empty():
		return true
	var stats: Node = stats_nodes[0]
	if not stats.has_method("spend_stamina"):
		return true
	var result: Variant = stats.call("spend_stamina", cost)
	return bool(result)

func _flat_distance(a: Vector3, b: Vector3) -> float:
	var delta: Vector2 = Vector2(a.x - b.x, a.z - b.z)
	return delta.length()

func _material(color_value: Color) -> StandardMaterial3D:
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = color_value
	material.roughness = 0.94
	return material

func _cylinder_prop(node_name: String, prop_position: Vector3, radius_value: float, height_value: float, color_value: Color, rotation_value: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var instance: MeshInstance3D = MeshInstance3D.new()
	instance.name = node_name
	var mesh: CylinderMesh = CylinderMesh.new()
	mesh.top_radius = radius_value * 0.92
	mesh.bottom_radius = radius_value
	mesh.height = height_value
	mesh.radial_segments = 8
	instance.mesh = mesh
	instance.position = prop_position
	instance.rotation_degrees = rotation_value
	instance.material_override = _material(color_value)
	add_child(instance)
	return instance

func _sphere_prop(node_name: String, prop_position: Vector3, radius_value: float, color_value: Color, scale_value: Vector3 = Vector3.ONE) -> MeshInstance3D:
	var instance: MeshInstance3D = MeshInstance3D.new()
	instance.name = node_name
	var mesh: SphereMesh = SphereMesh.new()
	mesh.radius = radius_value
	mesh.height = radius_value * 2.0
	mesh.radial_segments = 9
	mesh.rings = 5
	instance.mesh = mesh
	instance.position = prop_position
	instance.scale = scale_value
	instance.material_override = _material(color_value)
	add_child(instance)
	return instance

func _small_label(label_text: String, marker_position: Vector3, text_color: Color) -> void:
	var label: Label3D = Label3D.new()
	label.text = label_text
	label.position = marker_position
	label.font_size = 17
	label.modulate = text_color
	label.outline_size = 5
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	add_child(label)

func _build_markers() -> void:
	# Sleep: a small warm porch lantern, not a floating tutorial sentence.
	_cylinder_prop("SleepLanternPost", SLEEP_POSITION + Vector3(-1.45, 0.65, 0.15), 0.055, 1.25, Color("655044"))
	_sphere_prop("SleepLanternGlow", SLEEP_POSITION + Vector3(-1.45, 1.36, 0.15), 0.13, Color("f2d18a"), Vector3(1.0, 1.2, 1.0))
	_small_label("Tidur", SLEEP_POSITION + Vector3(0.0, 1.8, 0.0), Color("f4e0a6"))

	# Irrigation: gate is already visible in the world; only a tiny contextual label remains.
	_small_label("Irigasi", IRRIGATION_POSITION + Vector3(0.0, 1.65, 0.0), Color("9ad1dd"))

	# Fishing: wooden rod rest and two river stones.
	_cylinder_prop("FishingRodRest", FISHING_POSITION + Vector3(0.0, 0.68, 0.0), 0.045, 1.45, Color("7d5a3e"), Vector3(12.0, 0.0, -16.0))
	_sphere_prop("FishingStone", FISHING_POSITION + Vector3(-0.45, 0.14, 0.18), 0.28, Color("777b76"), Vector3(1.25, 0.55, 0.9))
	_sphere_prop("FishingStone", FISHING_POSITION + Vector3(0.38, 0.11, -0.12), 0.22, Color("858883"), Vector3(1.1, 0.52, 0.95))
	_small_label("Mancing", FISHING_POSITION + Vector3(0.0, 1.45, 0.0), Color("a9d7e6"))

	# Selling: a produce basket in front of the warung.
	_cylinder_prop("SellBasket", SELL_POSITION + Vector3(0.0, 0.22, 0.0), 0.44, 0.38, Color("9a7045"))
	_sphere_prop("BasketProduce", SELL_POSITION + Vector3(-0.18, 0.48, 0.02), 0.12, Color("d64a39"))
	_sphere_prop("BasketProduce", SELL_POSITION + Vector3(0.08, 0.50, -0.08), 0.13, Color("dda742"))
	_sphere_prop("BasketProduce", SELL_POSITION + Vector3(0.24, 0.47, 0.10), 0.11, Color("6d9f4d"))
	_small_label("Jual", SELL_POSITION + Vector3(0.0, 1.30, 0.0), Color("f0d28a"))
