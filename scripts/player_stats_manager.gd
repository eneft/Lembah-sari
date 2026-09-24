extends Node

signal stamina_changed(current: float, maximum: float)

const MAX_STAMINA: float = 100.0
const RUN_DRAIN_PER_SECOND: float = 4.0

var stamina: float = MAX_STAMINA

func _ready() -> void:
	add_to_group("player_stats")
	call_deferred("_bind_day_cycle")
	stamina_changed.emit(stamina, MAX_STAMINA)

func _bind_day_cycle() -> void:
	var farm_nodes: Array[Node] = get_tree().get_nodes_in_group("farm_manager")
	if farm_nodes.is_empty():
		return
	var farm_manager: Node = farm_nodes[0]
	if farm_manager.has_signal("day_changed"):
		farm_manager.connect("day_changed", Callable(self, "_on_day_changed"))

func _on_day_changed(_day: int) -> void:
	restore_full()

func get_stamina() -> float:
	return stamina

func get_max_stamina() -> float:
	return MAX_STAMINA

func has_stamina(amount: float = 0.1) -> bool:
	return stamina >= amount

func spend_stamina(amount: float) -> bool:
	if amount <= 0.0:
		return true
	if stamina + 0.001 < amount:
		return false
	stamina = maxf(0.0, stamina - amount)
	stamina_changed.emit(stamina, MAX_STAMINA)
	return true

func drain_running(delta: float) -> bool:
	if stamina <= 0.0:
		return false
	stamina = maxf(0.0, stamina - RUN_DRAIN_PER_SECOND * delta)
	stamina_changed.emit(stamina, MAX_STAMINA)
	return stamina > 0.0

func restore_full() -> void:
	stamina = MAX_STAMINA
	stamina_changed.emit(stamina, MAX_STAMINA)

func get_status_text() -> String:
	return "Stamina %d/%d" % [int(round(stamina)), int(MAX_STAMINA)]
