shader_type spatial;

uniform vec4 base_color  : source_color = vec4(0.02, 0.02, 0.07, 1.0);
uniform vec4 line_color  : source_color = vec4(0.05, 0.45, 1.0, 1.0);
uniform float cell_size      : hint_range(0.5, 8.0) = 2.0;
uniform float line_width     : hint_range(0.01, 0.3) = 0.05;
uniform float glow_intensity : hint_range(0.0, 3.0) = 0.6;

void fragment() {
	// World-space grid – consistent spacing regardless of UV mapping
	vec3 world = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	vec2 uv = fract(world.yz / cell_size);

	float lx = smoothstep(line_width, 0.0, uv.x) + smoothstep(1.0 - line_width, 1.0, uv.x);
	float ly = smoothstep(line_width, 0.0, uv.y) + smoothstep(1.0 - line_width, 1.0, uv.y);
	float grid = clamp(lx + ly, 0.0, 1.0);

	// Fade at distance so far end of corridor fades into darkness
	float dist_fade = smoothstep(85.0, 15.0, length(VERTEX));

	ALBEDO    = mix(base_color.rgb, line_color.rgb * 0.3, grid * 0.5);
	EMISSION  = line_color.rgb * grid * glow_intensity * dist_fade;
	METALLIC  = 0.7;
	ROUGHNESS = 0.4;
}
