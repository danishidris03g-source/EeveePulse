import bpy


class EEVEEPULSE_PT_main_panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'EeveePulse'
    bl_label = 'EeveePulse Studio Rig'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.eeveepulse_props

        # 1. Engine Status
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Render Engine:", icon='RENDER_STILL')
        row.label(text=scene.render.engine)
        row = box.row(align=True)
        row.scale_y = 1.2
        row.operator("eeveepulse.optimize_engine", text="Optimize Engine", icon='PREFERENCES')

        # 2. Rig Actions
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("eeveepulse.generate_rig", text="Generate Rig", icon='LIGHT')
        row.operator("eeveepulse.purge_rig", text="Purge Rig", icon='TRASH')

        # 3. Presets
        box = layout.box()
        box.label(text="Presets", icon='PRESET_NEW')
        row = box.row(align=True)
        row.prop(props, "preset_choice", text="")
        row.operator("eeveepulse.apply_preset", text="Apply Preset", icon='IMPORT')

        # 4. Color Harmonies
        box = layout.box()
        box.label(text="Color Harmonies", icon='COLOR')
        col = box.column(align=True)
        col.prop(props, "harmony_mode", text="Mode")
        col.prop(props, "harmony_intensity", slider=True)

        # 5. Light Controls
        box = layout.box()
        box.label(text="Light Controls", icon='LIGHT')
        col = box.column(align=True)
        col.prop(props, "key_intensity", slider=True)
        col.prop(props, "fill_intensity", slider=True)
        col.prop(props, "rim_intensity", slider=True)
        col.prop(props, "rig_scale_factor", slider=True)
        col.separator()
        col.prop(props, "key_color", text="Key Color")
        col.prop(props, "fill_color", text="Fill Color")
        col.prop(props, "rim_color", text="Rim Color")

        # 6. Shadows & Probes
        box = layout.box()
        box.label(text="Shadows & Probes", icon='OUTLINER_OB_LIGHTPROBE')
        col = box.column(align=True)
        col.prop(props, "auto_probes")
        col.prop(props, "auto_shadow_blockers")
        sub = col.column()
        sub.enabled = props.auto_shadow_blockers
        sub.prop(props, "blocker_distance_scale", slider=True)
        col.separator()
        col.prop(props, "optimize_eevee_shadows")

        # 7. Camera Relighting
        box = layout.box()
        box.label(text="Camera Relighting", icon='CAMERA_DATA')
        col = box.column(align=True)
        col.prop(props, "camera_lock_mode")

        # 8. Mood Sampler
        box = layout.box()
        box.label(text="Mood Sampler", icon='IMAGE_DATA')
        col = box.column(align=True)
        col.template_ID(props, "ref_image", open="image.open")
        row = box.row(align=True)
        row.scale_y = 1.2
        row.operator("eeveepulse.sample_image_colors", text="Sample Image Colors", icon='EYEDROPPER')

        # 9. Animation & Pulse
        box = layout.box()
        box.label(text="Animation & Pulse", icon='ANIM')
        col = box.column(align=True)
        col.prop(props, "anim_start_frame")
        col.prop(props, "anim_end_frame")
        col.separator()
        col.prop(props, "pulse_waveform", text="Waveform")
        col.prop(props, "pulse_frequency", slider=True)
        col.prop(props, "pulse_amplitude", slider=True)
        row = box.row(align=True)
        row.scale_y = 1.2
        row.operator("eeveepulse.bake_animation", text="Bake Pulse", icon='REC')
        row.operator("eeveepulse.clear_animation", text="Clear Pulse", icon='CANCEL')

        # 10. Environment Dome
        box = layout.box()
        box.label(text="Environment Dome", icon='WORLD')
        col = box.column(align=True)
        col.prop(props, "auto_world_dome")
        col.prop(props, "world_strength", slider=True)
        row = box.row(align=True)
        row.scale_y = 1.2
        row.operator("eeveepulse.generate_world", text="Generate Studio World", icon='WORLD')


classes = (
    EEVEEPULSE_PT_main_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)