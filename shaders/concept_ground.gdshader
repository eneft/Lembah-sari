shader_type spatial;
render_mode diffuse_burley, specular_disabled;

varying vec3 world_pos;

float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float value_noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = hash21(i);
	float b = hash21(i + vec2(1.0, 0.0));
	float c = hash21(i + vec2(0.0, 1.0));
	float d = hash21(i + vec2(1.0, 1.0));
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float broad = value_noise(world_pos.xz * 0.11);
	float medium = value_noise(world_pos.xz * 0.42);
	float fine = value_noise(world_pos.xz * 1.15);
	vec3 grass_a = vec3(0.34, 0.48, 0.22);
	vec3 grass_b = vec3(0.45, 0.58, 0.28);
	vec3 grass_c = vec3(0.39, 0.52, 0.23);
	vec3 base = mix(grass_a, grass_b, broad);
	base = mix(base, grass_c, medium * 0.42);
	base += (fine - 0.5) * 0.035;
	float dry_patch = smoothstep(0.72, 0.94, value_noise(world_pos.xz * 0.055 + vec2(7.0, 3.0)));
	base = mix(base, vec3(0.48, 0.49, 0.27), dry_patch * 0.30);
	ALBEDO = base;
	ROUGHNESS = 0.98;
}
