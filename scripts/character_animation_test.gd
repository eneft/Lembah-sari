extends Node3D

@onready var character_model: Node = $Character
var animation_player: AnimationPlayer
var clips: Array[StringName] = [&"Idle", &"Walk", &"Run"]
var clip_index: int = 0
var timer: float = 0.0

func _ready() -> void:
	animation_player = _find_animation_player(character_model)
	if animation_player == null:
		push_error("[LembahSari] AnimationPlayer tidak ditemukan.")
		return
	for clip: StringName in clips:
		if animation_player.has_animation(clip):
			var animation: Animation = animation_player.get_animation(clip)
			if animation != null:
				animation.loop_mode = Animation.LOOP_LINEAR
	_play_clip(0)

func _process(delta: float) -> void:
	if animation_player == null:
		return
	timer += delta
	if timer >= 3.0:
		timer = 0.0
		clip_index = (clip_index + 1) % clips.size()
		_play_clip(clip_index)

func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey:
		return
	var key_event := event as InputEventKey
	if not key_event.pressed or key_event.echo:
		return
	match key_event.keycode:
		KEY_1:
			_play_clip(0)
		KEY_2:
			_play_clip(1)
		KEY_3:
			_play_clip(2)

func _play_clip(index: int) -> void:
	clip_index = clampi(index, 0, clips.size() - 1)
	var clip: StringName = clips[clip_index]
	if animation_player.has_animation(clip):
		animation_player.play(clip, 0.15)
		print("[LembahSari] Preview animation: ", clip)

func _find_animation_player(root: Node) -> AnimationPlayer:
	if root is AnimationPlayer:
		return root as AnimationPlayer
	for child: Node in root.get_children():
		var found: AnimationPlayer = _find_animation_player(child)
		if found != null:
			return found
	return null
