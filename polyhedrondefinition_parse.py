def polyhedrondefinition_parse(lines):
    polyhedron = {
        'name': '',
        'bounding_radius': 0.0,
        'scale_factor': 1.0,
        'vertices': [],
        'faces': []
    }

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
        elif line.startswith("VERTEXLIST"):
            # Parse the vertex list directly from the line
            data = list(map(int, line.split()[1:]))
            num_vertices_in_face = data[0]
            vertex_list = data[1:num_vertices_in_face + 1]  # Extract the vertex indices for the face

            # Add the face to the polyhedron's face list
            face = {
                'num_vertices': num_vertices_in_face,
                'vertex_list': vertex_list
            }
            polyhedron['faces'].append(face)
            print(f"Added face: {face}")

        line_index += 1

    return polyhedron

# Example usage
if __name__ == '__main__':
    lines = [
        'TAG "example_polyhedron"',
        'BOUNDINGRADIUS 5.0',
        'SCALEFACTOR 1.0',
        'NUMVERTICES 5',
        'XYZ 0.0 0.0 0.0',
        'XYZ 1.0 0.0 0.0',
        'XYZ 1.0 1.0 0.0',
        'XYZ 0.0 1.0 0.0',
        'XYZ 0.5 0.5 1.0',
        'NUMFACES 3',
        'VERTEXLIST 3 0 1 2',
        'VERTEXLIST 3 2 3 4',
        'VERTEXLIST 3 0 4 1'
    ]

    polyhedron = polyhedrondefinition_parse(lines)
    print("POLYHEDRONDEFINITION Sections:")
    print(polyhedron)
