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

def is_dxt5_dds(texture_path):
    # Check if the texture is a DDS with DXT5 compression
    try:
        with open(texture_path, 'rb') as f:
            header = f.read(DDS_HEADER_SIZE)
            if len(header) < DDS_HEADER_SIZE:
                return False
            
            # The 'fourCC' for DXT5 starts at byte offset 84 in the header
            dxt5_indicator = header[84:88]
            return dxt5_indicator == b'DXT5'
    except IOError:
        return False

def add_texture_coordinate_and_mapping_nodes(nodes, links, image_texture_node, texture_path):
    """
    Adds a Texture Coordinate and Mapping node to the node tree, connects them to the image texture node,
    and flips the texture vertically if it is a DDS.

    :param nodes: Node tree of the material.
    :param links: Links of the node tree.
    :param image_texture_node: The image texture node to connect.
    :param texture_path: The path to the texture file.
    :return: None
    """
    
    # Calculate positions relative to the Image Texture node
    tex_coord_location = (image_texture_node.location.x - 600, image_texture_node.location.y)
    mapping_location = (image_texture_node.location.x - 300, image_texture_node.location.y)

    # Create a new Texture Coordinate node
    tex_coord_node = nodes.new(type='ShaderNodeTexCoord')
    tex_coord_node.location = tex_coord_location

    # Create a new Mapping node
    mapping_node = nodes.new(type='ShaderNodeMapping')
    mapping_node.location = mapping_location

    # Flip the texture vertically if it has a DDS header
    if has_dds_header(texture_path):
        mapping_node.inputs['Scale'].default_value[1] = -1  # Flip vertically

    # Connect nodes
    links.new(tex_coord_node.outputs['UV'], mapping_node.inputs['Vector'])
    links.new(mapping_node.outputs['Vector'], image_texture_node.inputs['Vector'])
