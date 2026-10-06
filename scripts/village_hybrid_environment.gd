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
 mats["ground"] = _material("35452f","8b9460","65724a",24,0,0.15,0.26)
 mats["ground_deep"] = _material("263d25","667a46","3b5c31",26,0,0.19,0.30)
 mats["ground_warm"] = _material("56613f","9c9a61","7c7148",24,0,0.14,0.27)
 mats["path"] = _material("765b40","c3ab7b","92734e",30,1,0.21,0.20)
 mats["soil"] = _material("493421","887049","5d4930",30,1,0.18,0.22)
 mats["bank_wet"] = _material("26372f","59634b","35483c",34,1,0.22,0.28)
 mats["wear"] = _material("3d3024","77634b","514232",34,1,0.24,0.18)
 mats["wood"] = _material("76593b","b19a68","62462f",15,2,0.15,0.12)
 var water := ShaderMaterial.new()
 water.shader = WATER
 mats["water"] = water
 for node: Node in hero.find_children("*","MeshInstance3D",true,false):
  var m := node as MeshInstance3D
  if _house(m,hero) or not m.is_visible_in_tree(): continue
  var label := String(m.name)
  var box: AABB = (hero.global_transform.affine_inverse()*m.global_transform)*m.get_aabb()
  if "Tree" in label or "Palm" in label or "Bush" in label or "Flower" in label:
   var kind: int = 1 if "Palm" in label else (2 if "Bush" in label or "Flower" in label else 0)
   var base := Vector3(box.get_center().x,-0.10,box.get_center().z)
   var scale_boost: float = 1.45 if kind == 2 else 1.0
   if "Flower" in label:
    scale_boost = 1.12
   _card(hero.to_global(base),maxf(box.end.y+0.10,0.35)*scale_boost,kind,label)
   if kind < 2: _trunk_block(hero.to_global(base),label)
   m.hide()
  elif "Hill" in label or "Ridge" in label or "Landform" in label:
   m.hide()
  elif "Rice" in label or label.begins_with("GardenPlant") or ("Grass" in label and not "Patch" in label):
   var card_height: float = 0.38 if "Rice" in label else (0.34 if "Grass" in label else 0.48)
   _card(m.global_position,card_height,3,label)
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

func _material(a: String,b: String,accent: String,grain: float,kind: float = 0,macro_scale: float = 0.16,macro_strength: float = 0.24) -> ShaderMaterial:
 var mat := ShaderMaterial.new()
 mat.shader = SURFACE
 mat.set_shader_parameter("low_color",Color(a))
 mat.set_shader_parameter("high_color",Color(b))
 mat.set_shader_parameter("accent_color",Color(accent))
 mat.set_shader_parameter("grain_scale",grain)
 mat.set_shader_parameter("surface_kind",kind)
 mat.set_shader_parameter("macro_scale",macro_scale)
 mat.set_shader_parameter("macro_strength",macro_strength)
 return mat

func _surface(m: MeshInstance3D) -> void:
 var mesh_label := String(m.name).to_lower()
 for i: int in range(m.mesh.get_surface_count()):
  var mat: Material = m.get_active_material(i)
  if mat == null: continue
  var label := mat.resource_name.to_lower()
  var key := ""

  # Preserve the authored ground islands instead of flattening every grass
  # material back to one identical override.
  if mesh_label.begins_with("v5grasspatch_"):
   key = "ground_warm" if mesh_label.ends_with("_1") else "ground_deep"
  elif mesh_label.begins_with("v5wetbank"):
   key = "bank_wet"
  elif mesh_label.begins_with("v5housewear"):
   key = "wear"
  elif "ground" in label or "grass" in label:
   key = "ground"
  elif "dirt" in label:
   key = "path"
  elif "earth" in label or "bund" in label or "bank" in label:
   key = "soil"
  elif "water" in label:
   key = "water"
  elif "wood" in label or "bamboo" in label:
   key = "wood"

  if key != "":
   m.set_surface_override_material(i,mats[key])

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
