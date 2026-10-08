extends RefCounted
## Organic 3D grass in four cheap MultiMesh batches. Masked patches eliminate
## the visible rectangular "field of spikes" in the mobile screenshot.
## Farming surfaces, fixed camera and distant 2.5D foliage remain unchanged.
const GROUND_Y: float = -0.045
const GRASS_SEED: int = 20261008
const TERRAIN_MIN: Vector2 = Vector2(-8.1,-3.85)
const TERRAIN_MAX: Vector2 = Vector2(9.1,9.65)
const REGIONS: Array[Dictionary] = [
	{"name":"LawnGrass3D","amount":600,"rect":Rect2(0.085,0.615,0.855,0.178),"min_h":0.055,"max_h":0.138},
	{"name":"LeftGardenGrass3D","amount":320,"rect":Rect2(0.065,0.490,0.395,0.209),"min_h":0.060,"max_h":0.146},
	{"name":"RightGardenGrass3D","amount":265,"rect":Rect2(0.650,0.540,0.295,0.178),"min_h":0.050,"max_h":0.117},
	{"name":"RiverBankGrass3D","amount":270,"rect":Rect2(0.090,0.756,0.845,0.045),"min_h":0.110,"max_h":0.252},
]

func apply(world: Node3D, view: Camera3D, player: CharacterBody3D) -> void:
	var root := Node3D.new()
	root.name = "ForegroundGrass3D"
	world.add_child(root)
	var mesh: ArrayMesh = _build_blade_mesh()
	mesh.surface_set_material(0,_grass_material())
	var rng := RandomNumberGenerator.new()
	rng.seed = GRASS_SEED
	var frame_size: Vector2 = view.get_viewport().get_visible_rect().size
	var count: int = 0
	var edge_tufts: int = 0
	for region: Dictionary in REGIONS:
		var zone: Rect2 = region["rect"]
		var target: int = int(region["amount"])
		var transforms: Array[Transform3D] = []
		var tones: Array[Color] = []
		for attempt: int in range(target):
			var is_path_edge: bool = String(region["name"]) == "LawnGrass3D" and attempt >= 490
			var sample: Vector2
			if is_path_edge:
				var t: float = (float(attempt-490)+rng.randf())/110.0
				var track_a := Vector2(0.49,0.565)
				var track_b := Vector2(1.02,0.685)
				var tangent := (track_b-track_a).normalized()
				var normal := Vector2(-tangent.y,tangent.x)
				var sign_side: float = -1.0 if attempt % 2 == 0 else 1.0
				sample = track_a.lerp(track_b,t*0.93)+normal*sign_side*rng.randf_range(0.064,0.090)
			else:
				sample = Vector2(
					rng.randf_range(zone.position.x,zone.end.x),
					rng.randf_range(zone.position.y,zone.end.y)
				)
				# No hard linear borders: organic taper and islands in each zone.
				if rng.randf() > _coverage(String(region["name"]),sample):
					continue
			if _is_clear_zone(sample):
				continue
			var position: Vector3 = _ground_point(view,sample*frame_size)
			if not _is_playable_ground(position,player) or _near_foreground_plant(world,position):
				continue
			var height: float = rng.randf_range(float(region["min_h"]),float(region["max_h"]))
			if is_path_edge:
				height = rng.randf_range(0.040,0.083)
				edge_tufts += 1
			# Shallow, broad curved leaves. Earlier height-to-width ratio created
			# upright green spikes and a conspicuous square lawn.
			var spread: float = height*rng.randf_range(1.60,2.30)
			var spin: float = rng.randf_range(-PI,PI)
			var lean: float = rng.randf_range(-0.16,0.16)
			var basis: Basis = Basis.from_euler(Vector3(lean,spin,0.0)) * Basis.from_scale(Vector3(spread,height,spread))
			transforms.append(Transform3D(basis,position))
			var hue: float = rng.randf_range(0.85,1.055)
			tones.append(Color(hue*0.985,hue,hue*0.86,1.0))
		if transforms.is_empty():
			push_warning("[LembahSari] Grass region is outside playable ground: "+String(region["name"]))
			continue
		var minimum: float = INF
		var maximum: float = -INF
		for tr: Transform3D in transforms:
			var h: float = tr.basis.get_scale().y
			minimum = minf(minimum,h)
			maximum = maxf(maximum,h)
		var multimesh := MultiMesh.new()
		multimesh.transform_format = MultiMesh.TRANSFORM_3D
		multimesh.use_colors = true
		multimesh.mesh = mesh
		multimesh.instance_count = transforms.size()
		for i: int in range(transforms.size()):
			multimesh.set_instance_transform(i,transforms[i])
			multimesh.set_instance_color(i,tones[i])
		var draw := MultiMeshInstance3D.new()
		draw.name = String(region["name"])
		draw.multimesh = multimesh
		draw.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		draw.set_meta("authored_min_height",minimum)
		draw.set_meta("authored_max_height",maximum)
		root.add_child(draw)
		count += transforms.size()
	root.set_meta("tufts",count)
	root.set_meta("path_edge_tufts",edge_tufts)
	root.set_meta("batches",root.get_child_count())
	root.set_meta("image_background_preserved",true)
	root.set_meta("organic_mask",true)
	root.set_meta("blade_profile","curved_broad")
	print("[LembahSari] ORGANIC_GRASS_READY tufts=%d batches=%d path_edge=%d masks=organic foreground=polygon far=image" % [count,root.get_child_count(),edge_tufts])

func _coverage(name: String,p: Vector2) -> float:
	# Several overlapping pockets, never an x/y-aligned solid rectangle.
	var distance: float = 3.0
	if name == "LawnGrass3D":
		distance = minf(distance,_oval(p,Vector2(0.27,0.711),Vector2(0.24,0.070)))
		distance = minf(distance,_oval(p,Vector2(0.53,0.734),Vector2(0.255,0.065)))
		distance = minf(distance,_oval(p,Vector2(0.77,0.708),Vector2(0.195,0.060)))
	elif name == "LeftGardenGrass3D":
		distance = minf(_oval(p,Vector2(0.25,0.580),Vector2(0.185,0.077)),_oval(p,Vector2(0.38,0.652),Vector2(0.135,0.048)))
	elif name == "RightGardenGrass3D":
		distance = minf(_oval(p,Vector2(0.79,0.657),Vector2(0.140,0.054)),_oval(p,Vector2(0.91,0.671),Vector2(0.085,0.048)))
	else:
		# The river fringe needs small irregular gaps between clusters.
		distance = minf(_oval(p,Vector2(0.23,0.778),Vector2(0.155,0.035)),_oval(p,Vector2(0.51,0.779),Vector2(0.210,0.034)))
		distance = minf(distance,_oval(p,Vector2(0.80,0.774),Vector2(0.155,0.035)))
	var irregularity: float = sin(p.x*54.0+p.y*73.0)*0.115 + sin(p.x*91.0-p.y*48.0)*0.085
	var edge: float = clampf((1.13-distance+irregularity)*1.65,0.0,1.0)
	# Keep small bare patches among plants, for depth and readability.
	var pocket: float = 0.70+0.30*(0.5+0.5*sin(p.x*128.0+p.y*53.0))
	return edge*pocket

func _oval(p: Vector2,center: Vector2,radius: Vector2) -> float:
	return ((p-center)/radius).length()

func _build_blade_mesh() -> ArrayMesh:
	# Eight curved leaves with a broad basal fan, an arch and drooping tips.
	# All blades are double-sided and receive the same sun/fog as tree meshes.
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for blade: int in range(8):
		var angle: float = TAU*float(blade)/8.0
		var outward := Vector3(cos(angle),0.0,sin(angle))
		var sideways := Vector3(-sin(angle),0.0,cos(angle))
		var length_factor: float = 0.72+float(blade%4)*0.085
		for step: int in range(3):
			var t0: float = float(step)/3.0
			var t1: float = float(step+1)/3.0
			var l0: Vector3 = _leaf_vertex(t0,-1.0,length_factor,outward,sideways)
			var r0: Vector3 = _leaf_vertex(t0,1.0,length_factor,outward,sideways)
			var l1: Vector3 = _leaf_vertex(t1,-1.0,length_factor,outward,sideways)
			var r1: Vector3 = _leaf_vertex(t1,1.0,length_factor,outward,sideways)
			_triangle(st,l0,r0,l1,t0,t0,t1)
			_triangle(st,r0,r1,l1,t0,t1,t1)
	st.generate_normals()
	return st.commit() as ArrayMesh

func _leaf_vertex(t: float,side: float,length_factor: float,radial: Vector3,tangent: Vector3) -> Vector3:
	var lean: float = t*t*0.76+0.06
	var tip_droop: float = 0.19*t*t*t
	var height: float = length_factor*(t-tip_droop)
	var broad: float = (1.0-t)*0.13*(0.55+0.45*sin(PI*t))
	return radial*(0.025+lean)+tangent*side*broad+Vector3.UP*height

func _triangle(st: SurfaceTool,a: Vector3,b: Vector3,c: Vector3,ta: float,tb: float,tc: float) -> void:
	for point: Dictionary in [
		{"p":a,"t":ta},
		{"p":b,"t":tb},
		{"p":c,"t":tc}
	]:
		var t: float = float(point["t"])
		var tint := Color("435735").lerp(Color("8b995e"),t*0.87)
		st.set_color(tint)
		st.set_uv(Vector2(t,0.5))
		st.add_vertex(point["p"])

func _grass_material() -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.resource_name = "LembahSariCurvedWarmGrass"
	mat.vertex_color_use_as_albedo = true
	mat.albedo_color = Color.WHITE
	mat.roughness = 1.0
	mat.metallic = 0.0
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	return mat

func _ground_point(view: Camera3D,pixel: Vector2) -> Vector3:
	var origin: Vector3 = view.project_ray_origin(pixel)
	var ray: Vector3 = view.project_ray_normal(pixel)
	if ray.y > -0.001:
		return Vector3(9999.0,GROUND_Y,9999.0)
	return origin+ray*((GROUND_Y-origin.y)/ray.y)

func _is_playable_ground(at: Vector3,player: CharacterBody3D) -> bool:
	if at.x < TERRAIN_MIN.x or at.x > TERRAIN_MAX.x or at.z < TERRAIN_MIN.y or at.z > TERRAIN_MAX.y:
		return false
	var delta := Vector2(at.x-player.global_position.x,at.z-player.global_position.z)
	return delta.length_squared() > 0.68*0.68

func _is_clear_zone(p: Vector2) -> bool:
	# Leave the walking strip, landing, crops and water free of ornamental grass.
	var a := Vector2(0.49,0.565)
	var b := Vector2(1.02,0.685)
	var ab := b-a
	var t: float = clampf((p-a).dot(ab)/ab.length_squared(),0.0,1.0)
	if p.distance_to(a+ab*t) < 0.055:
		return true
	if p.x > 0.66 and p.y < 0.59:
		return true
	if p.x > 0.37 and p.x < 0.66 and p.y < 0.57:
		return true
	return p.y >= 0.805

func _near_foreground_plant(world: Node3D,point: Vector3) -> bool:
	var hero: Node3D = world.get_node_or_null("HeroSceneV5") as Node3D
	if hero == null:
		return false
	var plants: Node3D = hero.get_node_or_null("ForegroundPlants3D") as Node3D
	if plants == null:
		return false
	for node: Node in plants.get_children():
		if not node is Node3D:
			continue
		var plant := node as Node3D
		var kind: int = int(plant.get_meta("plant_type",-1))
		var clearance: float = 0.57 if kind <= 1 else (0.49 if kind == 4 else 0.38)
		if Vector2(point.x-plant.global_position.x,point.z-plant.global_position.z).length_squared() < clearance*clearance:
			return true
	return false
