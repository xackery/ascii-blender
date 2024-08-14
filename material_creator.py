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

def create_materials(materials, textures, file_path, node_group_cache):
    created_materials = {}

    for mat_data in materials:
        mat_name = mat_data['name']
        # Check if the material already exists in the Blender file
        if mat_name in bpy.data.materials:
            print(f"Material '{mat_name}' already exists. Using existing material.")
            created_materials[mat_name] = bpy.data.materials[mat_name]
            continue

        if mat_name not in created_materials:
            texture_name = mat_data.get('texture_tag', '')
            texture_file = textures.get(texture_name, "")
            # Construct the full path to the texture file
            texture_full_path = os.path.join(os.path.dirname(file_path), texture_file)
            print(f"Creating material '{mat_name}' with texture '{texture_full_path}' and rendermethod '{mat_data['rendermethod']}'")

            rendermethod = mat_data['rendermethod']
            if rendermethod == 'TEXTURE5AMBIENTGOURAUD1':
                if 'TEXTURE5AMBIENTGOURAUD1' not in node_group_cache:
                    node_group_cache['TEXTURE5AMBIENTGOURAUD1'] = create_node_group_t5ag1()
                mat = create_material_with_node_group_t5ag1(mat_name, texture_full_path, node_group_cache['TEXTURE5AMBIENTGOURAUD1'])
            elif rendermethod == 'TRANSPARENT':
                if 'TRANSPARENT' not in node_group_cache:
                    node_group_cache['TRANSPARENT'] = create_node_group_transparent()
                mat = create_material_with_node_group_transparent(mat_name, node_group_cache['TRANSPARENT'])
            elif rendermethod == 'USERDEFINED_2':
                if 'USERDEFINED_2' not in node_group_cache:
                    node_group_cache['USERDEFINED_2'] = create_node_group_ud02()
                mat = create_material_with_node_group_ud02(mat_name, texture_full_path, node_group_cache['USERDEFINED_2'])
            elif rendermethod == 'USERDEFINED_6':
                if 'USERDEFINED_6' not in node_group_cache:
                    node_group_cache['USERDEFINED_6'] = create_node_group_ud06()
                mat = create_material_with_node_group_ud06(mat_name, texture_full_path, node_group_cache['USERDEFINED_6'])
            elif rendermethod == 'USERDEFINED_10':
                if 'USERDEFINED_10' not in node_group_cache:
                    node_group_cache['USERDEFINED_10'] = create_node_group_ud10()
                mat = create_material_with_node_group_ud10(mat_name, texture_full_path, node_group_cache['USERDEFINED_10'])
            elif rendermethod == 'USERDEFINED_12':
                if 'USERDEFINED_12' not in node_group_cache:
                    node_group_cache['USERDEFINED_12'] = create_node_group_ud12()
                mat = create_material_with_node_group_ud12(mat_name, texture_full_path, node_group_cache['USERDEFINED_12'])
            elif rendermethod == 'USERDEFINED_20':
                if 'USERDEFINED_20' not in node_group_cache:
                    node_group_cache['USERDEFINED_20'] = create_node_group_ud20()
                mat = create_material_with_node_group_ud20(mat_name, texture_full_path, node_group_cache['USERDEFINED_20'])
            elif rendermethod == 'USERDEFINED_21':
                if 'USERDEFINED_21' not in node_group_cache:
                    node_group_cache['USERDEFINED_21'] = create_node_group_ud21()
                mat = create_material_with_node_group_ud21(mat_name, texture_full_path, node_group_cache['USERDEFINED_21'])
            elif rendermethod == 'USERDEFINED_22':
                if 'USERDEFINED_22' not in node_group_cache:
                    node_group_cache['USERDEFINED_22'] = create_node_group_ud22()
                mat = create_material_with_node_group_ud22(mat_name, texture_full_path, node_group_cache['USERDEFINED_22'])                
            elif rendermethod == 'USERDEFINED_24':
                if 'USERDEFINED_24' not in node_group_cache:
                    node_group_cache['USERDEFINED_24'] = create_node_group_ud24()
                mat = create_material_with_node_group_ud24(mat_name, texture_full_path, node_group_cache['USERDEFINED_24'])
            else:
                mat = bpy.data.materials.new(name=mat_name)
                mat.use_nodes = True
                principled_bsdf = mat.node_tree.nodes.get('Principled BSDF')
                if principled_bsdf:
                    principled_bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)  # Set default color to white
            
            created_materials[mat_name] = mat
    
    # After materials are created, call the DDS checker
    scan_and_fix_dds_in_materials()

    return created_materials
