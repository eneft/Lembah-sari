shader_type spatial;
render_mode cull_disabled;
varying vec4 tint;
void vertex(){tint=COLOR;vec3 wp=(MODEL_MATRIX*vec4(VERTEX,1)).xyz;VERTEX.x+=sin(TIME*1.35+wp.x*1.8+wp.z)*0.012*UV.y;}
void fragment(){float vein=1.0-smoothstep(0.008,0.028,abs(UV.x-0.5));ALBEDO=tint.rgb*(0.82+0.2*sin(UV.x*3.14159)+0.07*vein);EMISSION=ALBEDO*0.16;ROUGHNESS=0.88;SPECULAR=0.18;if(!FRONT_FACING){NORMAL=-NORMAL;}}
