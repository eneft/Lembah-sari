extends CanvasLayer

var player: Node = null
var farm_manager: Node = null
var time_manager: Node = null
var inventory_manager: Node = null
var stats_manager: Node = null

@onready var joystick_control: Control = $Root/Joystick
@onready var action_button: Button = $Root/ActionButton
@onready var hoe_button: Button = $Root/HoeButton
@onready var seed_button: Button = $Root/SeedButton
@onready var water_button: Button = $Root/WaterButton
@onready var hand_button: Button = $Root/HandButton
@onready var rod_button: Button = $Root/RodButton
@onready var sell_button: Button = $Root/SellButton
@onready var day_button: Button = $Root/DayButton
@onready var status_label: Label = $Root/Status
@onready var inventory_label: Label = $Root/Inventory
@onready var stamina_bar: ProgressBar = $Root/StaminaBar
@onready var stamina_label: Label = $Root/StaminaLabel
@onready var feedback_label: Label = $Root/Feedback
@onready var hint_label: Label = $Root/Hint
@onready var dialogue_panel: Panel = $Root/DialoguePanel
@onready var dialogue_name: Label = $Root/DialoguePanel/Speaker
@onready var dialogue_text: Label = $Root/DialoguePanel/Text
@onready var dialogue_close: Button = $Root/DialoguePanel/CloseButton
@onready var day_transition: ColorRect = $Root/DayTransition
@onready var day_transition_text: Label = $Root/DayTransition/Text

func _ready() -> void:
	add_to_group("mobile_controls")
	action_button.pressed.connect(_on_action_pressed)
	hoe_button.pressed.connect(func() -> void: _select_tool("hoe"))
	seed_button.pressed.connect(func() -> void: _select_tool("seed"))
	water_button.pressed.connect(func() -> void: _select_tool("water"))
	hand_button.pressed.connect(func() -> void: _select_tool("hand"))
	rod_button.pressed.connect(func() -> void: _select_tool("rod"))
	sell_button.pressed.connect(func() -> void: _select_tool("sell"))
	day_button.pressed.connect(_on_next_day_pressed)
	dialogue_close.pressed.connect(_close_dialogue)
	dialogue_panel.visible = false
	day_transition.visible = false
	_apply_platform_layout()
	call_deferred("_bind_game")

func _apply_platform_layout() -> void:
	var platform_name: String = OS.get_name()
	var is_mobile_platform: bool = platform_name == "Android" or platform_name == "iOS"
	joystick_control.visible = is_mobile_platform
	action_button.visible = is_mobile_platform
	if is_mobile_platform:
		hint_label.text = "Lembah Sari 0.0.7b  •  pilih alat • AKSI"
	else:
		hint_label.text = "Lembah Sari 0.0.7b  •  1–6 alat • E interaksi"

func _unhandled_input(event: InputEvent) -> void:
	if dialogue_panel.visible and event.is_action_pressed("interact"):
		_close_dialogue()
		get_viewport().set_input_as_handled()

func _bind_game() -> void:
	var players: Array[Node] = get_tree().get_nodes_in_group("player")
	if not players.is_empty():
		player = players[0]
		if player.has_signal("tool_changed"):
			player.connect("tool_changed", Callable(self, "_on_tool_changed"))
		if player.has_signal("farming_feedback"):
			player.connect("farming_feedback", Callable(self, "_on_feedback"))
		if player.has_signal("dialogue_requested"):
			player.connect("dialogue_requested", Callable(self, "_on_dialogue_requested"))
		if player.has_signal("day_transition_requested"):
			player.connect("day_transition_requested", Callable(self, "_on_day_transition_requested"))

	var managers: Array[Node] = get_tree().get_nodes_in_group("farm_manager")
	if not managers.is_empty():
		farm_manager = managers[0]
		if farm_manager.has_signal("day_changed"):
			farm_manager.connect("day_changed", Callable(self, "_on_day_changed"))
		if farm_manager.has_signal("harvest_changed"):
			farm_manager.connect("harvest_changed", Callable(self, "_on_harvest_changed"))

	var clocks: Array[Node] = get_tree().get_nodes_in_group("game_time")
	if not clocks.is_empty():
		time_manager = clocks[0]
		if time_manager.has_signal("status_changed"):
			time_manager.connect("status_changed", Callable(self, "_refresh_status"))
		if time_manager.has_signal("weather_changed"):
			time_manager.connect("weather_changed", Callable(self, "_on_weather_changed"))

	var inventories: Array[Node] = get_tree().get_nodes_in_group("inventory_manager")
	if not inventories.is_empty():
		inventory_manager = inventories[0]
		if inventory_manager.has_signal("inventory_changed"):
			inventory_manager.connect("inventory_changed", Callable(self, "_refresh_inventory"))

	var stats_nodes: Array[Node] = get_tree().get_nodes_in_group("player_stats")
	if not stats_nodes.is_empty():
		stats_manager = stats_nodes[0]
		if stats_manager.has_signal("stamina_changed"):
			stats_manager.connect("stamina_changed", Callable(self, "_on_stamina_changed"))

	_on_tool_changed("hoe")
	_refresh_status()
	_refresh_inventory()
	_refresh_stamina()

func _on_action_pressed() -> void:
	if day_transition.visible:
		return
	if dialogue_panel.visible:
		_close_dialogue()
		return
	Input.action_press("interact")
	await get_tree().process_frame
	Input.action_release("interact")

func _select_tool(tool: String) -> void:
	if dialogue_panel.visible or day_transition.visible:
		return
	if player != null and player.has_method("set_tool"):
		player.call("set_tool", tool)

func _on_next_day_pressed() -> void:
	if dialogue_panel.visible or day_transition.visible:
		return
	if time_manager != null and time_manager.has_method("skip_to_next_day"):
		var day_value: Variant = time_manager.call("skip_to_next_day")
		if day_value is Dictionary:
			var result: Dictionary = day_value as Dictionary
			_on_feedback(str(result.get("message", "Hari berikutnya dimulai.")))
		_refresh_status()
		_refresh_stamina()
		return
	if farm_manager != null and farm_manager.has_method("next_day"):
		var fallback_value: Variant = farm_manager.call("next_day")
		if fallback_value is Dictionary:
			var fallback: Dictionary = fallback_value as Dictionary
			_on_feedback(str(fallback.get("message", "Hari berikutnya dimulai.")))
		_refresh_status()
		_refresh_stamina()
		return
	_on_feedback("Sistem waktu belum siap.")

func _on_tool_changed(tool: String) -> void:
	var labels: Dictionary = {
		"hoe": "Cangkul",
		"seed": "Benih",
		"water": "Siram",
		"hand": "Panen",
		"rod": "Pancing",
		"sell": "Jual"
	}
	hoe_button.text = "Cangkul"
	seed_button.text = "Benih"
	water_button.text = "Siram"
	hand_button.text = "Panen"
	rod_button.text = "Pancing"
	sell_button.text = "Jual"
	match tool:
		"hoe": hoe_button.text = "● Cangkul"
		"seed": seed_button.text = "● Benih"
		"water": water_button.text = "● Siram"
		"hand": hand_button.text = "● Panen"
		"rod": rod_button.text = "● Pancing"
		"sell": sell_button.text = "● Jual"
	var platform_name: String = OS.get_name()
	if platform_name == "Android" or platform_name == "iOS":
		hint_label.text = "Lembah Sari 0.0.7b  •  %s • AKSI" % str(labels.get(tool, tool))
	else:
		hint_label.text = "Lembah Sari 0.0.7b  •  %s • E interaksi" % str(labels.get(tool, tool))

func _on_dialogue_requested(speaker: String, text: String) -> void:
	dialogue_name.text = speaker
	dialogue_text.text = text
	dialogue_panel.visible = true
	feedback_label.text = ""
	if player != null and player.has_method("set_input_locked"):
		player.call("set_input_locked", true)

func _close_dialogue() -> void:
	if not dialogue_panel.visible:
		return
	dialogue_panel.visible = false
	if player != null and player.has_method("set_input_locked"):
		player.call("set_input_locked", false)

func _on_day_transition_requested(summary: String) -> void:
	if player != null and player.has_method("set_input_locked"):
		player.call("set_input_locked", true)
	day_transition_text.text = "Hari Baru\n\n%s" % summary
	day_transition.modulate.a = 0.0
	day_transition.visible = true
	var tween: Tween = create_tween()
	tween.tween_property(day_transition, "modulate:a", 1.0, 0.35)
	tween.tween_interval(1.1)
	tween.tween_property(day_transition, "modulate:a", 0.0, 0.6)
	await tween.finished
	day_transition.visible = false
	if player != null and player.has_method("set_input_locked"):
		player.call("set_input_locked", false)
	_refresh_status()
	_refresh_inventory()
	_refresh_stamina()

func _on_weather_changed(weather_value: String) -> void:
	if weather_value == "rain":
		_on_feedback("Hujan turun. Tanaman yang sudah ditanam akan tersiram.")

func _on_day_changed(_day: int) -> void:
	_refresh_status()
	_refresh_stamina()

func _on_harvest_changed(_total: int) -> void:
	_refresh_status()
	_refresh_inventory()

func _on_stamina_changed(_current: float, _maximum: float) -> void:
	_refresh_stamina()

func _on_feedback(text: String) -> void:
	if dialogue_panel.visible or day_transition.visible:
		return
	feedback_label.text = text
	feedback_label.modulate.a = 1.0
	var tween: Tween = create_tween()
	tween.tween_interval(2.2)
	tween.tween_property(feedback_label, "modulate:a", 0.35, 0.6)

func _refresh_status() -> void:
	var farm_text: String = "Hari 1  •  Cabai panen 0"
	if farm_manager != null and farm_manager.has_method("get_status_text"):
		farm_text = str(farm_manager.call("get_status_text"))
	var clock_text: String = "06:30  •  Pagi  •  Cerah"
	if time_manager != null and time_manager.has_method("get_status_text"):
		clock_text = str(time_manager.call("get_status_text"))
	status_label.text = "%s\n%s" % [farm_text, clock_text]

func _refresh_inventory() -> void:
	if inventory_manager != null and inventory_manager.has_method("get_inventory_text"):
		inventory_label.text = str(inventory_manager.call("get_inventory_text"))
	else:
		inventory_label.text = "Tas: Cabai 0  •  Ikan 0\nRp 0"

func _refresh_stamina() -> void:
	var current: float = 100.0
	var maximum: float = 100.0
	if stats_manager != null:
		if stats_manager.has_method("get_stamina"):
			current = float(stats_manager.call("get_stamina"))
		if stats_manager.has_method("get_max_stamina"):
			maximum = float(stats_manager.call("get_max_stamina"))
	stamina_bar.max_value = maximum
	stamina_bar.value = current
	stamina_label.text = "Stamina %d/%d" % [int(round(current)), int(round(maximum))]
