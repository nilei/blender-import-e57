import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, FloatProperty
from .core import process_e57_file

class IMPORT_OT_e57(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.e57"
    bl_label = "Import E57"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".e57"

    filter_glob: StringProperty(
        default="*.e57",
        options={'HIDDEN'},
        maxlen=255,
    )

    import_colors: BoolProperty(
        name="Import Colors",
        description="Extract and apply color data to the point cloud if present",
        default=True,
    )
    
    import_normals: BoolProperty(
        name="Import Normals",
        description="Extract normal vectors if present",
        default=True,
    )

    scale_factor: FloatProperty(
        name="Scale",
        description="Global scale multiplier for the imported coordinates",
        default=1.0,
        min=0.0001,
    )

    point_radius: FloatProperty(
        name="Point Radius",
        description="Base radius for each point in the cloud",
        default=0.05,
        min=0.0,
        step=0.01,
    )

    def execute(self, context):
        try:
            process_e57_file(
                context, 
                self.filepath, 
                self.import_colors, 
                self.import_normals, 
                self.scale_factor,
                self.point_radius
            )
            self.report({'INFO'}, "E57 file imported successfully.")
            return {'FINISHED'}
        except Exception as execution_error:
            self.report({'ERROR'}, str(execution_error))
            return {'CANCELLED'}

def menu_func_import(self, context):
    self.layout.operator(IMPORT_OT_e57.bl_idname, text="E57 Point Cloud (.e57)")

def register():
    bpy.utils.register_class(IMPORT_OT_e57)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(IMPORT_OT_e57)