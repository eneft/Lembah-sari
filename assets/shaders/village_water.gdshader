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

	// Calm tropical river: broad value drift plus two low-amplitude ripple sets.
	float broad=noise(p*0.115+vec2(TIME*0.008,-TIME*0.004));
	float a=sin(p.x*7.2+p.y*3.4+sin(p.y*1.8)*0.30+TIME*0.46);
	float b=sin(p.x*4.4-p.y*6.8+sin(p.x*1.1)*0.45-TIME*0.31);
	float ripple=a*0.58+b*0.42;

	vec3 deep=vec3(0.055,0.235,0.225);
	vec3 mid=vec3(0.095,0.365,0.315);
	vec3 shallow=vec3(0.235,0.515,0.405);
	vec3 base=mix(deep,mid,0.46+broad*0.34);
	base=mix(base,shallow,clamp((ripple+1.0)*0.035,0.0,0.075));

	// Sparse glints only; avoid the plastic/specular pool look.
	float glint=pow(max(0.0,a*b),14.0)*0.018;
	ALBEDO=base+vec3(glint);

	NORMAL_MAP=vec3(0.5+a*0.009,0.5+b*0.009,1.0);
	ROUGHNESS=0.72;
	SPECULAR=0.13;
}
