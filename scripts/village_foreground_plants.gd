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
# Offsets in hero-local coordinates relative to house; -X is screen-left
# for the approved 124-degree hero rotation and fixed gameplay camera.
const BANANA_PATH: String = "res://assets/models/foreground/05_Pohon_Pisang_Optimized.glb"
# Camera-locked, house-relative coordinates. Keep the front stairs/path clear.
# One big canopy and banana frame the left; two palms frame right/back.
const LAYOUT: Array[Dictionary] = [
	{"type":0,"name":"Canopy_Left_Hero","offset":Vector2(-4.8,-0.65),"scale":0.92,"yaw":34.0,"radius":1.65},
	{"type":2,"name":"Palm_Left_Back","offset":Vector2(-3.50,-3.20),"scale":1.12,"yaw":63.0,"radius":1.10},
	{"type":2,"name":"Palm_Right_Back","offset":Vector2(6.0,-2.20),"scale":1.10,"yaw":-37.0,"radius":1.05},
	{"type":1,"name":"Bush_Left_Front_A","offset":Vector2(-5.65,3.05),"scale":0.70,"yaw":51.0,"radius":0.88},
	{"type":1,"name":"Bush_Left_Front_B","offset":Vector2(-3.25,3.60),"scale":0.57,"yaw":-18.0,"radius":0.80},
	{"type":1,"name":"Bush_Garden_Edge","offset":Vector2(4.70,2.30),"scale":0.58,"yaw":-92.0,"radius":1.38},
	{"type":3,"name":"Reed_River_Left_A","offset":Vector2(-5.55,5.85),"scale":0.64,"yaw":-13.0,"radius":0.30},
	{"type":3,"name":"Reed_River_Left_B","offset":Vector2(-3.10,5.85),"scale":0.58,"yaw":57.0,"radius":0.30},
	{"type":3,"name":"Reed_River_Right","offset":Vector2(5.50,5.70),"scale":0.64,"yaw":-43.0,"radius":0.30},
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
	var grounding_material: StandardMaterial3D = _build_grounding_shadow_material()
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
		_harmonize_3d_plant_materials(model)
		_attach_root_grounding(model,kind,grounding_material)
		model.set_meta("plant_type",kind)
		model.set_meta("authored_height",SOURCE_HEIGHTS[kind] * float(entry["scale"]))
		placed += 1
		if layer != null:
			hidden += _hide_overlapping_cards(layer,loc,kind,float(entry["radius"]))
	# Real banana asset is optional until the user adds the optimized GLB.
	# No synthetic substitute: the source plant retains its own model/texture.
	var banana: Node3D = null
	if ResourceLoader.exists(BANANA_PATH):
		var banana_scene: PackedScene = load(BANANA_PATH) as PackedScene
		if banana_scene != null:
			banana = banana_scene.instantiate() as Node3D
	if banana != null:
		banana.name = "BananaTree_Left_Indonesian"
		banana.position = house.position + Vector3(-6.55,0.0,0.65)
		# User GLB is normalized to 1 m high. Target ~3.2 m near the house.
		banana.scale = Vector3.ONE * 3.2
		banana.rotation_degrees.y = -18.0
		root.add_child(banana)
		_harmonize_3d_plant_materials(banana)
		_attach_root_grounding(banana,4,grounding_material)
		banana.set_meta("plant_type",4)
		banana.set_meta("authored_height",3.2)
		var banana_position: Vector3 = banana.global_position
		if playerspace.distance_to(Vector2(banana_position.x,banana_position.z)) < 1.20:
			banana.queue_free()
			banana = null
		else:
			placed += 1
			if layer != null:
				hidden += _hide_near_banana_cards(layer,banana_position,1.6)
	root.set_meta("banana_active",banana != null)
	root.set_meta("installed",placed)
	root.set_meta("hidden_cards",hidden)
	root.set_meta("expected",LAYOUT.size()+(1 if banana != null else 0))
	print("[LembahSari] FOREGROUND_PLANTS_3D_ACTIVE models=%d banana=%s hidden_near_cards=%d background=image" % [placed,banana != null,hidden])
func _hide_overlapping_cards(layer: Node3D, location: Vector3, kind: int, radius: float) -> int:
	var removed := 0
	for child: Node in layer.get_children():
		if not child is Sprite3D:
			continue
		var sprite: Sprite3D = child as Sprite3D
		if not sprite.visible:
			continue
		var label := String(sprite.name)
		if "Mid" in label:
			continue
		var eligible := (kind == 0 and "Tree" in label) or (kind == 2 and "Palm" in label) or (kind == 1 and ("Bush" in label or "Flower" in label)) or (kind == 3 and ("Grass" in label or "Bank" in label))
		if not eligible:
			continue
		var center: Vector3 = sprite.global_position
		if Vector2(center.x,center.z).distance_to(Vector2(location.x,location.z)) <= radius:
			sprite.hide()
			var underlay: MeshInstance3D = layer.get_node_or_null("ContactShadow_"+label) as MeshInstance3D
			if underlay != null:
				underlay.hide()
			# Don't retain an invisible trunk collider where a 3D tree takes over.
			var legacy_trunk: StaticBody3D = layer.get_node_or_null("TrunkCollider_"+label.trim_prefix("Card_")) as StaticBody3D
			if legacy_trunk != null:
				legacy_trunk.queue_free()
			removed += 1
	return removed

func _hide_near_banana_cards(layer: Node3D, location: Vector3, radius: float) -> int:
	var hidden: int = 0
	for node: Node in layer.get_children():
		if not node is Sprite3D:
			continue
		var sprite: Sprite3D = node as Sprite3D
		var label: String = String(sprite.name)
		if not sprite.visible or "Mid" in label:
			continue
		if not ("Tree" in label or "Palm" in label or "Bush" in label):
			continue
		if Vector2(sprite.global_position.x-location.x,sprite.global_position.z-location.z).length() < radius:
			sprite.hide()
			var underlay: MeshInstance3D = layer.get_node_or_null("ContactShadow_"+label) as MeshInstance3D
			if underlay != null:
				underlay.hide()
			var legacy_trunk: StaticBody3D = layer.get_node_or_null("TrunkCollider_"+label.trim_prefix("Card_")) as StaticBody3D
			if legacy_trunk != null:
				legacy_trunk.queue_free()
			hidden += 1
	return hidden

func _harmonize_3d_plant_materials(model: Node3D) -> void:
	# Imported GLB PBR materials stay textured. Duplicate per instance so the
	# tint doesn't mutate source GLBs or affect unrelated scenes.
	for node: Node in model.find_children("*","MeshInstance3D",true,false):
		var mesh_instance: MeshInstance3D = node as MeshInstance3D
		if mesh_instance.mesh == null:
			continue
		for surface: int in range(mesh_instance.mesh.get_surface_count()):
			var authored: Material = mesh_instance.get_active_material(surface)
			if not authored is StandardMaterial3D:
				continue
			var warmed: StandardMaterial3D = authored.duplicate() as StandardMaterial3D
			warmed.albedo_color *= Color(0.958,0.988,0.900,1.0)
			warmed.roughness = maxf(warmed.roughness,0.77)
			mesh_instance.set_surface_override_material(surface,warmed)

func _build_grounding_shadow_material() -> StandardMaterial3D:
	# Soft radial green/soil shadow. Shared across all trees and banana.
	var image := Image.create_empty(48,48,false,Image.FORMAT_RGBA8)
	for y: int in range(48):
		for x: int in range(48):
			var p: Vector2 = (Vector2(float(x)+0.5,float(y)+0.5)/48.0-Vector2(0.5,0.5))*2.0
			var alpha: float = powf(maxf(0.0,1.0-p.length()),1.7)*0.24
			image.set_pixel(x,y,Color(0.23,0.23,0.16,alpha))
	var mat := StandardMaterial3D.new()
	mat.resource_name = "Grounded3DTreeRootShadow"
	mat.albedo_texture = ImageTexture.create_from_image(image)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_OPAQUE_ONLY
	return mat

func _attach_root_grounding(model: Node3D,kind: int,material: StandardMaterial3D) -> void:
	if kind == 3:
		return # river reed models already merge with volumetric grass
	var shadow := MeshInstance3D.new()
	shadow.name = "RootContactShadow"
	var plane := PlaneMesh.new()
	var extent: float = 1.24 if kind == 0 else (0.68 if kind == 4 else (0.57 if kind == 2 else 0.72))
	plane.size = Vector2(extent,extent*0.77)
	shadow.mesh = plane
	shadow.material_override = material
	shadow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	model.add_child(shadow)
	shadow.position = Vector3(0.0,0.023,0.0)
	# Trunk collider only for rooted trees, never ornamental shrub/grass.
	if kind == 0 or kind == 2 or kind == 4:
		var blocker := StaticBody3D.new()
		blocker.name = "RootTrunkCollider"
		var shape := CollisionShape3D.new()
		var cyl := CylinderShape3D.new()
		cyl.radius = 0.07 if kind == 4 else 0.14
		cyl.height = 0.72 if kind == 4 else 1.15
		shape.shape = cyl
		shape.position.y = cyl.height*0.5
		blocker.add_child(shape)
		model.add_child(blocker)
