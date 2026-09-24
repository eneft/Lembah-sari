extends Node3D

const WIDTH: float = 52.0
const DEPTH: float = 42.0
const COLS: int = 24
const ROWS: int = 20

func _ready() -> void:
	_build_ground_overlay()

func _terrain_height(x_value: float, z_value: float) -> float:
	var broad: float = sin(x_value * 0.11) * 0.07 + cos(z_value * 0.15) * 0.05
	var edge_lift: float = maxf(0.0, (absf(x_value) - 18.0) * 0.018) + maxf(0.0, (absf(z_value) - 15.0) * 0.025)
	return broad + edge_lift + 0.012

func _build_ground_overlay() -> void:
	var surface: SurfaceTool = SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for row: int in range(ROWS - 1):
		for col: int in range(COLS - 1):
			var x0: float = -WIDTH * 0.5 + WIDTH * float(col) / float(COLS - 1)
			var x1: float = -WIDTH * 0.5 + WIDTH * float(col + 1) / float(COLS - 1)
			var z0: float = -DEPTH * 0.5 + DEPTH * float(row) / float(ROWS - 1)
			var z1: float = -DEPTH * 0.5 + DEPTH * float(row + 1) / float(ROWS - 1)
			var a: Vector3 = Vector3(x0, _terrain_height(x0, z0), z0)
			var b: Vector3 = Vector3(x1, _terrain_height(x1, z0), z0)
			var c: Vector3 = Vector3(x1, _terrain_height(x1, z1), z1)
			var d: Vector3 = Vector3(x0, _terrain_height(x0, z1), z1)
			for vertex: Vector3 in [a, b, c, a, c, d]:
				surface.add_vertex(vertex)
	surface.generate_normals()
	var mesh: ArrayMesh = surface.commit()
	var mesh_instance: MeshInstance3D = MeshInstance3D.new()
	mesh_instance.name = "ConceptGroundOverlay"
	mesh_instance.mesh = mesh
	var shader: Shader = load("res://shaders/concept_ground.gdshader") as Shader
	var material: ShaderMaterial = ShaderMaterial.new()
	material.shader = shader
	mesh_instance.material_override = material
	add_child(mesh_instance)
