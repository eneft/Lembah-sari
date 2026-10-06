extends RefCounted
## Image cards supply decorative depth; only gameplay surfaces keep geometry.
const ATLAS = preload("res://assets/textures/hybrid/vegetation_atlas.webp")
const BACKDROP = preload("res://assets/textures/hybrid/valley_backdrop.webp")
const SURFACE = preload("res://assets/shaders/village_surface.gdshader")
const WATER = preload("res://assets/shaders/village_water.gdshader")
var regions: Array[AtlasTexture] = []
var camera: Camera3D
var layer: Node3D
var count_cards: int = 0
var mats: Dictionary = {}

func apply(hero: Node3D, view: Camera3D) -> void:
 camera = view
 layer = Node3D.new()
 layer.name = "HybridEnvironment"
 hero.add_child(layer)
 var size := ATLAS.get_size()
 var split_x := size.x*0.535
 var split_y := size.y*0.60
 var rects: Array[Rect2] = [Rect2(0,0,split_x,split_y),Rect2(split_x,0,size.x-split_x,split_y),Rect2(0,split_y,split_x,size.y-split_y),Rect2(split_x,split_y,size.x-split_x,size.y-split_y)]
 for rect: Rect2 in rects:
  var tex := AtlasTexture.new()
  tex.atlas = ATLAS
  tex.region = rect
  tex.filter_clip = true
  regions.append(tex)
 mats["ground"] = _material("435034","8b9460",24)
 mats["path"] = _material("765b40","c3ab7b",30)
 mats["soil"] = _material("493421","887049",30)
 mats["wood"] = _material("76593b","b19a68",15,2)
 var water := ShaderMaterial.new()
 water.shader = WATER
 mats["water"] = water
 for node: Node in hero.find_children("*","MeshInstance3D",true,false):
  var m := node as MeshInstance3D
  if _house(m,hero) or not m.is_visible_in_tree(): continue
  var label := String(m.name)
  var box: AABB = (hero.global_transform.affine_inverse()*m.global_transform)*m.get_aabb()
  if "Tree" in label or "Palm" in label or "Bush" in label:
   var kind: int = 1 if "Palm" in label else (2 if "Bush" in label else 0)
   var base := Vector3(box.get_center().x,-0.10,box.get_center().z)
   _card(hero.to_global(base),maxf(box.end.y+0.10,0.35)*(1.45 if kind == 2 else 1.0),kind,label)
   if kind < 2: _trunk_block(hero.to_global(base),label)
   m.hide()
  elif "Hill" in label or "Ridge" in label or "Landform" in label:
   m.hide()
  elif "Rice" in label or label.begins_with("GardenPlant"):
   _card(m.global_position,0.38 if "Rice" in label else 0.48,3,label)
   m.hide()
  elif "Flower" in label or "Grass" in label and not "Patch" in label:
   m.hide()
  else: _surface(m)
 _backdrop(hero)
 layer.set_meta("cards",count_cards)
 print("[LembahSari] HYBRID_25D_ACTIVE cards=%d background=image camera=fixed" % count_cards)

func _house(node: Node,hero: Node) -> bool:
 var p: Node = node
 while p != null and p != hero:
  if p.name == "PlayerHouseTraditionalV4" or String(p.name).begins_with("HeroHouseRoot"): return true
  p = p.get_parent()
 return false

func _card(base: Vector3,height: float,kind: int,label: String) -> void:
 var sprite := Sprite3D.new()
 sprite.name = "Card_"+label
 sprite.texture = regions[kind]
 sprite.pixel_size = height/regions[kind].get_height()
 sprite.shaded = false
 sprite.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
 sprite.alpha_scissor_threshold = 0.35
 sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
 sprite.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 layer.add_child(sprite)
 sprite.global_basis = camera.global_basis.orthonormalized()
 sprite.global_position = base+camera.global_basis.y.normalized()*height*0.48
 count_cards += 1

func _material(a: String,b: String,grain: float,kind: float = 0) -> ShaderMaterial:
 var mat := ShaderMaterial.new()
 mat.shader = SURFACE
 mat.set_shader_parameter("low_color",Color(a))
 mat.set_shader_parameter("high_color",Color(b))
 mat.set_shader_parameter("grain_scale",grain)
 mat.set_shader_parameter("surface_kind",kind)
 return mat

func _surface(m: MeshInstance3D) -> void:
 for i: int in range(m.mesh.get_surface_count()):
  var mat: Material = m.get_active_material(i)
  if mat == null: continue
  var label := mat.resource_name.to_lower()
  var key := ""
  if "ground" in label or "grass" in label: key = "ground"
  elif "dirt" in label: key = "path"
  elif "earth" in label or "bund" in label or "bank" in label: key = "soil"
  elif "water" in label: key = "water"
  elif "wood" in label or "bamboo" in label: key = "wood"
  if key != "": m.set_surface_override_material(i,mats[key])

func _backdrop(hero: Node3D) -> void:
 var sprite := Sprite3D.new()
 sprite.name = "ValleyBackgroundImage"
 var texture := AtlasTexture.new()
 texture.atlas = BACKDROP
 var size := BACKDROP.get_size()
 texture.region = Rect2(0,size.y*0.40,size.x,size.y*0.60)
 texture.filter_clip = true
 sprite.texture = texture
 sprite.pixel_size = 80.0/size.x
 sprite.shaded = false
 sprite.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 hero.add_child(sprite)
 sprite.global_basis = camera.global_basis.orthonormalized()
 # A distant image card perpendicular to the fixed viewing direction.
 sprite.global_position = camera.global_position-camera.global_basis.z*48.0+camera.global_basis.y*10.0

func _trunk_block(base: Vector3,label: String) -> void:
 var body := StaticBody3D.new()
 body.name = "TrunkCollider_"+label
 var collision := CollisionShape3D.new()
 var shape := CylinderShape3D.new()
 shape.radius = 0.14
 shape.height = 1.8
 collision.shape = shape
 body.add_child(collision)
 layer.add_child(body)
 body.global_position = base+Vector3.UP*0.9
