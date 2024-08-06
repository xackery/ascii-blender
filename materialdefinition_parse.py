def materialdefinition_parse(lines):
    materials = []
    current_material = None
    in_simple_sprite_inst = False

    for line in lines:
        line = line.strip()

        if line.startswith("TAG") and not in_simple_sprite_inst:
            if current_material:
                materials.append(current_material)
            current_material = {
                'name': line.split('"')[1],
                'rendermethod': '',
                'rgbpen': (1.0, 1.0, 1.0),
                'brightness': 0.0,
                'scaledambient': 0.75,
                'texture_tag': ''
            }
        elif current_material is not None:
            if line.startswith("RENDERMETHOD"):
                current_material['rendermethod'] = " ".join(line.split()[1:])
            elif line.startswith("RGBPEN"):
                parts = line.split()
                current_material['rgbpen'] = (int(parts[1]) / 255.0, int(parts[2]) / 255.0, int(parts[3]) / 255.0)
            elif line.startswith("BRIGHTNESS"):
                current_material['brightness'] = float(line.split()[1])
            elif line.startswith("SCALEDAMBIENT"):
                current_material['scaledambient'] = float(line.split()[1])
            elif line.startswith("SIMPLESPRITEINST"):
                in_simple_sprite_inst = True
            elif line.startswith("ENDSIMPLESPRITEINST"):
                in_simple_sprite_inst = False
            elif in_simple_sprite_inst and line.startswith("TAG"):
                current_material['texture_tag'] = line.split('"')[1]

    if current_material:
        materials.append(current_material)
    
    return materials
