shader_type spatial;

varying vec3 place;

float hash(vec2 p){
	return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);
}

float noise(vec2 p){
	vec2 i=floor(p);
	vec2 f=fract(p);
	f=f*f*(3.0-2.0*f);
	return mix(
		mix(hash(i),hash(i+vec2(1.0,0.0)),f.x),
		mix(hash(i+vec2(0.0,1.0)),hash(i+vec2(1.0,1.0)),f.x),
		f.y
	);
}

void vertex(){
	place=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;
}

void fragment(){
	vec2 p=place.xz;

	// Flooded rice terraces should read as shallow, still water rather than
	// miniature rivers. Keep movement slow and specular response restrained.
	float broad=noise(p*0.22+vec2(TIME*0.003,-TIME*0.002));
	float s1=sin(p.x*3.6+p.y*2.1+TIME*0.12);
	float s2=sin(p.x*2.2-p.y*3.0-TIME*0.09);
	float ripple=(s1+s2)*0.5;

	vec3 mud=vec3(0.205,0.285,0.185);
	vec3 green=vec3(0.235,0.405,0.285);
	vec3 sky=vec3(0.405,0.570,0.455);
	vec3 base=mix(mud,green,0.48+broad*0.28);
	base=mix(base,sky,clamp((ripple+1.0)*0.035,0.0,0.07));

	ALBEDO=base;
	NORMAL_MAP=vec3(0.5+s1*0.004,0.5+s2*0.004,1.0);
	ROUGHNESS=0.80;
	SPECULAR=0.10;
}
