def simplespritedef_parse(lines):
    textures = {}
    current_texture = None
    for line in lines:
        line = line.strip()
        if line.startswith("SIMPLESPRITETAG"):
            current_texture = {'name': '', 'file': ''}
            current_texture['name'] = line.split('"')[1]
        elif line.startswith("BMINFO"):
            parts = line.split('"')
            if len(parts) > 3:
                current_texture['file'] = parts[3].strip()
                textures[current_texture['name']] = current_texture['file']
            current_texture = None
    return textures
