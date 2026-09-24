extends Node

signal inventory_changed
signal money_changed(amount: int)

const SELL_PRICES: Dictionary = {
	"chili": 5000,
	"fish_wader": 8000,
	"fish_lele": 12000,
	"fish_nila": 15000
}

var items: Dictionary = {
	"chili": 0,
	"fish_wader": 0,
	"fish_lele": 0,
	"fish_nila": 0
}
var money: int = 0
var last_harvest_total: int = 0

func _ready() -> void:
	add_to_group("inventory_manager")
	call_deferred("_bind_farm_manager")

func _bind_farm_manager() -> void:
	var farm_nodes: Array[Node] = get_tree().get_nodes_in_group("farm_manager")
	if farm_nodes.is_empty():
		return
	var farm_manager: Node = farm_nodes[0]
	last_harvest_total = int(farm_manager.get("chili_harvested"))
	if farm_manager.has_signal("harvest_changed"):
		farm_manager.connect("harvest_changed", Callable(self, "_on_harvest_changed"))

func _on_harvest_changed(total: int) -> void:
	var gained: int = maxi(0, total - last_harvest_total)
	last_harvest_total = total
	if gained > 0:
		add_item("chili", gained)

func add_item(item_id: String, amount: int = 1) -> void:
	if amount <= 0:
		return
	var current_count: int = int(items.get(item_id, 0))
	items[item_id] = current_count + amount
	inventory_changed.emit()

func get_count(item_id: String) -> int:
	return int(items.get(item_id, 0))

func get_total_fish() -> int:
	return get_count("fish_wader") + get_count("fish_lele") + get_count("fish_nila")

func get_money() -> int:
	return money

func get_inventory_text() -> String:
	return "Tas: Cabai %d  •  Ikan %d\nRp %s" % [get_count("chili"), get_total_fish(), _format_number(money)]

func sell_all() -> Dictionary:
	var total_value: int = 0
	var sold_count: int = 0
	var item_keys: Array = items.keys()
	for key_value: Variant in item_keys:
		var item_id: String = str(key_value)
		var count: int = int(items.get(item_id, 0))
		if count <= 0:
			continue
		var unit_price: int = int(SELL_PRICES.get(item_id, 0))
		total_value += count * unit_price
		sold_count += count
		items[item_id] = 0

	if sold_count <= 0:
		return {"ok": false, "message": "Tas belum berisi hasil yang bisa dijual."}

	money += total_value
	inventory_changed.emit()
	money_changed.emit(money)
	return {
		"ok": true,
		"sold_count": sold_count,
		"earned": total_value,
		"message": "%d hasil terjual. Dapat Rp %s." % [sold_count, _format_number(total_value)]
	}

func _format_number(value: int) -> String:
	var raw: String = str(value)
	var result: String = ""
	var digit_count: int = 0
	for index: int in range(raw.length() - 1, -1, -1):
		if digit_count > 0 and digit_count % 3 == 0:
			result = "." + result
		result = raw.substr(index, 1) + result
		digit_count += 1
	return result
