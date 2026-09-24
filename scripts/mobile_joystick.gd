extends Control

@export var radius: float = 68.0
var output := Vector2.ZERO
var touch_id := -1
var center := Vector2.ZERO

@onready var knob: Control = $Knob

func _ready() -> void:
	add_to_group("mobile_joystick")
	center = size * 0.5
	_reset_knob()

func get_output() -> Vector2:
	return output

func _gui_input(event: InputEvent) -> void:
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
	elif event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed:
				touch_id = 999
				_update_from_local(event.position)
			else:
				touch_id = -1
				output = Vector2.ZERO
				_reset_knob()
	elif event is InputEventMouseMotion and touch_id == 999 and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		_update_from_local(event.position)

func _update_from_local(local_pos: Vector2) -> void:
	var delta := local_pos - center
	if delta.length() > radius:
		delta = delta.normalized() * radius
	output = delta / radius
	knob.position = center + delta - knob.size * 0.5

func _reset_knob() -> void:
	knob.position = center - knob.size * 0.5
