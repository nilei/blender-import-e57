import bpy
import numpy as np

def create_point_cloud_material(name, has_color, has_normal):
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    nodes.clear()

    node_principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_principled.location = (0, 0)
    
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    node_output.location = (300, 0)
    
    links.new(node_principled.outputs['BSDF'], node_output.inputs['Surface'])

    if has_normal:
        node_attr_normal = nodes.new(type='ShaderNodeAttribute')
        node_attr_normal.attribute_name = "normal"
        node_attr_normal.location = (-600, -200)

        node_map = nodes.new(type='ShaderNodeVectorMath')
        node_map.operation = 'MULTIPLY_ADD'
        node_map.inputs[1].default_value = (0.5, 0.5, 0.5)
        node_map.inputs[2].default_value = (0.5, 0.5, 0.5)
        node_map.location = (-300, -200)
        
        links.new(node_attr_normal.outputs['Vector'], node_map.inputs[0])

    if has_color:
        node_attr_color = nodes.new(type='ShaderNodeAttribute')
        node_attr_color.attribute_name = "color"
        node_attr_color.location = (-300, 100)

    if has_color:
        links.new(node_attr_color.outputs['Color'], node_principled.inputs['Base Color'])
    elif has_normal:
        links.new(node_map.outputs['Vector'], node_principled.inputs['Base Color'])

    return material

def process_e57_file(context, filepath, import_colors, import_normals, scale_factor, point_radius):
    import pye57

    e57_file = pye57.E57(filepath)
    scan_count = e57_file.scan_count
    imported_objects = []

    if context.active_object and context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    for scan_index in range(scan_count):
        data = e57_file.read_scan_raw(scan_index)

        coord_x = data.get('cartesianX')
        coord_y = data.get('cartesianY')
        coord_z = data.get('cartesianZ')

        if coord_x is None or coord_y is None or coord_z is None:
            continue

        points = np.vstack((coord_x, coord_y, coord_z)).transpose()
        points = points * scale_factor

        temp_mesh = bpy.data.meshes.new(name=f"E57_Mesh_{scan_index}")
        temp_mesh.vertices.add(len(points))
        temp_mesh.vertices.foreach_set("co", points.flatten())

        has_color = False
        has_normal = False

        if import_colors:
            color_r = data.get('colorRed')
            color_g = data.get('colorGreen')
            color_b = data.get('colorBlue')

            if color_r is not None and color_g is not None and color_b is not None:
                if color_r.max() > 1.0 or color_g.max() > 1.0 or color_b.max() > 1.0:
                    color_r = color_r / 255.0
                    color_g = color_g / 255.0
                    color_b = color_b / 255.0

                alpha_channel = np.ones_like(color_r)
                colors = np.vstack((color_r, color_g, color_b, alpha_channel)).transpose()
                
                color_attr = temp_mesh.attributes.new(name="color", type='FLOAT_COLOR', domain='POINT')
                color_attr.data.foreach_set("color", colors.flatten())
                has_color = True

        if import_normals:
            normal_x = data.get('normalX')
            normal_y = data.get('normalY')
            normal_z = data.get('normalZ')

            if normal_x is not None and normal_y is not None and normal_z is not None:
                normals = np.vstack((normal_x, normal_y, normal_z)).transpose()
                normal_attr = temp_mesh.attributes.new(name="normal", type='FLOAT_VECTOR', domain='POINT')
                normal_attr.data.foreach_set("vector", normals.flatten())
                has_normal = True

        temp_mesh.update()

        pc_obj = bpy.data.objects.new(name=f"E57_Scan_{scan_index}", object_data=temp_mesh)
        context.collection.objects.link(pc_obj)

        pc_obj.select_set(True)
        context.view_layer.objects.active = pc_obj
        
        bpy.ops.object.convert(target='POINTCLOUD')
        
        final_pc_obj = context.active_object
        
        radius_attr = final_pc_obj.data.attributes.new(name="radius", type='FLOAT', domain='POINT')
        radius_values = np.full(len(points), point_radius, dtype=np.float32)
        radius_attr.data.foreach_set("value", radius_values)
        
        if has_color or has_normal:
            mat_name = f"Material_E57_{scan_index}"
            material = create_point_cloud_material(mat_name, has_color, has_normal)
            if final_pc_obj.data.materials:
                final_pc_obj.data.materials[0] = material
            else:
                final_pc_obj.data.materials.append(material)

        final_pc_obj.select_set(False)
        imported_objects.append(final_pc_obj)

    return imported_objects