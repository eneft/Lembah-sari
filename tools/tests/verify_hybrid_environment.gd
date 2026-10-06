extends SceneTree
var failed := false
func _initialize() -> void:
 _run.call_deferred()
func _run() -> void:
 for path: String in ["res://assets/textures/hybrid/vegetation_atlas.webp", "res://assets/textures/hybrid/valley_backdrop.webp", "res://assets/shaders/village_surface.gdshader", "res://assets/shaders/village_water.gdshader", "res://assets/shaders/village_paddy_water.gdshader"]:
  _check(ResourceLoader.exists(path), "Missing exported environment asset: " + path)
 if failed:
  quit(1)
  return
 var world: Node = load("res://scenes/PlayableV5Test.tscn").instantiate()
 root.add_child(world)
 current_scene = world
 for i in range(40): await physics_frame
 var hero: Node3D = world.get_node("HeroSceneV5")
 var layer: Node3D = hero.get_node("HybridEnvironment")
 var background: Sprite3D = hero.get_node("ValleyBackgroundImage")
 _check(background.texture != null and background.texture.get_width() > 0,"Background image must load")
 _check(int(layer.get_meta("cards",0)) > 100,"Vegetation cards must replace decorative meshes")
 var cards := 0
 var trunks := 0
 for child in layer.get_children():
  if child is Sprite3D:
   cards += 1
   _check(child.texture != null and child.texture.get_height() > 0,"Card texture must load")
   _check(child.alpha_cut == SpriteBase3D.ALPHA_CUT_DISCARD,"Cards must depth-test cutout silhouettes")
  elif child is StaticBody3D: trunks += 1
 _check(trunks > 0,"Trees need simple trunk collision")
 var old_tree: MeshInstance3D = hero.find_child("*Tree*",true,false) as MeshInstance3D
 _check(old_tree != null and not old_tree.visible,"Original decorative tree geometry must be hidden")

 var deep_patch: MeshInstance3D = hero.find_child("V5GrassPatch_0",true,false) as MeshInstance3D
 var warm_patch: MeshInstance3D = hero.find_child("V5GrassPatch_1",true,false) as MeshInstance3D
 _check(deep_patch != null and warm_patch != null,"Ground polish patches must remain in the V5 composition")
 if deep_patch != null and warm_patch != null:
  var deep_mat: ShaderMaterial = deep_patch.get_surface_override_material(0) as ShaderMaterial
  var warm_mat: ShaderMaterial = warm_patch.get_surface_override_material(0) as ShaderMaterial
  _check(deep_mat != null and warm_mat != null,"Ground polish patches need hybrid shader overrides")
  if deep_mat != null and warm_mat != null:
   _check(deep_mat.get_shader_parameter("low_color") != warm_mat.get_shader_parameter("low_color"),"Deep and warm grass patches must retain distinct palettes")
 var wet_bank: MeshInstance3D = hero.find_child("V5WetBank",true,false) as MeshInstance3D
 var stream_bank: MeshInstance3D = hero.find_child("V5StreamBank",true,false) as MeshInstance3D
 var stream_water: MeshInstance3D = hero.find_child("V5StreamWater",true,false) as MeshInstance3D
 _check(wet_bank != null and stream_bank != null and stream_water != null,"Riverbank polish geometry must remain in the V5 composition")
 if wet_bank != null and stream_bank != null and stream_water != null:
  var wet_mat: ShaderMaterial = wet_bank.get_surface_override_material(0) as ShaderMaterial
  var dry_mat: ShaderMaterial = stream_bank.get_surface_override_material(0) as ShaderMaterial
  var water_mat: ShaderMaterial = stream_water.get_surface_override_material(0) as ShaderMaterial
  _check(wet_mat != null and dry_mat != null and water_mat != null,"Riverbank polish needs wet, dry and water materials")
  if wet_mat != null and dry_mat != null:
   _check(wet_mat.get_shader_parameter("low_color") != dry_mat.get_shader_parameter("low_color"),"Wet shoreline must remain visually distinct from dry bank soil")

 var bank_cards := 0
 for child in layer.get_children():
  if child is Sprite3D and String(child.name).begins_with("Card_V5BankGrass_"):
   bank_cards += 1
 _check(bank_cards >= 20,"Riverbank polish needs clustered reed/grass cards")

 var paddy_water_nodes: Array[Node] = hero.find_children("V5PaddyWater_*","MeshInstance3D",true,false)
 var paddy_earth_nodes: Array[Node] = hero.find_children("V5PaddyEarth_*","MeshInstance3D",true,false)
 var paddy_bund_nodes: Array[Node] = hero.find_children("V5PaddyBund_*","MeshInstance3D",true,false)
 _check(paddy_water_nodes.size() == 4 and paddy_earth_nodes.size() == 4 and paddy_bund_nodes.size() == 4,"Rice terrace polish must keep four stepped paddies with water earth and bunds")

 var paddy_min_y := INF
 var paddy_max_y := -INF
 for node: Node in paddy_water_nodes:
  var paddy := node as MeshInstance3D
  var paddy_bounds: AABB = paddy.global_transform * paddy.get_aabb()
  var paddy_height := paddy_bounds.get_center().y
  paddy_min_y = minf(paddy_min_y,paddy_height)
  paddy_max_y = maxf(paddy_max_y,paddy_height)
  var paddy_mat: ShaderMaterial = paddy.get_surface_override_material(0) as ShaderMaterial
  _check(paddy_mat != null and paddy_mat.shader != null,"Each paddy needs its dedicated shallow-water shader")
  if paddy_mat != null and paddy_mat.shader != null:
   _check("village_paddy_water" in paddy_mat.shader.resource_path,"Paddy water must not reuse the river shader")
 _check(paddy_max_y - paddy_min_y > 0.12,"Rice terraces need visibly stepped elevation")

 var rice_cards := 0
 for child in layer.get_children():
  if child is Sprite3D and String(child.name).begins_with("Card_V5Rice_"):
   rice_cards += 1
 _check(rice_cards >= 35,"Rice terrace polish needs enough irregular rice clumps")

 var player: CharacterBody3D = world.get_node("Player")
 var camera: Camera3D = player.get_node("CameraRig/Camera3D")
 var camera_start := camera.global_transform
 var player_start := player.global_position
 Input.action_press("move_right")
 for i in range(30): await physics_frame
 Input.action_release("move_right")
 await process_frame
 _check(player.global_position.distance_to(player_start) > 0.3,"Player must still move")
 _check(camera.global_transform.is_equal_approx(camera_start),"Camera must remain fixed during movement")
 if not failed: print("HYBRID_ENVIRONMENT_VALIDATED cards=%d trunks=%d background=image camera=fixed movement=ok" % [cards,trunks])
 quit(1 if failed else 0)
func _check(condition: bool,message: String) -> void:
 if not condition:
  failed = true
  push_error(message)
