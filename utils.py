import bpy
import colorsys
import math
from mathutils import Vector, noise


def rgb_to_hsv(rgb):
    r, g, b = rgb[:3]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return (h, s, v)


def hsv_to_rgb(hsv):
    h, s, v = hsv
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b)


def compute_harmony_colors(key_rgb, mode, intensity, fill_rgb=None, rim_rgb=None):
    if mode == 'OFF':
        return (fill_rgb or key_rgb[:3], rim_rgb or key_rgb[:3])

    h, s, v = rgb_to_hsv(key_rgb)
    harmony_s = max(s, 0.6)

    if mode == 'COMPLEMENTARY':
        fill_h = (h + 0.5) % 1.0
        rim_h = (h + 0.5) % 1.0
    elif mode == 'TRIADIC':
        fill_h = (h + 1.0 / 3.0) % 1.0
        rim_h = (h + 2.0 / 3.0) % 1.0
    elif mode == 'ANALOGOUS':
        fill_h = (h - 1.0 / 12.0) % 1.0
        rim_h = (h + 1.0 / 12.0) % 1.0
    elif mode == 'CINEMATIC':
        fill_h = 0.55
        rim_h = 0.55
    else:
        fill_h = h
        rim_h = h

    fill_rgb_computed = hsv_to_rgb((fill_h, harmony_s, v))
    rim_rgb_computed = hsv_to_rgb((rim_h, harmony_s, v))

    if intensity < 1.0:
        orig_fill = fill_rgb or key_rgb[:3]
        orig_rim = rim_rgb or key_rgb[:3]
        fill_rgb_computed = tuple(
            fill_rgb_computed[i] * intensity + orig_fill[i] * (1.0 - intensity)
            for i in range(3)
        )
        rim_rgb_computed = tuple(
            rim_rgb_computed[i] * intensity + orig_rim[i] * (1.0 - intensity)
            for i in range(3)
        )

    return (fill_rgb_computed, rim_rgb_computed)


def sample_image_dominant_color(image):
    if image is None or not hasattr(image, 'pixels'):
        return (0.5, 0.5, 0.5, 1.0)

    # Access image.pixels to force Blender to load the buffer; retry once on failure
    try:
        total_pixels = len(image.pixels) // 4
    except RuntimeError:
        try:
            image.reload()
            total_pixels = len(image.pixels) // 4
        except RuntimeError:
            return (0.5, 0.5, 0.5, 1.0)
    except (TypeError, AttributeError):
        return (0.5, 0.5, 0.5, 1.0)

    if total_pixels == 0:
        return (0.5, 0.5, 0.5, 1.0)

    # Subsample to max 10,000 pixels to avoid freezing on large images
    max_samples = 10000
    step = max(1, total_pixels // max_samples)

    r_sum = g_sum = b_sum = a_sum = 0.0
    sample_count = 0

    try:
        pixels = image.pixels
        for i in range(0, total_pixels, step):
            idx = i * 4
            if idx + 3 >= len(pixels):
                break
            r_sum += pixels[idx]
            g_sum += pixels[idx + 1]
            b_sum += pixels[idx + 2]
            a_sum += pixels[idx + 3]
            sample_count += 1
    except (RuntimeError, TypeError, AttributeError, IndexError):
        return (0.5, 0.5, 0.5, 1.0)

    if sample_count == 0:
        return (0.5, 0.5, 0.5, 1.0)

    inv_count = 1.0 / sample_count
    return (r_sum * inv_count, g_sum * inv_count, b_sum * inv_count, a_sum * inv_count)


def build_procedural_world_nodes(scene, key_rgb, fill_rgb, strength=0.1):
    if scene.world is None:
        scene.world = bpy.data.worlds.new(name="EeveePulse_World")

    world = scene.world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    nodes.clear()

    output = nodes.new('ShaderNodeOutputWorld')
    output.location = (400, 0)

    background = nodes.new('ShaderNodeBackground')
    background.location = (200, 0)
    background.inputs['Strength'].default_value = strength

    color_ramp = nodes.new('ShaderNodeValToRGB')
    color_ramp.location = (0, 0)
    color_ramp.color_ramp.interpolation = 'LINEAR'
    color_ramp.color_ramp.elements[0].position = 0.0
    color_ramp.color_ramp.elements[0].color = (*key_rgb[:3], 1.0)
    color_ramp.color_ramp.elements[1].position = 1.0
    color_ramp.color_ramp.elements[1].color = (*fill_rgb[:3], 1.0)

    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-400, 0)

    separate_xyz = nodes.new('ShaderNodeSeparateXYZ')
    separate_xyz.location = (-200, 0)

    map_range = nodes.new('ShaderNodeMapRange')
    map_range.location = (-100, 0)
    map_range.inputs['From Min'].default_value = -1.0
    map_range.inputs['From Max'].default_value = 1.0
    map_range.inputs['To Min'].default_value = 0.0
    map_range.inputs['To Max'].default_value = 1.0

    links.new(tex_coord.outputs['Generated'], separate_xyz.inputs['Vector'])
    links.new(separate_xyz.outputs['Z'], map_range.inputs['Value'])
    links.new(map_range.outputs['Result'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], background.inputs['Color'])
    links.new(background.outputs['Background'], output.inputs['Surface'])

    return world


def calculate_pulse_offset(frame, waveform, frequency, amplitude):
    t = frame * frequency * 2.0 * math.pi

    if waveform == 'SINE':
        return math.sin(t) * amplitude
    elif waveform == 'BREATHE':
        return (1.0 - math.cos(t)) * 0.5 * amplitude
    elif waveform == 'SAWTOOTH':
        return (t / math.pi % 2.0 - 1.0) * amplitude
    elif waveform == 'NOISE':
        return noise.noise(Vector((frame * 0.01, 0, 0))) * amplitude
    else:
        return 0.0


def update_rig_properties(props, context):
    key_rgb = props.key_color[:3]
    fill_rgb, rim_rgb = compute_harmony_colors(
        key_rgb, props.harmony_mode, props.harmony_intensity,
        props.fill_color[:3], props.rim_color[:3]
    )

    dist = 2.5
    target = bpy.data.objects.get("EeveePulse_Target")
    if target:
        dist = target.get("eeveepulse_dist_factor", 2.5)
    energy_scale = (dist / 2.5) ** 2

    for obj in bpy.data.objects:
        if obj.get("eeveepulse_rig") == True and obj.type == 'LIGHT':
            if obj.name == "EeveePulse_Key":
                obj.data.energy = props.key_intensity * energy_scale
                obj.data.color = props.key_color[:3]
            elif obj.name == "EeveePulse_Fill":
                obj.data.energy = props.fill_intensity * energy_scale
                obj.data.color = fill_rgb
            elif obj.name == "EeveePulse_Rim":
                obj.data.energy = props.rim_intensity * energy_scale
                obj.data.color = rim_rgb


PRESETS_DATA = {
    'NEUTRAL_STUDIO': {
        'key_intensity': 1000.0,
        'fill_intensity': 300.0,
        'rim_intensity': 500.0,
        'key_color': (1.0, 1.0, 1.0, 1.0),
        'fill_color': (1.0, 1.0, 1.0, 1.0),
        'rim_color': (1.0, 1.0, 1.0, 1.0),
        'harmony_mode': 'OFF',
        'harmony_intensity': 0.0,
        'rig_scale_factor': 1.5,
        'auto_probes': True,
        'optimize_eevee_shadows': True,
    },
    'DRAMATIC_NOIR': {
        'key_intensity': 1000.0,
        'fill_intensity': 100.0,
        'rim_intensity': 50.0,
        'key_color': (1.0, 0.95, 0.85, 1.0),
        'fill_color': (0.2, 0.2, 0.25, 1.0),
        'rim_color': (0.1, 0.1, 0.15, 1.0),
        'harmony_mode': 'COMPLEMENTARY',
        'harmony_intensity': 1.0,
        'rig_scale_factor': 1.5,
        'auto_probes': True,
        'optimize_eevee_shadows': True,
    },
    'SOFT_COMMERCIAL': {
        'key_intensity': 800.0,
        'fill_intensity': 600.0,
        'rim_intensity': 400.0,
        'key_color': (1.0, 0.98, 0.9, 1.0),
        'fill_color': (0.9, 0.95, 1.0, 1.0),
        'rim_color': (0.95, 1.0, 0.9, 1.0),
        'harmony_mode': 'ANALOGOUS',
        'harmony_intensity': 0.5,
        'rig_scale_factor': 1.2,
        'auto_probes': True,
        'optimize_eevee_shadows': True,
    },
    'CYBERPUNK_NEON': {
        'key_intensity': 1200.0,
        'fill_intensity': 800.0,
        'rim_intensity': 1000.0,
        'key_color': (1.0, 0.0, 0.5, 1.0),
        'fill_color': (0.0, 1.0, 1.0, 1.0),
        'rim_color': (1.0, 0.0, 1.0, 1.0),
        'harmony_mode': 'TRIADIC',
        'harmony_intensity': 1.0,
        'rig_scale_factor': 1.8,
        'auto_probes': True,
        'optimize_eevee_shadows': True,
    },
    'HIGH_KEY': {
        'key_intensity': 1500.0,
        'fill_intensity': 1200.0,
        'rim_intensity': 800.0,
        'key_color': (1.0, 1.0, 0.95, 1.0),
        'fill_color': (1.0, 1.0, 0.9, 1.0),
        'rim_color': (1.0, 0.95, 1.0, 1.0),
        'harmony_mode': 'OFF',
        'harmony_intensity': 0.0,
        'rig_scale_factor': 2.0,
        'auto_probes': True,
        'optimize_eevee_shadows': False,
    },
}


def register():
    pass


def unregister():
    pass