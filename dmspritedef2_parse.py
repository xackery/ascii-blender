import bpy
import bmesh
import mathutils
import os
import sys

def process_skin_assignment_groups(data_string):
    parts = data_string.split()
    num_groups = int(parts[0])
    group_data = parts[1:]  # Directly split without joining, assuming no commas

    vertex_groups = []
    vertex_start = 0
    for i in range(num_groups):
        num_vertices = int(group_data[i * 2].strip())
        bone_index = int(group_data[i * 2 + 1].strip())  # Adjust bone index to be zero-based
        vertex_end = vertex_start + num_vertices
        vertex_groups.append((vertex_start, vertex_end, bone_index))
        vertex_start = vertex_end

    return vertex_groups

def process_face_material_groups(data_string):
    parts = data_string.split()
    num_groups = int(parts[0])
    group_data = parts[1:]  # Directly split without joining, assuming no commas

    face_material_groups = []
    face_start = 0
    for i in range(num_groups):
        num_faces = int(group_data[i * 2].strip())
        material_index = int(group_data[i * 2 + 1].strip())  # Adjust material index to be zero-based
        face_end = face_start + num_faces
        face_material_groups.append((face_start, face_end, material_index))
        face_start = face_end

    return face_material_groups

def process_vertex_material_groups(data_string):
    parts = data_string.split()
    num_groups = int(parts[0])
    group_data = parts[1:]  # Directly split without joining, assuming no commas

    vertex_material_groups = []
    vertex_start = 0
    for i in range(num_groups):
        num_vertices = int(group_data[i * 2].strip())
        material_index = int(group_data[i * 2 + 1].strip())  # Adjust material index to be zero-based
        vertex_end = vertex_start + num_vertices
        vertex_material_groups.append((vertex_start, vertex_end, material_index))
        vertex_start = vertex_end

    return vertex_material_groups

def process_dmtrack(data_lines):
    for line in data_lines:
        if line.startswith("DEFINITION"):
            return line.split('"')[1]
    return None

def process_polyhedron(data_lines):
    for line in data_lines:
        if line.startswith("DEFINITION"):
            return line.split('"')[1]
    return None

def dmspritedef2_parse(lines):
    mesh = {}
    vertices = []
    uvs = []
    normals = []
    colors = []  # To store RGBA colors
    faces = []
    meshops = []
    num_vertices = 0
    num_uvs = 0
    num_normals = 0
    num_colors = 0  # Number of RGBA entries
    num_faces = 0
    num_meshops = 0
    current_face = None
    face_no_collision = False  # Flag to indicate if the current face has no collision
    dmsprite_sections = {}
    current_section = None
    dmtrack_data = []
    polyhedron_data = []
    bounding_box_data = []
    keywords = [
        "BOUNDINGBOXMIN",
        "BOUNDINGBOXMAX",
        "BOUNDINGRADIUS",
        "CENTEROFFSET",
        "DMTRACK",
        "FACEMATERIALGROUPS",
        "FPSCALE",
        "MATERIALPALETTE",
        "NUMFACE2S",
        "NUMMESHOPS",
        "NUMUVS",
        "NUMVERTEXNORMALS",
        "NUMVERTEXCOLORS",
        "PARAMS2",
        "POLYHEDRON",
        "REGIONPOLYHEDRON",
        "SKINASSIGNMENTGROUPS",
        "SPRITEDEFPOLYHEDRON",
        "TAG",
        "VERTEXMATERIALGROUPS"
    ]

    line_index = 0
    while line_index < len(lines):
        line = lines[line_index]

        if line.startswith("TAG"):
            mesh['name'] = line.split('"')[1]
        elif line.startswith("CENTEROFFSET"):
            mesh['center_offset'] = list(map(float, line.split()[1:]))
        elif line.startswith("NUMVERTICES"):
            num_vertices = int(line.split()[1])
        elif line.startswith("XYZ") and num_vertices > 0:
            vertices.append(list(map(float, line.split()[1:])))
            num_vertices -= 1
        elif line.startswith("NUMUVS"):
            num_uvs = int(line.split()[1])
        elif line.startswith("UV") and num_uvs > 0:
            parts = line.split()
            u = float(parts[1])
            v = float(parts[2])
            uvs.append((u, v))
            num_uvs -= 1
        elif line.startswith("NUMVERTEXNORMALS"):
            num_normals = int(line.split()[1])
        elif line.startswith("XYZ") and num_normals > 0:
            normals.append(list(map(float, line.split()[1:])))
            num_normals -= 1
        elif line.startswith("NUMVERTEXCOLORS"):
            num_colors = int(line.split()[1])
        elif line.startswith("RGBA") and num_colors > 0:
            parts = line.split()
            r = int(parts[1]) / 255.0
            g = int(parts[2]) / 255.0
            b = int(parts[3]) / 255.0
            a = int(parts[4]) / 255.0
            colors.append((r, g, b, a))
            num_colors -= 1
        elif line.startswith("NUMFACE2S"):
            num_faces = int(line.split()[1])
        elif line.startswith("DMFACE2") and num_faces > 0:
            face = []
            face_no_collision = False  # Reset the collision flag for each new face
        elif line.startswith("TRIANGLE"):
            parts = line.split()
            v1 = int(parts[1].strip(","))  # 0-based now
            v2 = int(parts[2].strip(","))  # 0-based now
            v3 = int(parts[3])  # 0-based now
            current_face = (v3, v2, v1, face_no_collision)  # Add the no collision flag to the face tuple
            faces.append(current_face)
            num_faces -= 1
        elif line.startswith("PASSABLE"):
            face_no_collision = True  # Set the flag if the current face has no collision
        elif line.startswith("ENDDMFACE2"):
            if current_face is not None:
                faces[-1] = (faces[-1][0], faces[-1][1], faces[-1][2], face_no_collision)  # Update the last face with the no collision flag
        elif line.startswith("NUMMESHOPS"):
            num_meshops = int(line.split()[1])
        elif any(line.startswith(op) for op in ["MESHOP_VA", "MESHOP_SW", "MESHOP_EL", "MESHOP_FA"]):
            parts = line.split()
            meshops.append(parts)
        elif line.startswith("FACEMATERIALGROUPS"):
            current_section = "FACEMATERIALGROUPS"
            if current_section not in dmsprite_sections:
                dmsprite_sections[current_section] = []
            dmsprite_sections[current_section].append(line.split(current_section)[1].strip())
        elif line.startswith("VERTEXMATERIALGROUPS"):
            current_section = "VERTEXMATERIALGROUPS"
            if current_section not in dmsprite_sections:
                dmsprite_sections[current_section] = []
            dmsprite_sections[current_section].append(line.split(current_section)[1].strip())
        elif line.startswith("SKINASSIGNMENTGROUPS"):
            current_section = "SKINASSIGNMENTGROUPS"
            if current_section not in dmsprite_sections:
                dmsprite_sections[current_section] = []
            dmsprite_sections[current_section].append(line.split(current_section)[1].strip())
        elif line.startswith("MATERIALPALETTE"):
            palette_name = line.split('"')[1]
            mesh['material_palette'] = palette_name
        elif line.startswith("BOUNDINGRADIUS"):
            mesh['bounding_radius'] = float(line.split()[1])
        elif line.startswith("BOUNDINGBOXMIN"):
            current_section = "BOUNDINGBOX"
            bounding_box_data = []
            bounding_box_data.append(list(map(float, line.split()[1:])))
        elif line.startswith("BOUNDINGBOXMAX"):
            bounding_box_data.append(list(map(float, line.split()[1:])))
            mesh['bounding_box'] = bounding_box_data
            current_section = None
        elif line.startswith("DMTRACK"):
            current_section = "DMTRACK"
            dmtrack_data = []
        elif line.startswith("ENDDMTRACK"):
            mesh['dmtrack'] = process_dmtrack(dmtrack_data)
            current_section = None
        elif line.startswith("POLYHEDRON"):
            current_section = "POLYHEDRON"
            polyhedron_data = []
        elif line.startswith("ENDPOLYHEDRON"):
            mesh['polyhedron'] = process_polyhedron(polyhedron_data)
            current_section = None
        elif line.startswith("SPRITEDEFPOLYHEDRON"):
            mesh['has_spritedefpolyhedron'] = True
        elif line.startswith("REGIONPOLYHEDRON"):
            mesh['has_regionpolyhedron'] = True
        elif line.startswith("PARAMS2"):
            mesh['params2'] = list(map(float, line.split()[1:]))
        elif current_section and any(line.startswith(keyword) for keyword in keywords):
            current_section = None
            continue  # Re-process the current line by skipping the increment
        elif current_section:
            if current_section == "DMTRACK":
                dmtrack_data.append(line.strip())
            elif current_section == "POLYHEDRON":
                polyhedron_data.append(line.strip())
            else:
                dmsprite_sections[current_section][-1] += " " + line.strip()

        line_index += 1  # Increment the line index

    # Process SKINASSIGNMENTGROUPS and add to mesh data
    if "SKINASSIGNMENTGROUPS" in dmsprite_sections:
        skin_assignment_data = ' '.join(dmsprite_sections["SKINASSIGNMENTGROUPS"])
        mesh['vertex_groups'] = process_skin_assignment_groups(skin_assignment_data)

    # Process FACEMATERIALGROUPS and add to mesh data
    if "FACEMATERIALGROUPS" in dmsprite_sections:
        face_material_data = ' '.join(dmsprite_sections["FACEMATERIALGROUPS"])
        mesh['face_materials'] = process_face_material_groups(face_material_data)

    # Process VERTEXMATERIALGROUPS and add to mesh data
    if "VERTEXMATERIALGROUPS" in dmsprite_sections:
        vertex_material_data = ' '.join(dmsprite_sections["VERTEXMATERIALGROUPS"])
        mesh['vertex_materials'] = process_vertex_material_groups(vertex_material_data)

    mesh['vertices'] = vertices
    mesh['uvs'] = uvs
    mesh['normals'] = normals
    mesh['colors'] = colors  # Add vertex colors to mesh data
    mesh['faces'] = faces
    mesh['meshops'] = meshops

    return mesh, dmsprite_sections
