#TransparentMasked

import bpy
import struct

DDS_HEADER_SIZE = 128  # Size of DDS header
DDS_MAGIC = b'DDS '  # The first 4 bytes of a DDS file should be "DDS "

def has_dds_header(texture_path):
    try:
        with open(texture_path, 'rb') as f:
            header = f.read(DDS_HEADER_SIZE)
            return len(header) >= DDS_HEADER_SIZE and header[:4] == DDS_MAGIC
    except IOError:
        return False

def read_bmp_palette_color(file_path):
    with open(file_path, 'rb') as f:
        f.seek(54)  # BMP header is 54 bytes
        palette_data = f.read(4)  # Read the first color in the palette (4 bytes: BGRX)
        blue, green, red, _ = struct.unpack('BBBB', palette_data)
        return red / 255.0, green / 255.0, blue / 255.0

def create_node_group_ud20():
    # Create the node group
    node_group = bpy.data.node_groups.new(name="USERDEFINED_20", type='ShaderNodeTree')
    
    # Add Group Input and Output nodes to the node group
    group_input = node_group.nodes.new('NodeGroupInput')
    group_input.location = (-800, 0)
    group_output = node_group.nodes.new('NodeGroupOutput')
    group_output.location = (800, 0)
    node_group.inputs.new('NodeSocketColor', 'Index 0 Color')
    node_group.inputs.new('NodeSocketColor', 'Non-Color Texture')
    node_group.inputs.new('NodeSocketColor', 'sRGB Texture')
    node_group.outputs.new('NodeSocketShader', 'Shader')
    
    # Create nodes in the node group
    math_node1 = node_group.nodes.new(type='ShaderNodeMath')
    math_node1.operation = 'SUBTRACT'
    math_node1.location = (-400, 400)

    math_node2 = node_group.nodes.new(type='ShaderNodeMath')
    math_node2.operation = 'SUBTRACT'
    math_node2.location = (-400, 200)

    math_node3 = node_group.nodes.new(type='ShaderNodeMath')
    math_node3.operation = 'SUBTRACT'
    math_node3.location = (-400, 0)

    separate_color_node1 = node_group.nodes.new(type='ShaderNodeSeparateColor')
    separate_color_node1.location = (-600, 300)
    
    separate_color_node2 = node_group.nodes.new(type='ShaderNodeSeparateColor')
    separate_color_node2.location = (-600, 100)

    transparent_bsdf_node = node_group.nodes.new(type='ShaderNodeBsdfTransparent')
    transparent_bsdf_node.location = (200, -200)

    abs_node1 = node_group.nodes.new(type='ShaderNodeMath')
    abs_node1.operation = 'ABSOLUTE'
    abs_node1.location = (-200, 400)

    abs_node2 = node_group.nodes.new(type='ShaderNodeMath')
    abs_node2.operation = 'ABSOLUTE'
    abs_node2.location = (-200, 200)

    abs_node3 = node_group.nodes.new(type='ShaderNodeMath')
    abs_node3.operation = 'ABSOLUTE'
    abs_node3.location = (-200, 0)

    diffuse_bsdf_node = node_group.nodes.new(type='ShaderNodeBsdfDiffuse')
    diffuse_bsdf_node.location = (-200, -200)

    add_node1 = node_group.nodes.new(type='ShaderNodeMath')
    add_node1.operation = 'ADD'
    add_node1.location = (0, 400)

    add_node2 = node_group.nodes.new(type='ShaderNodeMath')
    add_node2.operation = 'ADD'
    add_node2.location = (200, 300)

    less_than_node = node_group.nodes.new(type='ShaderNodeMath')
    less_than_node.operation = 'LESS_THAN'
    less_than_node.location = (400, 200)
    less_than_node.inputs[1].default_value = 1.5e-05  # Threshold value

    mix_shader_node = node_group.nodes.new(type='ShaderNodeMixShader')
    mix_shader_node.location = (600, 100)

    # Create links within the node group
    group_links = node_group.links
    group_links.new(separate_color_node1.outputs['Red'], math_node1.inputs[1])
    group_links.new(separate_color_node1.outputs['Green'], math_node2.inputs[1])
    group_links.new(separate_color_node1.outputs['Blue'], math_node3.inputs[1])
    group_links.new(separate_color_node2.outputs['Red'], math_node1.inputs[0])
    group_links.new(separate_color_node2.outputs['Green'], math_node2.inputs[0])
    group_links.new(separate_color_node2.outputs['Blue'], math_node3.inputs[0])
    group_links.new(group_input.outputs['Non-Color Texture'], separate_color_node2.inputs['Color'])
    group_links.new(group_input.outputs['sRGB Texture'], diffuse_bsdf_node.inputs['Color'])
    group_links.new(group_input.outputs['Index 0 Color'], separate_color_node1.inputs['Color'])

    group_links.new(math_node1.outputs['Value'], abs_node1.inputs[0])
    group_links.new(math_node2.outputs['Value'], abs_node2.inputs[0])
    group_links.new(math_node3.outputs['Value'], abs_node3.inputs[0])
    group_links.new(abs_node1.outputs['Value'], add_node1.inputs[0])
    group_links.new(abs_node2.outputs['Value'], add_node1.inputs[1])
    group_links.new(abs_node3.outputs['Value'], add_node2.inputs[1])
    group_links.new(add_node1.outputs['Value'], add_node2.inputs[0])
    group_links.new(add_node2.outputs['Value'], less_than_node.inputs[0])
    group_links.new(less_than_node.outputs['Value'], mix_shader_node.inputs['Fac'])
    group_links.new(diffuse_bsdf_node.outputs['BSDF'], mix_shader_node.inputs[1])
    group_links.new(transparent_bsdf_node.outputs['BSDF'], mix_shader_node.inputs[2])
    group_links.new(mix_shader_node.outputs['Shader'], group_output.inputs['Shader'])

    return node_group

def create_material_with_node_group_ud20(material_name, image_texture_file, node_group):
    # Read the first color from the BMP palette
    first_palette_color = read_bmp_palette_color(image_texture_file)
    
    # Create a new material
    material = bpy.data.materials.new(name=material_name)
    material.use_nodes = True
    material.blend_method = 'BLEND'  # Set blend mode to Alpha Blend
    material.show_transparent_back = False  # Uncheck "Show Backface"
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Clear default nodes
    for node in nodes:
        nodes.remove(node)
    
    # Convert high precision Decimal to float
    red_value = float(first_palette_color[0])
    green_value = float(first_palette_color[1])
    blue_value = float(first_palette_color[2])

    # Add the node group to the material
    group_node = nodes.new(type='ShaderNodeGroup')
    group_node.node_tree = node_group
    group_node.location = (0, 0)

    # Add other nodes outside the group
    image_texture_node1 = nodes.new(type='ShaderNodeTexImage')
    image_texture_node1.location = (-300, -50)
    image_texture_node1.image = bpy.data.images.load(image_texture_file)
    image_texture_node1.interpolation = 'Closest'
    image_texture_node1.image.colorspace_settings.name = 'Non-Color'

    image_texture_node2 = nodes.new(type='ShaderNodeTexImage')
    image_texture_node2.location = (-300, -400)
    image_texture_node2.image = bpy.data.images.load(image_texture_file)

    rgb_node = nodes.new(type='ShaderNodeRGB')
    rgb_node.location = (-300, 200)
    rgb_node.outputs[0].default_value = (red_value, green_value, blue_value, 1.0)

    # Add a Texture Coordinate node
    tex_coord_node = nodes.new(type='ShaderNodeTexCoord')
    tex_coord_node.location = (-900, 0)

    # Add a Mapping node
    mapping_node1 = nodes.new(type='ShaderNodeMapping')
    mapping_node1.location = (-600, -50)

    mapping_node2 = nodes.new(type='ShaderNodeMapping')
    mapping_node2.location = (-600, -400)
    
    # Flip the texture vertically if it has a DDS header
    if has_dds_header(image_texture_file):
        mapping_node1.inputs['Scale'].default_value[1] = -1  # Flip vertically
        mapping_node2.inputs['Scale'].default_value[1] = -1  # Flip vertically

    material_output_node = nodes.new(type='ShaderNodeOutputMaterial')
    material_output_node.location = (300, 0)

    # Create links outside the group
    links.new(tex_coord_node.outputs['UV'], mapping_node1.inputs['Vector'])
    links.new(mapping_node1.outputs['Vector'], image_texture_node1.inputs['Vector'])

    links.new(tex_coord_node.outputs['UV'], mapping_node2.inputs['Vector'])
    links.new(mapping_node2.outputs['Vector'], image_texture_node2.inputs['Vector'])

    links.new(image_texture_node1.outputs['Color'], group_node.inputs['Non-Color Texture'])
    links.new(image_texture_node2.outputs['Color'], group_node.inputs['sRGB Texture'])
    links.new(rgb_node.outputs[0], group_node.inputs['Index 0 Color'])
    links.new(group_node.outputs['Shader'], material_output_node.inputs['Surface'])

    return material