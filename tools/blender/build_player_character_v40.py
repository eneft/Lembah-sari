import bpy
import os
from mathutils import Vector

# Lembah Sari Character V4.0 — corrective face/hair/hand pass.
# Keeps V3.9 outfit/body/gear, but replaces the three remaining prototype reads:
# angular mask-like eyes, upright crown spikes, and blocky hands.

BASE = os.path.join(os.path.dirname(__file__), "build_player_character_v39.py")
exec(compile(open(BASE, "r", encoding="utf-8").read(), BASE, "exec"), globals(), globals())

def rm(names):
    for name in names:
        obj=bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

# FACE: soft oval eye surfaces; white stays visible but no polygon-mask silhouette.
rm(["EyeWhite_-1","EyeWhite_1","Iris_-1","Iris_1","Pupil_-1","Pupil_1",
    "EyeGlint_-1","EyeGlint_1","BrowL","BrowR","Nose","Smile"])
for side in (-1,1):
    s=float(side); x=.078*s
    uv(f"EyeWhite_{side}",(x,-.219,1.758),(.054,.0045,.036),EYE_WHITE,28,18)
    uv(f"Iris_{side}",(x+.003*s,-.224,1.756),(.030,.0038,.031),IRIS,24,16)
    uv(f"Pupil_{side}",(x+.004*s,-.228,1.755),(.013,.0030,.019),PUPIL,20,14)
    uv(f"EyeGlint_{side}",(x-.007*s,-.232,1.770),(.0055,.0018,.0065),EYE_WHITE,14,10)
curve("BrowL",[(-.132,-.213,1.817),(-.086,-.219,1.830),(-.045,-.214,1.824)],HAIR,.0048)
curve("BrowR",[(.045,-.214,1.824),(.086,-.219,1.830),(.132,-.213,1.817)],HAIR,.0048)
uv("Nose",(0,-.218,1.675),(.0042,.0020,.0048),SKIN,14,8)
curve("Smile",[(-.045,-.214,1.620),(-.022,-.219,1.612),(0,-.220,1.611),(.023,-.219,1.614),(.046,-.213,1.622)],MOUTH,.0028)

# HAIR: retain side/back volume and dominant sweep; remove upright crown spikes.
rm(["V39CrownL","V39CrownC","V39CrownR"])
loft_lock("V40CrownLeft",[
 (-.176,.012,1.938,.064,.036),(-.142,.000,1.970,.068,.037),
 (-.098,-.008,1.994,.058,.034),(-.052,-.013,2.006,.038,.027),
 (-.018,-.014,2.006,.008,.007)],HAIR_WARM,14)
loft_lock("V40CrownMid",[
 (-.060,.010,1.965,.058,.034),(-.022,.000,1.994,.062,.035),
 (.020,-.006,2.014,.052,.032),(.060,-.008,2.022,.034,.025),
 (.090,-.006,2.018,.008,.007)],HAIR,14)
loft_lock("V40CrownRight",[
 (.040,.014,1.952,.055,.033),(.082,.005,1.978,.059,.034),
 (.124,.000,1.994,.049,.030),(.160,.000,2.000,.032,.024),
 (.184,.004,1.996,.008,.007)],HAIR_WARM,14)

# HANDS: rebuild smaller coherent palm with short embedded finger pads.
for side in (-1,1):
    s=float(side)
    rm([f"Palm_{side}",f"Thumb_{side}",f"ThumbTip_{side}"]+
       [f"Finger_{side}_{i}" for i in range(4)]+[f"FingerTip_{side}_{i}" for i in range(4)])
    p=Vector((.224*s,-.071,.770))
    profile(f"Palm_{side}",[
      (p.z+.044,.032,.028,p.x,p.y),(p.z+.018,.039,.032,p.x,p.y),
      (p.z-.012,.040,.032,p.x,p.y-.002),(p.z-.038,.036,.029,p.x,p.y-.003)
    ],SKIN,30)
    offs=(-.022,-.007,.008,.022); lens=(.027,.033,.032,.025)
    for i,(off,ln) in enumerate(zip(offs,lens)):
        x=p.x+off
        uv(f"Finger_{side}_{i}",(x,p.y-.004,p.z-.042-ln*.35),(.0118,.0120,ln),SKIN,20,12)
    a=Vector((p.x+.030*s,p.y-.002,p.z+.004)); b=Vector((p.x+.050*s,p.y-.010,p.z-.022))
    tapered(f"Thumb_{side}",a,b,.0130,.0100,SKIN,20,.003)
    uv(f"ThumbTip_{side}",tuple(b),(.0102,.0105,.0115),SKIN,16,10)

# Export.
bpy.ops.object.select_all(action="DESELECT")
ROOT.select_set(True)
for obj in ROOT.children_recursive: obj.select_set(True)
bpy.context.view_layer.objects.active=ROOT
bpy.ops.export_scene.gltf(filepath=OUT_PATH,export_format="GLB",use_selection=True,export_apply=True,export_yup=True)
print(f"Exported Lembah Sari Character V4.0 corrective candidate to {OUT_PATH}")
