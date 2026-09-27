extends Node3D

@onready var camera: Camera3D = $Camera3D

func _ready() -> void:
	# The sprite already contains the authored 3/4 perspective. The Godot camera
	# only supplies the lightweight 3D stage used by the final game pipeline.
	camera.look_at(Vector3(0.0, 2.6, 0.0), Vector3.UP)
