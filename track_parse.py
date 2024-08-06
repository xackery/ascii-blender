import re
from calculations import euler_to_quaternion

# Define the list of animation prefixes
animation_prefixes = [
    "C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10", "C11",
    "D01", "D02", "D03", "D04", "D05", "L01", "L02", "L03", "L04", "L05", "L06", "L07", "L08", "L09",
    "O01", "S01", "S02", "S03", "S04", "S05", "P01", "P02", "P03", "P04", "P05", "P06", "P07",
    "T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09", "S06", "S07", "S08", "S09", "S10",
    "S11", "S12", "S13", "S14", "S15", "S16", "S17", "S18", "S19", "S20", "S21", "S22", "S23", "S24",
    "S25", "S26", "S27", "S28", "P08", "O02", "O03"
]

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
        'frame_transforms': [],
        'location_denominator': None
    }
    
    for line in lines:
        if line.startswith("TAG"):
            base_name = line.split('"')[1]
            track_def['name'] = generate_unique_name(base_name, existing_track_definitions)
            existing_track_definitions.add(track_def['name'])
        elif line.startswith("NUMFRAMES"):
            track_def['num_frames'] = int(line.split()[1])
        elif line.startswith("FRAMETRANSFORM"):
            parts = line.split()
            loc_denom = float(parts[1])
            z = int(parts[2])
            y = int(parts[3])
            x = int(parts[4])
            tx = float(parts[5]) / loc_denom
            ty = float(parts[6]) / loc_denom
            tz = float(parts[7]) / loc_denom
            rotation = euler_to_quaternion(x, y, z)
            frame_transform = {
                'rotation': rotation,
                'translation': (tx, ty, tz)
            }
            track_def['frame_transforms'].append(frame_transform)
            track_def['location_denominator'] = loc_denom

    return track_def

def process_track_instance(lines, existing_track_instances, track_def_suffixes):
    track_instance = {
        'name': '',
        'definition': '',
        'interpolate': False,
        'sleep': 0
    }
    
    for line in lines:
        if line.startswith("TAG"):
            base_name = line.split('"')[1]
            track_instance['name'] = generate_unique_name(base_name, existing_track_instances)
            existing_track_instances.add(track_instance['name'])
        elif line.startswith("DEFINITION"):
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
            track_instance['interpolate'] = True
        elif line.startswith("SLEEP"):
            track_instance['sleep'] = int(line.split()[1])

    return track_instance

def track_parse(sections):
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
            if any(track_instance['name'].startswith(prefix) for prefix in animation_prefixes):
                animations[track_instance['name']] = {
                    'instance': track_instance,
                    'definition': track_def
                }
            else:
                armature_tracks[track_instance['name']] = {
                    'instance': track_instance,
                    'definition': track_def
                }

    return {'animations': animations, 'armature_tracks': armature_tracks}

# Example usage
#sections = {
    #'TRACKDEFINITION': [
        # Add track definition lines here
    #],
    #'TRACKINSTANCE': [
        # Add track instance lines here
   # ]
#}

#track_data = track_parse(sections)
#print("Parsed track data:")
#print(track_data)
