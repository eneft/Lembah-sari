extends SceneTree
var failed: bool = false
func _initialize() -> void:
	_run.call_deferred()
func _run() -> void:
	var packed: PackedScene = load("res://scenes/PlayableV5Test.tscn") as PackedScene
	var world: Node3D = packed.instantiate() as Node3D
	root.add_child(world)
	current_scene = world
	for i: int in range(30):
		await physics_frame
	var hero: Node3D = world.get_node("HeroSceneV5") as Node3D
	var layer: Node3D = hero.get_node("HybridEnvironment") as Node3D
	var plants: Node3D = hero.get_node("ForegroundPlants3D") as Node3D
	var rocks: Node3D = world.get_node_or_null("LandscapedGroundDetails") as Node3D
	_check(rocks != null,"Organic rock layer must be present")
	if rocks != null:
		_check(int(rocks.get_meta("rock_count",0)) == 6,"Exactly six carefully placed rock accents")
		for child: Node in rocks.get_children():
			_check(child is MeshInstance3D,"Rocks must be real geometry")
			_check(bool(child.get_meta("partly_buried",false)),"Rocks must be visually planted")
			_check(child.get_child_count() == 0,"Render-only rocks must not block gameplay")
	var shadow_count: int = 0
	var ghost_shadows: int = 0
	var visible_cards: int = 0
	for child: Node in layer.get_children():
		if child is Sprite3D:
			var card: Sprite3D = child as Sprite3D
			if card.visible: visible_cards += 1
			var contact: Node3D = layer.get_node_or_null("ContactShadow_"+String(card.name)) as Node3D
			if contact == null: continue
			shadow_count += 1
			if not card.visible and contact.visible:
				ghost_shadows += 1
	_check(shadow_count > 25,"Near image vegetation must have planted soft contact shadows")
	_check(ghost_shadows == 0,"Hidden image foliage cannot leave detached contact shadows")
	_check(visible_cards > 90,"Hybrid backdrop and midground cards must remain visible")
	_check(int(layer.get_meta("thinned_front_cards",-1)) >= 0,"Deterministic card decluttering must run")
	_check(plants.get_child_count() >= 9 and plants.get_child_count() <= 10,"Only curated near 3D plants may remain")
	var rooted_models: int = 0
	for node: Node in plants.get_children():
		if not node is Node3D:
			continue
		var model: Node3D = node as Node3D
		var kind: int = int(model.get_meta("plant_type",-1))
		if kind == 3:
			continue
		var root_shadow: MeshInstance3D = model.get_node_or_null("RootContactShadow") as MeshInstance3D
		_check(root_shadow != null,"Polygon trees and bushes must be rooted with contact shadows: "+String(model.name))
		if root_shadow != null:
			rooted_models += 1
			_check(root_shadow.material_override is StandardMaterial3D,"Root shadow must use a feathered transparent material")
			_check(absf(root_shadow.scale.x*model.scale.x-1.0) < 0.05,"Root shadow must be normalized against scaled GLB: "+String(model.name))
			_check(absf(root_shadow.global_position.y+0.027) < 0.10,"Root shadow should meet the actual soil plane: "+String(model.name))
		if kind == 2 or kind == 4:
			var soil: MeshInstance3D = model.get_node_or_null("RootSoilMound") as MeshInstance3D
			_check(soil != null and soil.visible,"Banana and palms should have gently buried soil collars")
		if kind == 0 or kind == 2 or kind == 4:
			_check(model.get_node_or_null("RootTrunkCollider") is StaticBody3D,"Rooted tree trunk must block passing straight through its base")
	_check(rooted_models >= 6,"At least six major polygon plants must be grounded")
	var right_palm: Node3D = plants.get_node_or_null("Palm_Right_Back") as Node3D
	_check(right_palm != null,"Main right-hand framing palm must remain present")
	if right_palm != null:
		for name: String in ["PalmUnderstoryGrass_A","PalmUnderstoryGrass_B","PalmUnderstoryBush"]:
			var cover: Node3D = right_palm.get_node_or_null(name) as Node3D
			_check(cover != null and cover.visible,"Right palm understory must hide bare roots: "+name)
			if cover != null:
				_check(bool(cover.get_meta("ornamental_ground_cover",false)),"Palms must only have ornamental low understory")
				_check(cover.find_children("*","CollisionShape3D",true,false).is_empty(),"Palm ground cover must not obstruct farming gameplay")
	var banana_active: bool = bool(plants.get_meta("banana_active",false))
	if banana_active:
		_check(plants.get_node_or_null("BananaTree_Left_Indonesian") != null,"Source banana asset must load")
	if not failed:
		print("GROUNDED_LANDSCAPE_VALIDATED shadows=%d polygon_roots=%d hidden_ghosts=%d rocks=%d banana=%s far=image" % [shadow_count,rooted_models,ghost_shadows,rocks.get_child_count(),banana_active])
	world.queue_free()
	await process_frame
	quit(1 if failed else 0)
func _check(condition: bool, message: String) -> void:
	if not condition:
		failed = true
		push_error(message)
