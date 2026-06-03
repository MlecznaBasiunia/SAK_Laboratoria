shader_type sky;
render_mode use_half_res_pass;

float hash(vec2 p) {
	p = fract(p * vec2(234.34, 435.345));
	p += dot(p, p + 34.23);
	return fract(p.x * p.y);
}

float stars(vec3 dir, float density, vec2 offset) {
	vec2 sph = vec2(
		atan(dir.x, dir.z) * 0.15915,
		asin(clamp(dir.y, -0.9999, 0.9999)) * 0.31831
	) * density + offset;
	vec2 cell = floor(sph);
	vec2 f = fract(sph) - 0.5;
	float h = hash(cell);
	float threshold = 0.92;
	float edge = smoothstep(0.4, 0.0, length(f));
	return edge * step(threshold, h) * (h - threshold) / (1.0 - threshold);
}

void sky() {
	vec3 dir = normalize(EYEDIR);

	// Dark space background
	vec3 col = vec3(0.0, 0.0, 0.025) + vec3(0.003, 0.0, 0.01) * smoothstep(-0.2, 0.8, dir.y);

	// Nebula wisps
	float n1 = smoothstep(0.7, 0.0, abs(dir.y - 0.05)) * smoothstep(0.6, 0.0, abs(dir.x - 0.1));
	float n2 = smoothstep(0.5, 0.0, abs(dir.y + 0.15)) * smoothstep(0.5, 0.0, abs(dir.z + 0.4));
	col += vec3(0.025, 0.008, 0.12) * n1 * 0.8;
	col += vec3(0.005, 0.03, 0.1) * n2 * 0.6;

	// Stars – 3 layers (size, brightness, colour vary)
	col += vec3(1.0, 0.95, 0.85) * stars(dir, 50.0, vec2(0.0, 0.0));
	col += vec3(0.8, 0.85, 1.0)  * stars(dir, 80.0, vec2(17.3, 5.7))  * 0.6;
	col += vec3(1.0, 0.75, 0.6)  * stars(dir, 130.0, vec2(3.9, 22.1)) * 0.35;

	// Gas giant – orange/red, visible forward-right
	vec3 planet_dir = normalize(vec3(0.45, 0.18, -0.875));
	float pd = acos(clamp(dot(dir, planet_dir), -1.0, 1.0));
	float planet = smoothstep(0.088, 0.080, pd);
	vec3 p_local = normalize(dir - planet_dir * dot(dir, planet_dir));
	float bands = sin(p_local.y * 120.0) * 0.5 + 0.5;
	vec3 planet_col = mix(vec3(0.62, 0.22, 0.04), vec3(0.82, 0.45, 0.15), bands);
	col = mix(col, planet_col, planet);
	col += vec3(0.35, 0.1, 0.01) * smoothstep(0.14, 0.088, pd) * (1.0 - planet) * 0.3;

	// Moon – grey-blue, forward-left
	vec3 moon_dir = normalize(vec3(-0.65, 0.12, -0.75));
	float md = acos(clamp(dot(dir, moon_dir), -1.0, 1.0));
	float moon = smoothstep(0.033, 0.026, md);
	float crater = hash(floor(p_local.yz * 40.0 + 7.3));
	col = mix(col, vec3(0.48, 0.52, 0.62) * (0.8 + crater * 0.2), moon);

	COLOR = vec4(col, 1.0);
}
