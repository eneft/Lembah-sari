extends CanvasLayer

var player: Node = null
var farm_manager: Node = null
var time_manager: Node = null

@onready var action_button: Button = $Root/ActionButton
@onready var hoe_button: Button = $Root/HoeButton
@onready var seed_button: Button = $Root/SeedButton
@onready var water_button: Button = $Root/WaterButton
@onready var hand_button: Button = $Root/HandButton
@onready var day_button: Button = $Root/DayButton
@onready var status_label: Label = $Root/Status
@onready var feedback_label: Label = $Root/Feedback
@onready var hint_label: Label = $Root/Hint

func _ready() -> void:
	add_to_group("mobile_controls")
	action_button.pressed.connect(_on_action_pressed)
	hoe_button.pressed.connect(func(): _select_tool("hoe"))
	seed_button.pressed.connect(func(): _select_tool("seed"))
	water_button.pressed.connect(func(): _select_tool("water"))
	hand_button.pressed.connect(func(): _select_tool("hand"))
	day_button.pressed.connect(_on_next_day_pressed)
	call_deferred("_bind_game")

func _bind_game() -> void:
	var players := get_tree().get_nodes_in_group("player")
	if not players.is_empty():
		player = players[0]
		if player.has_signal("tool_changed"):
			player.tool_changed.connect(_on_tool_changed)
		if player.has_signal("farming_feedback"):
			player.farming_feedback.connect(_on_feedback)

	var managers := get_tree().get_nodes_in_group("farm_manager")
	if not managers.is_empty():
		farm_manager = managers[0]
		if farm_manager.has_signal("day_changed"):
			farm_manager.day_changed.connect(func(_day): _refresh_status())
		if farm_manager.has_signal("harvest_changed"):
			farm_manager.harvest_changed.connect(func(_total): _refresh_status())

	var clocks := get_tree().get_nodes_in_group("game_time")
	if not clocks.is_empty():
		time_manager = clocks[0]
		if time_manager.has_signal("status_changed"):
			time_manager.status_changed.connect(_refresh_status)
		if time_manager.has_signal("weather_changed"):
			time_manager.weather_changed.connect(func(weather): _on_weather_changed(str(weather)))

	_on_tool_changed("hoe")
	_refresh_status()

func _on_action_pressed() -> void:
	Input.action_press("interact")
	await get_tree().process_frame
	Input.action_release("interact")

func _select_tool(tool: String) -> void:
	if player != null and player.has_method("set_tool"):
		player.set_tool(tool)

func _on_next_day_pressed() -> void:
	if time_manager != null and time_manager.has_method("skip_to_next_day"):
		var result: Dictionary = time_manager.skip_to_next_day()
		_on_feedback(str(result.get("message", "Hari berikutnya dimulai.")))
		_refresh_status()
		return
	if farm_manager != null:
		var fallback: Dictionary = farm_manager.next_day()
		_on_feedback(str(fallback.get("message", "Hari berikutnya dimulai.")))
		_refresh_status()
		return
	_on_feedback("Sistem waktu belum siap.")

func _on_tool_changed(tool: String) -> void:
	var labels := {
		"hoe": "Cangkul",
		"seed": "Benih",
		"water": "Siram",
		"hand": "Panen"
	}
	hoe_button.text = "Cangkul"
	seed_button.text = "Benih"
	water_button.text = "Siram"
	hand_button.text = "Panen"
	match tool:
		"hoe": hoe_button.text = "● Cangkul"
		"seed": seed_button.text = "● Benih"
		"water": water_button.text = "● Siram"
		"hand": hand_button.text = "● Panen"
	hint_label.text = "Lembah Sari 0.0.3  •  %s dipilih  •  A = gunakan" % labels.get(tool, tool)

func _on_weather_changed(weather: String) -> void:
	if weather == "rain":
		_on_feedback("Hujan turun. Tanaman yang sudah ditanam akan tersiram.")

func _on_feedback(text: String) -> void:
	feedback_label.text = text
	feedback_label.modulate.a = 1.0
	var tween := create_tween()
	tween.tween_interval(2.2)
	tween.tween_property(feedback_label, "modulate:a", 0.35, 0.6)

func _refresh_status() -> void:
	var farm_text := "Hari 1  •  Cabai 0"
	if farm_manager != null and farm_manager.has_method("get_status_text"):
		farm_text = farm_manager.get_status_text()
	var clock_text := "06:30  •  Pagi  •  Cerah"
	if time_manager != null and time_manager.has_method("get_status_text"):
		clock_text = time_manager.get_status_text()
	status_label.text = "%s\n%s" % [farm_text, clock_text]
