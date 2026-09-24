extends Control

@export var radius: float = 68.0

var output := Vector2.ZERO
var touch_id := -1
var center := Vector2.ZERO
var mouse_active := false

@onready var knob: Control = $Knob

func _ready() -> void:
	add_to_group("mobile_joystick")
	center = size * 0.5
	_reset_knob()
	set_process_input(true)

func get_output() -> Vector2:
	return output

func _input(event: InputEvent) -> void:
	# Xogot/iOS can route touch through the viewport instead of _gui_input,
	# so handle it globally and only claim touches that begin on the joystick.
	if event is InputEventScreenTouch:
		if event.pressed:
			if touch_id == -1 and _contains_screen_point(event.position):
				touch_id = event.index
				_update_from_screen(event.position)
		elif event.index == touch_id:
			touch_id = -1
			output = Vector2.ZERO
			_reset_knob()
		return

	if event is InputEventScreenDrag and event.index == touch_id:
		_update_from_screen(event.position)
		return

	# Fallback for runtimes that emulate touch as mouse input.
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed and _contains_screen_point(event.position):
			mouse_active = true
			_update_from_screen(event.position)
		elif not event.pressed and mouse_active:
			mouse_active = false
			output = Vector2.ZERO
			_reset_knob()
		return

	if event is InputEventMouseMotion and mouse_active:
		_update_from_screen(event.position)

func _gui_input(event: InputEvent) -> void:
	# Keep normal Control input working on desktop/editor previews too.
	if event is InputEventScreenTouch:
		if event.pressed and touch_id == -1:
			touch_id = event.index
			_update_from_local(event.position)
		elif not event.pressed and event.index == touch_id:
			touch_id = -1
			output = Vector2.ZERO
			_reset_knob()
	elif event is InputEventScreenDrag and event.index == touch_id:
		_update_from_local(event.position)

func _contains_screen_point(screen_pos: Vector2) -> bool:
	return get_global_rect().grow(24.0).has_point(screen_pos)

func _update_from_screen(screen_pos: Vector2) -> void:
	var rect := get_global_rect()
	_update_from_local(screen_pos - rect.position)

func _update_from_local(local_pos: Vector2) -> void:
	var delta := local_pos - center
	if delta.length() > radius:
		delta = delta.normalized() * radius
	output = delta / radius
	if output.length() < 0.08:
		output = Vector2.ZERO
	knob.position = center + delta - knob.size * 0.5

func _reset_knob() -> void:
	knob.position = center - knob.size * 0.5
