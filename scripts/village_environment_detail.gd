extends RefCounted
## Deterministic natural village art pass. Imported house branches stay excluded.
const SURFACE = preload("res://assets/shaders/village_surface.gdshader")
const LEAF = preload("res://assets/shaders/village_leaf.gdshader")
const WATER = preload("res://assets/shaders/village_water.gdshader")
var rng := RandomNumberGenerator.new()
var leaves: Array[Transform3D] = []
var colors: Array[Color] = []
var stones: Array[Transform3D] = []
var shadows: Array[Transform3D] = []
var mats: Dictionary = {}
var detail: Node3D
var branches: SurfaceTool
var grass: SurfaceTool
var trees: int = 0
var bushes: int = 0
var palms: int = 0

func apply(hero: Node3D) -> void:
 rng.seed = 64026
 detail = Node3D.new()
 detail.name = "VillageNaturalDetail"
 hero.add_child(detail)
 mats["ground"] = _material("35452a","829053",21)
 mats["path"] = _material("68503a","baa076",32)
 mats["soil"] = _material("3d3023","816442",35)
 mats["stone"] = _material("535a4e","9a9c81",14,1)
 mats["bark"] = _material("423529","917355",18,2)
 mats["bamboo"] = _material("695336","bda578",15,2)
 mats["hill"] = _material("637a59","7c8a64",5,1)
 var water := ShaderMaterial.new()
 water.shader = WATER
 mats["water"] = water
 branches = SurfaceTool.new()
 branches.begin(Mesh.PRIMITIVE_TRIANGLES)
 grass = SurfaceTool.new()
 grass.begin(Mesh.PRIMITIVE_TRIANGLES)
 for node: Node in hero.find_children("*","MeshInstance3D",true,false):
  var m := node as MeshInstance3D
  if _house(m,hero) or not m.is_visible_in_tree(): continue
  var label := String(m.name)
  var box: AABB = (hero.global_transform.affine_inverse()*m.global_transform)*m.get_aabb()
  if "Tree" in label:
   _tree(box)
   m.hide()
  elif "Bush" in label:
   _bush(box)
   m.hide()
  elif "Palm" in label:
   _palm(box,hero.to_local(m.global_position))
   m.hide()
  elif "Rock" in label:
   var p := box.get_center()
   p.y = box.size.y*0.35-0.04
   stones.append(Transform3D(Basis(Vector3.UP,rng.randf()*TAU).scaled(box.size*Vector3(1.25,1.15,1.15)),p))
   m.hide()
  else: _surfaces(m)
 _mesh(branches,mats["bark"],"TreeBranches")
 _ground_details()
 _banks()
 var grass_mat := StandardMaterial3D.new()
 grass_mat.vertex_color_use_as_albedo = true
 grass_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
 grass_mat.roughness = 1
 _mesh(grass,grass_mat,"MeadowTufts")
 _leaves()
 _stones()
 detail.set_meta("trees",trees)
 detail.set_meta("bushes",bushes)
 detail.set_meta("palms",palms)
 detail.set_meta("leaves",leaves.size())
 print("[LembahSari] NATURAL_ENVIRONMENT_ACTIVE trees=%d bushes=%d palms=%d leaves=%d" % [trees,bushes,palms,leaves.size()])

func _house(node: Node, hero: Node) -> bool:
 var p: Node = node
 while p != null and p != hero:
  if String(p.name).begins_with("HeroHouseRoot") or p.name == "PlayerHouseTraditionalV4": return true
  p = p.get_parent()
 return false

func _material(a: String,b: String,grain: float,kind: float = 0) -> ShaderMaterial:
 var mat := ShaderMaterial.new()
 mat.shader = SURFACE
 mat.set_shader_parameter("low_color",Color(a))
 mat.set_shader_parameter("high_color",Color(b))
 mat.set_shader_parameter("grain_scale",grain)
 mat.set_shader_parameter("surface_kind",kind)
 return mat

func _surfaces(m: MeshInstance3D) -> void:
 for i: int in range(m.mesh.get_surface_count()):
  var mat: Material = m.get_active_material(i)
  if mat == null: continue
  var label := mat.resource_name.to_lower()
  var key := ""
  if "ground" in label or "grass" in label: key = "ground"
  elif "dirt" in label: key = "path"
  elif "garden earth" in label or "bund" in label or "bank" in label: key = "soil"
  elif "water" in label: key = "water"
  elif "hill" in label or "ridge" in label: key = "hill"
  elif "bamboo" in label: key = "bamboo"
  elif "wood" in label or "bark" in label: key = "bark"
  if key != "": m.set_surface_override_material(i,mats[key])

func _tree(box: AABB) -> void:
 trees += 1
 var base := Vector3(box.get_center().x,-0.10,box.get_center().z)
 var h := box.end.y+0.10
 var radius := minf(box.size.x,box.size.z)*0.47
 _branch(base,base+Vector3(0.07,h*0.7,0.04),h*0.041,h*0.019)
 for j: int in range(5):
  var a := TAU*float(j)/5+rng.randf()*0.4
  var center := base+Vector3(cos(a)*radius*0.42,h*(0.66+rng.randf()*0.15),sin(a)*radius*0.42)
  _branch(base+Vector3(0,h*0.42,0),center,h*0.019,h*0.005)
  _cluster(center,Vector3(radius*0.67,h*0.20,radius*0.67),220,0.12,0.19)

func _bush(box: AABB) -> void:
 bushes += 1
 var center := box.get_center()
 center.y = box.size.y*0.38-0.05
 _cluster(center,box.size*0.48,240,0.085,0.15)

func _cluster(center: Vector3,radii: Vector3,amount: int,lo: float,hi: float) -> void:
 shadows.append(Transform3D(Basis().scaled(radii*1.65),center))
 for i: int in range(amount):
  var dir := Vector3(rng.randf_range(-1,1),rng.randf_range(-1,1),rng.randf_range(-1,1)).normalized()
  var p := center+dir*radii*pow(rng.randf_range(0.08,1),0.3333)
  var size := rng.randf_range(lo,hi)
  var basis := Basis.from_euler(Vector3(rng.randf_range(-1.1,1.1),rng.randf()*TAU,rng.randf_range(-0.7,0.7))).scaled(Vector3(size*0.62,size,size))
  leaves.append(Transform3D(basis,p))
  colors.append(Color("4e6a36").lerp(Color("9ead61"),rng.randf()*0.75+maxf(dir.y,0)*0.25))

func _palm(box: AABB,base: Vector3) -> void:
 palms += 1
 base.y = -0.12
 var h := box.end.y*0.86
 var top := base+Vector3(0.22,h,0.12)
 var middle := base+Vector3(0.06,h*0.5,0.02)
 _branch(base,middle,0.105,0.076)
 _branch(middle,top,0.076,0.05)
 var reach := minf(box.size.x,box.size.z)*0.48
 for frond: int in range(9):
  var a := float(frond)*TAU/9+rng.randf()*0.2
  var dir := Vector3(cos(a),0,sin(a))
  var side := Vector3(-dir.z,0,dir.x)
  for seg: int in range(16):
   var t := (float(seg)+1)/17
   var p := top+dir*reach*t+Vector3(0,sin(t*PI)*0.38-t*t*0.4,0)
   for sign_value: float in [-1.0,1.0]:
    var length := sin(t*PI)*reach*0.36+0.07
    var along := (side*sign_value+dir*0.28+Vector3(0,-0.3,0)).normalized()
    var basis := Basis()
    basis.z = along*length
    basis.x = dir*0.09
    basis.y = basis.z.cross(basis.x).normalized()*length
    leaves.append(Transform3D(basis,p+along*length*0.4))
    colors.append(Color("667b3c").lerp(Color("a2ad60"),rng.randf()))

func _branch(a: Vector3,b: Vector3,ra: float,rb: float) -> void:
 var up := (b-a).normalized()
 var x := up.cross(Vector3.FORWARD).normalized()
 var z := up.cross(x).normalized()
 for k: int in range(7):
  var angle := float(k)*TAU/7
  var next := float(k+1)*TAU/7
  var u := x*cos(angle)+z*sin(angle)
  var v := x*cos(next)+z*sin(next)
  _tri(branches,a+u*ra,b+u*rb,b+v*rb,Color.WHITE)
  _tri(branches,a+u*ra,b+v*rb,a+v*ra,Color.WHITE)

func _tri(st: SurfaceTool,a: Vector3,b: Vector3,c: Vector3,color: Color) -> void:
 st.set_color(color)
 st.set_normal((b-a).cross(c-a).normalized())
 st.add_vertex(a)
 st.add_vertex(b)
 st.add_vertex(c)

func _tuft(p: Vector3,height: float) -> void:
 for blade: int in range(5):
  var angle := rng.randf()*TAU
  var width := Vector3(cos(angle),0,sin(angle))*0.018
  var tip := p+Vector3(rng.randf_range(-0.06,0.06),height*rng.randf_range(0.6,1.2),rng.randf_range(-0.06,0.06))
  _tri(grass,p-width,p+width,tip,Color("48552b").lerp(Color("919755"),rng.randf()))

func _ground_details() -> void:
 var beds: Array[Vector3] = [Vector3(-8,0,2.5),Vector3(-6.8,0,3.2),Vector3(-9.5,0,0.8),Vector3(8.4,0,1),Vector3(9.4,0,3),Vector3(-8,0,-5.8),Vector3(7,0,-6.8)]
 for center: Vector3 in beds:
  for i: int in range(95): _tuft(center+Vector3(rng.randf_range(-1.1,1.1),-0.09,rng.randf_range(-0.65,0.65)),rng.randf_range(0.10,0.25))

func _banks() -> void:
 var points: Array[Vector3] = [Vector3(-12,0,7.35),Vector3(-9.2,0,6.75),Vector3(-6.3,0,6.28),Vector3(-3.5,0,5.6),Vector3(-0.6,0,4.92),Vector3(2.25,0,4.12),Vector3(4.9,0,3.38),Vector3(7.4,0,2.52),Vector3(9.7,0,1.7),Vector3(12,0,0.82)]
 var widths: Array[float] = [2.15,2,1.88,1.96,1.84,1.92,1.78,1.66,1.55,1.44]
 for i: int in range(points.size()-1):
  var side := (points[i+1]-points[i]).normalized().cross(Vector3.UP)
  for j: int in range(18):
   var t := rng.randf()
   var center := points[i].lerp(points[i+1],t)
   if absf(center.x-2.25)<1.2: continue
   for sign_value: float in [-1.0,1.0]:
    var p := center+side*sign_value*(lerpf(widths[i],widths[i+1],t)*0.5+rng.randf_range(0.02,0.26))
    p.y = -0.055
    var size := rng.randf_range(0.065,0.18)
    stones.append(Transform3D(Basis(Vector3.UP,rng.randf()*TAU).scaled(Vector3(size,size*0.55,size*0.8)),p+Vector3(0,size*0.17,0)))
    if j%2 == 0: _tuft(p+side*sign_value*0.18,rng.randf_range(0.10,0.24))
 var path: Array[Vector3] = [Vector3(-4.8,0,-1.15),Vector3(-4.2,0,-0.15),Vector3(-3.25,0,0.95),Vector3(-2.05,0,2.05),Vector3(-0.65,0,3),Vector3(0.75,0,3.65)]
 var path_widths: Array[float] = [0.92,1.02,1.18,1.28,1.34,1.22]
 for i: int in range(1,path.size()-1):
  var side := (path[i+1]-path[i]).normalized().cross(Vector3.UP)
  for j: int in range(12):
   var t := rng.randf()
   for sign_value: float in [-1.0,1.0]:
    var p := path[i].lerp(path[i+1],t)+side*sign_value*(lerpf(path_widths[i],path_widths[i+1],t)*0.5+0.045)
    p.y = -0.06
    _tuft(p,0.11)

func _mesh(st: SurfaceTool,mat: Material,label: String) -> void:
 var instance := MeshInstance3D.new()
 instance.name = label
 instance.mesh = st.commit()
 instance.material_override = mat
 detail.add_child(instance)

func _batch(mesh: Mesh,transforms: Array[Transform3D],label: String,mat: Material) -> MultiMeshInstance3D:
 var mm := MultiMesh.new()
 mm.transform_format = MultiMesh.TRANSFORM_3D
 mm.use_colors = label == "BatchedNaturalLeaves"
 mm.mesh = mesh
 mm.instance_count = transforms.size()
 for i: int in range(transforms.size()):
  mm.set_instance_transform(i,transforms[i])
  if mm.use_colors: mm.set_instance_color(i,colors[i].srgb_to_linear())
 var batch := MultiMeshInstance3D.new()
 batch.name = label
 batch.multimesh = mm
 batch.material_override = mat
 detail.add_child(batch)
 return batch

func _leaves() -> void:
 var st := SurfaceTool.new()
 st.begin(Mesh.PRIMITIVE_TRIANGLES)
 var points: Array[Vector3] = [Vector3(0,0,-1),Vector3(-0.30,0,-0.55),Vector3(-0.44,0,0),Vector3(-0.29,0,0.55),Vector3(0,0,1),Vector3(0.29,0,0.55),Vector3(0.44,0,0),Vector3(0.30,0,-0.55),Vector3(0,0.10,0)]
 for i: int in range(8):
  for index: int in [i,(i+1)%8,8]:
   st.set_normal(Vector3.UP)
   st.set_uv(Vector2(points[index].x+0.5,(points[index].z+1)*0.5))
   st.add_vertex(points[index])
 var mat := ShaderMaterial.new()
 mat.shader = LEAF
 var batch := _batch(st.commit(),leaves,"BatchedNaturalLeaves",mat)
 batch.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 # Cheap silhouette proxies keep foliage out of repeated shadow cascades.
 var sphere := SphereMesh.new()
 sphere.radius = 0.5
 sphere.height = 1
 sphere.radial_segments = 10
 sphere.rings = 4
 var proxy := _batch(sphere,shadows,"CanopyShadowProxies",null)
 proxy.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY

func _stones() -> void:
 var sphere := SphereMesh.new()
 sphere.radial_segments = 14
 sphere.rings = 7
 sphere.radius = 0.5
 sphere.height = 1
 var arrays := sphere.get_mesh_arrays()
 var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
 for i: int in range(vertices.size()):
  var p := vertices[i]
  vertices[i] *= 1+0.13*sin(p.x*16+p.z*9)*cos(p.y*11)
 arrays[Mesh.ARRAY_VERTEX] = vertices
 var mesh := ArrayMesh.new()
 mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
 _batch(mesh,stones,"RiverStoneClusters",mats["stone"])
