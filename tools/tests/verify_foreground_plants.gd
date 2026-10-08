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
   var banana_path: String = "res://assets/models/foreground/05_Pohon_Pisang_Optimized.glb"
   var banana_available: bool = ResourceLoader.exists(banana_path)
   var expected_models: int = 11
   _check(int(plants.get_meta("installed",0)) == expected_models,"Curated plant count must match available GLBs")
   var models := 0
   for child: Node in plants.get_children():
    if not child is Node3D: continue
    models += 1
    var meshes: Array[Node] = child.find_children("*","MeshInstance3D",true,false)
    _check(not meshes.is_empty(),"Each hero plant must retain actual polygon geometry")
    var height: float = float(child.get_meta("authored_height",0.0))
    _check(height >= 0.50 and height <= 5.20,"Vegetation must retain house-relative proportions")
    # Inspect physical placement against existing sprites and fixed camera.
    var plant := child as Node3D
    var nearest := INF
    var nearest_label := ""
    var nearest_same := INF
    var kind: int = int(child.get_meta("plant_type",-1))
    var cam: Camera3D = world.get_node("Player/CameraRig/Camera3D") as Camera3D
    var px: Vector2 = cam.unproject_position(plant.global_position + Vector3.UP * height * 0.35)
    for card_node: Node in layer.get_children():
     if not card_node is Sprite3D: continue
     var card := card_node as Sprite3D
     var distance: float = Vector2(card.global_position.x-plant.global_position.x,card.global_position.z-plant.global_position.z).length()
     if distance < nearest:
      nearest = distance
      nearest_label = String(card.name)
     var label: String = String(card.name)
     var match_kind: bool = (kind == 0 and "Tree" in label) or (kind == 1 and ("Bush" in label or "Flower" in label)) or (kind == 2 and "Palm" in label) or (kind == 3 and ("Grass" in label or "Bank" in label))
     if match_kind and distance < nearest_same:
      nearest_same = distance
    print("PLANT_POSITION name=%s world=%s screen=%s nearest_card=%s nearest_dist=%.2f same_type_dist=%.2f" % [plant.name,plant.global_position,px,nearest_label,nearest,nearest_same])
   _check(models == expected_models,"Only ten curated plants plus one real banana may occupy the foreground")
   _check(bool(plants.get_meta("banana_active",false)),"A banana tree must always frame the left house")
   _check(bool(plants.get_meta("banana_source_glb",false)) == banana_available,"Original banana GLB must supersede procedural fallback when present")
   var banana: Node3D = plants.get_node_or_null("BananaTree_Left_Indonesian") as Node3D
   _check(banana != null,"Banana geometry must have distinct node")
   if banana != null:
    _check(absf(float(banana.get_meta("authored_height",0.0))-2.92) < 0.01,"Banana must keep natural house scale")
    _check((banana.find_children("*","MeshInstance3D",true,false) as Array).size() >= 2,"Banana needs trunk, leaves and ground-shadow polygon geometry")
    _check(bool(plants.get_meta("banana_relocated_left",false)),"Original 3D banana must be moved out from behind the mature tree crowns")
    _check(bool(plants.get_meta("banana_left_focus_zone",false)),"Banana must be placed by fixed-camera foreground selection")
    var banana_cam: Camera3D = world.get_node("Player/CameraRig/Camera3D") as Camera3D
    var red_uv: Vector2 = banana_cam.unproject_position(banana.global_position)/banana_cam.get_viewport().get_visible_rect().size
    var clear_m: float = float(banana.get_meta("player_clearance_m",0.0))
    print("BANANA_RED_CIRCLE_AUDIT position=%s normalized_screen=%s player_clearance=%.2f" % [banana.global_position,red_uv,clear_m])
    _check(red_uv.x > 0.10 and red_uv.x < 0.26 and red_uv.y > 0.49 and red_uv.y < 0.69,"3D banana trunk must land inside the red-marked left foreground")
    _check(clear_m >= 1.45,"3D banana must not obstruct character spawn")
    var mature_gap: float = INF
    for n: String in ["Tree_LeftFieldFill","Tree_LeftLarge_A","Tree_LeftLarge_B"]:
     var mature_tree: Node3D = plants.get_node_or_null(n) as Node3D
     if mature_tree != null:
      mature_gap = minf(mature_gap,Vector2(mature_tree.global_position.x-banana.global_position.x,mature_tree.global_position.z-banana.global_position.z).length())
    _check(mature_gap >= 1.30,"Relocated banana trunk cannot overlap mature tree trunks")

   _check(int(plants.get_meta("hidden_cards",0)) >= 3,"Foreground 3D replacement must hide neighboring redundant 2.5D tree/palm cards")
   _check(int(layer.get_meta("banana_cards",0)) == 2,"Two banana image companions must join the existing real banana tree")
   var primary_png: String = "res://assets/textures/hybrid/banana_tree_card.png"
   var fallback_svg: String = "res://assets/textures/hybrid/banana_tree_card.svg"
   var png_available: bool = ResourceLoader.exists(primary_png)
   var expected_texture: String = primary_png if png_available else fallback_svg
   _check(ResourceLoader.exists(expected_texture),"At least one banana card image must be in the exported game")
   for name: String in ["Card_BananaRearLeft","Card_BananaMidLeft"]:
    var card: Sprite3D = layer.get_node_or_null(name) as Sprite3D
    _check(card != null and card.visible,"Missing lit banana image card: "+name)
    if card != null:
     _check(card.shaded and card.alpha_cut == SpriteBase3D.ALPHA_CUT_DISCARD,"Banana image must match real polygon lighting and depth: "+name)
     _check(card.texture != null and card.texture.get_height() >= 500,"Banana must have a botanical cutout, not a generic palm texture")
     _check(String(card.get_meta("source_texture","")) == expected_texture,"Banana images must select supplied PNG when it exists, or SVG fallback")
     _check(bool(card.get_meta("image_is_png",false)) == png_available,"PNG image flag must reflect the actual chosen texture")
     if png_available:
      _check(card.texture.get_width() >= 700 and card.texture.get_height() >= 1000,"Supplied transparent banana PNG must load at its imported 768x1024 or higher resolution, not a placeholder")
     print("BANANA_CARD_TEXTURE_OK name=%s source=%s image_size=%s" % [name,expected_texture,card.texture.get_size()])
     var contact: MeshInstance3D = layer.get_node_or_null("ContactShadow_"+name) as MeshInstance3D
     _check(contact != null and contact.visible,"Banana image roots require ground-contact shadow")
     var groundcover: Node3D = layer.get_node_or_null("BananaImageRootCover_"+name) as Node3D
     _check(groundcover != null and groundcover.visible,"Banana image card roots must be hidden by real 3D grass")
   var banana_camera: Camera3D = world.get_node("Player/CameraRig/Camera3D") as Camera3D
   var a_card: Sprite3D = layer.get_node("Card_BananaRearLeft") as Sprite3D
   var b_card: Sprite3D = layer.get_node("Card_BananaMidLeft") as Sprite3D
   if a_card != null and b_card != null:
    var a_screen: Vector2 = banana_camera.unproject_position(a_card.global_position)
    var b_screen: Vector2 = banana_camera.unproject_position(b_card.global_position)
    print("BANANA_IMAGE_COMPOSITION screen_rear=%s screen_mid=%s" % [a_screen,b_screen])
    _check(a_screen.distance_to(b_screen) >= 55.0,"Banana image silhouettes should be staggered, not visually stacked")

   # Three distinct polygon trees, not the two little round bushes from
   # the last screenshot. One must fill the far-left visual gap.
   _check(bool(plants.get_meta("left_side_recomposed",false)),"Left canopy scene must be reconstructed")
   _check(bool(plants.get_meta("left_empty_gap_filled",false)),"Left field must have a real mature tree")
   _check(int(plants.get_meta("left_large_canopy_count",0)) == 3,"Three mature left trees required")
   var large_trees: Array[String] = ["Tree_LeftFieldFill","Tree_LeftLarge_A","Tree_LeftLarge_B"]
   var composition_camera: Camera3D = world.get_node("Player/CameraRig/Camera3D") as Camera3D
   var left_positions: Array[float] = []
   for tree_name: String in large_trees:
    var mature: Node3D = plants.get_node_or_null(tree_name) as Node3D
    _check(mature != null and mature.visible,"Missing mature tree at left: "+tree_name)
    if mature != null:
     _check(int(mature.get_meta("plant_type",-1)) == 0,"Mature tree cannot still be a bush: "+tree_name)
     var maturity: float = float(mature.get_meta("authored_height",0.0))
     _check(maturity >= 2.90,"Larger tree canopy is not scaled large enough: "+tree_name)
     var projection: Vector2 = composition_camera.unproject_position(mature.global_position+Vector3.UP*maturity*0.40)
     print("LEFT_CANOPY_FINAL name=%s screen=%s height=%.2f" % [tree_name,projection,maturity])
     left_positions.append(projection.x)
   if left_positions.size() == 3:
    _check(left_positions[0] < left_positions[1] and left_positions[1] < left_positions[2],"Left trees should be spread from field to house, not overlapping into one crown")
    _check(left_positions[0] > -150.0 and left_positions[0] < 330.0,"Left filler canopy must sit inside the left field, not outside the camera")
   var house: Node3D = hero.get_node("PlayerHouseTraditionalV4") as Node3D
   var canopy: Node3D = plants.get_node("Canopy_Left_Hero") as Node3D
   var right_palm: Node3D = plants.get_node("Palm_Right_Back") as Node3D
   var fixed_camera: Camera3D = world.get_node("Player/CameraRig/Camera3D") as Camera3D
   var house_x: float = fixed_camera.unproject_position(house.global_position).x
   var canopy_x: float = fixed_camera.unproject_position(canopy.global_position).x
   var palm_x: float = fixed_camera.unproject_position(right_palm.global_position).x
   _check(canopy_x < house_x and palm_x > house_x,"3D trees must flank the house correctly in the fixed-camera composition")
   print("FOREGROUND_COMPOSITION_OK house_x=%.1f canopy_left_x=%.1f palm_right_x=%.1f hidden_old_cards=%d" % [house_x,canopy_x,palm_x,int(plants.get_meta("hidden_cards",0))])
   print("FOREGROUND_PLANTS_VALIDATED instances=%d banana=%s midground=image backdrop=image" % [models,banana_available])
 world.queue_free()
 await process_frame
 quit(1 if failed else 0)
func _check(ok: bool, message: String) -> void:
 if not ok:
  failed = true
  push_error(message)
