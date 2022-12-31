import time

import moderngl as mgl
from PIL import Image

ctx = mgl.create_standalone_context()

width, height = 1080, 1080
gw, gh = 16, 16

code = '''
#version 430

#define SMOOTHSTEP_OFFSET 0.0001

layout (local_size_x = 16, local_size_y = 16) in;

layout(rgba8, location=0) writeonly uniform image2D destTex;

uniform vec2 offset;
uniform float radius;

float sdf_circle(in vec2 p, in float r) {
    return length(p)-r;
}

void main() {
    ivec2 texelPos = ivec2(gl_GlobalInvocationID.xy);

    float distance = sdf_circle(texelPos - offset, radius);
    
    float fill = smoothstep(-0.75, 0.75+SMOOTHSTEP_OFFSET, distance);
    
    vec4 col1 = vec4(1.0);
    vec4 col2 = vec4(vec3(1.0), 0.0);
    
    vec4 col = mix(col1, col2, fill);
    
    imageStore(destTex, texelPos, col);
}
'''

radius = 100
center = (450, 450)

shader1 = ctx.compute_shader(code)
shader1['destTex'] = 0
shader1['offset'] = center
shader1['radius'] = radius

# Method 1

local_size = int(width / gw + 0.5), int(height / gh + 0.5), 1

tex1 = ctx.texture((width, height), 4)
tex1.bind_to_image(0, read=False, write=True)

start = time.time_ns()

for _ in range(10000):
    shader1.run(*local_size)

print((time.time_ns() - start) / 1e6)

image = Image.frombytes("RGBA", tex1.size, tex1.read(), "raw")
image = image.transpose(Image.FLIP_TOP_BOTTOM)
image.show()
image.save("without_bb.png")

# Method 2

code = '''
#version 430

#define SMOOTHSTEP_OFFSET 0.0001

layout (local_size_x = 16, local_size_y = 16) in;

layout(rgba8, location=0) writeonly uniform image2D destTex;

uniform vec2 center;
uniform float radius;

uniform vec2 offset;

float sdf_circle(in vec2 p, in float r) {
    return length(p)-r;
}

void main() {
    ivec2 texelPos = ivec2(gl_GlobalInvocationID.xy) + ivec2(offset);

    float distance = sdf_circle(texelPos - center, radius);
    
    float fill = smoothstep(-0.75, 0.75+SMOOTHSTEP_OFFSET, distance);
    
    vec4 col1 = vec4(1.0);
    vec4 col2 = vec4(vec3(1.0), 0.0);
    
    vec4 col = mix(col1, col2, fill);
    
    imageStore(destTex, texelPos, col);
}
'''

shader2 = ctx.compute_shader(code)
shader2['destTex'] = 0
shader2['center'] = center
shader2['radius'] = radius

tex2 = ctx.texture((width, height), 4)
tex2.bind_to_image(0, read=False, write=True)

rw, rh = int(radius * 2 + 5), int(radius * 2 + 5)

render_offset = int(center[0] - radius - 3), int(center[0] - radius - 3)

local_size = int(rw / gw + 0.5), int(rh / gh + 0.5), 1

shader2['offset'] = render_offset

start = time.time_ns()

for _ in range(10000):
    shader2.run(*local_size)

print((time.time_ns() - start) / 1e6)

image = Image.frombytes("RGBA", tex2.size, tex2.read(), "raw")
image = image.transpose(Image.FLIP_TOP_BOTTOM)
image.show()
image.save("with_bb.png")
