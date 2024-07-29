def polyhedrondefinition_parse(lines):
    polyhedron = {
        'name': '',
        'bounding_radius': 0.0,
        'scale_factor': 1.0,
        'vertices': [],
        'faces': []
    }

    current_face = None
    num_vertices = 0
    num_faces = 0

    line_index = 0
    while line_index < len(lines):
        line = lines[line_index].strip()
        print(f"Processing line: {line}")  # Debug print to check each line

        if line.startswith("TAG"):
            polyhedron['name'] = line.split('"')[1]
        elif line.startswith("BOUNDINGRADIUS"):
            polyhedron['bounding_radius'] = float(line.split()[1])
        elif line.startswith("SCALEFACTOR"):
            polyhedron['scale_factor'] = float(line.split()[1])
        elif line.startswith("NUMVERTICES"):
            num_vertices = int(line.split()[1])
            print(f"Parsing {num_vertices} vertices")
        elif line.startswith("XYZ") and num_vertices > 0:
            vertices = list(map(float, line.split()[1:]))
            polyhedron['vertices'].append(vertices)
            num_vertices -= 1
            print(f"Added vertex: {vertices}")
        elif line.startswith("NUMFACES"):
            num_faces = int(line.split()[1])
            print(f"Parsing {num_faces} faces")
        elif line.startswith("FACE"):
            current_face = {
                'num_vertices': 0,
                'vertex_list': []
            }
        elif line.startswith("NUMVERTICES") and current_face is not None:
            current_face['num_vertices'] = int(line.split()[1])
        elif line.startswith("VERTEXLIST") and current_face is not None:
            vertex_list = [int(v.strip(',')) - 1 for v in line.split()[1:]]
            current_face['vertex_list'] = vertex_list
            print(f"Added face: {vertex_list}")
        elif line.startswith("ENDFACE") and current_face is not None:
            polyhedron['faces'].append(current_face)
            current_face = None

        line_index += 1

    return polyhedron

# Example usage
if __name__ == '__main__':
    lines = [
        # Add your test lines here for example usage
    ]

    polyhedron = polyhedrondefinition_parse(lines)
    print("POLYHEDRONDEFINITION Sections:")
    print(polyhedron)
