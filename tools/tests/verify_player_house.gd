extends SceneTree

var failed: bool = false

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var scene: PackedScene = load(str(ProjectSettings.get_setting("application/run/main_scene"))) as PackedScene
	var world: Node = scene.instantiate()
	root.add_child(world)
	current_scene = world
	for frame: int in range(30):
		await physics_frame
	var hero: Node3D = world.get_node_or_null("HeroSceneV5") as Node3D
	var house: Node3D = hero.get_node_or_null("PlayerHouseTraditionalV4") as Node3D if hero != null else null
	if house == null:
		push_error("The traditional house must load in the playable scene.")
		quit(1)
		return
	_check(hero.find_children("HeroHouseRoot*", "", true, false).is_empty(), "The old embedded house must be removed.")
	_check(hero.find_children("PlayerHouseRepairedV3", "", true, false).is_empty(), "The previous replacement must not overlap the new house.")
	var approach: Vector3 = hero.to_global(Vector3(-4.8, 0, -1.15)) - house.global_position
	approach.y = 0
	var front: Vector3 = (house.global_basis * Vector3.BACK).normalized()
	_check(front.dot(approach.normalized()) > .9, "The front porch must face the village path.")
	var meshes: Array[Node] = house.find_children("*", "MeshInstance3D", true, false)
	var bounds: AABB
	var initialized: bool = false
	var roof_panels: int = 0
	var textured_body: bool = false
	for node: Node in meshes:
		var mesh: MeshInstance3D = node as MeshInstance3D
		var box: AABB = house.global_transform.affine_inverse() * mesh.global_transform * mesh.get_aabb()
		bounds = box if not initialized else bounds.merge(box)
		initialized = true
		for surface: int in range(mesh.mesh.get_surface_count()):
			var material: StandardMaterial3D = mesh.get_active_material(surface) as StandardMaterial3D
			if String(mesh.name).begins_with("RoofTiles_"):
				roof_panels += 1
				_check(material != null and material.albedo_texture != null, "Roof clay texture must load.")
				_check(material != null and material.metallic < .01 and material.roughness > .8, "Roof tiles must use matte clay PBR.")
			elif material != null and String(material.resource_name).begins_with("TraditionalHouseTimberStonePlaster"):
				textured_body = material.albedo_texture != null
	_check(roof_panels == 6, "All six roof panels must load.")
	_check(textured_body, "The original timber, plaster, and stone texture must load.")
	_check(bounds.size.x < 1.02 and bounds.size.z < 1.02 and bounds.size.y > .57, "The complete house must retain its normalized footprint.")
	var player: CharacterBody3D = world.get_node("Player") as CharacterBody3D
	_check(house.to_local(player.global_position).z > bounds.end.z + .01, "The player must spawn on the approach, clear of the stairs.")
	_check(player.is_on_floor(), "The player must stand on the playable floor.")
	if not failed:
		print("PLAYABLE_HOUSE_VALIDATED front=path roof_panels=%d textures=ok spawn=clear bounds=%s" % [roof_panels, bounds.size])
	world.queue_free()
	await process_frame
	quit(1 if failed else 0)

func _check(condition: bool, message: String) -> void:
	if not condition:
		failed = true
		push_error(message)
