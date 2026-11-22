import bpy
from mathutils import Vector
from . import utils


def _safe_set(obj, attr, value):
    if obj is not None and hasattr(obj, attr):
        try:
            setattr(obj, attr, value)
        except TypeError:
            pass


def _create_shadow_blocker(context, target, light, scale_factor, distance_scale):
    direction = (target.location - light.location).normalized()
    distance = (target.location - light.location).length * distance_scale
    blocker_loc = light.location + direction * distance
    size = max(scale_factor) * 2.0

    bpy.ops.mesh.primitive_plane_add(size=size, location=blocker_loc)
    blocker = context.active_object
    blocker.name = f"{light.name}_ShadowBlocker"
    blocker.data.name = blocker.name
    blocker.display_type = 'WIRE'
    blocker.hide_render = True

    track = blocker.constraints.new('TRACK_TO')
    track.target = target
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'

    blocker["eeveepulse_rig"] = True
    blocker.parent = target
    return blocker


class EEVEEPULSE_OT_generate_rig(bpy.types.Operator):
    bl_idname = "eeveepulse.generate_rig"
    bl_label = "Generate EeveePulse Rig"
    bl_description = "Generate a three-point area light rig with probes and optional shadow blockers"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        props = scene.eeveepulse_props

        # Save existing target location and base_size before removing existing rig
        saved_location = None
        saved_base_size = None
        existing_target = bpy.data.objects.get("EeveePulse_Target")
        if existing_target:
            saved_location = existing_target.location.copy()
            saved_base_size = existing_target.get("eeveepulse_base_size")

        # Remove any existing rig objects before generating new ones
        existing = [o for o in bpy.data.objects if o.get("eeveepulse_rig") == True]
        for obj in existing:
            bpy.data.objects.remove(obj, do_unlink=True)

        # Remove orphaned light probe data-blocks
        for probe in list(bpy.data.lightprobes):
            if probe.name.startswith("EeveePulse_") and probe.users == 0:
                bpy.data.lightprobes.remove(probe)

        # Remove orphaned light data-blocks
        for light in list(bpy.data.lights):
            if light.name.startswith("EeveePulse_") and light.users == 0:
                bpy.data.lights.remove(light)

        # Remove orphaned mesh data-blocks
        for mesh in list(bpy.data.meshes):
            if mesh.name.startswith("EeveePulse_") and mesh.users == 0:
                bpy.data.meshes.remove(mesh)

        # Compute combined bounding box from all selected mesh objects
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if selected_meshes:
            min_co = Vector((float('inf'), float('inf'), float('inf')))
            max_co = Vector((float('-inf'), float('-inf'), float('-inf')))
            for obj in selected_meshes:
                corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
                obj_min = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
                obj_max = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
                min_co = Vector((min(min_co.x, obj_min.x), min(min_co.y, obj_min.y), min(min_co.z, obj_min.z)))
                max_co = Vector((max(max_co.x, obj_max.x), max(max_co.y, obj_max.y), max(max_co.z, obj_max.z)))
            center = (min_co + max_co) * 0.5
            size = max_co - min_co
        else:
            # Fallback to active object
            obj = context.active_object
            if obj is not None and obj.type == 'MESH':
                corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
                min_co = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
                max_co = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
                center = (min_co + max_co) * 0.5
                size = max_co - min_co
            elif saved_location is not None and saved_base_size is not None:
                # Use saved location and size from previous rig
                center = saved_location
                size = Vector(saved_base_size)
            else:
                center = Vector((0.0, 0.0, 0.0))
                size = Vector((2.0, 2.0, 2.0))

        max_dim = max(size.x, size.y, size.z)
        radius = (max_dim * 0.5) * props.rig_scale_factor
        dim = Vector((max(size.x, 0.01), max(size.y, 0.01), max(size.z, 0.01))) * props.rig_scale_factor

        # Distance factor for inverse-square energy scaling
        dist = max(radius * 2.0, 1.0)

        bpy.ops.object.select_all(action='DESELECT')

        # Parent empty at target center
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=center)
        target = context.active_object
        target.name = "EeveePulse_Target"
        target.empty_display_size = max_dim * 0.25 * props.rig_scale_factor
        target["eeveepulse_rig"] = True
        target["eeveepulse_dist_factor"] = dist
        target["eeveepulse_base_size"] = tuple(size)

        # Three-point area light rig
        key_light = None
        light_size = max(radius * 1.0, 0.5)
        lights = (
            ("EeveePulse_Key", props.key_intensity, props.key_color, Vector((radius * 1.5, -radius * 1.5, radius * 1.2))),
            ("EeveePulse_Fill", props.fill_intensity, props.fill_color, Vector((-radius * 1.5, radius * 1.2, radius * 0.8))),
            ("EeveePulse_Rim", props.rim_intensity, props.rim_color, Vector((-radius * 0.6, -radius * 1.5, -radius * 0.8))),
        )
        for name, energy, color, offset in lights:
            bpy.ops.object.light_add(type='AREA', location=center + offset)
            light = context.active_object
            light.name = name
            light.data.name = name
            # Inverse-square law energy scaling
            light.data.energy = energy * ((dist / 2.5) ** 2)
            light.data.color = color[:3]
            light.data.size = max(radius * 1.0, 0.5)
            light.parent = target
            track = light.constraints.new('TRACK_TO')
            track.target = target
            track.track_axis = 'TRACK_NEGATIVE_Z'
            track.up_axis = 'UP_Y'
            light["eeveepulse_rig"] = True
            # Apply contact shadow setting based on property
            _safe_set(light.data, "use_contact_shadow", props.optimize_eevee_shadows)
            if name == "EeveePulse_Key":
                key_light = light

        # Light probes surrounding the bounding box
        if props.auto_probes:
            # Irradiance Volume/Grid
            try:
                probe_data = bpy.data.lightprobes.new(name="EeveePulse_Irradiance_Data", type='VOLUME')
            except TypeError:
                probe_data = bpy.data.lightprobes.new(name="EeveePulse_Irradiance_Data", type='GRID')
            irr = bpy.data.objects.new("EeveePulse_Irradiance", probe_data)
            context.scene.collection.objects.link(irr)
            irr.location = center
            irr.scale = (dim.x, dim.y, dim.z)
            _safe_set(irr.data, "influence_distance", max(dim) * 2.0)
            irr["eeveepulse_rig"] = True

            # Reflection Probe (Cubemap/Sphere)
            try:
                cube_data = bpy.data.lightprobes.new(name="EeveePulse_Reflection_Data", type='SPHERE')
            except TypeError:
                cube_data = bpy.data.lightprobes.new(name="EeveePulse_Reflection_Data", type='CUBEMAP')
            cub = bpy.data.objects.new("EeveePulse_Reflection", cube_data)
            context.scene.collection.objects.link(cub)
            cub.location = center
            cub.scale = (dim.x, dim.y, dim.z)
            _safe_set(cub.data, "influence_distance", max(dim) * 2.0)
            cub["eeveepulse_rig"] = True

        # Shadow blockers
        if props.auto_shadow_blockers and key_light:
            for light in (key_light,):
                _create_shadow_blocker(context, target, light, dim, props.blocker_distance_scale)

        bpy.ops.object.select_all(action='DESELECT')
        target.select_set(True)
        context.view_layer.objects.active = target
        utils.update_rig_properties(props, context)
        self.report({'INFO'}, "EeveePulse rig generated")
        return {'FINISHED'}


class EEVEEPULSE_OT_apply_preset(bpy.types.Operator):
    bl_idname = "eeveepulse.apply_preset"
    bl_label = "Apply Lighting Preset"
    bl_description = "Load selected lighting preset into panel properties"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.eeveepulse_props
        preset_name = props.preset_choice

        if preset_name not in utils.PRESETS_DATA:
            self.report({'ERROR'}, f"Preset '{preset_name}' not found")
            return {'CANCELLED'}

        preset = utils.PRESETS_DATA[preset_name]

        props.key_intensity = preset['key_intensity']
        props.fill_intensity = preset['fill_intensity']
        props.rim_intensity = preset['rim_intensity']
        props.key_color = preset['key_color']
        props.fill_color = preset['fill_color']
        props.rim_color = preset['rim_color']
        props.harmony_mode = preset.get('harmony_mode', 'OFF')
        props.harmony_intensity = preset.get('harmony_intensity', 0.0)
        props.rig_scale_factor = preset.get('rig_scale_factor', 1.5)
        props.auto_probes = preset.get('auto_probes', True)
        props.optimize_eevee_shadows = preset.get('optimize_eevee_shadows', True)

        self.report({'INFO'}, f"Applied preset: {preset_name}")
        return {'FINISHED'}


class EEVEEPULSE_OT_optimize_engine(bpy.types.Operator):
    bl_idname = "eeveepulse.optimize_engine"
    bl_label = "Optimize Eevee Engine"
    bl_description = "Switch to Eevee and enable screen space reflections and contact shadows"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        try:
            scene.render.engine = 'BLENDER_EEVEE_NEXT'
        except TypeError:
            scene.render.engine = 'BLENDER_EEVEE'

        eevee = scene.eevee

        _safe_set(eevee, "use_ssr", True)
        _safe_set(eevee, "use_screen_space_reflections", True)
        _safe_set(eevee, "use_ssr_refraction", True)
        _safe_set(eevee, "screen_space_refraction", True)

        # Contact shadows on created EeveePulse lights
        for obj in bpy.data.objects:
            if obj.get("eeveepulse_rig") == True and obj.type == 'LIGHT':
                _safe_set(obj.data, "use_contact_shadow", True)

        self.report({'INFO'}, "Eevee engine optimized")
        return {'FINISHED'}


class EEVEEPULSE_OT_purge_rig(bpy.types.Operator):
    bl_idname = "eeveepulse.purge_rig"
    bl_label = "Purge EeveePulse Rig"
    bl_description = "Delete all objects tagged as EeveePulse rig and orphaned light probe data-blocks"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        tagged = [o for o in bpy.data.objects if o.get("eeveepulse_rig") == True]
        if not tagged:
            self.report({'INFO'}, "No EeveePulse rig found")
            return {'CANCELLED'}

        for obj in tagged:
            bpy.data.objects.remove(obj, do_unlink=True)

        # Remove orphaned light probe data-blocks
        for probe in list(bpy.data.lightprobes):
            if probe.name.startswith("EeveePulse_") and probe.users == 0:
                bpy.data.lightprobes.remove(probe)

        # Remove orphaned light data-blocks
        for light in list(bpy.data.lights):
            if light.name.startswith("EeveePulse_") and light.users == 0:
                bpy.data.lights.remove(light)

        # Remove orphaned mesh data-blocks
        for mesh in list(bpy.data.meshes):
            if mesh.name.startswith("EeveePulse_") and mesh.users == 0:
                bpy.data.meshes.remove(mesh)

        self.report({'INFO'}, "EeveePulse rig and orphaned data purged")
        return {'FINISHED'}


class EEVEEPULSE_OT_clear_animation(bpy.types.Operator):
    bl_idname = "eeveepulse.clear_animation"
    bl_label = "Clear Animation"
    bl_description = "Clear animation data from rig lights and update rig properties"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.eeveepulse_props

        for obj in bpy.data.objects:
            if obj.get("eeveepulse_rig") == True and obj.type == 'LIGHT':
                if obj.data.animation_data:
                    obj.data.animation_data_clear()

        # Update rig properties to reset to current property values
        utils.update_rig_properties(props, context)

        self.report({'INFO'}, "Pulse animation cleared")
        return {'FINISHED'}


class EEVEEPULSE_OT_bake_animation(bpy.types.Operator):
    bl_idname = "eeveepulse.bake_animation"
    bl_label = "Bake Pulse Animation"
    bl_description = "Bake pulse energy modulation to keyframes across frame range"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.eeveepulse_props

        key_light = None
        fill_light = None
        rim_light = None

        for obj in bpy.data.objects:
            if obj.get("eeveepulse_rig") == True and obj.type == 'LIGHT':
                if obj.name == "EeveePulse_Key":
                    key_light = obj
                elif obj.name == "EeveePulse_Fill":
                    fill_light = obj
                elif obj.name == "EeveePulse_Rim":
                    rim_light = obj

        if not key_light:
            self.report({'ERROR'}, "No EeveePulse rig found")
            return {'CANCELLED'}

        # Read dist_factor from target for intensity scaling
        dist_factor = 1.0
        for obj in bpy.data.objects:
            if obj.get("eeveepulse_rig") == True and obj.name == "EeveePulse_Target":
                dist_factor = obj.get("eeveepulse_dist_factor", 1.0)
                break
        energy_scale = (dist_factor / 2.5) ** 2

        start = props.anim_start_frame
        end = props.anim_end_frame
        waveform = props.pulse_waveform
        freq = props.pulse_frequency
        amp = props.pulse_amplitude

        base_key = props.key_intensity * energy_scale
        base_fill = props.fill_intensity * energy_scale
        base_rim = props.rim_intensity * energy_scale

        for frame in range(start, end + 1):
            context.scene.frame_set(frame)

            offset = utils.calculate_pulse_offset(frame, waveform, props.pulse_frequency, props.pulse_amplitude)

            if key_light:
                key_light.data.energy = max(0.0, base_key + offset * base_key * 0.5)
                key_light.data.keyframe_insert("energy", frame=frame)

            if fill_light:
                fill_light.data.energy = max(0.0, base_fill + offset * base_fill * 0.5)
                fill_light.data.keyframe_insert("energy", frame=frame)

            if rim_light:
                rim_light.data.energy = max(0.0, base_rim + offset * base_rim * 0.5)
                rim_light.data.keyframe_insert("energy", frame=frame)

        context.scene.frame_set(start)
        self.report({'INFO'}, f"Baked pulse animation ({start}-{end})")
        return {'FINISHED'}


class EEVEEPULSE_OT_sample_image_colors(bpy.types.Operator):
    bl_idname = "eeveepulse.sample_image_colors"
    bl_label = "Sample Image Colors"
    bl_description = "Sample dominant color from reference image and update key color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.eeveepulse_props

        if not props.ref_image:
            self.report({'ERROR'}, "No reference image selected")
            return {'CANCELLED'}

        image = props.ref_image

        color = utils.sample_image_dominant_color(image)
        props.key_color = color

        self.report({'INFO'}, f"Sampled color: {color[:3]}")
        return {'FINISHED'}


class EEVEEPULSE_OT_generate_world(bpy.types.Operator):
    bl_idname = "eeveepulse.generate_world"
    bl_label = "Generate World Dome"
    bl_description = "Build procedural world node setup with key/fill gradient"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.eeveepulse_props

        key_rgb = props.key_color[:3]
        fill_rgb, _ = utils.compute_harmony_colors(key_rgb, props.harmony_mode, props.harmony_intensity, props.fill_color[:3], props.rim_color[:3])

        utils.build_procedural_world_nodes(context.scene, key_rgb, fill_rgb, props.world_strength)

        self.report({'INFO'}, "Procedural world dome generated")
        return {'FINISHED'}

classes = (
    EEVEEPULSE_OT_generate_rig,
    EEVEEPULSE_OT_apply_preset,
    EEVEEPULSE_OT_optimize_engine,
    EEVEEPULSE_OT_purge_rig,
    EEVEEPULSE_OT_bake_animation,
    EEVEEPULSE_OT_sample_image_colors,
    EEVEEPULSE_OT_generate_world,
    EEVEEPULSE_OT_clear_animation,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
