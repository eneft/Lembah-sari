extends RefCounted
## Lightweight recognizable banana tree. Used only until the user's optimized
## GLB is present; then the original textured model replaces this fallback.
func build() -> Node3D:
	var plant := Node3D.new()
	plant.name = "IndonesianBananaTreeFallback"
	var stem := CylinderMesh.new()
	stem.height = 0.67
	stem.top_radius = 0.046
	stem.bottom_radius = 0.078
	stem.radial_segments = 10
	stem.rings = 2
	var trunk := MeshInstance3D.new()
	trunk.name = "BananaPseudostem"
	trunk.mesh = stem
	trunk.position.y = 0.335
	var bark := StandardMaterial3D.new()
	bark.albedo_color = Color("7f8a48")
	bark.roughness = 0.93
	trunk.material_override = bark
	plant.add_child(trunk)
	var leaves := SurfaceTool.new()
	leaves.begin(Mesh.PRIMITIVE_TRIANGLES)
	for leaf_index: int in range(9):
		var theta: float = TAU*float(leaf_index)/9.0+0.13
		var heading := Vector3(cos(theta),0.0,sin(theta))
		var tangent := Vector3(-sin(theta),0.0,cos(theta))
		var length: float = 0.35+0.09*float(leaf_index%3)
		var narrow: float = 0.095+0.015*float(leaf_index%2)
		var tilt: float = float(leaf_index%4)*0.055
		for step: int in range(8):
			var t0: float = float(step)/8.0
			var t1: float = float(step+1)/8.0
			var left0 := _leaf_point(t0,-1.0,length,narrow,tilt,heading,tangent)
			var right0 := _leaf_point(t0,1.0,length,narrow,tilt,heading,tangent)
			var left1 := _leaf_point(t1,-1.0,length,narrow,tilt,heading,tangent)
			var right1 := _leaf_point(t1,1.0,length,narrow,tilt,heading,tangent)
			_leaf_triangle(leaves,left0,right0,left1,t0,t0,t1)
			_leaf_triangle(leaves,right0,right1,left1,t0,t1,t1)
	var blade_mesh: ArrayMesh = leaves.commit() as ArrayMesh
	var foliage := MeshInstance3D.new()
	foliage.name = "BananaLeafCanopy"
	foliage.mesh = blade_mesh
	var leaf_material := StandardMaterial3D.new()
	leaf_material.resource_name = "BananaLeafWarmTropical"
	leaf_material.vertex_color_use_as_albedo = true
	leaf_material.albedo_color = Color.WHITE
	leaf_material.cull_mode = BaseMaterial3D.CULL_DISABLED
	leaf_material.roughness = 0.94
	foliage.material_override = leaf_material
	plant.add_child(foliage)
	plant.set_meta("fallback_banana",true)
	return plant

func _leaf_point(t: float,side: float,length: float,width: float,tilt: float,direction: Vector3,tangent: Vector3) -> Vector3:
	# Petiole lifts, broad center droops and the tip hangs like a banana leaf.
	var distance: float = length*t
	var shape: float = sin(PI*t)
	var elevation: float = 0.65+0.42*t-0.18*t*t-tilt*t
	return direction*distance+tangent*side*width*shape*0.5+Vector3.UP*(elevation+0.018*shape*(1.0-absf(side)))

func _leaf_triangle(st: SurfaceTool,a: Vector3,b: Vector3,c: Vector3,ha: float,hb: float,hc: float) -> void:
	for vertex: Dictionary in [
		{"position":a,"t":ha},
		{"position":b,"t":hb},
		{"position":c,"t":hc},
	]:
		var t: float = float(vertex["t"])
		var tone: Color = Color("416c2a").lerp(Color("8baf4b"),0.35+0.55*sin(PI*t))
		st.set_color(tone)
		st.set_uv(Vector2(t,0.5))
		st.add_vertex(vertex["position"])
