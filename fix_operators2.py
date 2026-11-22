with open(r'C:\Users\User\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons\EeveePulse\operators.py', 'r') as f:
    content = f.read()

# Find the purge_rig class and replace it
start_idx = content.find('class EEVEEPULSE_OT_purge_rig(bpy.types.Operator):')
if start_idx == -1:
    print('Could not find purge_rig class')
else:
    # Find the next class after purge_rig
    next_class = content.find('\nclass EEVEEPULSE_OT_optimize_engine', start_idx)
    if next_class == -1:
        print('Could not find next class')
    else:
        # Replace from start_idx to next_class
        new_content = content[:start_idx] + '''class EEVEEPULSE_OT_purge_rig(bpy.types.Operator):
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
        for probe in bpy.data.lightprobes:
            if probe.name.startswith("EeveePulse_") and probe.users == 0:
                bpy.data.lightprobes.remove(probe)

        self.report({'INFO'}, "EeveePulse rig and orphaned probes purged")
        return {'FINISHED'}


class EEVEEPULSE_OT_clear_animation(bpy.types.Operator):
    bl_idname = "eeveepulse.clear_animation"
    bl_label = "Clear Pulse Animation"
    bl_description = "Remove all keyframes from rig lights and update rig properties"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.eeveepulse_props

        for obj in bpy.data.objects:
            if obj.get("eeveepulse_rig") == True and obj.type == 'LIGHT':
                if obj.animation_data:
                    obj.data.animation_data_clear()

        # Update rig properties to reset to current property values
        from .properties import update_rig_properties
        update_rig_properties(props, context)

        self.report({'INFO'}, "Pulse animation cleared")
        return {'FINISHED'}


class EEVEEPULSE_OT_optimize_engine(bpy.types.Operator):''' + content[next_class + len('class EEVEEPULSE_OT_optimize_engine(bpy.types.Operator):'):]

    with open(r'C:\Users\User\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons\EeveePulse\operators.py', 'w') as f:
        f.write(new_content)
    print('Replacement successful')