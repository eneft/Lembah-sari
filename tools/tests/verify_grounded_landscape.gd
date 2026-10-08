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
	_check(plants.get_child_count() <= 10,"Only curated near 3D plants may remain")
	var banana_active: bool = bool(plants.get_meta("banana_active",false))
	if banana_active:
		_check(plants.get_node_or_null("BananaTree_Left_Indonesian") != null,"Source banana asset must load")
	if not failed:
		print("GROUNDED_LANDSCAPE_VALIDATED shadows=%d hidden_ghosts=%d rocks=%d banana=%s far=image" % [shadow_count,ghost_shadows,rocks.get_child_count(),banana_active])
	world.queue_free()
	await process_frame
	quit(1 if failed else 0)
func _check(condition: bool, message: String) -> void:
	if not condition:
		failed = true
		push_error(message)
