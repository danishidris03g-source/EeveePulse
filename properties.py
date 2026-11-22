import bpy
from mathutils import Vector
from . import utils


def _register_camera_handler():
    if _camera_lock_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_camera_lock_handler)


def _unregister_camera_handler():
    if _camera_lock_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_camera_lock_handler)


def _camera_lock_handler(scene, depsgraph):
    props = scene.eeveepulse_props
    if not props.camera_lock_mode:
        return

    target_obj = None
    for obj in scene.objects:
        if obj.get("eeveepulse_rig") == True and obj.name == "EeveePulse_Target":
            target_obj = obj
            break

    if target_obj and scene.camera:
        cam_mat = scene.camera.matrix_world
        cam_forward = cam_mat.to_quaternion() @ Vector((0, 0, -1))
        cam_up = cam_mat.to_quaternion() @ Vector((0, 1, 0))
        cam_right = cam_mat.to_quaternion() @ Vector((1, 0, 0))

        dist = target_obj.get("eeveepulse_dist_factor", 2.5)
        radius = dist * 0.5

        for obj in scene.objects:
            if obj.get("eeveepulse_rig") == True and obj.type == 'LIGHT':
                if obj.name == "EeveePulse_Key":
                    offset = Vector((1.5, 1.2, -1.5)) * radius
                elif obj.name == "EeveePulse_Fill":
                    offset = Vector((-1.5, 0.8, -1.2)) * radius
                elif obj.name == "EeveePulse_Rim":
                    offset = Vector((-0.6, 0.8, 1.5)) * radius
                else:
                    continue

                new_loc = cam_right * offset.x + cam_up * offset.y + cam_forward * offset.z
                if (obj.location - new_loc).length > 1e-5:
                    obj.location = new_loc


def update_rig_properties(self, context):
    utils.update_rig_properties(self, context)
    update_world_dome(self, context)


def update_camera_lock(self, context):
    if self.camera_lock_mode:
        _register_camera_handler()
    else:
        _unregister_camera_handler()


def update_world_dome(self, context):
    if self.auto_world_dome:
        props = context.scene.eeveepulse_props
        key_rgb = props.key_color[:3]
        fill_rgb, _ = utils.compute_harmony_colors(key_rgb, props.harmony_mode, props.harmony_intensity, props.fill_color[:3], props.rim_color[:3])
        utils.build_procedural_world_nodes(context.scene, key_rgb, fill_rgb, props.world_strength)


class EeveePulseSettings(bpy.types.PropertyGroup):
    key_intensity: bpy.props.FloatProperty(
        name="Key Intensity",
        description="Intensity of the key light",
        default=1000.0,
        min=0.0,
        max=10000000.0,
        soft_max=100000.0,
        update=update_rig_properties
    )
    fill_intensity: bpy.props.FloatProperty(
        name="Fill Intensity",
        description="Intensity of the fill light",
        default=300.0,
        min=0.0,
        max=10000000.0,
        soft_max=100000.0,
        update=update_rig_properties
    )
    rim_intensity: bpy.props.FloatProperty(
        name="Rim Intensity",
        description="Intensity of the rim light",
        default=500.0,
        min=0.0,
        max=10000000.0,
        soft_max=100000.0,
        update=update_rig_properties
    )

    key_color: bpy.props.FloatVectorProperty(
        name="Key Color",
        description="Color of the key light",
        subtype='COLOR',
        size=4,
        default=(1.0, 0.95, 0.85, 1.0),
        min=0.0,
        max=1.0,
        update=update_rig_properties
    )
    fill_color: bpy.props.FloatVectorProperty(
        name="Fill Color",
        description="Color of the fill light",
        subtype='COLOR',
        size=4,
        default=(0.7, 0.85, 1.0, 1.0),
        min=0.0,
        max=1.0,
        update=update_rig_properties
    )
    rim_color: bpy.props.FloatVectorProperty(
        name="Rim Color",
        description="Color of the rim light",
        subtype='COLOR',
        size=4,
        default=(1.0, 1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        update=update_rig_properties
    )

    rig_scale_factor: bpy.props.FloatProperty(
        name="Rig Scale Factor",
        description="Scale factor applied to the light rig",
        default=1.5,
        min=0.1,
        max=10.0
    )

    auto_probes: bpy.props.BoolProperty(
        name="Auto Probes",
        description="Automatically place reflection probes",
        default=True
    )
    optimize_eevee_shadows: bpy.props.BoolProperty(
        name="Optimize Eevee Shadows",
        description="Optimize shadow settings for Eevee",
        default=True
    )
    auto_shadow_blockers: bpy.props.BoolProperty(
        name="Auto Shadow Blockers",
        description="Automatically add shadow blocker planes",
        default=False
    )

    blocker_distance_scale: bpy.props.FloatProperty(
        name="Blocker Distance Scale",
        description="Distance scale for shadow blocker planes",
        default=1.2,
        min=0.5,
        max=5.0
    )

    harmony_mode: bpy.props.EnumProperty(
        name="Harmony Mode",
        description="Color harmony mode for fill and rim lights",
        items=(
            ('OFF', "Off", "No color harmony, use colors as-is"),
            ('COMPLEMENTARY', "Complementary", "Fill and Rim opposite to Key hue"),
            ('TRIADIC', "Triadic", "Fill and Rim at +120° and +240° from Key"),
            ('ANALOGOUS', "Analogous", "Fill and Rim at ±30° from Key"),
            ('CINEMATIC', "Cinematic", "Warm Key (orange), Cool Fill/Rim (teal)"),
        ),
        default='OFF',
        update=update_rig_properties
    )
    harmony_intensity: bpy.props.FloatProperty(
        name="Harmony Intensity",
        description="Strength of color harmony blending (0 = original colors, 1 = full harmony)",
        default=0.0,
        min=0.0,
        max=1.0,
        update=update_rig_properties
    )

    # Animation
    anim_start_frame: bpy.props.IntProperty(
        name="Start Frame",
        description="Animation start frame for pulse",
        default=1,
        min=1
    )
    anim_end_frame: bpy.props.IntProperty(
        name="End Frame",
        description="Animation end frame for pulse",
        default=250,
        min=1
    )
    pulse_waveform: bpy.props.EnumProperty(
        name="Pulse Waveform",
        description="Waveform type for pulse animation",
        items=(
            ('SINE', "Sine", "Smooth sine wave"),
            ('BREATHE', "Breathe", "Ease-in/out breathing curve"),
            ('SAWTOOTH', "Sawtooth", "Sharp linear ramp"),
            ('NOISE', "Noise", "Procedural mathutils noise"),
        ),
        default='SINE'
    )
    pulse_frequency: bpy.props.FloatProperty(
        name="Pulse Frequency",
        description="Cycles per frame for pulse animation",
        default=0.05,
        min=0.001,
        max=1.0
    )
    pulse_amplitude: bpy.props.FloatProperty(
        name="Pulse Amplitude",
        description="Strength of pulse modulation",
        default=0.5,
        min=0.0,
        max=2.0
    )

    # Camera Lock
    camera_lock_mode: bpy.props.BoolProperty(
        name="Camera Lock",
        description="Lock camera to rig target",
        default=False,
        update=update_camera_lock
    )

    # Image Sampler
    ref_image: bpy.props.PointerProperty(
        name="Reference Image",
        description="Image to sample dominant color from",
        type=bpy.types.Image
    )

    # World Environment
    auto_world_dome: bpy.props.BoolProperty(
        name="Auto World Dome",
        description="Automatically build procedural world node setup",
        default=False,
        update=update_world_dome
    )
    world_strength: bpy.props.FloatProperty(
        name="World Strength",
        description="Brightness strength of procedural world dome",
        default=0.1,
        min=0.0,
        max=5.0,
        update=update_world_dome
    )

    preset_choice: bpy.props.EnumProperty(
        name="Preset",
        description="Lighting preset",
        items=(
            ('NEUTRAL_STUDIO', "Neutral Studio", "Pure white lights, uncolored setup"),
            ('DRAMATIC_NOIR', "Dramatic Noir", "High contrast, moody"),
            ('SOFT_COMMERCIAL', "Soft Commercial", "Balanced, even lighting"),
            ('CYBERPUNK_NEON', "Cyberpunk Neon", "High saturation, triadic"),
            ('HIGH_KEY', "High Key", "Bright, minimal shadows"),
        ),
        default='NEUTRAL_STUDIO'
    )


def register():
    bpy.utils.register_class(EeveePulseSettings)
    bpy.types.Scene.eeveepulse_props = bpy.props.PointerProperty(type=EeveePulseSettings)


def unregister():
    _unregister_camera_handler()
    del bpy.types.Scene.eeveepulse_props
    bpy.utils.unregister_class(EeveePulseSettings)