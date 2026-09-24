extends Node

signal time_changed(display_time: String)
signal weather_changed(weather: String)
signal day_cycle_changed(period: String)
signal status_changed

const START_MINUTES := 6 * 60 + 30
const END_MINUTES := 24 * 60
const REAL_SECONDS_PER_GAME_DAY := 900.0
const GAME_MINUTES_PER_REAL_SECOND := float(END_MINUTES - START_MINUTES) / REAL_SECONDS_PER_GAME_DAY

var current_minutes: float = START_MINUTES
var weather: String = "sunny"
var period: String = "morning"
var rng: RandomNumberGenerator = RandomNumberGenerator.new()
var rain_visual: Node3D
var rain_drops: Array[Node3D] = []

@onready var world_environment: WorldEnvironment = get_parent().get_node("WorldEnvironment")
@onready var sun: DirectionalLight3D = get_parent().get_node("Sun")

func _ready() -> void:
	add_to_group("game_time")
	rng.randomize()
	_build_rain_visual()
	_roll_weather(false)
	_apply_world_lighting()
	status_changed.emit()

func _process(delta: float) -> void:
	current_minutes += GAME_MINUTES_PER_REAL_SECOND * delta
	if current_minutes >= END_MINUTES:
		_start_next_day()
	_update_period()
	_apply_world_lighting()
	_update_rain(delta)
	time_changed.emit(get_time_text())
	status_changed.emit()

func get_time_text() -> String:
	var total: int = int(current_minutes)
	var hour: int = total / 60
	var minute: int = total % 60
	return "%02d:%02d" % [hour, minute]

func get_period_text() -> String:
	match period:
		"morning": return "Pagi"
		"day": return "Siang"
		"evening": return "Sore"
		"night": return "Malam"
	return ""

func get_weather_text() -> String:
	return "Hujan" if weather == "rain" else "Cerah"

func get_status_text() -> String:
	return "%s  •  %s  •  %s" % [get_time_text(), get_period_text(), get_weather_text()]

func skip_to_next_day() -> Dictionary:
	return _start_next_day()

func _start_next_day() -> Dictionary:
	current_minutes = START_MINUTES
	var message: String = "Hari berikutnya dimulai."
	var managers: Array[Node] = get_tree().get_nodes_in_group("farm_manager")
	if not managers.is_empty():
		var result_value: Variant = managers[0].call("next_day")
		if result_value is Dictionary:
			var result: Dictionary = result_value as Dictionary
			message = str(result.get("message", message))
	_roll_weather(true)
	_update_period()
	_apply_world_lighting()
	status_changed.emit()
	return {"message": "%s Cuaca: %s." % [message, get_weather_text()]}

func _roll_weather(apply_rain_water: bool) -> void:
	weather = "rain" if rng.randf() < 0.35 else "sunny"
	if apply_rain_water and weather == "rain":
		var managers: Array[Node] = get_tree().get_nodes_in_group("farm_manager")
		if not managers.is_empty() and managers[0].has_method("water_all_planted"):
			managers[0].call("water_all_planted")
	_update_rain_visibility()
	weather_changed.emit(weather)

func _update_period() -> void:
	var hour: float = current_minutes / 60.0
	var next_period: String = "morning"
	if hour >= 18.5:
		next_period = "night"
	elif hour >= 16.5:
		next_period = "evening"
	elif hour >= 10.5:
		next_period = "day"
	if next_period != period:
		period = next_period
		day_cycle_changed.emit(period)

func _apply_world_lighting() -> void:
	if world_environment == null or world_environment.environment == null:
		return
	var env: Environment = world_environment.environment
	var hour: float = current_minutes / 60.0
	var daylight: float = 1.0
	var sky_color: Color = Color("a9cad1")
	var ambient: Color = Color("dedfc8")
	var sun_color: Color = Color("ffe8bd")

	if hour < 8.0:
		var dawn_t: float = clampf((hour - 6.5) / 1.5, 0.0, 1.0)
		daylight = lerpf(0.52, 0.88, dawn_t)
		sky_color = Color("e6b08e").lerp(Color("a9cad1"), dawn_t)
		ambient = Color("dcc0a7").lerp(Color("dedfc8"), dawn_t)
		sun_color = Color("efaa76").lerp(Color("ffe8bd"), dawn_t)
	elif hour < 15.5:
		daylight = 0.88
		sky_color = Color("a6cbd5")
		ambient = Color("dfdfc9")
		sun_color = Color("ffecc7")
	elif hour < 19.0:
		var evening_t: float = clampf((hour - 15.5) / 3.5, 0.0, 1.0)
		daylight = lerpf(0.88, 0.18, evening_t)
		sky_color = Color("aacbd2").lerp(Color("334158"), evening_t)
		ambient = Color("dfdec7").lerp(Color("626a78"), evening_t)
		sun_color = Color("ffe6b5").lerp(Color("e89568"), minf(1.0, evening_t * 1.2))
	else:
		daylight = 0.18
		sky_color = Color("334158")
		ambient = Color("626a78")
		sun_color = Color("b4c0d8")

	if weather == "rain":
		sky_color = sky_color.lerp(Color("778489"), 0.58)
		ambient = ambient.lerp(Color("9ba29c"), 0.40)
		sun_color = sun_color.lerp(Color("c4c9c3"), 0.55)
		daylight *= 0.68

	env.background_color = sky_color
	env.ambient_light_color = ambient
	env.ambient_light_energy = maxf(0.26, daylight * 0.64)
	sun.light_color = sun_color
	sun.light_energy = maxf(0.08, daylight * 0.92)

	var day_progress: float = clampf((current_minutes - START_MINUTES) / float(END_MINUTES - START_MINUTES), 0.0, 1.0)
	sun.rotation_degrees = Vector3(lerpf(-34.0, -142.0, day_progress), lerpf(-62.0, 62.0, day_progress), 0.0)

func _build_rain_visual() -> void:
	rain_visual = Node3D.new()
	rain_visual.name = "RainVisual"
	get_parent().add_child.call_deferred(rain_visual)
	for _index: int in range(56):
		var root: Node3D = Node3D.new()
		var mesh_instance: MeshInstance3D = MeshInstance3D.new()
		var mesh: BoxMesh = BoxMesh.new()
		mesh.size = Vector3(0.025, 0.65, 0.025)
		mesh_instance.mesh = mesh
		var material: StandardMaterial3D = StandardMaterial3D.new()
		material.albedo_color = Color(0.72, 0.88, 1.0, 0.72)
		material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mesh_instance.material_override = material
		root.add_child(mesh_instance)
		root.position = Vector3(rng.randf_range(-15.0, 15.0), rng.randf_range(2.0, 12.0), rng.randf_range(-12.0, 18.0))
		rain_visual.add_child(root)
		rain_drops.append(root)
	_update_rain_visibility()

func _update_rain_visibility() -> void:
	if rain_visual != null:
		rain_visual.visible = weather == "rain"

func _update_rain(delta: float) -> void:
	if weather != "rain" or rain_visual == null:
		return
	var players: Array[Node] = get_tree().get_nodes_in_group("player")
	var center: Vector3 = Vector3.ZERO
	if not players.is_empty():
		center = players[0].global_position
	for drop: Node3D in rain_drops:
		drop.position.y -= 15.0 * delta
		if drop.position.y < 0.2:
			drop.position = Vector3(center.x + rng.randf_range(-13.0, 13.0), rng.randf_range(8.0, 14.0), center.z + rng.randf_range(-10.0, 10.0))
