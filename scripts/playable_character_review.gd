extends Node

const MIN_MASK_PIXELS: int = 120
const MIN_MASK_WIDTH: int = 10
const MIN_MASK_HEIGHT: int = 30

@onready var world: Node3D = $World

func _ready() -> void:
	await _capture_and_validate()

func _capture_and_validate() -> void:
	for _frame: int in range(55):
		await get_tree().physics_frame
	await RenderingServer.frame_post_draw

	var player: CharacterBody3D = world.get_node("Player") as CharacterBody3D
	var visual: Node3D = player.get_node("Visual") as Node3D
	var camera: Camera3D = player.get_node("CameraRig/Camera3D") as Camera3D
	if visual == null or camera == null:
		push_error("Playable character visual review is missing player Visual or camera.")
		get_tree().quit(1)
		return

	var natural: Image = get_viewport().get_texture().get_image()
	if natural.save_png("playable_character_review.png") != OK:
		push_error("Failed to save playable character review.")
		get_tree().quit(1)
		return

	var mask_material := StandardMaterial3D.new()
	mask_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mask_material.cull_mode = BaseMaterial3D.CULL_DISABLED
	mask_material.albedo_color = Color(1.0, 0.0, 1.0, 1.0)
	mask_material.metallic = 0.0
	mask_material.roughness = 1.0

	var meshes: Array[MeshInstance3D] = []
	var originals: Array[Material] = []
	for node: Node in visual.find_children("*", "MeshInstance3D", true, false):
		var mesh := node as MeshInstance3D
		if mesh.mesh == null:
			continue
		meshes.append(mesh)
		originals.append(mesh.material_override)
		mesh.material_override = mask_material

	if meshes.is_empty():
		push_error("Playable character visual review found no character meshes.")
		get_tree().quit(1)
		return

	for _frame: int in range(3):
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var mask_image: Image = get_viewport().get_texture().get_image()
	mask_image.save_png("playable_character_mask.png")

	var mask_pixels: int = 0
	var min_x: int = mask_image.get_width()
	var min_y: int = mask_image.get_height()
	var max_x: int = -1
	var max_y: int = -1
	const STEP: int = 2
	for y: int in range(0, mask_image.get_height(), STEP):
		for x: int in range(0, mask_image.get_width(), STEP):
			var p: Color = mask_image.get_pixel(x, y)
			if p.r < 0.70 or p.b < 0.70 or p.g > 0.35:
				continue
			mask_pixels += 1
			min_x = mini(min_x, x)
			min_y = mini(min_y, y)
			max_x = maxi(max_x, x)
			max_y = maxi(max_y, y)

	for i: int in range(meshes.size()):
		meshes[i].material_override = originals[i]

	var width: int = 0 if max_x < 0 else max_x - min_x + 1
	var height: int = 0 if max_y < 0 else max_y - min_y + 1
	var screen_size: Vector2 = camera.get_viewport().get_visible_rect().size
	var center_screen: Vector2 = camera.unproject_position(player.global_position + Vector3(0.0, 0.78, 0.0))
	var visible: bool = mask_pixels >= MIN_MASK_PIXELS and width >= MIN_MASK_WIDTH and height >= MIN_MASK_HEIGHT
	print("PLAYABLE_CHARACTER_VISUAL pixels=%d bbox=%dx%d screen=(%.1f,%.1f)/(%d,%d)" % [mask_pixels, width, height, center_screen.x, center_screen.y, int(screen_size.x), int(screen_size.y)])
	if not visible:
		push_error("Playable character is off-screen, occluded, collapsed, or too small in the real gameplay composition.")
		get_tree().quit(1)
		return

	print("PLAYABLE_CHARACTER_VISUAL_VALIDATED pixels=%d bbox=%dx%d" % [mask_pixels, width, height])
	get_tree().quit(0)
