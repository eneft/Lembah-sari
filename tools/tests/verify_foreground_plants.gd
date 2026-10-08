extends SceneTree
var failed: bool = false
const PATHS: Array[String] = [
 "res://assets/models/foreground/01_Pohon_Rindang_Besar.glb",
 "res://assets/models/foreground/02_Semak_Rimbun.glb",
 "res://assets/models/foreground/03_Palem_Lengkung.glb",
 "res://assets/models/foreground/04_Rumput_Tinggi.glb",
]
func _initialize() -> void:
 _run.call_deferred()
func _run() -> void:
 var scene: PackedScene = load("res://scenes/PlayableV5Test.tscn")
 var world: Node3D = scene.instantiate() as Node3D
 root.add_child(world)
 current_scene = world
 for frame: int in range(30): await physics_frame
 var hero: Node3D = world.get_node("HeroSceneV5") as Node3D
 var plants: Node3D = hero.get_node_or_null("ForegroundPlants3D") as Node3D
 var layer: Node3D = hero.get_node("HybridEnvironment") as Node3D
 var background: Sprite3D = hero.get_node("ValleyBackgroundImage") as Sprite3D
 var installed := 0
 for path: String in PATHS:
  if ResourceLoader.exists(path): installed += 1
 _check(plants != null, "Foreground layer must exist, even before binary assets are installed")
 _check(background != null and background.visible, "Distant background must remain image-based")
 _check(layer != null and int(layer.get_meta("midground_cards",0)) >= 24, "Midground image cards must remain intact")
 if plants != null:
  if installed == 0:
   _check(int(plants.get_meta("installed",-1)) == 0,"Scene should gracefully await split GLB upload")
   print("FOREGROUND_PLANTS_STAGED awaiting_binary_glbs=4 backdrop=image")
  elif installed != PATHS.size():
   _check(false,"Four split GLB files must be installed together")
  else:
   _check(int(plants.get_meta("installed",0)) == 11,"Eleven selected hero 3D instances must be active")
   var models := 0
   for child: Node in plants.get_children():
    if not child is Node3D: continue
    models += 1
    var meshes: Array[Node] = child.find_children("*","MeshInstance3D",true,false)
    _check(not meshes.is_empty(),"Each hero plant must retain actual polygon geometry")
    var height: float = float(child.get_meta("authored_height",0.0))
    _check(height >= 0.50 and height <= 4.60,"Vegetation must retain house-relative proportions")
   _check(models == 11,"Exactly eleven curated instances must be active")
   print("FOREGROUND_PLANTS_VALIDATED instances=%d midground=image backdrop=image" % models)
 world.queue_free()
 await process_frame
 quit(1 if failed else 0)
func _check(ok: bool, message: String) -> void:
 if not ok:
  failed = true
  push_error(message)
