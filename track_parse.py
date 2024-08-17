import bpy
import re
import mathutils

# Define the list of animation prefixes
animation_prefixes = [
    "C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10", "C11",
    "D01", "D02", "D03", "D04", "D05", "L01", "L02", "L03", "L04", "L05", "L06", "L07", "L08", "L09",
    "O01", "S01", "S02", "S03", "S04", "S05", "P01", "P02", "P03", "P04", "P05", "P06", "P07",
    "T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09", "S06", "S07", "S08", "S09", "S10",
    "S11", "S12", "S13", "S14", "S15", "S16", "S17", "S18", "S19", "S20", "S21", "S22", "S23", "S24",
    "S25", "S26", "S27", "S28", "P08", "O02", "O03"
]

# Create a new list that includes the variants with "A" and "B"
animation_prefix_variants = animation_prefixes + [prefix + "A" for prefix in animation_prefixes] + [prefix + "B" for prefix in animation_prefixes]

def generate_unique_name(base_name, existing_names):
    if base_name not in existing_names:
        return base_name
    
    suffix = 1
    while True:
        new_name = f"{base_name}.{suffix:03d}"
        if new_name not in existing_names:
            return new_name
        suffix += 1

def process_track_definition(lines, existing_track_definitions):
    track_def = {
        'name': '',
        'num_frames': 0,
        'frame_transforms': []
    }
    
    frame_transform = None

    for line in lines:
        if line.startswith("TAG") and not line.startswith("TAGINDEX"):
            base_name = line.split('"')[1]
            track_def['name'] = generate_unique_name(base_name, existing_track_definitions)
            existing_track_definitions.add(track_def['name'])
        elif line.startswith("NUMFRAMES"):
            track_def['num_frames'] = int(line.split()[1])
        elif line.startswith("FRAMETRANSFORM"):
            frame_transform = {
                'translation': None,
                'rotation': None
            }
        elif line.startswith("XYZSCALE"):
            xyz_scale = float(line.split()[1])
        elif line.startswith("XYZ"):
            parts = line.split()
            tx = float(parts[1]) / xyz_scale
            ty = float(parts[2]) / xyz_scale
            tz = float(parts[3]) / xyz_scale
            frame_transform['translation'] = (tx, ty, tz)
        elif line.startswith("ROTSCALE?"):
            rot_scale = float(line.split()[1])
        elif line.startswith("ROTABC?"):
            parts = line.split()
            rx = float(parts[1])
            ry = float(parts[2])
            rz = float(parts[3])
            rotation = mathutils.Quaternion((rot_scale, rx, ry, rz))
            rotation.normalize()
#            print(f"Quaternion: {rotation}")  # Print out the quaternion
            frame_transform['rotation'] = rotation
        elif line.startswith("ENDFRAMETRANSFORM"):
            if frame_transform:
                track_def['frame_transforms'].append(frame_transform)

    return track_def

def process_track_instance(lines, existing_track_instances, track_def_suffixes):
    track_instance = {
        'name': '',
        'definition': '',
        'interpolate': False,
        'sleep': 0
    }
    
    for line in lines:
        if line.startswith("TAG") and not line.startswith("TAGINDEX"):
            base_name = line.split('"')[1]
            track_instance['name'] = generate_unique_name(base_name, existing_track_instances)
            existing_track_instances.add(track_instance['name'])
        elif line.startswith("DEFINITION") and not line.startswith("DEFINITIONINDEX"):
            base_name = line.split('"')[1]
            if base_name in track_def_suffixes:
                suffix = track_def_suffixes[base_name]
                new_definition_name = f"{base_name}.{suffix:03d}"
                track_instance['definition'] = new_definition_name
                track_def_suffixes[base_name] += 1
            else:
                track_instance['definition'] = base_name
                track_def_suffixes[base_name] = 1
        elif line.startswith("INTERPOLATE"):
            track_instance['interpolate'] = bool(int(line.split()[1]))
        elif line.startswith("SLEEP?"):
            track_instance['sleep'] = int(line.split()[1]) if line.split()[1] != "NULL" else None

    return track_instance

def track_parse(sections, base_name):
    track_definitions = {}
    animations = {}
    armature_tracks = {}

    existing_track_definitions = set()
    existing_track_instances = set()
    track_def_suffixes = {}

    for instance in sections.get('TRACKDEFINITION', []):
        track_def = process_track_definition(instance, existing_track_definitions)
        track_definitions[track_def['name']] = track_def

    for instance in sections.get('TRACKINSTANCE', []):
        track_instance = process_track_instance(instance, existing_track_instances, track_def_suffixes)
        definition_name = track_instance['definition']

        track_def = track_definitions.get(definition_name)

        if track_def:
            # Extract the part before the base_name for comparison
            if base_name in track_instance['name']:
                prefix_part = track_instance['name'].split(base_name)[0]

                # Perform an exact match with the animation prefix variants
                if prefix_part in animation_prefix_variants:
                    animations[track_instance['name']] = {
                        'instance': track_instance,
                        'definition': track_def,
                        'animation_prefix': prefix_part  # Store the animation prefix
                    }
                    # Debugging: Ensure the prefix is stored correctly
                    print(f"Stored animation prefix '{prefix_part}' for track '{track_instance['name']}'")
                else:
                    armature_tracks[track_instance['name']] = {
                        'instance': track_instance,
                        'definition': track_def
                    }

    return {'animations': animations, 'armature_tracks': armature_tracks}

def build_animation(armature_obj, animations, frame_rate=30):
    for anim_name, anim_data in animations.items():
        track_instance = anim_data['instance']
        track_definition = anim_data['definition']
        animation_prefix = anim_data.get('animation_prefix', 'Unknown')
        num_frames = track_definition['num_frames']

        # Debugging: Print the animation prefix
        print(f"Building animation '{anim_name}' with prefix '{animation_prefix}'")

        # Create a new action for the animation
        action = bpy.data.actions.new(name=anim_name)
        armature_obj.animation_data_create()
        armature_obj.animation_data.action = action

        # Build the animation
        current_frame = 0
        for i, frame_transform in enumerate(track_definition['frame_transforms']):
            current_frame += (track_instance['sleep'] or 100) / 1000.0 * frame_rate
            frame = round(current_frame)

            for bone_name, bone in armature_obj.pose.bones.items():
                if bone_name in track_instance['name']:
                    bone.location = frame_transform['translation']
                    bone.rotation_quaternion = frame_transform['rotation']
                    bone.keyframe_insert(data_path="location", frame=frame)
                    bone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                    break

        print(f"Animation '{anim_name}' created with {num_frames} frames.")

# Example usage after parsing the sections:
# base_name = "FRO"  # Replace with the actual base name from your model
# track_data = track_parse(sections, base_name)
# build_animation(armature_obj, track_data['animations'], frame_rate=30)
