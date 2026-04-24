# Entry point for the Blender extension

import bpy
from . import operators

def register():
    operators.register()

def unregister():
    operators.unregister()