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
const BANANA_FALLBACK: String = "res://scripts/village_banana_fallback.gd"
# The supplied photorealistic RGBA PNG is the primary map for BOTH distant
# banana cards. SVG stays as a graceful fallback until binary upload completes.
const BANANA_CARD_PNG: String = "res://assets/textures/hybrid/banana_tree_card.png"
const BANANA_CARD_SVG: String = "res://assets/textures/hybrid/banana_tree_card.svg"
# Camera-locked, house-relative coordinates. Keep the front stairs/path clear.
# Three foreground polygon trees frame the left (field + two house trees); banana and two PNG cards remain accents.
const LAYOUT: Array[Dictionary] = [
	{"type":0,"name":"Canopy_Left_Hero","offset":Vector2(-4.8,-0.65),"scale":0.90,"yaw":34.0,"radius":1.65},
	{"type":0,"name":"Tree_LeftFieldFill","offset":Vector2(-8.0,0.45),"scale":1.10,"yaw":17.0,"radius":1.95},
	{"type":2,"name":"Palm_Left_Back","offset":Vector2(-3.50,-3.20),"scale":1.12,"yaw":63.0,"radius":1.10},
	{"type":2,"name":"Palm_Right_Back","offset":Vector2(6.0,-2.20),"scale":1.10,"yaw":-37.0,"radius":1.05},
	{"type":0,"name":"Tree_LeftLarge_A","offset":Vector2(-5.05,2.42),"scale":0.76,"yaw":-14.0,"radius":1.45},
	{"type":0,"name":"Tree_LeftLarge_B","offset":Vector2(-3.45,2.34),"scale":0.68,"yaw":8.0,"radius":1.32},
	{"type":1,"name":"Bush_Garden_Edge","offset":Vector2(4.55,2.16),"scale":0.52,"yaw":-86.0,"radius":1.38},
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
		# One small understory grouping on the right palm, without entering
		# the playable farming beds or creating extra collision bodies.
		if String(model.name) == "Palm_Right_Back":
			_attach_right_palm_base(model,imported[3],imported[1])
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
	if banana == null:
		# The real source asset stays authoritative. Show a small polygon
		# fallback rather than an empty slot until its GLB is uploaded.
		var banana_script: Script = load(BANANA_FALLBACK) as Script
		if banana_script != null and banana_script.can_instantiate():
			banana = banana_script.new().build() as Node3D
	if banana != null:
		banana.name = "BananaTree_Left_Indonesian"
		banana.position = house.position + Vector3(-5.55,0.0,1.18)
		# User GLB is normalized to 1 m high. Target ~3.2 m near the house.
		banana.scale = Vector3.ONE * 2.92
		banana.rotation_degrees.y = -8.0
		root.add_child(banana)
		_harmonize_3d_plant_materials(banana)
		_attach_root_grounding(banana,4,grounding_material)
		banana.set_meta("plant_type",4)
		banana.set_meta("authored_height",2.92)
		var banana_position: Vector3 = banana.global_position
		if playerspace.distance_to(Vector2(banana_position.x,banana_position.z)) < 1.28:
			banana.queue_free()
			banana = null
		else:
			placed += 1
			if imported[3] != null:
				_attach_banana_ground_cover(banana,imported[3])
			if layer != null:
				hidden += _hide_near_banana_cards(layer,banana_position,1.6)
	# One real banana plus two shaded transparent image companions.
	# These are authored after card decluttering, so they are not accidentally
	# hidden by the older generic "Tree/Palm" culling logic.
	var banana_cards: int = 0
	if banana != null and layer != null:
		banana_cards = _install_banana_image_companions(hero,house,layer,player,grounding_material)
	if layer != null:
		layer.set_meta("banana_cards",banana_cards)
	root.set_meta("banana_active",banana != null)
	root.set_meta("banana_source_glb",banana != null and not bool(banana.get_meta("fallback_banana",false)))
	root.set_meta("installed",placed)
	root.set_meta("hidden_cards",hidden)
	root.set_meta("expected",LAYOUT.size()+(1 if banana != null else 0))
	root.set_meta("left_side_recomposed",true)
	root.set_meta("left_large_canopy_count",3)
	root.set_meta("left_empty_gap_filled",root.has_node("Tree_LeftFieldFill"))
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
			var alpha: float = pow(maxf(0.0,1.0-p.length()),1.7)*0.24
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
	# Use metres, not source-model scale: a 3.1x GLB must not turn a subtle
	# contact shadow into a two-metre black disk around the trunk.
	var extent: float = 1.40 if kind == 0 else (1.02 if kind == 4 else (0.85 if kind == 2 else 0.78))
	plane.size = Vector2(extent,extent*0.79)
	shadow.mesh = plane
	shadow.material_override = material
	shadow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	model.add_child(shadow)
	# Normalize root shadow against the GLB scale and put it on the same
	# world soil plane as the image billboards (rather than hovering 3x higher).
	var parent_scale: float = maxf(absf(model.scale.y),0.001)
	shadow.scale = Vector3.ONE/parent_scale
	shadow.position = Vector3(0.0,(-0.027-model.global_position.y)/parent_scale,0.0)
	if kind == 2 or kind == 4:
		_attach_root_soil_mound(model,kind)
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

func _install_banana_image_companions(hero: Node3D,house: Node3D,layer: Node3D,player: CharacterBody3D,shadow_mat: StandardMaterial3D) -> int:
	var texture_path: String = BANANA_CARD_PNG if ResourceLoader.exists(BANANA_CARD_PNG) else BANANA_CARD_SVG
	if not ResourceLoader.exists(texture_path):
		push_error("[LembahSari] Banana card image unavailable (PNG/SVG): "+texture_path)
		return 0
	var texture: Texture2D = load(texture_path) as Texture2D
	var fixed_camera: Camera3D = player.get_node_or_null("CameraRig/Camera3D") as Camera3D
	if texture == null or fixed_camera == null:
		push_error("[LembahSari] Banana card texture or fixed camera is missing")
		return 0
	var layout: Array[Dictionary] = [
		{"name":"Card_BananaRearLeft","offset":Vector3(-6.55,0.0,-0.05),"height":1.96,"flip":true,"tint":Color(0.89,0.94,0.85,1.0)},
		{"name":"Card_BananaMidLeft","offset":Vector3(-4.95,0.0,0.88),"height":1.84,"flip":false,"tint":Color(0.86,0.92,0.84,1.0)},
	]
	var count: int = 0
	var viewport_size: Vector2 = fixed_camera.get_viewport().get_visible_rect().size
	for placement: Dictionary in layout:
		var base: Vector3 = hero.to_global(house.position+placement["offset"])
		var height: float = float(placement["height"])
		var sprite := Sprite3D.new()
		sprite.name = String(placement["name"])
		sprite.texture = texture
		sprite.pixel_size = height/float(texture.get_height())
		sprite.flip_h = bool(placement["flip"])
		sprite.modulate = placement["tint"]
		sprite.shaded = true
		sprite.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
		sprite.alpha_scissor_threshold = 0.35
		sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		sprite.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		layer.add_child(sprite)
		sprite.global_basis = fixed_camera.global_basis.orthonormalized()
		sprite.global_position = base+fixed_camera.global_basis.y.normalized()*height*0.48
		# A small physical grass clump conceals the lower edge of the 2D card.
		var grass_scene: PackedScene = load(PLANT_PATHS[3]) as PackedScene
		if grass_scene != null:
			var understory: Node3D = grass_scene.instantiate() as Node3D
			if understory != null:
				understory.name = "BananaImageRootCover_"+sprite.name
				layer.add_child(understory)
				understory.global_position = Vector3(base.x+(-0.10 if count == 0 else 0.12),-0.042,base.z+0.09)
				understory.scale = Vector3.ONE*0.17
				understory.rotation_degrees.y = -24.0 if count == 0 else 31.0
				for n: Node in understory.find_children("*","MeshInstance3D",true,false):
					(n as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var contact := MeshInstance3D.new()
		contact.name = "ContactShadow_"+sprite.name
		var plane := PlaneMesh.new()
		plane.size = Vector2(0.72,0.46)
		contact.mesh = plane
		contact.material_override = shadow_mat
		contact.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		layer.add_child(contact)
		contact.global_position = Vector3(base.x,-0.024,base.z)
		contact.rotation_degrees.y = -26.0 if count == 0 else 19.0
		sprite.set_meta("banana_image",true)
		sprite.set_meta("ground_anchor",base)
		sprite.set_meta("source_texture",texture_path)
		sprite.set_meta("image_is_png",texture_path == BANANA_CARD_PNG)
		sprite.set_meta("image_resolution",texture.get_size())
		var screen: Vector2 = fixed_camera.unproject_position(sprite.global_position)/viewport_size
		print("[LembahSari] BANANA_IMAGE_CARD name=%s source=%s screen_uv=%s height=%.2f" % [sprite.name,texture_path,screen,height])
		count += 1
	return count

func _attach_banana_ground_cover(banana: Node3D,grass_scene: PackedScene) -> void:
	# These authored grasses share existing lightweight mesh assets.
	# Children inherit the banana's normalized 3.25x transform.
	for i: int in range(3):
		var clump: Node3D = grass_scene.instantiate() as Node3D
		if clump == null:
			continue
		clump.name = "BananaRootGrass_"+str(i)
		clump.position = [Vector3(-0.16,0.0,0.08),Vector3(0.13,0.0,-0.10),Vector3(0.03,0.0,0.18)][i]
		clump.scale = Vector3.ONE*[0.13,0.10,0.08][i]
		clump.rotation_degrees.y = [18.0,-42.0,62.0][i]
		banana.add_child(clump)
		for n: Node in clump.find_children("*","MeshInstance3D",true,false):
			(n as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

func _attach_root_soil_mound(model: Node3D,kind: int) -> void:
	# Small, shallow soil collar fixes the "floating palm trunk" illusion.
	var soil := MeshInstance3D.new()
	soil.name = "RootSoilMound"
	var sphere := SphereMesh.new()
	sphere.radial_segments = 12
	sphere.rings = 6
	soil.mesh = sphere
	var material := StandardMaterial3D.new()
	material.resource_name = "WarmSoilAtTrunk"
	material.albedo_color = Color("64704b")
	material.roughness = 0.98
	soil.material_override = material
	soil.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	model.add_child(soil)
	var model_scale: float = maxf(absf(model.scale.y),0.001)
	var width: float = 0.42 if kind == 2 else 0.33
	soil.scale = Vector3(width,0.082,width*0.77)/model_scale
	# Half-buried green soil, not a visible raised rock around the trunk.
	soil.position = Vector3(0.0,(-0.048-model.global_position.y)/model_scale,0.0)

func _attach_right_palm_base(palm: Node3D,grass_scene: PackedScene,bush_scene: PackedScene) -> void:
	var layout: Array[Dictionary] = [
		{"name":"PalmUnderstoryGrass_A","at":Vector3(-0.24,0.0,0.23),"scale":0.22,"yaw":28.0,"bush":false},
		{"name":"PalmUnderstoryGrass_B","at":Vector3(0.23,0.0,-0.15),"scale":0.18,"yaw":-35.0,"bush":false},
		{"name":"PalmUnderstoryBush","at":Vector3(0.37,0.0,0.16),"scale":0.19,"yaw":75.0,"bush":true},
	]
	for entry: Dictionary in layout:
		var packed: PackedScene = bush_scene if bool(entry["bush"]) else grass_scene
		var cover: Node3D = packed.instantiate() as Node3D if packed != null else null
		if cover == null:
			continue
		cover.name = String(entry["name"])
		cover.position = entry["at"]
		cover.scale = Vector3.ONE*float(entry["scale"])
		cover.rotation_degrees.y = float(entry["yaw"])
		palm.add_child(cover)
		cover.set_meta("ornamental_ground_cover",true)
		for child: Node in cover.find_children("*","MeshInstance3D",true,false):
			(child as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
