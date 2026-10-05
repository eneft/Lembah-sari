extends Node3D

@export var walk_animation: StringName = &"Walk"
@export var run_animation: StringName = &"Run"
@export var idle_animation: StringName = &"Idle"
@export var run_speed_threshold: float = 5.2
@export var blend_time: float = 0.16

var animation_player: AnimationPlayer
var current_animation: StringName = &""

func _ready() -> void:
	animation_player = _find_animation_player(self)
	if animation_player == null:
		push_warning("[LembahSari] AnimationPlayer tidak ditemukan pada karakter baru.")
		return
	for animation_name: StringName in [idle_animation, walk_animation, run_animation]:
		if not animation_player.has_animation(animation_name):
			push_warning("[LembahSari] Clip tidak ditemukan: %s" % animation_name)
			continue
		var clip: Animation = animation_player.get_animation(animation_name)
		if clip != null:
			clip.loop_mode = Animation.LOOP_LINEAR
	_play(idle_animation)

func _process(_delta: float) -> void:
	if animation_player == null:
		return
	var body: CharacterBody3D = get_parent() as CharacterBody3D
	if body == null:
		return
	var horizontal_speed: float = Vector2(body.velocity.x, body.velocity.z).length()
	if horizontal_speed < 0.15:
		_play(idle_animation)
	elif horizontal_speed >= run_speed_threshold:
		_play(run_animation)
	else:
		_play(walk_animation)

func _play(animation_name: StringName) -> void:
	if current_animation == animation_name:
		return
	if not animation_player.has_animation(animation_name):
		return
	animation_player.play(animation_name, blend_time)
	current_animation = animation_name

func _find_animation_player(root: Node) -> AnimationPlayer:
	if root is AnimationPlayer:
		return root as AnimationPlayer
	for child: Node in root.get_children():
		var found: AnimationPlayer = _find_animation_player(child)
		if found != null:
			return found
	return null
