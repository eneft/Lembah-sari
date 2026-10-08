shader_type spatial;

uniform vec4 low_color : source_color;
uniform vec4 high_color : source_color;
uniform vec4 accent_color : source_color = vec4(0.35,0.42,0.25,1.0);
uniform float grain_scale = 20.0;
uniform float macro_scale = 0.16;
uniform float macro_strength = 0.24;
uniform float surface_kind = 0.0;
uniform float footpath_detail = 0.0;

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

	// Paths/soil receive a slight height projection so slopes do not smear.
	if(surface_kind>0.5&&surface_kind<1.5){
		p+=place.y*vec2(0.73,0.91);
	}
	// Timber/bamboo keeps grain running along a more useful axis.
	if(surface_kind>1.5){
		p=vec2(place.x+place.z,place.y);
	}

	float macro=noise(p*macro_scale);
	float broad=noise(p*0.72+vec2(17.3,-9.1));
	float medium=noise(p*1.85);
	float fine=noise(p*grain_scale);
	float micro=noise(p*grain_scale*4.0);

	float t=medium*0.38+fine*0.39+micro*0.13+broad*0.10;
	vec3 base=mix(low_color.rgb,high_color.rgb,clamp(t,0.0,1.0));

	// Large soft islands remove the flat "game-board" lawn read without adding
	// another texture download. Accent hue is intentionally restrained.
	float island=smoothstep(0.48,0.82,macro)*macro_strength;
	base=mix(base,accent_color.rgb,island);

	if(surface_kind<0.5){
		// Grass: gentle sun-dry variation and darker low-frequency pockets.
		float dry=smoothstep(0.62,0.90,noise(p*0.095+vec2(-31.0,12.0)));
		float pocket=smoothstep(0.58,0.88,noise(p*0.23+vec2(4.0,41.0)));
		base=mix(base,base*vec3(1.06,1.035,0.90),dry*0.18);
		base*=1.0-pocket*0.10;
	}else if(surface_kind<1.5){
		// Dirt/soil: compressed tracks and slightly darker damp mottling.
		float compact=noise(p*vec2(0.34,1.65));
		base*=mix(0.92,1.045,compact);
		if(footpath_detail>0.5){
			// Tiny stone specks and soft compressed footprints live INSIDE
			// the existing path geometry; no duplicated road and no z-fighting.
			float pressed=noise(p*vec2(0.61,1.4)+vec2(18.0,-7.0));
			float pebbles=smoothstep(0.83,0.96,noise(p*7.8+vec2(31.0,17.0)));
			base*=1.0-pressed*0.055;
			base=mix(base,base*vec3(0.90,0.92,0.87),pebbles*0.21);
		}
	}else{
		float grain=noise(p*vec2(45.0,3.0));
		base=mix(base,accent_color.rgb,grain*0.12);
	}

	ALBEDO=base;
	ROUGHNESS=0.94;
	SPECULAR=0.14;
}
