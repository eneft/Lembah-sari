extends Node3D

const HOUSE_MODEL_PATH: String = "res://assets/models/player_house_traditional_v4.glb"
const HOUSE_POSITION: Vector3 = Vector3(15.7, 0.0, 13.2)
const HOUSE_ROTATION_Y: float = 180.0
const HOUSE_SCALE: float = 6.6

const PROCEDURAL_HOUSE_PREFIXES: PackedStringArray = [
	"HouseWalls",
	"HouseCollision",
	"HouseGableRoof",
	"HouseDoor",
	"WindowGlass",
	"WindowAwning",
	"PorchFloor",
	"PorchPost",
	"PorchRoof",
	"HouseStep",
]

func _ready() -> void:
	# Main/world_builder creates the procedural fallback in its own _ready().
	# Deferred replacement guarantees we only remove it after the world exists.
	call_deferred("_replace_player_house")

func _replace_player_house() -> void:
	if not ResourceLoader.exists(HOUSE_MODEL_PATH):
		push_warning("[LembahSari] Repaired player-house GLB belum tersedia; procedural fallback dipertahankan.")
		return

	var packed_resource: Resource = load(HOUSE_MODEL_PATH)
	if not packed_resource is PackedScene:
		push_error("[LembahSari] Player-house GLB gagal dibaca sebagai PackedScene: %s" % HOUSE_MODEL_PATH)
		return

	var world_root: Node = get_parent()
	if world_root == null:
		return

	_remove_procedural_house(world_root)

	var house_scene: PackedScene = packed_resource as PackedScene
	var house_instance: Node3D = house_scene.instantiate() as Node3D
	if house_instance == null:
		push_error("[LembahSari] Repaired player-house gagal di-instantiate.")
		return

	house_instance.name = "PlayerHouseTraditionalV4"
	house_instance.position = HOUSE_POSITION
	house_instance.rotation_degrees.y = HOUSE_ROTATION_Y
	house_instance.scale = Vector3.ONE * HOUSE_SCALE
	world_root.add_child(house_instance)

	_add_gameplay_collision(world_root)
	print("[LembahSari] Player house replaced with traditional V4 GLB.")

func _remove_procedural_house(world_root: Node) -> void:
	for child: Node in world_root.get_children():
		if child == self:
			continue
		var child_name: String = String(child.name)
		for prefix: String in PROCEDURAL_HOUSE_PREFIXES:
			if child_name.begins_with(prefix):
				world_root.remove_child(child)
				child.queue_free()
				break

func _add_gameplay_collision(world_root: Node) -> void:
	# Keep collision intentionally simpler than the visual mesh for stable gameplay.
	# The front porch/stairs remain approachable while the solid house body blocks movement.
	var body: StaticBody3D = StaticBody3D.new()
	body.name = "HouseCollisionTraditionalV4"
	body.position = HOUSE_POSITION + Vector3(0.20, 1.3, 0.38)

	var collision: CollisionShape3D = CollisionShape3D.new()
	var shape: BoxShape3D = BoxShape3D.new()
	shape.size = Vector3(4.4, 2.6, 3.2)
	collision.shape = shape
	body.add_child(collision)
	world_root.add_child(body)
