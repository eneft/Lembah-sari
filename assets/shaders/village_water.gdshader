shader_type spatial;
varying vec3 place;
void vertex(){place=(MODEL_MATRIX*vec4(VERTEX,1)).xyz;}
void fragment(){
 vec2 p=place.xz;float a=sin(p.x*12.0+p.y*6.0+sin(p.y*3.0)*0.35+TIME*0.7);float b=sin(p.x*7.0-p.y*11.0+sin(p.x*1.5)*0.6-TIME*0.45);
 float glint=pow(max(0.0,a*b),10.0)*0.009;
 ALBEDO=mix(vec3(0.085,0.25,0.235),vec3(0.24,0.47,0.38),(a*0.55+b*0.45)*0.055+0.52)+glint;
 NORMAL_MAP=vec3(0.5+a*0.013,0.5+b*0.013,1.0);ROUGHNESS=0.62;SPECULAR=0.18;
}
