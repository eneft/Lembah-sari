extends Node

signal time_changed(display_time: String)
signal weather_changed(weather: String)
signal day_cycle_changed(period: String)
signal status_changed

# 06:30 -> 24:00 takes about 15 real minutes at 1x speed.
const START_MINUTES := 6 * 60 + 30
const END_MINUTES := 24 * 60
const REAL_SECONDS_PER_GAME_DAY := 900.0
const GAME_MINUTES_PER_REAL_SECOND := float(END_MINUTES - START_MINUTES) / REAL_SECONDS_PER_GAME_DAY

var current_minutes: float = START_MINUTES
var weather: String = "sunny"
var period: String = "morning"
var rng := RandomNumberGenerator.new()
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
	var total := int(current_minutes)
	var hour := total / 60
	var minute := total % 60
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
	var message := "Hari berikutnya dimulai."
	var managers := get_tree().get_nodes_in_group("farm_manager")
	if not managers.is_empty():
		var result: Dictionary = managers[0].next_day()
		message = str(result.get("message", message))
	_roll_weather(true)
	_update_period()
	_apply_world_lighting()
	status_changed.emit()
	return {"message": "%s Cuaca: %s." % [message, get_weather_text()]}

func _roll_weather(apply_rain_water: bool) -> void:
	# Prototype rainy-season bias: 35% chance of rain each new day.
	weather = "rain" if rng.randf() < 0.35 else "sunny"
	if apply_rain_water and weather == "rain":
		var managers := get_tree().get_nodes_in_group("farm_manager")
		if not managers.is_empty() and managers[0].has_method("water_all_planted"):
			managers[0].water_all_planted()
	_update_rain_visibility()
	weather_changed.emit(weather)

func _update_period() -> void:
	var hour := current_minutes / 60.0
	var next_period := "morning"
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
	var env := world_environment.environment
	var hour := current_minutes / 60.0
	var daylight := 1.0
	var sky_color := Color("94cdf2")
	var ambient := Color("d5e4ff")

	if hour < 8.0:
		var t := clamp((hour - 6.5) / 1.5, 0.0, 1.0)
		daylight = lerp(0.55, 1.0, t)
		sky_color = Color("efaa83").lerp(Color("94cdf2"), t)
		ambient = Color("e7b49b").lerp(Color("d5e4ff"), t)
	elif hour < 16.5:
		daylight = 1.0
	elif hour < 19.0:
		var t := clamp((hour - 16.5) / 2.5, 0.0, 1.0)
		daylight = lerp(1.0, 0.22, t)
		sky_color = Color("94cdf2").lerp(Color("172844"), t)
		ambient = Color("d5e4ff").lerp(Color("52627f"), t)
	else:
		daylight = 0.22
		sky_color = Color("172844")
		ambient = Color("52627f")

	if weather == "rain":
		sky_color = sky_color.lerp(Color("657786"), 0.55)
		ambient = ambient.lerp(Color("91a1ad"), 0.35)
		daylight *= 0.72

	env.background_color = sky_color
	env.ambient_light_color = ambient
	env.ambient_light_energy = max(0.25, daylight * 0.85)
	sun.light_energy = max(0.08, daylight * 1.2)

	# Sun travels east to west during the playable day.
	var day_progress := clamp((current_minutes - START_MINUTES) / float(END_MINUTES - START_MINUTES), 0.0, 1.0)
	sun.rotation_degrees = Vector3(lerp(-22.0, -158.0, day_progress), lerp(-70.0, 70.0, day_progress), 0.0)

func _build_rain_visual() -> void:
	rain_visual = Node3D.new()
	rain_visual.name = "RainVisual"
	get_parent().add_child.call_deferred(rain_visual)
	for i in range(56):
		var root := Node3D.new()
		var mesh_instance := MeshInstance3D.new()
		var mesh := BoxMesh.new()
		mesh.size = Vector3(0.025, 0.65, 0.025)
		mesh_instance.mesh = mesh
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.72, 0.88, 1.0, 0.72)
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mesh_instance.material_override = mat
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
	var players := get_tree().get_nodes_in_group("player")
	var center := Vector3.ZERO
	if not players.is_empty():
		center = players[0].global_position
	for drop in rain_drops:
		drop.position.y -= 15.0 * delta
		if drop.position.y < 0.2:
			drop.position = Vector3(center.x + rng.randf_range(-13.0, 13.0), rng.randf_range(8.0, 14.0), center.z + rng.randf_range(-10.0, 10.0))
