extends RefCounted
## Foreground polygon plants from four independent, bottom-pivot user GLBs.
## Distant midground vegetation and valley panorama always stay as images.
const PLANT_PATHS: Array[String] = [
	"res://assets/models/foreground/01_Pohon_Rindang_Besar.glb",
	"res://assets/models/foreground/02_Semak_Rimbun.glb",
	"res://assets/models/foreground/03_Palem_Lengkung.glb",
	"res://assets/models/foreground/04_Rumput_Tinggi.glb",
]
const SOURCE_HEIGHTS: Array[float] = [4.4, 1.2, 3.6, 0.9]
# Offsets in hero-local coordinates relative to house; +X is screen-left.
const LAYOUT: Array[Dictionary] = [
	{"type":0, "name":"Canopy_Left_Hero",  "offset":Vector2(4.8,-0.45), "scale":0.94, "yaw":34.0, "radius":1.10},
	{"type":0, "name":"Canopy_Left_Small", "offset":Vector2(7.0,1.45),  "scale":0.68, "yaw":-28.0,"radius":0.85},
	{"type":2, "name":"Palm_Left_Back",    "offset":Vector2(3.50,-3.20),"scale":1.24, "yaw":63.0, "radius":0.60},
	{"type":2, "name":"Palm_Right_Back",   "offset":Vector2(-6.0,-2.20),"scale":1.12,"yaw":-37.0,"radius":0.60},
	{"type":1, "name":"Bush_Left_Front_A", "offset":Vector2(5.6,3.15),  "scale":0.83, "yaw":51.0, "radius":0.85},
	{"type":1, "name":"Bush_Left_Front_B", "offset":Vector2(3.65,4.20), "scale":0.71, "yaw":-18.0,"radius":0.75},
	{"type":1, "name":"Bush_House_Left",  "offset":Vector2(3.25,2.15), "scale":0.61, "yaw":112.0,"radius":0.65},
	{"type":1, "name":"Bush_Garden_Edge", "offset":Vector2(-4.7,2.30), "scale":0.67, "yaw":-92.0,"radius":0.70},
	{"type":3, "name":"Reed_River_Left_A", "offset":Vector2(5.55,5.85), "scale":0.64, "yaw":-13.0,"radius":0.30},
	{"type":3, "name":"Reed_River_Left_B", "offset":Vector2(3.10,5.85), "scale":0.58, "yaw":57.0, "radius":0.30},
	{"type":3, "name":"Reed_River_Right",  "offset":Vector2(-5.5,5.70), "scale":0.64, "yaw":-43.0,"radius":0.30},
]
func apply(hero: Node3D, player: CharacterBody3D) -> void:
	var house: Node3D = hero.get_node_or_null("PlayerHouseTraditionalV4") as Node3D
	if house == null:
		push_warning("[LembahSari] Foreground vegetation needs the traditional house anchor.")
		return
	var root := Node3D.new()
	root.name = "ForegroundPlants3D"
	hero.add_child(root)
	var layer: Node3D = hero.get_node_or_null("HybridEnvironment") as Node3D
	var imported: Array[PackedScene] = []
	for path: String in PLANT_PATHS:
		var packed: PackedScene = null
		if ResourceLoader.exists(path):
			packed = load(path) as PackedScene
		imported.append(packed)
	var available := 0
	for packed: PackedScene in imported:
		if packed != null:
			available += 1
	# Never hide old 2.5D cards if the four GLBs have not all been installed.
	if available != PLANT_PATHS.size():
		root.set_meta("installed", 0)
		root.set_meta("expected", PLANT_PATHS.size())
		print("[LembahSari] FOREGROUND_PLANTS_AWAITING_ASSETS found=%d expected=%d" % [available,PLANT_PATHS.size()])
		return
	var placed := 0
	var hidden := 0
	var playerspace := Vector2(player.global_position.x, player.global_position.z)
	for entry: Dictionary in LAYOUT:
		var kind: int = int(entry["type"])
		var model: Node3D = imported[kind].instantiate() as Node3D
		if model == null:
			push_error("[LembahSari] Foreground GLB did not instantiate: %s" % PLANT_PATHS[kind])
			continue
		var delta: Vector2 = entry["offset"]
		model.name = String(entry["name"])
		model.position = house.position + Vector3(delta.x,0.0,delta.y)
		model.scale = Vector3.ONE * float(entry["scale"])
		model.rotation_degrees.y = float(entry["yaw"])
		root.add_child(model)
		# Keep the player spawn and access to the house unobstructed.
		var loc: Vector3 = model.global_position
		var player_distance := playerspace.distance_to(Vector2(loc.x,loc.z))
		if player_distance < 1.10:
			push_warning("[LembahSari] Plant too close to player spawn: %s" % model.name)
			model.queue_free()
			continue
		# Only hero canopies and palms need realtime shadows.
		if kind == 1 or kind == 3:
			for mesh: Node in model.find_children("*", "MeshInstance3D", true, false):
				(mesh as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		model.set_meta("plant_type",kind)
		model.set_meta("authored_height",SOURCE_HEIGHTS[kind] * float(entry["scale"]))
		placed += 1
		if layer != null:
			hidden += _hide_overlapping_cards(layer,loc,kind,float(entry["radius"]))
	root.set_meta("installed",placed)
	root.set_meta("hidden_cards",hidden)
	root.set_meta("expected",LAYOUT.size())
	print("[LembahSari] FOREGROUND_PLANTS_3D_ACTIVE models=%d hidden_near_cards=%d background=image" % [placed,hidden])
func _hide_overlapping_cards(layer: Node3D, location: Vector3, kind: int, radius: float) -> int:
	var removed := 0
	for child: Node in layer.get_children():
		if not child is Sprite3D or not child.visible:
			continue
		var label := String(child.name)
		if "Mid" in label:
			continue
		var eligible := (kind == 0 and "Tree" in label) or (kind == 2 and "Palm" in label) or (kind == 1 and ("Bush" in label or "Flower" in label)) or (kind == 3 and ("Grass" in label or "Bank" in label))
		if not eligible:
			continue
		var center: Vector3 = (child as Sprite3D).global_position
		if Vector2(center.x,center.z).distance_to(Vector2(location.x,location.z)) <= radius:
			child.hide()
			removed += 1
	return removed
