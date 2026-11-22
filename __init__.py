bl_info = {
    "name": "EeveePulse",
    "author": "EeveePulse Team",
    "version": (3, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > EeveePulse",
    "description": "Studio light rigs with color harmonies, mood sampling, camera tracking, and procedural world dome for Eevee",
    "category": "Lighting",
}

import importlib

if "bpy" in locals():
    if "utils" in locals():
        importlib.reload(utils)
    if "properties" in locals():
        importlib.reload(properties)
    if "operators" in locals():
        importlib.reload(operators)
    if "ui" in locals():
        importlib.reload(ui)
else:
    from . import utils
    from . import properties
    from . import operators
    from . import ui


def register():
    properties.register()
    operators.register()
    ui.register()


def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()


if __name__ == "__main__":
    register()