def material_palette_parse(instance):
    palette = {
        'name': '',
        'materials': []
    }
    for line in instance:
        if line.startswith("TAG"):
            palette['name'] = line.split('"')[1]
        elif line.startswith("NUMMATERIALS"):
            palette['num_materials'] = int(line.split()[1])
        elif line.startswith("MATERIAL"):
            if 'materials' not in palette:
                palette['materials'] = []
            palette['materials'].append(line.split('"')[1])
    return palette