extends Node

const NPC_LABEL_DISTANCE: float = 3.6
const ACTIVITY_LABEL_DISTANCE: float = 4.2

var player: Node3D = null
var npc_labels: Array[Label3D] = []
var activity_labels: Array[Label3D] = []

func _ready() -> void:
	call_deferred("_bind_scene")

func _process(_delta: float) -> void:
	if player == null:
		return
	_update_labels(npc_labels, NPC_LABEL_DISTANCE)
	_update_labels(activity_labels, ACTIVITY_LABEL_DISTANCE)

func _bind_scene() -> void:
	var players: Array[Node] = get_tree().get_nodes_in_group("player")
	if not players.is_empty() and players[0] is Node3D:
		player = players[0] as Node3D

	var npc_nodes: Array[Node] = get_tree().get_nodes_in_group("npc_manager")
	if not npc_nodes.is_empty():
		_collect_labels(npc_nodes[0], npc_labels)

	var activity_nodes: Array[Node] = get_tree().get_nodes_in_group("activity_manager")
	if not activity_nodes.is_empty():
		_collect_labels(activity_nodes[0], activity_labels)

	var controls_nodes: Array[Node] = get_tree().get_nodes_in_group("mobile_controls")
	if not controls_nodes.is_empty():
		var controls: Node = controls_nodes[0]
		if OS.get_name() != "Android" and OS.get_name() != "iOS":
			var day_button: Node = controls.get_node_or_null("Root/DayButton")
			if day_button is CanvasItem:
				(day_button as CanvasItem).visible = false
			var hint: Node = controls.get_node_or_null("Root/Hint")
			if hint is CanvasItem:
				(hint as CanvasItem).visible = false

func _collect_labels(root_node: Node, target: Array[Label3D]) -> void:
	for child: Node in root_node.get_children():
		if child is Label3D:
			var label: Label3D = child as Label3D
			label.visible = false
			target.append(label)
		_collect_labels(child, target)

func _update_labels(labels: Array[Label3D], visible_distance: float) -> void:
	for label: Label3D in labels:
		if not is_instance_valid(label):
			continue
		var distance: float = player.global_position.distance_to(label.global_position)
		label.visible = distance <= visible_distance
