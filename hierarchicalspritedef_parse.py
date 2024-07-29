def process_dag_section(lines, bone_index, existing_bone_names, track_suffix_map):
    bone_data = {
        'name': '',
        'track': None,
        'num_subdags': 0,
        'subdag_list': [],
        'sprite': None
    }
    relationships = []

    line_index = 0
    while line_index < len(lines):
        line = lines[line_index].strip()
        print(f"Processing DAG line: {line}")  # Debug print

        if line.startswith("TAG"):
            base_name = line.split('"')[1]
            # Ensure unique bone name
            if base_name in existing_bone_names:
                suffix = 1
                new_name = f"{base_name}.{suffix:03d}"
                while new_name in existing_bone_names:
                    suffix += 1
                    new_name = f"{base_name}.{suffix:03d}"
                bone_data['name'] = new_name
                track_suffix_map[base_name] = suffix
            else:
                bone_data['name'] = base_name
                track_suffix_map[base_name] = 0
            existing_bone_names.add(bone_data['name'])
        elif line.startswith("NULLSPRITE"):
            bone_data['sprite'] = None
        elif line.startswith("DMSPRITE"):
            bone_data['sprite'] = line.split('"')[1]
        elif line.startswith("TRACK"):
            base_track = line.split('"')[1]
            # Only append suffix if bone name was modified
            if bone_data['name'] != base_name:
                suffix = track_suffix_map[base_name]
                new_track = f"{base_track}.{suffix:03d}"
                bone_data['track'] = new_track
            else:
                bone_data['track'] = base_track
        elif line.startswith("NUMSUBDAGS"):
            bone_data['num_subdags'] = int(line.split()[1])
        elif line.startswith("SUBDAGLIST"):
            subdag_list = [int(x.strip(',')) - 1 for x in line.split()[1:]]
            bone_data['subdag_list'] = subdag_list
            relationships.append((bone_index, subdag_list))
        elif line.startswith("ENDDAG"):
            break

        line_index += 1

    return bone_data, relationships

def hierarchicalspritedef_parse(lines):
    armature_data = {
        'name': '',
        'bones': [],
        'relationships': [],
        'attached_skins': [],
        'center_offset': [],
        'bounding_radius': None,
        'dag_collisions': False
    }

    current_section = None
    num_dags = 0
    num_attached_skins = 0
    existing_bone_names = set()
    track_suffix_map = {}

    line_index = 0
    bone_index = 0

    while line_index < len(lines):
        line = lines[line_index].strip()
        print(f"Parsing line: {line}")  # Debugging statement

        if line.startswith("TAG "):
            armature_data['name'] = line.split('"')[1]
        elif line.startswith("NUMDAGS "):
            num_dags = int(line.split()[1])
        elif line == "DAG":  # Explicitly check for "DAG " or "DAG"
            dag_lines = []
            while line_index < len(lines) and not lines[line_index].startswith("ENDDAG"):
                dag_lines.append(lines[line_index])
                line_index += 1
            if line_index < len(lines):  # Add the ENDDAG line
                dag_lines.append(lines[line_index])
            bone_data, relationships = process_dag_section(dag_lines, bone_index, existing_bone_names, track_suffix_map)
            armature_data['bones'].append(bone_data)
            armature_data['relationships'].extend(relationships)
            bone_index += 1
        elif line.startswith("NUMATTACHEDSKINS "):
            num_attached_skins = int(line.split()[1])
        elif line.startswith("DMSPRITE ") and num_attached_skins > 0:
            attached_skin = {
                'sprite': line.split('"')[1],
                'link_skin_updates_to_dag_index': None
            }
            armature_data['attached_skins'].append(attached_skin)
            num_attached_skins -= 1
        elif line.startswith("LINKSKINUPDATESTODAGINDEX "):
            armature_data['attached_skins'][-1]['link_skin_updates_to_dag_index'] = int(line.split()[1])
        elif line.startswith("CENTEROFFSET "):
            armature_data['center_offset'] = list(map(float, line.split()[1:]))
        elif line.startswith("DAGCOLLISIONS"):
            armature_data['dag_collisions'] = True
            print(f"DAGCOLLISIONS set to True")  # Debugging statement
        elif line.startswith("BOUNDINGRADIUS "):
            armature_data['bounding_radius'] = float(line.split()[1])
            print(f"BOUNDINGRADIUS set to {armature_data['bounding_radius']}")  # Debugging statement
        elif line.startswith("ENDHIERARCHICALSPRITEDEF"):
            break

        line_index += 1

    return armature_data

# Example usage
lines = [
    # Add your input lines here
]

armature_data = hierarchicalspritedef_parse(lines)
print("HIERARCHICALSPRITEDEF Sections:")
print(armature_data)
