import bpy
import os
from texture5ambientgouraud1 import create_node_group_t5ag1, create_material_with_node_group_t5ag1
from transparent import create_node_group_transparent, create_material_with_node_group_transparent
from userdefined_02 import create_node_group_ud02, create_material_with_node_group_ud02
from userdefined_06 import create_node_group_ud06, create_material_with_node_group_ud06
from userdefined_10 import create_node_group_ud10, create_material_with_node_group_ud10
from userdefined_12 import create_node_group_ud12, create_material_with_node_group_ud12
from userdefined_20 import create_node_group_ud20, create_material_with_node_group_ud20
from userdefined_21 import create_node_group_ud21, create_material_with_node_group_ud21
from userdefined_22 import create_node_group_ud22, create_material_with_node_group_ud22
from userdefined_24 import create_node_group_ud24, create_material_with_node_group_ud24
from dds_checker import scan_and_fix_dds_in_materials

def get_or_create_node_group(group_name, create_function, node_group_cache, texture_path=None):
    """
    Retrieves an existing node group or creates a new one if it doesn't exist.

    :param group_name: Name of the node group to retrieve or create.
    :param create_function: Function to create a new node group if it doesn't exist.
    :param node_group_cache: Cache dictionary for storing created node groups.
    :param texture_path: The path to the texture file, used if needed by the create_function.
    :return: The node group instance.
    """
    # Check if the node group already exists in Blender's data
    if group_name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[group_name]
        node_group_cache[group_name] = node_group
        print(f"Using existing node group: {group_name}")
    else:
        # If not, create a new node group using the provided function
        if texture_path:
            node_group = create_function(texture_path)
        else:
            node_group = create_function()
        node_group_cache[group_name] = node_group
        print(f"Created new node group: {group_name}")
    
    return node_group

def create_materials(materials, textures, file_path, node_group_cache):
    created_materials = {}

    for mat_data in materials:
        mat_name = mat_data['name']
        # Check if the material already exists in the Blender file
        if mat_name in bpy.data.materials:
            created_materials[mat_name] = bpy.data.materials[mat_name]
            continue

        if mat_name not in created_materials:
            texture_name = mat_data.get('texture_tag', '')
            texture_file = textures.get(texture_name, "")
            # Construct the full path to the texture file
            texture_full_path = os.path.join(os.path.dirname(file_path), texture_file)

            rendermethod = mat_data['rendermethod']
            if rendermethod == 'TEXTURE5AMBIENTGOURAUD1':
                node_group = get_or_create_node_group('TEXTURE5AMBIENTGOURAUD1', create_node_group_t5ag1, node_group_cache)
                mat = create_material_with_node_group_t5ag1(mat_name, texture_full_path, node_group)
            elif rendermethod == 'TRANSPARENT':
                node_group = get_or_create_node_group('TRANSPARENT', create_node_group_transparent, node_group_cache)
                mat = create_material_with_node_group_transparent(mat_name, node_group)
            elif rendermethod == 'USERDEFINED_2':
                node_group = get_or_create_node_group('USERDEFINED_2', create_node_group_ud02, node_group_cache)
                mat = create_material_with_node_group_ud02(mat_name, texture_full_path, node_group)
            elif rendermethod == 'USERDEFINED_6':
                node_group = get_or_create_node_group('USERDEFINED_6', create_node_group_ud06, node_group_cache)
                mat = create_material_with_node_group_ud06(mat_name, texture_full_path, node_group)
            elif rendermethod == 'USERDEFINED_10':
                node_group = get_or_create_node_group('USERDEFINED_10', create_node_group_ud10, node_group_cache)
                mat = create_material_with_node_group_ud10(mat_name, texture_full_path, node_group)
            elif rendermethod == 'USERDEFINED_12':
                node_group = get_or_create_node_group('USERDEFINED_12', create_node_group_ud12, node_group_cache)
                mat = create_material_with_node_group_ud12(mat_name, texture_full_path, node_group)
            elif rendermethod == 'USERDEFINED_20':
                # Pass texture_full_path as an argument for USERDEFINED_20
                node_group = get_or_create_node_group('USERDEFINED_20', create_node_group_ud20, node_group_cache, texture_full_path)
                mat = create_material_with_node_group_ud20(mat_name, texture_full_path, node_group)
            elif rendermethod == 'USERDEFINED_21':
                node_group = get_or_create_node_group('USERDEFINED_21', create_node_group_ud21, node_group_cache)
                mat = create_material_with_node_group_ud21(mat_name, texture_full_path, node_group)
            elif rendermethod == 'USERDEFINED_22':
                node_group = get_or_create_node_group('USERDEFINED_22', create_node_group_ud22, node_group_cache)
                mat = create_material_with_node_group_ud22(mat_name, texture_full_path, node_group)
            elif rendermethod == 'USERDEFINED_24':
                node_group = get_or_create_node_group('USERDEFINED_24', create_node_group_ud24, node_group_cache)
                mat = create_material_with_node_group_ud24(mat_name, texture_full_path, node_group)
            else:
                # Default to a simple Principled BSDF material
                mat = bpy.data.materials.new(name=mat_name)
                mat.use_nodes = True
                principled_bsdf = mat.node_tree.nodes.get('Principled BSDF')
                if principled_bsdf:
                    principled_bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)  # Set default color to white
            
            created_materials[mat_name] = mat

    # After materials are created, call the DDS checker
    scan_and_fix_dds_in_materials()

    return created_materials
