extends SceneTree
var failed := false
func _initialize() -> void:
 _run.call_deferred()
func _run() -> void:
 for path: String in ["res://assets/textures/hybrid/vegetation_atlas.webp", "res://assets/textures/hybrid/valley_backdrop.webp", "res://assets/shaders/village_surface.gdshader", "res://assets/shaders/village_water.gdshader"]:
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
