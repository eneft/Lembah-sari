extends SceneTree
# Ensures grass is physically raised polygon geometry, not a flat texture,
# and image-backed foliage receives the same lighting as foreground models.
var failed: bool = false
const EXPECTED_BATCHES: Array[String] = [
	"LawnGrass3D",
	"LeftGardenGrass3D",
	"RightGardenGrass3D",
	"RiverBankGrass3D",
]
func _initialize() -> void:
	_run.call_deferred()
func _run() -> void:
	var world: Node3D = load("res://scenes/PlayableV5Test.tscn").instantiate() as Node3D
	root.add_child(world)
	current_scene = world
	for i: int in range(30):
		await physics_frame
	var grass: Node3D = world.get_node_or_null("ForegroundGrass3D") as Node3D
	_check(grass != null,"A dedicated real-geometry grass layer must exist")
	if grass == null:
		quit(1)
		return
	_check(int(grass.get_meta("batches",0)) == 4,"Grass must use four fast MultiMesh batches")
	var count: int = 0
	var tall: int = 0
	for name: String in EXPECTED_BATCHES:
		var draw: MultiMeshInstance3D = grass.get_node_or_null(name) as MultiMeshInstance3D
		_check(draw != null,"Missing grass geometry: "+name)
		if draw == null or draw.multimesh == null:
			continue
		var multimesh: MultiMesh = draw.multimesh
		_check(multimesh.mesh is ArrayMesh,"Grass tufts must use polygon ArrayMesh geometry")
		_check(multimesh.instance_count > 18,"Grass region is too sparse: "+name)
		_check(not draw.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_ON,"Decorative grass must avoid costly shadow maps")
		var material: StandardMaterial3D = multimesh.mesh.surface_get_material(0) as StandardMaterial3D
		_check(material != null and material.vertex_color_use_as_albedo,"Grass requires warm green-gold blade gradients")
		var arrays: Array = multimesh.mesh.surface_get_arrays(0)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var max_y: float = 0.0
		for point: Vector3 in vertices:
			max_y = maxf(max_y,point.y)
		_check(max_y > 0.74,"Grass mesh must rise visibly above the ground")
		# Dummy/headless rasterizer does not preserve GPU MultiMesh readback.
		# Validate the CPU-authored transform bounds recorded at creation time.
		var min_height: float = float(draw.get_meta("authored_min_height",-1.0))
		var max_height: float = float(draw.get_meta("authored_max_height",-1.0))
		print("GRASS_BATCH_HEIGHT name=%s min=%.4f max=%.4f instances=%d" % [name,min_height,max_height,multimesh.instance_count])
		_check(min_height > 0.034 and max_height < 0.32 and max_height > min_height,"Grass authored height outside approved limits: "+name)
		if max_height > 0.20:
			tall += multimesh.instance_count
		count += multimesh.instance_count
	_check(count > 270 and count < 1150,"Grass must be visibly dense but bounded")
	_check(tall > 35,"Riverside/yard need raised grass, not a flat lawn")
	_check(int(grass.get_meta("tufts",0)) == count,"Grass instancing metadata must match GPU transforms")
	_check(int(grass.get_meta("path_edge_tufts",0)) >= 8,"Walking path must gain small dimensional grass at its edges")
	_check(bool(grass.get_meta("organic_mask",false)),"Grass should scatter as soft-edged islands, never a rectangular lawn")
	_check(String(grass.get_meta("blade_profile","")) == "curved_broad","Grass mesh must have curved broad tips instead of spikes")
	var hero: Node3D = world.get_node("HeroSceneV5") as Node3D
	var hybrid: Node3D = hero.get_node("HybridEnvironment") as Node3D
	var cards: int = 0
	var lit_cards: int = 0
	for node: Node in hybrid.get_children():
		if node is Sprite3D:
			cards += 1
			if (node as Sprite3D).shaded: lit_cards += 1
	_check(cards > 100 and lit_cards == cards,"Image foliage must share the real-world lighting model")
	var backdrop: Sprite3D = hero.get_node("ValleyBackgroundImage") as Sprite3D
	_check(backdrop.texture != null and not backdrop.shaded,"Distant valley remains a cheap atmospheric image")
	var player: CharacterBody3D = world.get_node("Player") as CharacterBody3D
	_check(player.is_on_floor(),"Foreground grass must not disturb player floor or collision")
	if not failed:
		print("VOLUMETRIC_GRASS_VALIDATED tufts=%d batches=4 raised=%d card_lighting=%d/%d background=image" % [count,tall,lit_cards,cards])
	world.queue_free()
	await process_frame
	quit(1 if failed else 0)
func _check(condition: bool,message: String) -> void:
	if not condition:
		failed = true
		push_error(message)
