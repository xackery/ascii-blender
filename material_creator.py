import bpy
import os
import shutil
from material_utils import has_dds_header, add_texture_coordinate_and_mapping_nodes, apply_detail_mapping
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
from dds_checker import check_and_fix_dds, scan_and_fix_dds_in_materials

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
            texture_info = textures.get(texture_name, {})
            if isinstance(texture_info, dict):
                texture_file = texture_info.get('frames', [{}])[0].get('file', '')
            else:
                texture_file = texture_info

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
                mat = bpy.data.materials.new(name=mat_name)
                mat.use_nodes = True
                principled_bsdf = mat.node_tree.nodes.get('Principled BSDF')
                if principled_bsdf:
                    principled_bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)
            
            # Check if texture is animated
            if texture_info.get('animated', False):
                add_animated_texture_nodes(mat, texture_info, base_path=os.path.dirname(file_path))
            
            # Check for layered textures
            for frame in texture_info.get('frames', []):
                if frame.get('type') == 'layer':
                    add_layered_texture_nodes(mat, frame, rendermethod, node_group_cache)
                elif frame.get('type') == 'detail':
                    add_detail_texture_nodes(mat, frame, node_group_cache)
                elif frame.get('type') == 'palette_mask':
                    add_palette_mask_texture_nodes(mat, frame, node_group_cache)
                elif frame.get('type') == 'tiled':
                    add_tiled_texture_nodes(mat, frame, node_group_cache)
            
            created_materials[mat_name] = mat

    scan_and_fix_dds_in_materials()

    return created_materials

# Helper functions to handle special texture types

def add_animated_texture_nodes(material, texture_info, base_path=None):
    """
    Adds animated texture nodes to a material and checks for DDS files to fix headers.
    
    :param material: The material to modify.
    :param texture_info: A dictionary containing texture information, including animation details.
    :param base_path: The base path where texture files are located.
    """
    import re

    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Retrieve the main image texture node (assuming it's named "Image Texture")
    image_texture_node = None
    for node in nodes:
        if node.type == 'TEX_IMAGE':
            image_texture_node = node
            break

    if not image_texture_node:
        print(f"No image texture node found in material: {material.name}")
        return

    # Set the image texture node to use an image sequence
    image_texture_node.image.source = 'SEQUENCE'
    image_texture_node.image_user.use_auto_refresh = True  # Enable auto refresh for animated textures

    # Set the number of frames and start frame based on texture_info
    number_frames = texture_info.get('number_frames', 1)
    image_texture_node.image_user.frame_duration = number_frames
    image_texture_node.image_user.frame_start = -(number_frames - 2)

    # Process all files in the animation frames
    frame_files = texture_info.get('frame_files', [])
    frames_info = texture_info.get('frames', [])
    
    for frame_data in frames_info:
        frame_file = frame_data['file']
        animation_frame = frame_data['animation_frame']

        # Construct the full path to the file
        if base_path:
            full_path = os.path.join(base_path, frame_file)
        else:
            print(f"Warning: base_path is not provided. Using frame file as is: {frame_file}")
            full_path = frame_file

        texture_path = bpy.path.abspath(full_path)  # Convert to absolute path

        print(f"Processing file: {texture_path}")  # Debugging output

        if not os.path.isfile(texture_path):
            print(f"File not found: {texture_path}")
            continue

        # Extract the number from the original frame file name
        match = re.search(r'(\d+)(?=\.\w+$)', frame_file)
        if match:
            actual_frame_number = int(match.group(1))
        else:
            print(f"No numeric frame number found in file name: {frame_file}")
            continue

        # Check if the actual frame number matches the expected animation frame number
        if actual_frame_number != animation_frame:
            # Copy and rename the file to match the correct frame number
            base_name, ext = os.path.splitext(frame_file)
            new_file_name = re.sub(r'\d+$', f"{animation_frame}", base_name) + ext
            new_full_path = os.path.join(base_path, new_file_name)

            try:
                shutil.copy(texture_path, new_full_path)
                print(f"Copied and renamed {texture_path} to {new_full_path}")
                frame_file = new_file_name  # Update frame file to the newly created file
            except Exception as e:
                print(f"Error copying and renaming file {texture_path} to {new_full_path}: {e}")
                continue

        # Update the frame_file path after copying and renaming
        full_path = os.path.join(base_path, frame_file) if base_path else frame_file
        texture_path = bpy.path.abspath(full_path)

        # Pass the absolute file path to the check_and_fix_dds function
        try:
            check_and_fix_dds(texture_path)  # Ensure DDS headers are correct
            print(f"Processed file: {texture_path}")
        except Exception as e:
            print(f"Failed to process file {texture_path}: {e}")

    # Set up the driver for the offset
    offset_driver = image_texture_node.image_user.driver_add("frame_offset").driver
    offset_driver.type = 'SCRIPTED'
    offset_driver.expression = "int((frame / (fps * sleep)) % num_frames) - (num_frames - 1)"

    # Add input variables for the driver
    var_frame = offset_driver.variables.new()
    var_frame.name = 'frame'
    var_frame.targets[0].id_type = 'SCENE'
    var_frame.targets[0].id = bpy.context.scene
    var_frame.targets[0].data_path = 'frame_current'

    var_fps = offset_driver.variables.new()
    var_fps.name = 'fps'
    var_fps.targets[0].id_type = 'SCENE'
    var_fps.targets[0].id = bpy.context.scene
    var_fps.targets[0].data_path = 'render.fps'

    var_sleep = offset_driver.variables.new()
    var_sleep.name = 'sleep'
    var_sleep.targets[0].id_type = 'MATERIAL'
    var_sleep.targets[0].id = material
    var_sleep.targets[0].data_path = '["sleep"]'

    var_num_frames = offset_driver.variables.new()
    var_num_frames.name = 'num_frames'
    var_num_frames.targets[0].id_type = 'MATERIAL'
    var_num_frames.targets[0].id = material
    var_num_frames.targets[0].data_path = '["number_frames"]'

    # Set custom properties for the material
    sleep_value = texture_info.get('sleep', 'NULL')
    number_frames = texture_info.get('number_frames', 1)

    material["sleep"] = sleep_value if sleep_value != 'NULL' else 'NULL'
    material["number_frames"] = number_frames

    # Set custom properties with zero-padded frame names
    for idx, frame_file in enumerate(frame_files):
        frame_name = f"Frame name {idx + 1:03}"  # Zero-padded frame number
        material[frame_name] = frame_file

    print(f"Added animated texture nodes to material: {material.name}")
    pass

def add_layered_texture_nodes(material, texture_info, node_group_cache):
    """
    Adds layered texture nodes to a material.

    :param material: The material to modify.
    :param texture_info: A dictionary containing texture information, including layering details.
    :param node_group_cache: A cache to store and retrieve existing node groups.
    """
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Retrieve the main rendermethod node group (assuming it's named according to the rendermethod)
    main_node_group = None
    for node in nodes:
        if node.type == 'GROUP' and node.node_tree.name in node_group_cache:
            main_node_group = node
            break

    if not main_node_group:
        print(f"No main node group found in material: {material.name}")
        return

    # Process layered frames
    for frame_data in texture_info.get('frames', []):
        if frame_data.get('type') == 'layer':
            frame_file = frame_data['file']
            layer_file_name = os.path.basename(frame_file)
            layer_name = f"{layer_file_name}_LAYER"

            # Add Image Texture node for the layer
            image_texture_node = nodes.new(type='ShaderNodeTexImage')
            image_texture_node.location = (-600, 200)
            image_texture_node.image = bpy.data.images.load(frame_file)
            image_texture_node.name = layer_name
            image_texture_node.label = layer_name

            # Add Texture Coordinate and Mapping nodes for the new image texture
            tex_coord_node, mapping_node = add_texture_coordinate_and_mapping_nodes(nodes, links, image_texture_node, frame_file)

            # Create another rendermethod node group for the layer
            layer_node_group = nodes.new(type='ShaderNodeGroup')
            layer_node_group.node_tree = main_node_group.node_tree
            layer_node_group.location = (200, 200)

            # Connect the color output of the Image Texture node to the input of the layer's rendermethod node group
            links.new(image_texture_node.outputs['Color'], layer_node_group.inputs[0])

            # Add a Mix Shader node to blend the main texture and the layer
            mix_shader_node = nodes.new(type='ShaderNodeMixShader')
            mix_shader_node.location = (400, 0)

            # Connect main texture node group to the first shader input of Mix Shader
            links.new(main_node_group.outputs[0], mix_shader_node.inputs[1])

            # Connect the layer's node group output to the second shader input of Mix Shader
            links.new(layer_node_group.outputs[0], mix_shader_node.inputs[2])

            # Connect the alpha output of the layer's Image Texture node to the "Fac" input of the Mix Shader
            links.new(image_texture_node.outputs['Alpha'], mix_shader_node.inputs['Fac'])

            # Update the output connection to go through the Mix Shader
            for link in links:
                if link.to_node == material.node_tree.nodes.get('Material Output'):
                    links.new(mix_shader_node.outputs[0], link.to_socket)
                    break

    print(f"Added layered texture nodes to material: {material.name}")
    pass

def add_detail_texture_nodes(material, texture_info, node_group_cache):
    """
    Adds detail texture nodes to a material.

    :param material: The material to modify.
    :param texture_info: A dictionary containing texture information, including detail frames.
    :param node_group_cache: A cache to store and retrieve existing node groups.
    """
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Retrieve the main rendermethod node group
    main_node_group = None
    for node in nodes:
        if node.type == 'GROUP' and node.node_tree.name in node_group_cache:
            main_node_group = node
            break

    if not main_node_group:
        print(f"No main node group found in material: {material.name}")
        return

    # Process detail frames
    for frame_data in texture_info.get('frames', []):
        if frame_data.get('type') == 'detail':
            frame_file = frame_data['file']
            detail_value = frame_data.get('detail_value', 1.0)
            detail_file_name = os.path.basename(frame_file)
            detail_name = f"{detail_file_name}_DETAIL"

            # Add Image Texture node for the detail
            detail_texture_node = nodes.new(type='ShaderNodeTexImage')
            detail_texture_node.location = (-600, -200)
            detail_texture_node.image = bpy.data.images.load(frame_file)
            detail_texture_node.name = detail_name
            detail_texture_node.label = detail_name

            # Add Texture Coordinate and Mapping nodes for the detail texture
            tex_coord_node, mapping_node = add_texture_coordinate_and_mapping_nodes(
                nodes, links, detail_texture_node, frame_file
            )

            # Apply detail_value to the Mapping node's scale inputs
            mapping_node.inputs['Scale'].default_value[0] = detail_value  # X scale
            mapping_node.inputs['Scale'].default_value[1] = -detail_value if has_dds_header(frame_file) else detail_value  # Y scale

            # Create another rendermethod node group for the detail texture
            detail_node_group = nodes.new(type='ShaderNodeGroup')
            detail_node_group.node_tree = main_node_group.node_tree
            detail_node_group.location = (200, -200)

            # Connect the color output of the detail Image Texture node to the input of the detail rendermethod node group
            links.new(detail_texture_node.outputs['Color'], detail_node_group.inputs[0])

            # Add a Mix Shader node to blend the main texture and the detail texture
            mix_shader_node = nodes.new(type='ShaderNodeMixShader')
            mix_shader_node.location = (400, -200)
            mix_shader_node.inputs['Fac'].default_value = 0.25  # Set the blending factor to 0.25

            # Connect main texture node group to the first shader input of Mix Shader
            links.new(main_node_group.outputs[0], mix_shader_node.inputs[1])

            # Connect the detail texture's node group output to the second shader input of Mix Shader
            links.new(detail_node_group.outputs[0], mix_shader_node.inputs[2])

            # Update the output connection to go through the Mix Shader
            for link in links:
                if link.to_node == material.node_tree.nodes.get('Material Output'):
                    links.new(mix_shader_node.outputs[0], link.to_socket)
                    break

    print(f"Added detail texture nodes to material: {material.name}")
    pass

def add_palette_mask_texture_nodes(material, texture_info, node_group_cache):
    """
    Adds palette mask texture nodes to a material.

    :param material: The material to modify.
    :param texture_info: A dictionary containing texture information, including palette mask frames.
    :param node_group_cache: A cache to store and retrieve existing node groups.
    """
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Create or get the Blur node group
    blur_node_group_name = "Blur"
    if blur_node_group_name not in bpy.data.node_groups:
        blur_node_group = bpy.data.node_groups.new(name=blur_node_group_name, type='ShaderNodeTree')
        create_blur_node_group(blur_node_group)
    else:
        blur_node_group = bpy.data.node_groups[blur_node_group_name]

    # Process palette mask frames
    for frame_data in texture_info.get('frames', []):
        if frame_data.get('type') == 'palette_mask':
            frame_file = frame_data['file']

            # Add Image Texture node for the palette mask
            palette_mask_texture_node = nodes.new(type='ShaderNodeTexImage')
            palette_mask_texture_node.location = (-400, -200)
            palette_mask_texture_node.image = bpy.data.images.load(frame_file)
            palette_mask_texture_node.image.colorspace_settings.name = 'Non-Color'

            # Connect the Blur node group to the palette mask texture
            blur_node = nodes.new(type='ShaderNodeGroup')
            blur_node.node_tree = blur_node_group
            blur_node.location = (-600, -200)

            links.new(blur_node.outputs[0], palette_mask_texture_node.inputs['Vector'])

            # Store the palette mask node for future use in tiled textures
            texture_info['palette_mask_node'] = palette_mask_texture_node
            print(f"Added palette mask texture node to material: {material.name}")

def create_blur_node_group(blur_node_group):
    """
    Creates the Blur node group used for palette mask textures.

    :param blur_node_group: The node group to be populated.
    """
    nodes = blur_node_group.nodes
    links = blur_node_group.links

    # Add nodes inside the Blur node group
    group_output = nodes.new('NodeGroupOutput')
    group_output.location = (400, 0)
    blur_node_group.outputs.new('NodeSocketVector', 'Vector')

    tex_coord_node = nodes.new(type='ShaderNodeTexCoord')
    tex_coord_node.location = (-600, 0)

    add_vector_node = nodes.new(type='ShaderNodeVectorMath')
    add_vector_node.operation = 'ADD'
    add_vector_node.location = (0, 0)

    noise_texture_node = nodes.new(type='ShaderNodeTexWhiteNoise')
    noise_texture_node.location = (-400, 0)

    map_range_node = nodes.new(type='ShaderNodeMapRange')
    map_range_node.data_type = 'FLOAT_VECTOR'  # Updated data type to 'FLOAT_VECTOR'
    map_range_node.location = (-200, 0)

    value_node = nodes.new(type='ShaderNodeValue')
    value_node.location = (-800, 0)
    value_node.outputs[0].default_value = 0.005

    multiply_node = nodes.new(type='ShaderNodeMath')
    multiply_node.operation = 'MULTIPLY'
    multiply_node.location = (-600, -200)
    multiply_node.inputs[1].default_value = -1

    # Create links within the Blur node group
    links.new(tex_coord_node.outputs['UV'], add_vector_node.inputs[0])
    links.new(tex_coord_node.outputs['UV'], noise_texture_node.inputs['Vector'])
    links.new(noise_texture_node.outputs['Color'], map_range_node.inputs['Value'])  # Changed 'Vector' to 'Value'
    links.new(value_node.outputs[0], map_range_node.inputs['To Max'])
    links.new(value_node.outputs[0], multiply_node.inputs[0])
    links.new(multiply_node.outputs[0], map_range_node.inputs['To Min'])
    links.new(map_range_node.outputs['Result'], add_vector_node.inputs[1])  # Changed 'Vector' to 'Result'
    links.new(add_vector_node.outputs['Vector'], group_output.inputs['Vector'])

    print("Created Blur node group")
    pass

def add_tiled_texture_nodes(material, texture_info, node_group_cache):
    """
    Adds tiled texture nodes to a material.

    :param material: The material to modify.
    :param texture_info: A dictionary containing texture information, including tiled frames.
    :param node_group_cache: A cache to store and retrieve existing node groups.
    """
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    last_palette_mask_node = None
    previous_palette_mask_group_output = None
    transparent_bsdf_node = None

    # Create or get the PaletteMask node group
    palette_mask_node_group_name = "PaletteMask"
    if palette_mask_node_group_name not in bpy.data.node_groups:
        palette_mask_node_group = bpy.data.node_groups.new(name=palette_mask_node_group_name, type='ShaderNodeTree')
        create_palette_mask_node_group(palette_mask_node_group)
    else:
        palette_mask_node_group = bpy.data.node_groups[palette_mask_node_group_name]

    # Iterate through tiled frames
    for frame_index, frame_data in enumerate(texture_info.get('frames', [])):
        if frame_data.get('type') == 'tiled':
            frame_file = frame_data['file']
            color_index = frame_data['color_index']
            scale = frame_data['scale'] / 10.0
            blend = frame_data['blend']

            tiled_texture_name = f"{color_index + 1}, {int(scale * 10)}, {blend}, {os.path.basename(frame_file)}"

            # Create Image Texture node for the tiled texture
            tiled_texture_node = nodes.new(type='ShaderNodeTexImage')
            tiled_texture_node.image = bpy.data.images.load(frame_file)
            tiled_texture_node.location = (-400, -200 - frame_index * 300)
            tiled_texture_node.name = tiled_texture_name
            tiled_texture_node.label = tiled_texture_name

            # Add the necessary nodes to manipulate the tiled texture
            index_color_node = nodes.new(type='ShaderNodeRGB')
            index_color_node.location = (-600, -200 - frame_index * 300)
            index_color_node.name = f"Index {color_index + 1} Color"
            # Here you should define the RGB values from the palette; use (1.0, 0.0, 0.0, 1.0) as a placeholder
            index_color_node.outputs[0].default_value = (1.0, 0.0, 0.0, 1.0)

            # Add a Texture Coordinate and Mapping nodes
            add_texture_coordinate_and_mapping_nodes(nodes, links, tiled_texture_node, frame_file, scale)

            # Create a PaletteMask node group node
            palette_mask_group_node = nodes.new(type='ShaderNodeGroup')
            palette_mask_group_node.node_tree = palette_mask_node_group
            palette_mask_group_node.location = (0, -200 - frame_index * 300)
            
            # Connect nodes for palette masking
            if 'palette_mask_node' in texture_info:
                palette_mask_node = texture_info['palette_mask_node']
                links.new(palette_mask_node.outputs['Color'], palette_mask_group_node.inputs['ClrPalette'])
            
            links.new(index_color_node.outputs['Color'], palette_mask_group_node.inputs['NdxClr'])
            links.new(tiled_texture_node.outputs['Color'], palette_mask_group_node.inputs['Texture'])
            
            if color_index > 0 and previous_palette_mask_group_output:
                links.new(previous_palette_mask_group_output, palette_mask_group_node.inputs['Mix'])

            previous_palette_mask_group_output = palette_mask_group_node.outputs['Shader']

            last_palette_mask_node = palette_mask_group_node

    # Create the final mix shader to blend the last tiled texture with the base material
    if last_palette_mask_node:
        mix_shader = nodes.new(type='ShaderNodeMixShader')
        mix_shader.location = (300, 0)

        # Add a Transparent BSDF if not already created
        if not transparent_bsdf_node:
            transparent_bsdf_node = nodes.new(type='ShaderNodeBsdfTransparent')
            transparent_bsdf_node.location = (100, 0)
        
        links.new(transparent_bsdf_node.outputs['BSDF'], mix_shader.inputs[1])
        links.new(last_palette_mask_node.outputs['Shader'], mix_shader.inputs[2])

        # Connect the mix shader to the material output
        material_output_node = nodes.get("Material Output")
        if material_output_node:
            links.new(mix_shader.outputs['Shader'], material_output_node.inputs['Surface'])

        # Connect the main material shader output to the mix shader
        main_shader_node = nodes.get('ShaderNodeGroup')
        if main_shader_node:
            links.new(main_shader_node.outputs['Shader'], mix_shader.inputs[0])

def create_palette_mask_node_group(palette_mask_node_group):
    """
    Creates the PaletteMask node group used for tiled textures.

    :param palette_mask_node_group: The node group to be populated.
    """
    nodes = palette_mask_node_group.nodes
    links = palette_mask_node_group.links

    # Create nodes inside the PaletteMask node group
    group_input = nodes.new('NodeGroupInput')
    group_input.location = (-600, 0)
    palette_mask_node_group.inputs.new('NodeSocketColor', 'ClrPalette')
    palette_mask_node_group.inputs.new('NodeSocketColor', 'NdxClr')
    palette_mask_node_group.inputs.new('NodeSocketShader', 'Mix')
    palette_mask_node_group.inputs.new('NodeSocketColor', 'Texture')

    group_output = nodes.new('NodeGroupOutput')
    group_output.location = (600, 0)
    palette_mask_node_group.outputs.new('NodeSocketShader', 'Shader')

    separate_clr_palette = nodes.new(type='ShaderNodeSeparateColor')
    separate_clr_palette.location = (-400, 200)

    separate_ndx_clr = nodes.new(type='ShaderNodeSeparateColor')
    separate_ndx_clr.location = (-400, 0)

    less_than_red = nodes.new(type='ShaderNodeMath')
    less_than_red.operation = 'LESS_THAN'
    less_than_red.location = (-200, 300)

    greater_than_red = nodes.new(type='ShaderNodeMath')
    greater_than_red.operation = 'GREATER_THAN'
    greater_than_red.location = (-200, 250)

    less_than_green = nodes.new(type='ShaderNodeMath')
    less_than_green.operation = 'LESS_THAN'
    less_than_green.location = (-200, 200)

    greater_than_green = nodes.new(type='ShaderNodeMath')
    greater_than_green.operation = 'GREATER_THAN'
    greater_than_green.location = (-200, 150)

    less_than_blue = nodes.new(type='ShaderNodeMath')
    less_than_blue.operation = 'LESS_THAN'
    less_than_blue.location = (-200, 100)

    greater_than_blue = nodes.new(type='ShaderNodeMath')
    greater_than_blue.operation = 'GREATER_THAN'
    greater_than_blue.location = (-200, 50)

    add_red = nodes.new(type='ShaderNodeMath')
    add_red.operation = 'ADD'
    add_red.location = (-400, -100)

    sub_red = nodes.new(type='ShaderNodeMath')
    sub_red.operation = 'SUBTRACT'
    sub_red.location = (-400, -150)

    add_green = nodes.new(type='ShaderNodeMath')
    add_green.operation = 'ADD'
    add_green.location = (-400, -200)

    sub_green = nodes.new(type='ShaderNodeMath')
    sub_green.operation = 'SUBTRACT'
    sub_green.location = (-400, -250)

    add_blue = nodes.new(type='ShaderNodeMath')
    add_blue.operation = 'ADD'
    add_blue.location = (-400, -300)

    sub_blue = nodes.new(type='ShaderNodeMath')
    sub_blue.operation = 'SUBTRACT'
    sub_blue.location = (-400, -350)

    multiply_red = nodes.new(type='ShaderNodeMath')
    multiply_red.operation = 'MULTIPLY'
    multiply_red.location = (0, 300)

    multiply_green = nodes.new(type='ShaderNodeMath')
    multiply_green.operation = 'MULTIPLY'
    multiply_green.location = (0, 200)

    multiply_blue = nodes.new(type='ShaderNodeMath')
    multiply_blue.operation = 'MULTIPLY'
    multiply_blue.location = (0, 100)

    final_multiply = nodes.new(type='ShaderNodeMath')
    final_multiply.operation = 'MULTIPLY'
    final_multiply.location = (200, 200)

    final_multiply_2 = nodes.new(type='ShaderNodeMath')
    final_multiply_2.operation = 'MULTIPLY'
    final_multiply_2.location = (400, 100)

    mix_shader = nodes.new(type='ShaderNodeMixShader')
    mix_shader.location = (500, 0)

    emission_shader = nodes.new(type='ShaderNodeEmission')
    emission_shader.inputs['Strength'].default_value = 5
    emission_shader.location = (200, -100)

    # Create links within the PaletteMask node group
    links.new(group_input.outputs['ClrPalette'], separate_clr_palette.inputs['Color'])
    links.new(group_input.outputs['NdxClr'], separate_ndx_clr.inputs['Color'])

    links.new(separate_clr_palette.outputs['Red'], less_than_red.inputs[0])  # Corrected output name
    links.new(separate_clr_palette.outputs['Red'], greater_than_red.inputs[0])  # Corrected output name
    links.new(separate_clr_palette.outputs['Green'], less_than_green.inputs[0])  # Corrected output name
    links.new(separate_clr_palette.outputs['Green'], greater_than_green.inputs[0])  # Corrected output name
    links.new(separate_clr_palette.outputs['Blue'], less_than_blue.inputs[0])  # Corrected output name
    links.new(separate_clr_palette.outputs['Blue'], greater_than_blue.inputs[0])  # Corrected output name

    links.new(separate_ndx_clr.outputs['Red'], add_red.inputs[0])  # Corrected output name
    links.new(separate_ndx_clr.outputs['Red'], sub_red.inputs[0])  # Corrected output name
    links.new(separate_ndx_clr.outputs['Green'], add_green.inputs[0])  # Corrected output name
    links.new(separate_ndx_clr.outputs['Green'], sub_green.inputs[0])  # Corrected output name
    links.new(separate_ndx_clr.outputs['Blue'], add_blue.inputs[0])  # Corrected output name
    links.new(separate_ndx_clr.outputs['Blue'], sub_blue.inputs[0])  # Corrected output name

    links.new(add_red.outputs['Value'], less_than_red.inputs[1])
    links.new(sub_red.outputs['Value'], greater_than_red.inputs[1])
    links.new(add_green.outputs['Value'], less_than_green.inputs[1])
    links.new(sub_green.outputs['Value'], greater_than_green.inputs[1])
    links.new(add_blue.outputs['Value'], less_than_blue.inputs[1])
    links.new(sub_blue.outputs['Value'], greater_than_blue.inputs[1])

    links.new(less_than_red.outputs['Value'], multiply_red.inputs[0])
    links.new(greater_than_red.outputs['Value'], multiply_red.inputs[1])
    links.new(less_than_green.outputs['Value'], multiply_green.inputs[0])
    links.new(greater_than_green.outputs['Value'], multiply_green.inputs[1])
    links.new(less_than_blue.outputs['Value'], multiply_blue.inputs[0])
    links.new(greater_than_blue.outputs['Value'], multiply_blue.inputs[1])

    links.new(multiply_red.outputs['Value'], final_multiply.inputs[0])
    links.new(multiply_green.outputs['Value'], final_multiply.inputs[1])
    links.new(final_multiply.outputs['Value'], final_multiply_2.inputs[0])
    links.new(multiply_blue.outputs['Value'], final_multiply_2.inputs[1])

    links.new(final_multiply_2.outputs['Value'], mix_shader.inputs['Fac'])
    links.new(group_input.outputs['Mix'], mix_shader.inputs[1])
    links.new(group_input.outputs['Texture'], emission_shader.inputs['Color'])
    links.new(emission_shader.outputs['Emission'], mix_shader.inputs[2])
    links.new(mix_shader.outputs['Shader'], group_output.inputs['Shader'])

    print("Created PaletteMask node group")
    pass