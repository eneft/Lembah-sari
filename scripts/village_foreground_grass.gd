extends RefCounted
## Organic, short, curved real grass in four batched foreground zones.
## Fixed-camera *screen masks* delimit playable grass only; density and silhouette
## are noise-shaped so a rectangular hedge cannot form beside the river.
const GROUND_Y: float = -0.043
const GRASS_SEED: int = 20261008
const TERRAIN_MIN: Vector2 = Vector2(-8.1,-3.85)
const TERRAIN_MAX: Vector2 = Vector2(9.1,9.65)
const REGIONS: Array[Dictionary] = [
	{"name":"LawnGrass3D","amount":1210,"rect":Rect2(0.065,0.638,0.87,0.149),"min_h":0.075,"max_h":0.165},
	{"name":"LeftGardenGrass3D","amount":570,"rect":Rect2(0.078,0.49,0.39,0.21),"min_h":0.082,"max_h":0.165},
	{"name":"RightGardenGrass3D","amount":1450,"rect":Rect2(0.66,0.51,0.30,0.20),"min_h":0.070,"max_h":0.148},
	{"name":"RiverBankGrass3D","amount":590,"rect":Rect2(0.09,0.741,0.81,0.062),"min_h":0.13,"max_h":0.245},
]

func apply(world: Node3D,view: Camera3D,player: CharacterBody3D) -> void:
	var root := Node3D.new()
	root.name = "ForegroundGrass3D"
	world.add_child(root)
	var grass_mesh: ArrayMesh = _build_leaf_mesh()
	grass_mesh.surface_set_material(0,_grass_material())
	var rng := RandomNumberGenerator.new()
	rng.seed = GRASS_SEED
	var noise := FastNoiseLite.new()
	noise.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	noise.seed = GRASS_SEED
	noise.frequency = 0.016
	noise.fractal_type = FastNoiseLite.FRACTAL_FBM
	noise.fractal_octaves = 2
	var pixels: Vector2 = view.get_viewport().get_visible_rect().size
	var count: int = 0
	var short_path_edges: int = 0
	for region: Dictionary in REGIONS:
		var area: Rect2 = region["rect"]
		var records: Array[Transform3D] = []
		var colors: Array[Color] = []
		for attempt: int in range(int(region["amount"])):
			var along_path: bool = String(region["name"]) == "LawnGrass3D" and attempt >= 1110
			var uv: Vector2
			if along_path:
				# Low, broken grass on *either edge*, not the walking surface.
				var t: float = (float(attempt-1110)+rng.randf())/100.0
				var curve_t: float = 0.06+t*0.84
				var tangent: Vector2 = (_path_screen(minf(1.0,curve_t+0.006))-_path_screen(maxf(0.0,curve_t-0.006))).normalized()
				var normal := Vector2(-tangent.y,tangent.x)
				var side: float = -1.0 if attempt % 2 == 0 else 1.0
				uv = _path_screen(curve_t)+normal*side*rng.randf_range(0.065,0.079)
				if rng.randf() > 0.64:
					continue
			else:
				uv = Vector2(rng.randf_range(area.position.x,area.end.x),rng.randf_range(area.position.y,area.end.y))
				if rng.randf() > _organic_coverage(uv,area,noise,String(region["name"])):
					continue
			if _is_clear_zone(uv):
				continue
			var position: Vector3 = _ground_point(view,uv*pixels)
			if not _is_playable_ground(position,player) or _near_foreground_plant(world,position):
				continue
			var height: float = rng.randf_range(float(region["min_h"]),float(region["max_h"]))
			if along_path:
				height = rng.randf_range(0.068,0.103)
				short_path_edges += 1
			# Real curved leaflets are wider than the old needle-shaped spikes.
			# Sideways lean has more variety than just vertical height variation.
			var width: float = height*rng.randf_range(1.05,1.50)
			var angle: float = rng.randf_range(-PI,PI)
			var lean: float = rng.randf_range(-0.18,0.18)
			var basis := Basis.from_euler(Vector3(lean,angle,rng.randf_range(-0.09,0.09)))
			basis = basis*Basis.from_scale(Vector3(width,height,width))
			records.append(Transform3D(basis,position))
			var tint: float = rng.randf_range(0.90,1.04)
			colors.append(Color(tint*0.91,tint,tint*0.78,1.0))
		if records.is_empty():
			push_warning("[LembahSari] Organic grass is missing region: "+String(region["name"]))
			continue
		var min_h: float = INF
		var max_h: float = -INF
		for tr: Transform3D in records:
			min_h = minf(min_h,tr.basis.get_scale().y)
			max_h = maxf(max_h,tr.basis.get_scale().y)
		var multi := MultiMesh.new()
		multi.transform_format = MultiMesh.TRANSFORM_3D
		multi.use_colors = true
		multi.mesh = grass_mesh
		multi.instance_count = records.size()
		for i: int in range(records.size()):
			multi.set_instance_transform(i,records[i])
			multi.set_instance_color(i,colors[i])
		var display := MultiMeshInstance3D.new()
		display.name = String(region["name"])
		display.multimesh = multi
		display.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		display.set_meta("authored_min_height",min_h)
		display.set_meta("authored_max_height",max_h)
		root.add_child(display)
		count += records.size()
	root.set_meta("tufts",count)
	root.set_meta("path_edge_tufts",short_path_edges)
	root.set_meta("batches",root.get_child_count())
	root.set_meta("image_background_preserved",true)
	root.set_meta("organic_distribution",true)
	root.set_meta("curved_blades",true)
	root.set_meta("organic_mask",true)
	root.set_meta("blade_profile","curved_broad")
	root.set_meta("path_curve_enabled",true)
	root.set_meta("riverbank_irregular",true)
	root.set_meta("foreground_cluster_mask",true)
	print("[LembahSari] ORGANIC_GRASS_ACTIVE tufts=%d batches=%d path_edges=%d far=image" % [count,root.get_child_count(),short_path_edges])

func _organic_coverage(uv: Vector2,rect: Rect2,noise: FastNoiseLite,region: String) -> float:
	var normalized := (uv-rect.position)/rect.size
	# Feather all four rectangle edges; no straight wall of spiky vegetation.
	var edge: float = minf(minf(normalized.x,1.0-normalized.x),minf(normalized.y,1.0-normalized.y))
	var softness: float = smoothstep(0.0,0.17,edge)
	var patch: float = noise.get_noise_2d(uv.x*310.0,uv.y*310.0)
	var secondary: float = noise.get_noise_2d(uv.x*540.0+103.0,uv.y*400.0-41.0)
	var clouds: float = clampf(0.57+patch*0.56+secondary*0.19,0.0,1.0)
	if region == "RiverBankGrass3D":
		# Follow a meandering irregular waterline instead of a straight band.
		var side_fade: float = smoothstep(0.0,0.11,normalized.x)*smoothstep(0.0,0.12,1.0-normalized.x)
		var shore_y: float = 0.768+sin(uv.x*18.0)*0.009+noise.get_noise_2d(uv.x*720.0,113.0)*0.012
		var shore_distance: float = absf(uv.y-shore_y)
		var shore_envelope: float = 1.0-smoothstep(0.014,0.034,shore_distance)
		return shore_envelope*side_fade*(0.23+clouds*0.61)
	if region == "LeftGardenGrass3D":
		# Three intersecting irregular ground-cover islands under the banana
		# and main canopy. No square grass carpet against the camera edge.
		var a: float = _ellipse_island(uv,Vector2(0.20,0.58),Vector2(0.145,0.087))
		var b: float = _ellipse_island(uv,Vector2(0.365,0.625),Vector2(0.10,0.062))
		var c: float = _ellipse_island(uv,Vector2(0.12,0.656),Vector2(0.065,0.055))
		return maxf(a,maxf(b,c))*(0.24+clouds*0.68)
	if region == "LawnGrass3D":
		var dry_opening: float = smoothstep(0.22,0.70,noise.get_noise_2d(uv.x*135.0+36.0,uv.y*260.0))
		return softness*(0.22+clouds*0.48)*(1.0-0.33*dry_opening)
	return softness*(0.20+clouds*0.52)

func _ellipse_island(uv: Vector2,center: Vector2,radii: Vector2) -> float:
	var distance: float = ((uv-center)/radii).length()
	return 1.0-smoothstep(0.65,1.13,distance)

func _path_screen(t: float) -> Vector2:
	# Screen-space read of the existing footpath. The geometry/collision remains
	# untouched: the curved line only manages grass along its irregular edges.
	var path_start := Vector2(0.49,0.565)
	var path_end := Vector2(1.02,0.685)
	var p: Vector2 = path_start.lerp(path_end,t)
	p.y += sin(t*PI)*0.024
	p.x -= sin(t*PI)*0.008
	return p

func _path_distance(point: Vector2) -> float:
	var nearest: float = INF
	var prev: Vector2 = _path_screen(0.0)
	for index: int in range(1,25):
		var next: Vector2 = _path_screen(float(index)/24.0)
		var segment: Vector2 = next-prev
		var t: float = clampf((point-prev).dot(segment)/maxf(segment.length_squared(),0.0000001),0.0,1.0)
		nearest = minf(nearest,point.distance_to(prev+segment*t))
		prev = next
	return nearest

func _build_leaf_mesh() -> ArrayMesh:
	# Eight overlapping broad, curved banana-like grass leaflets per low tuft.
	# Each bent strip has 3 triangles; this avoids wire-thin upright needles.
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for blade: int in range(8):
		var a: float = TAU*float(blade)/8.0+float(blade%3)*0.10
		var radial := Vector3(cos(a),0.0,sin(a))
		var tangent := Vector3(-sin(a),0.0,cos(a))
		var spread: float = 0.12+float(blade%3)*0.055
		var origin: Vector3 = radial*spread
		var wide: float = 0.18+float(blade%3)*0.015
		var start_left := origin-tangent*wide
		var start_right := origin+tangent*wide
		var shoulder: Vector3 = origin+radial*0.13+Vector3.UP*(0.48+float(blade%2)*0.035)
		var left_mid := shoulder-tangent*wide*0.80
		var right_mid := shoulder+tangent*wide*0.80
		# Curved, lowered tip plus asymmetry make grass soft, not cactus-like.
		var tip: Vector3 = origin+radial*(0.32+float(blade%3)*0.065)+tangent*(0.025 if blade%2==0 else -0.025)+Vector3.UP*(0.72+float(blade%3)*0.045)
		_triangle(st,start_left,start_right,left_mid,0.0,0.0,0.48)
		_triangle(st,start_right,right_mid,left_mid,0.0,0.48,0.48)
		_triangle(st,left_mid,right_mid,tip,0.48,0.48,0.78)
	st.generate_normals()
	return st.commit() as ArrayMesh

func _triangle(st: SurfaceTool,a: Vector3,b: Vector3,c: Vector3,va: float,vb: float,vc: float) -> void:
	for entry: Dictionary in [
		{"p":a,"t":va},
		{"p":b,"t":vb},
		{"p":c,"t":vc},
	]:
		var t: float = float(entry["t"])
		st.set_color(Color("4d6934").lerp(Color("96ae55"),clampf(t,0.0,1.0)))
		st.set_uv(Vector2(0.5,t))
		st.add_vertex(entry["p"])

func _grass_material() -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.resource_name = "SoftWarmCurvedMeadowGrass"
	mat.vertex_color_use_as_albedo = true
	mat.albedo_color = Color.WHITE
	mat.roughness = 0.98
	mat.metallic = 0.0
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	return mat

func _ground_point(view: Camera3D,pixel: Vector2) -> Vector3:
	var origin: Vector3 = view.project_ray_origin(pixel)
	var ray: Vector3 = view.project_ray_normal(pixel)
	if ray.y >= -0.001:
		return Vector3(9999.0,GROUND_Y,9999.0)
	return origin+ray*((GROUND_Y-origin.y)/ray.y)

func _is_playable_ground(at: Vector3,player: CharacterBody3D) -> bool:
	if at.x < TERRAIN_MIN.x or at.x > TERRAIN_MAX.x or at.z < TERRAIN_MIN.y or at.z > TERRAIN_MAX.y:
		return false
	return Vector2(at.x-player.global_position.x,at.z-player.global_position.z).length_squared() > 0.68*0.68

func _is_clear_zone(p: Vector2) -> bool:
	if _path_distance(p) < 0.055:
		return true
	# Nothing on the house porch, game farm beds, or river surface.
	if p.x > 0.66 and p.y < 0.59:
		return true
	if p.x > 0.37 and p.x < 0.66 and p.y < 0.57:
		return true
	return p.y >= 0.81

func _near_foreground_plant(world: Node3D,point: Vector3) -> bool:
	var hero: Node3D = world.get_node_or_null("HeroSceneV5") as Node3D
	if hero == null:
		return false
	var plants: Node3D = hero.get_node_or_null("ForegroundPlants3D") as Node3D
	if plants == null:
		return false
	for child: Node in plants.get_children():
		if not child is Node3D:
			continue
		var plant: Node3D = child as Node3D
		var kind: int = int(plant.get_meta("plant_type",-1))
		var distance: float = 0.56 if kind <= 1 else 0.42
		if Vector2(point.x-plant.global_position.x,point.z-plant.global_position.z).length_squared() < distance*distance:
			return true
	return false
