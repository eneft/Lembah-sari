shader_type spatial;
uniform vec4 low_color : source_color;
uniform vec4 high_color : source_color;
uniform float grain_scale = 20.0;
uniform float surface_kind = 0.0;
varying vec3 place;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p);vec2 f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1)),f.x),f.y);}
void vertex(){place=(MODEL_MATRIX*vec4(VERTEX,1)).xyz;}
void fragment(){
 vec2 p=place.xz;
 if(surface_kind>0.5&&surface_kind<1.5){p+=place.y*vec2(0.73,0.91);}
 if(surface_kind>1.5){p=vec2(place.x+place.z,place.y);}
 float t=noise(p*1.3)*0.48+noise(p*grain_scale)*0.36+noise(p*grain_scale*4.0)*0.16;
 if(surface_kind>1.5){t=t*0.65+noise(p*vec2(45,3))*0.35;}
 ALBEDO=mix(low_color.rgb,high_color.rgb,t);ROUGHNESS=0.93;SPECULAR=0.18;
}
