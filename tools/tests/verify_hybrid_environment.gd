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

 var midground_cards := 0
 var flipped_cards := 0
 var unflipped_cards := 0
 for child in layer.get_children():
  if child is Sprite3D:
   var sprite := child as Sprite3D
   if String(sprite.name).begins_with("Card_V5Mid"):
    midground_cards += 1
    _check(sprite.modulate.g >= sprite.modulate.r,"Midground foliage needs a subtle atmospheric green falloff")
   if String(sprite.name).begins_with("Card_V5") and ("Tree" in String(sprite.name) or "Bush" in String(sprite.name) or "Palm" in String(sprite.name)):
    if sprite.flip_h:
     flipped_cards += 1
    else:
     unflipped_cards += 1
 _check(midground_cards >= 24,"Foliage polish needs a broken midground vegetation belt")
 _check(int(layer.get_meta("midground_cards",0)) == midground_cards,"Midground card metadata must match runtime cards")
 _check(flipped_cards > 0 and unflipped_cards > 0,"Foliage cards must use mirrored and unmirrored variants")

 var yard_apron: MeshInstance3D = hero.find_child("V5YardApron",true,false) as MeshInstance3D
 var yard_jar: MeshInstance3D = hero.find_child("V5YardJarBody",true,false) as MeshInstance3D
 var tool_rack: MeshInstance3D = hero.find_child("V5YardToolRackRail",true,false) as MeshInstance3D
 var crate: MeshInstance3D = hero.find_child("V5YardCrateBase",true,false) as MeshInstance3D
 var firewood: Array[Node] = hero.find_children("V5YardFirewood_*","MeshInstance3D",true,false)
 var steps: Array[Node] = hero.find_children("V5YardStep_*","MeshInstance3D",true,false)
 _check(yard_apron != null and yard_jar != null and tool_rack != null and crate != null,"House-yard polish needs apron jar tool rack and produce crate")
 _check(firewood.size() >= 5 and steps.size() >= 3,"House-yard polish needs compact firewood and stepping-stone groups")
 if yard_apron != null:
  var yard_mat: ShaderMaterial = yard_apron.get_surface_override_material(0) as ShaderMaterial
  _check(yard_mat != null,"Packed house yard must receive its dedicated hybrid material")

 var yard_cards := 0
 for child in layer.get_children():
  if child is Sprite3D and (String(child.name).begins_with("Card_V5YardGrass_") or String(child.name).begins_with("Card_V5YardBushFlower_")):
   yard_cards += 1
 _check(yard_cards >= 7,"House-yard edges need lightweight grass and flower accents")

 _check(world.get_node_or_null("PlayableV5TestHUD") == null,"Final playable build must not overlay the old 2.5D debug badge")

 var readability_shadow: MeshInstance3D = world.get_node_or_null("Player/PlayerContactShadow") as MeshInstance3D
 _check(readability_shadow != null and readability_shadow.mesh != null,"Player needs a subtle contact shadow for ground readability")
 if readability_shadow != null:
  var readability_mat: StandardMaterial3D = readability_shadow.material_override as StandardMaterial3D
  _check(readability_mat != null and readability_mat.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA,"Player contact shadow must stay lightweight transparent geometry")

 var fixed_rig: Node3D = world.get_node_or_null("Player/CameraRig") as Node3D
 var fixed_camera: Camera3D = world.get_node_or_null("Player/CameraRig/Camera3D") as Camera3D
 _check(fixed_rig != null and fixed_camera != null and fixed_rig.is_set_as_top_level(),"Final camera rig must be detached from player translation")
 if fixed_camera != null:
  _check(fixed_camera.global_position.distance_to(Vector3(12.3,4.88,-3.9)) < 0.02,"Final fixed camera world position must remain locked")
  var screen_size := fixed_camera.get_viewport().get_visible_rect().size
  var spawn_screen := fixed_camera.unproject_position(world.get_node("Player").global_position + Vector3(0.0,0.82,0.0))
  _check(spawn_screen.x > screen_size.x * 0.30 and spawn_screen.x < screen_size.x * 0.70,"Player spawn should begin inside the central horizontal readability zone")
  _check(spawn_screen.y > screen_size.y * 0.25 and spawn_screen.y < screen_size.y * 0.78,"Player spawn should begin clear of top/bottom HUD zones")

 var world_env: WorldEnvironment = world.get_node_or_null("V5WorldEnvironment") as WorldEnvironment
 var sun: DirectionalLight3D = world.get_node_or_null("WarmMorningSun") as DirectionalLight3D
 var fill: DirectionalLight3D = world.get_node_or_null("SoftSkyFill") as DirectionalLight3D
 _check(world_env != null and world_env.environment != null,"Lighting polish requires the V5 world environment")
 _check(sun != null and fill != null,"Lighting polish requires warm sun and sky fill")
 if world_env != null and world_env.environment != null:
  var env := world_env.environment
  _check(env.ambient_light_energy >= 0.30,"Morning polish must lift ambient shadow readability")
  _check(env.adjustment_brightness >= 0.92 and env.adjustment_contrast <= 1.03,"Morning grade should avoid crushed block shadows")
 if sun != null:
  _check(sun.shadow_enabled,"Warm morning sun must still cast gameplay shadows")
  _check(sun.shadow_opacity < 0.82 and sun.shadow_opacity > 0.60,"House shadows must remain present but softened")
  _check(sun.shadow_blur >= 1.15,"Sun shadow filtering must soften hard block edges")
  _check(sun.directional_shadow_blend_splits,"Directional shadow splits should blend for smoother fixed-camera shadows")
 if fill != null:
  _check(fill.light_energy >= 0.10 and not fill.shadow_enabled,"Sky fill must lift character/porch readability without a second shadow")

 _check(background.modulate.r < 0.98 and background.modulate.g >= background.modulate.r,"Backdrop should remain slightly quieter than the playable foreground")

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
