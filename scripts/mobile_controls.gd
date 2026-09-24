extends CanvasLayer

func _ready() -> void:
	$Root/ActionButton.pressed.connect(_on_action_pressed)

func _on_action_pressed() -> void:
	Input.action_press("interact")
	await get_tree().process_frame
	Input.action_release("interact")
