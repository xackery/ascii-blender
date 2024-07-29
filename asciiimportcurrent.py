import bpy
import bmesh
import mathutils
import os
import sys

# Manually set the directory containing your scripts
script_dir = r'C:\Users\dariu\Documents\Quail\Importer'  # Replace with the actual path
print(f"Script directory: {script_dir}")  # Check the path
if script_dir not in sys.path:
    sys.path.append(script_dir)

# Import the modules
from texture5ambientgouraud1 import create_node_group_t5ag1, create_material_with_node_group_t5ag1
from userdefined_02 import create_node_group_ud02, create_material_with_node_group_ud02
from userdefined_12 import create_node_group_ud12, create_material_with_node_group_ud12
from userdefined_20 import create_node_group_ud20, create_material_with_node_group_ud20
from userdefined_21 import create_node_group_ud21, create_material_with_node_group_ud21
from userdefined_22 import create_node_group_ud22, create_material_with_node_group_ud22
from userdefined_24 import create_node_group_ud24, create_material_with_node_group_ud24
from eq_ascii_wld_parser import eq_ascii_parse
from calculations import euler_to_quaternion
from create_polyhedron import create_polyhedron

# Path to the text file
file_path = r"C:\Users\dariu\Documents\Quail\pre.spk"

# Get the base name for the main object
base_name = os.path.splitext(os.path.basename(file_path))[0]
prefix = base_name.upper()

def clear_console():
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        os.system('clear')

# Call the function to clear the console
clear_console()

# Read 3D data from file using eq_ascii_wld_parser
meshes, armature_data, track_definitions, material_palettes, include_files, polyhedrons = eq_ascii_parse(file_path)

# Dictionary to store created materials
created_materials = {}

# Dictionary to store created polyhedron objects
polyhedron_objects = {}

# Cache for node groups
node_group_cache = {}

# Function to read .mdf files and create materials
def read_mdf_file(file_path):
    materials = {}
    current_texture_path = ""
    in_simple_sprite_inst = False
    print(f"Reading .mdf file from path: {file_path}")  # Debug print
    with open(file_path, 'r') as file:
        lines = iter(file.readlines())
        current_material = None

        for line in lines:
            line = line.strip()
            
            # Skip lines between SIMPLESPRITEINST and ENDSIMPLESPRITEINST
            if line.startswith("SIMPLESPRITEINST"):
                in_simple_sprite_inst = True
                continue
            if line.startswith("ENDSIMPLESPRITEINST"):
                in_simple_sprite_inst = False
                continue
            if in_simple_sprite_inst:
                continue

            if line.startswith("INCLUDE"):
                texture_file = line.split('"')[1]
                current_texture_path = os.path.join(os.path.dirname(file_path), texture_file)
                print(f"Found INCLUDE, set texture path: {current_texture_path}")  # Debug print
                if current_material is not None:
                    current_material['texture_path'] = current_texture_path
                continue
            if line.startswith("MATERIALDEFINITION"):
                current_material = {
                    'name': '',
                    'rendermethod': '',
                    'rgbpen': (1.0, 1.0, 1.0),
                    'brightness': 0.0,
                    'scaledambient': 0.75,
                    'texture_path': current_texture_path
                }
                continue
            if line.startswith("ENDMATERIALDEFINITION"):
                if current_material:
                    materials[current_material['name']] = current_material
                    print(f"Created material definition: {current_material}")  # Debug print
                current_material = None
                continue
            if current_material is not None:
                if line.startswith("TAG"):
                    current_material['name'] = line.split('"')[1]
                elif line.startswith("RENDERMETHOD"):
                    current_material['rendermethod'] = " ".join(line.split()[1:])
                elif line.startswith("RGBPEN"):
                    parts = line.split()
                    current_material['rgbpen'] = (int(parts[1]) / 255.0, int(parts[2]) / 255.0, int(parts[3]) / 255.0)
                elif line.startswith("BRIGHTNESS"):
                    current_material['brightness'] = float(line.split()[1])
                elif line.startswith("SCALEDAMBIENT"):
                    current_material['scaledambient'] = float(line.split()[1])
    return materials

# Function to read .sps files and get texture paths
def read_sps_file(file_path):
    textures = {}
    current_texture = None
    print(f"Reading .sps file from path: {file_path}")  # Debug print
    with open(file_path, 'r') as file:
        lines = iter(file.readlines())
        for line in lines:
            line = line.strip()
            if line.startswith("SIMPLESPRITEDEF"):
                current_texture = {'name': '', 'file': ''}
                continue
            if line.startswith("ENDSIMPLESPRITEDEF"):
                if current_texture:
                    textures[current_texture['name']] = current_texture['file']
                    print(f"Created texture definition: {current_texture}")  # Debug print
                current_texture = None
                continue
            if current_texture is not None:
                if line.startswith("SIMPLESPRITETAG"):
                    current_texture['name'] = line.split('"')[1]
                elif line.startswith("BMINFO"):
                    parts = line.split('"')
                    if len(parts) > 3:
                        current_texture['file'] = parts[3].strip()
    return textures

# Process each included .mdf file
for include_file in include_files:
    mdf_path = os.path.join(os.path.dirname(file_path), include_file)
    materials = read_mdf_file(mdf_path)
    for mat_name, mat_data in materials.items():
        if mat_name not in created_materials:
            texture_file = mat_data['texture_path']
            print(f"Looking for .sps file at path: {texture_file}")  # Debug print
            if not os.path.isfile(texture_file):
                print(f"Error: .sps file '{texture_file}' not found.")
                continue
            
            texture_data = read_sps_file(texture_file)
            for tex_name, tex_path in texture_data.items():
                tex_full_path = os.path.join(os.path.dirname(texture_file), tex_path)
                print(f"Using texture file at path: {tex_full_path}")  # Debug print

            # Create material based on the rendermethod
            rendermethod = mat_data['rendermethod']
            print(f"Creating material '{mat_name}' with texture '{tex_full_path}' and rendermethod '{rendermethod}'")
            if rendermethod == 'TEXTURE5AMBIENTGOURAUD1':
                if 'TEXTURE5AMBIENTGOURAUD1' not in node_group_cache:
                    node_group_cache['TEXTURE5AMBIENTGOURAUD1'] = create_node_group_t5ag1()
                mat = create_material_with_node_group_t5ag1(mat_name, tex_full_path, node_group_cache['TEXTURE5AMBIENTGOURAUD1'])
            elif rendermethod == 'USERDEFINED 2':
                if 'USERDEFINED 2' not in node_group_cache:
                    node_group_cache['USERDEFINED 2'] = create_node_group_ud02()
                mat = create_material_with_node_group_ud02(mat_name, tex_full_path, node_group_cache['USERDEFINED 2'])
            elif rendermethod == 'USERDEFINED 12':
                if 'USERDEFINED 2' not in node_group_cache:
                    node_group_cache['USERDEFINED 12'] = create_node_group_ud12()
                mat = create_material_with_node_group_ud12(mat_name, tex_full_path, node_group_cache['USERDEFINED 12'])
            elif rendermethod == 'USERDEFINED 20':
                if 'USERDEFINED 20' not in node_group_cache:
                    node_group_cache['USERDEFINED 20'] = create_node_group_ud20()
                mat = create_material_with_node_group_ud20(mat_name, tex_full_path, node_group_cache['USERDEFINED 20'])
            elif rendermethod == 'USERDEFINED 21':
                if 'USERDEFINED 21' not in node_group_cache:
                    node_group_cache['USERDEFINED 21'] = create_node_group_ud21()
                mat = create_material_with_node_group_ud21(mat_name, tex_full_path, node_group_cache['USERDEFINED 21'])
            elif rendermethod == 'USERDEFINED 22':
                if 'USERDEFINED 22' not in node_group_cache:
                    node_group_cache['USERDEFINED 22'] = create_node_group_ud22()
                mat = create_material_with_node_group_ud22(mat_name, tex_full_path, node_group_cache['USERDEFINED 22'])                
            elif rendermethod == 'USERDEFINED 24':
                if 'USERDEFINED 24' not in node_group_cache:
                    node_group_cache['USERDEFINED 24'] = create_node_group_ud24()
                mat = create_material_with_node_group_ud24(mat_name, tex_full_path, node_group_cache['USERDEFINED 24'])
            else:
                mat = bpy.data.materials.new(name=mat_name)
                mat.use_nodes = True
                principled_bsdf = mat.node_tree.nodes.get('Principled BSDF')
                if principled_bsdf:
                    principled_bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)  # Set default color to white
            
            created_materials[mat_name] = mat

# Create polyhedron objects
for polyhedron_data in polyhedrons:
    polyhedron_obj = create_polyhedron(polyhedron_data)
    polyhedron_objects[polyhedron_data['name']] = polyhedron_obj

# Create a new main object
main_obj = bpy.data.objects.new(base_name, None)
bpy.context.collection.objects.link(main_obj)

# Function to create a mesh from given data and link to the main object
def create_mesh(mesh_data, parent_obj, armature_obj=None, cumulative_matrices=None):
    print(f"Creating mesh '{mesh_data['name']}'")

    mesh = bpy.data.meshes.new(mesh_data['name'])
    obj = bpy.data.objects.new(mesh_data['name'], mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent_obj

    # Adjust origin by the center_offset value
    center_offset = mathutils.Vector(mesh_data.get('center_offset', [0.0, 0.0, 0.0]))
    obj.location = center_offset

    # Extract only the first three vertices for each face
    faces_for_creation = [face[:3] for face in mesh_data['faces']]

    mesh.from_pydata(mesh_data['vertices'], [], faces_for_creation)
    mesh.update()

    # == UV mapping ==
    uvlayer = mesh.uv_layers.new(name=mesh_data['name'] + "_uv")
    for i, triangle in enumerate(mesh.polygons):
        vertices = list(triangle.vertices)
        for j, vertex in enumerate(vertices):
            uvlayer.data[triangle.loop_indices[j]].uv = (mesh_data['uvs'][vertex][0], mesh_data['uvs'][vertex][1] - 1)

    # Create vertex groups if armature data is available
    if armature_obj and cumulative_matrices:
        if 'vertex_groups' in mesh_data and mesh_data['vertex_groups']:
            for vg_start, vg_end, bone_index in mesh_data['vertex_groups']:
                bone_name = armature_data['bones'][bone_index]['name']
                group = obj.vertex_groups.new(name=bone_name)
                group.add(range(vg_start, vg_end), 1.0, 'ADD')
                
                # Apply cumulative transformation to vertices in this group
                cumulative_matrix = cumulative_matrices[bone_name]
                for vert_index in range(vg_start, vg_end):
                    vert = obj.data.vertices[vert_index]
                    vert.co = cumulative_matrix @ vert.co
        else:
            # No vertex groups, find bone with matching sprite
            for bone in armature_data['bones']:
                if bone.get('sprite') == mesh_data['name']:
                    bone_obj = armature_obj.pose.bones.get(bone['name'])
                    if bone_obj:
                        # Apply cumulative matrix to the mesh
                        #cumulative_matrix = cumulative_matrices[bone['name']]
                        #for vert in obj.data.vertices:
                            #vert.co = cumulative_matrix @ vert.co

                        # Parent the bone to the mesh
                        #obj.matrix_world = armature_obj.matrix_world @ bone_obj.matrix
                        obj.parent = armature_obj
                        obj.parent_bone = bone_obj.name
                        obj.parent_type = 'BONE'
                        break

        # Add an armature modifier
        modifier = obj.modifiers.new(name="Armature", type='ARMATURE')
        modifier.object = armature_obj

    # Create materials only if face materials exist
    if 'face_materials' in mesh_data and mesh_data['face_materials']:
        palette_name = mesh_data.get('material_palette', None)
        if palette_name:
            if palette_name not in material_palettes:
                print(f"Error: Material palette '{palette_name}' not found for mesh '{mesh_data['name']}'")
                return None

            materials = material_palettes[palette_name]
            for mat_name in materials:
                if mat_name in created_materials:
                    obj.data.materials.append(created_materials[mat_name])
                else:
                    print(f"Warning: Material '{mat_name}' not found in created materials")
        else:
            print(f"Warning: No material palette found for mesh '{mesh_data['name']}'")
            materials = []

        # Assign materials to faces
        face_index = 0
        for face_data in mesh_data['face_materials']:
            start_face, end_face, material_index = face_data[:3]
            num_faces = end_face - start_face

            if material_index < len(materials):
                material_name = materials[material_index]
                material_list_index = obj.data.materials.find(material_name)
                if material_list_index == -1:
                    material_list_index = len(obj.data.materials) - 1

                for i in range(num_faces):
                    if face_index < len(obj.data.polygons):
                        obj.data.polygons[face_index].material_index = material_list_index
                        face_index += 1

                print(f"Material index: {material_list_index}, Material name: {material_name}")
            else:
                print(f"Material index: {material_index}, Material name: Unknown")

    return obj

# Function to create an armature from given data
def create_armature(armature_data, armature_tracks, parent_obj):
    bpy.context.view_layer.objects.active = parent_obj

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_pattern(pattern=parent_obj.name)

    bpy.ops.object.armature_add(enter_editmode=True)
    armature_obj = bpy.context.object
    armature_obj.name = armature_data['name']
    armature = armature_obj.data
    armature.name = armature_data['name']
    armature_obj.parent = parent_obj

    armature.edit_bones.remove(armature.edit_bones[0])

    bone_map = {}
    cumulative_matrices = {}
    for index, bone in enumerate(armature_data['bones']):
        bone_name = bone['name']
        bone_bpy = armature.edit_bones.new(bone_name)
        print(f"Created bone: {bone_name} at index {index}")

        track_instance = armature_tracks.get(bone['track'], None)
        if track_instance:
            track_def = track_instance['definition']
            transform = track_def['frame_transforms'][0]  # Assuming the first frame for initial transform
            bone_bpy.head = transform['translation']
            bone_bpy.tail = (transform['translation'][0], transform['translation'][1] + 1, transform['translation'][2])
            rotation = mathutils.Quaternion((transform['rotation'][0], transform['rotation'][1], transform['rotation'][2], transform['rotation'][3]))
            bone_bpy.matrix = mathutils.Matrix.Translation(transform['translation']) @ rotation.to_matrix().to_4x4()
        bone_map[index] = bone_bpy

    bpy.ops.object.mode_set(mode='EDIT')

    for parent_index, child_indices in armature_data['relationships']:
        print(f"Parent: {parent_index}, Children: {child_indices}")
        parent_bone = bone_map.get(parent_index)
        if not parent_bone:
            continue
        parent_matrix = parent_bone.matrix.copy()
        for child_index in child_indices:
            child_bone = bone_map.get(child_index)
            if child_bone:
                print(f"Setting parent of {child_bone.name} to {parent_bone.name}")
                child_bone.matrix = parent_matrix @ child_bone.matrix
                child_bone.parent = parent_bone

                cumulative_matrices[child_bone.name] = child_bone.matrix

        if not parent_bone.children:
            parent_bone.tail = parent_bone.head + mathutils.Vector((0, 1, 0))

    bpy.ops.object.mode_set(mode='OBJECT')

    preferred_children = ["AB_DAG", "CH_DAG", "NE_DAG", "HEAD_DAG", "HE_DAG", "CHEST01_DAG", "NECK01_DAG", "NECK02_DAG", "HEAD01_DAG", "HEAD_POINT_DAG", "HORSECHEST01_DAG"]

    # Set the tail of each bone to the head of its child bone
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in armature.edit_bones:
        if bone.children:
            preferred_child = None
            for child in bone.children:
                child_name_no_prefix = child.name.replace(prefix, "")
                if child_name_no_prefix in preferred_children:
                    preferred_child = child
                    break
            if preferred_child:
                if (bone.head - preferred_child.head).length < 0.001:
                    bone.tail = bone.head + mathutils.Vector((0, 0.001, 0))
                else:
                    bone.tail = preferred_child.head
            else:
                if (bone.head - bone.children[0].head).length < 0.001:
                    bone.tail = bone.head + mathutils.Vector((0, 0.001, 0))
                else:
                    bone.tail = bone.children[0].head
        else:
            bone.tail = bone.head + mathutils.Vector((1, 0, 0))
    bpy.ops.object.mode_set(mode='OBJECT')

    # Adjust origin by the center_offset value
    center_offset = mathutils.Vector(armature_data.get('center_offset', [0.0, 0.0, 0.0]))
    armature_obj.location = center_offset

    print("Final bone hierarchy:")
    for bone in armature.bones:
        print(f"Bone: {bone.name}, Parent: {bone.parent.name if bone.parent else 'None'}")

    return armature_obj, bone_map, cumulative_matrices

# Create armature and link it to the main object if armature data is available
if armature_data and track_definitions:
    armature_tracks = track_definitions['armature_tracks']
    armature_obj, bone_map, cumulative_matrices = create_armature(armature_data, armature_tracks, main_obj)
    for mesh_data in meshes:
        mesh_obj = create_mesh(mesh_data, main_obj, armature_obj, cumulative_matrices)
else:
    # If no armature data, just create meshes
    for mesh_data in meshes:
        mesh_obj = create_mesh(mesh_data, main_obj)

# Parent polyhedron to matching DMSPRITEDEF mesh
for polyhedron_name, polyhedron_obj in polyhedron_objects.items():
    for mesh_data in meshes:
        if mesh_data.get('polyhedron') == polyhedron_name:
            mesh_obj = bpy.data.objects.get(mesh_data['name'])
            if polyhedron_obj:
                polyhedron_obj.parent = mesh_obj

print("Created object '{}' with {} meshes and armature '{}'".format(base_name, len(meshes), armature_data['name'] if armature_data else "None"))
print("Included files:", include_files)  # Print the list of include files for reference
