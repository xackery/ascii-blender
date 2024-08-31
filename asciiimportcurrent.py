import bpy
import bmesh
import mathutils
from mathutils import Quaternion
import os
import sys

# Manually set the directory containing your scripts
script_dir = r'C:\Users\dariu\Documents\Quail\Importer'  # Replace with the actual path
print(f"Script directory: {script_dir}")  # Check the path
if script_dir not in sys.path:
    sys.path.append(script_dir)

# Import the modules
from eq_ascii_wld_parser import eq_ascii_parse
from calculations import euler_to_quaternion
from create_polyhedron import create_polyhedron
from material_creator import create_materials  # Import the material creation function

# Path to the text file
file_path = r"C:\Users\dariu\Documents\Quail\twilight.quail\r.mod"

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
meshes, armature_data, track_definitions, material_palettes, include_files, polyhedrons, textures, materials = eq_ascii_parse(file_path)

# Cache for node groups
node_group_cache = {}

# Create materials using the separate script
created_materials = create_materials(materials, textures, file_path, node_group_cache)

# Create polyhedron objects
polyhedron_objects = {}

for polyhedron_data in polyhedrons:
    polyhedron_obj = create_polyhedron(polyhedron_data)
    polyhedron_objects[polyhedron_data['name']] = polyhedron_obj

# Create a new main object
main_obj = bpy.data.objects.new(base_name, None)
bpy.context.collection.objects.link(main_obj)

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
    if 'uvs' in mesh_data and mesh_data['uvs']:  # Check if UV data is present
        uvlayer = mesh.uv_layers.new(name=mesh_data['name'] + "_uv")
        for i, triangle in enumerate(mesh.polygons):
            vertices = list(triangle.vertices)
            for j, vertex in enumerate(vertices):
                uvlayer.data[triangle.loop_indices[j]].uv = (mesh_data['uvs'][vertex][0], mesh_data['uvs'][vertex][1] - 1)

    # == Apply Custom Normals ==
    if 'normals' in mesh_data and len(mesh_data['normals']) == len(mesh_data['vertices']):
        mesh.use_auto_smooth = True  # Enable auto smooth for custom normals
        mesh.normals_split_custom_set_from_vertices(mesh_data['normals'])

    # Print global and local transforms before parenting to bone
#    print(f"Mesh '{obj.name}' initial global location: {obj.matrix_world.translation}")
#    print(f"Mesh '{obj.name}' initial global rotation (Quaternion): {obj.matrix_world.to_quaternion()}")
#    print(f"Mesh '{obj.name}' initial local location: {obj.location}")
#    print(f"Mesh '{obj.name}' initial local rotation (Quaternion): {obj.rotation_quaternion}")

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
#                        print(f"Bone '{bone_obj.name}' initial rotation (Quaternion): {track_definitions['armature_tracks'][bone['track']]['definition']['frame_transforms'][0]['rotation']}")
#                        print(f"Bone '{bone_obj.name}' final rotation (Quaternion): {bone_obj.matrix.to_quaternion()}")
                        q2 = Quaternion(track_definitions['armature_tracks'][bone['track']]['definition']['frame_transforms'][0]['rotation'])
                        q1 = bone_obj.matrix.to_quaternion()
                        q_r = q2 @ q1.conjugated()
                        w, x, y, z = q_r
                        q_r_modified = mathutils.Quaternion((-w, -z, y, x))
                        print(f"Bone '{bone_obj.name}' rotation difference (Quaternion): {q_r_modified}")
                        
                        # Adjust the center offset by the difference in the source and final bone rotation
                        center_offset_modified = q_r_modified @ center_offset
                        obj.location = center_offset_modified

                        # Parent the mesh to the bone
                        obj.parent = armature_obj
                        obj.parent_bone = bone_obj.name
                        obj.parent_type = 'BONE'

                        # Apply the rotation difference to the mesh after parenting
                        bpy.context.view_layer.update()  # Update the scene graph
                        obj.matrix_world = bone_obj.matrix @ obj.matrix_parent_inverse @ mathutils.Matrix.Translation(obj.location) @ q_r_modified.to_matrix().to_4x4()
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

    # Print global and local transforms after parenting to bone
#    print(f"Mesh '{obj.name}' final global location: {obj.matrix_world.translation}")
#    print(f"Mesh '{obj.name}' final global rotation (Quaternion): {obj.matrix_world.to_quaternion()}")
#    print(f"Mesh '{obj.name}' final local location: {obj.location}")
#    print(f"Mesh '{obj.name}' final local rotation (Quaternion): {obj.rotation_quaternion}")

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
#        print(f"Created bone: {bone_name} at index {index}")

        track_instance = armature_tracks.get(bone['track'], None)
        if track_instance:
            track_def = track_instance['definition']
            transform = track_def['frame_transforms'][0]  # Assuming the first frame for initial transform
            bone_bpy.head = transform['translation']
            bone_bpy.tail = (transform['translation'][0], transform['translation'][1] + .5, transform['translation'][2])
            rotation = mathutils.Quaternion((transform['rotation'][0], transform['rotation'][1], transform['rotation'][2], transform['rotation'][3]))
            bone_bpy.matrix = mathutils.Matrix.Translation(transform['translation']) @ rotation.to_matrix().to_4x4()
            
            # Print the translation values
#            print(f"Bone '{bone_name}' initial translation: {transform['translation']}")
#            print(f"Bone '{bone_name}' initial rotation (Quaternion): {rotation}")

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
            parent_bone.tail = parent_bone.head + mathutils.Vector((0, .5, 0))

    bpy.ops.object.mode_set(mode='OBJECT')

    preferred_children = ["AB_DAG", "CH_DAG", "NE_DAG", "HEAD_DAG", "HE_DAG", "CHEST01_DAG", "NECK01_DAG", "NECK02_DAG", "HEAD01_DAG", "HEAD_POINT_DAG", "HORSECHEST01_DAG", "MID11_DAG"]

    # Set the tail of each bone to the head of its child bone
#    bpy.ops.object.mode_set(mode='EDIT')
#    for bone in armature.edit_bones:
#        if bone.children:
#            preferred_child = None
#            for child in bone.children:
#                child_name_no_prefix = child.name.replace(prefix, "")
#                if child_name_no_prefix in preferred_children:
#                    preferred_child = child
#                    break
#            if preferred_child:
#                if (bone.head - preferred_child.head).length < 0.001:
#                    bone.tail = bone.head + mathutils.Vector((0, 0.001, 0))
#                else:
#                    bone.tail = preferred_child.head
#            else:
#                if (bone.head - bone.children[0].head).length < 0.001:
#                    bone.tail = bone.head + mathutils.Vector((0, 0.001, 0))
#                else:
#                    bone.tail = bone.children[0].head
#        else:
#            bone.tail = bone.head + mathutils.Vector((1, 0, 0))
#    bpy.ops.object.mode_set(mode='OBJECT')

    # Adjust origin by the center_offset value only if it exists and is not NULL
    center_offset_data = armature_data.get('center_offset')
    if center_offset_data:
        center_offset = mathutils.Vector(center_offset_data)
        armature_obj.location = center_offset
        print(f"Applied center_offset: {center_offset}")
    else:
        print("No valid center_offset found, using default location.")

#    print("Final bone hierarchy:")
#    for bone in armature.bones:
#        print(f"Bone: {bone.name}, Parent: {bone.parent.name if bone.parent else 'None'}, Final rotation (Quaternion): {bone.matrix.to_quaternion()}")
#        print(f"Bone: {bone.name}, Final head location: {bone.head}")  # Print the final head location

    return armature_obj, bone_map, cumulative_matrices

# Function to create and apply animations
def create_animation(armature_obj, track_definitions, armature_data, model_prefix=prefix):
    # Group tracks by their animation key and model prefix
    animations_by_key = {}

    for animation_name, animation_data in track_definitions['animations'].items():
        # Use the stored animation prefix instead of extracting it
        animation_key = animation_data.get('animation_prefix', animation_name[:3])  # Fallback to old method if prefix isn't found

        # Use the correct action name
        action_name = f"{animation_key}_{model_prefix}"

        if action_name not in animations_by_key:
            animations_by_key[action_name] = []
        
        animations_by_key[action_name].append(animation_data)

    # Create actions for each animation key
    for action_name, tracks in animations_by_key.items():
        action = bpy.data.actions.new(name=action_name)
        armature_obj.animation_data_create()
        armature_obj.animation_data.action = action
        
        fcurves = {}  # Initialize the fcurves dictionary

        # Go through each track in the animation data
        for track_data in tracks:
            track = track_data['definition']
            track_instance_name = track_data['instance']['name']

            # Debugging: Print bone name and track instance name
#            print(f"Checking bone '{track_instance_name}' against track instance '{track_instance_name}'")

            # Identify which bone this track belongs to
            for bone_name, bone in armature_obj.pose.bones.items():
                # Strip '_DAG' from the bone name
                stripped_bone_name = bone_name.replace('_DAG', '')

                # Strip the animation prefix and '_TRACK' from the track instance name
                stripped_track_instance_name = track_instance_name[len(animation_key):].replace('_TRACK', '')

                # Compare the stripped names
                if stripped_bone_name == stripped_track_instance_name:
                    # Initialize FCurves if they don't exist
                    if bone_name not in fcurves:
                        fcurves[bone_name] = {
                            'location': [],
                            'rotation_quaternion': []
                        }

                        # Get or create fcurves for location and rotation_quaternion
                        for i in range(3):  # Location has 3 components: X, Y, Z
                            fcurves[bone_name]['location'].append(action.fcurves.new(data_path=f'pose.bones["{bone_name}"].location', index=i))

                        for i in range(4):  # Rotation quaternion has 4 components: W, X, Y, Z
                            fcurves[bone_name]['rotation_quaternion'].append(action.fcurves.new(data_path=f'pose.bones["{bone_name}"].rotation_quaternion', index=i))

                    # Retrieve the initial translation and rotation from the armature creation data
                    corresponding_bone = next((b for b in armature_data['bones'] if b['name'] == bone_name), None)
                    if corresponding_bone:
                        track_name = corresponding_bone['track']
                        initial_transform = armature_tracks[track_name]['definition']['frame_transforms'][0]
                        armature_translation = initial_transform.get('translation', [0, 0, 0])
                        armature_rotation = initial_transform.get('rotation', Quaternion((1, 0, 0, 0)))

                        # Debugging: Print the initial translation and rotation
#                        print(f"Bone '{bone_name}' initial translation from armature creation: {armature_translation}")
#                        print(f"Bone '{bone_name}' initial rotation from armature creation (Quaternion): {armature_rotation}")

                    # Insert keyframes for each frame
                    for frame_index, frame in enumerate(track['frame_transforms']):
                        # Debugging: Print the frame data
#                        print(f"Processing frame {frame_index + 1} for bone '{bone_name}' in animation '{action_name}':")
#                        print(f"  Translation: {frame.get('translation')}")
#                        print(f"  Rotation: {frame.get('rotation')}")

                        # Adjust the translation by subtracting the armature's initial translation
                        location = [frame.get('translation', [0, 0, 0])[i] - armature_translation[i] for i in range(3)]

                        # Adjust the rotation by multiplying with the conjugate of the initial armature rotation
                        frame_rotation = Quaternion(frame.get('rotation', [1, 0, 0, 0]))
                        adjusted_rotation = armature_rotation.conjugated() @ frame_rotation

                        # Insert location keyframes
                        for i, value in enumerate(location):
                            fcurve = fcurves[bone_name]['location'][i]
                            kf = fcurve.keyframe_points.insert(frame_index + 1, value)
                            kf.interpolation = 'LINEAR'

                        # Insert rotation keyframes
                        for i, value in enumerate(adjusted_rotation):
                            fcurve = fcurves[bone_name]['rotation_quaternion'][i]
                            kf = fcurve.keyframe_points.insert(frame_index + 1, value)
                            kf.interpolation = 'LINEAR'

        # Debugging: Scan the created animation and count keyframes
#        print(f"Created animation '{action_name}' with {len(tracks)} tracks.")
#        total_keyframes = 0
#        for fcurve in action.fcurves:
#            num_keyframes = len(fcurve.keyframe_points)
#            total_keyframes += num_keyframes
#            print(f"FCurve for data path '{fcurve.data_path}', index {fcurve.array_index} has {num_keyframes} keyframes.")

#        print(f"Total keyframes in '{action_name}': {total_keyframes}\n")


# Create armature and link it to the main object if armature data is available
if armature_data and track_definitions:
    armature_tracks = track_definitions['armature_tracks']
    armature_obj, bone_map, cumulative_matrices = create_armature(armature_data, armature_tracks, main_obj)
    
    for mesh_data in meshes:
        mesh_obj = create_mesh(mesh_data, main_obj, armature_obj, cumulative_matrices)
    
    # Pass armature_data to the create_animation function
    create_animation(armature_obj, track_definitions, armature_data)
else:
    # If no armature data, just create meshes
    for mesh_data in meshes:
        mesh_obj = create_mesh(mesh_data, main_obj)

# Parent polyhedron to matching DMSPRITEDEF mesh
for polyhedron_name, polyhedron_obj in polyhedron_objects.items():
    actual_polyhedron_name = polyhedron_obj.name  # Access the actual Blender name of the polyhedron object
    base_name = actual_polyhedron_name.split('.')[0]  # Get the base name without the suffix
    appendix = actual_polyhedron_name.split('.')[-1] if '.' in actual_polyhedron_name else ''
    
    print(f"Polyhedron Name: '{actual_polyhedron_name}', Base Name: '{base_name}', Appendix: '{appendix}'")
    
    for mesh_data in meshes:
        if mesh_data.get('polyhedron') == base_name:
            # Look for the mesh object with the same appendix
            mesh_name_with_appendix = f"{mesh_data['name']}.{appendix}" if appendix else mesh_data['name']
            mesh_obj = bpy.data.objects.get(mesh_name_with_appendix)
            if mesh_obj:
                print(f"Matching mesh found: {mesh_obj.name} for polyhedron: {actual_polyhedron_name}")
                polyhedron_obj.parent = mesh_obj
                break  # Stop searching once the correct parent is found

print("Created object '{}' with {} meshes and armature '{}'".format(base_name, len(meshes), armature_data['name'] if armature_data else "None"))
print("Included files:", include_files)  # Print the list of include files for reference