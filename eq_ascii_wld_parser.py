import os
import sys

# Manually set the directory containing your scripts
script_dir = r'C:\Users\dariu\Documents\Quail\Importer'  # Replace with the actual path
print(f"Script directory: {script_dir}")  # Check the path
if script_dir not in sys.path:
    sys.path.append(script_dir)

from main_parse import main_parse
from material_palette_parse import material_palette_parse
from dmspritedef2_parse import dmspritedef2_parse
from hierarchicalspritedef_parse import hierarchicalspritedef_parse
from track_parse import track_parse
from polyhedrondefinition_parse import polyhedrondefinition_parse

def eq_ascii_parse(filepath):
    sections, includes = main_parse(filepath)
    
    # Print out the sections for debugging
    #print("\nSections:")
    #for section, instances in sections.items():
        #print(f"Section: {section}")
        #for instance in instances:
            #print("Instance:", instance)

    # Parse material palettes
    material_palettes = {}
    for instance in sections.get('MATERIALPALETTE', []):
        material_palette = material_palette_parse(instance)
        if material_palette['name']:
            material_palettes[material_palette['name']] = material_palette['materials']

    # Parse DMSPRITEDEF2 sections
    meshes = []
    for instance in sections.get('DMSPRITEDEF2', []):
        dmspritedef2, inner_sections = dmspritedef2_parse(instance)
        meshes.append(dmspritedef2)
    
    # Parse HIERARCHICALSPRITEDEF sections
    armature_data = None
    for instance in sections.get('HIERARCHICALSPRITEDEF', []):
        armature_data = hierarchicalspritedef_parse(instance)
    
    # Parse POLYHEDRONDEFINITION sections
    polyhedrons = []
    for instance in sections.get('POLYHEDRONDEFINITION', []):
        print(f"Polyhedron Instance: {instance}")  # Debug print to check instance content
        polyhedron = polyhedrondefinition_parse(instance)
        polyhedrons.append(polyhedron)

    # Parse track definitions and instances
    track_definitions = track_parse(sections)
    
    return meshes, armature_data, track_definitions, material_palettes, includes, polyhedrons

if __name__ == '__main__':
    # Example usage:
    filepath = 'C:\\Users\\dariu\\Documents\\Quail\\pre.spk'
    meshes, armature_data, track_definitions, material_palettes, include_files, polyhedrons = eq_ascii_parse(filepath)

    # Print out the includes
    print("Includes:")
    for include in include_files:
        print(f"  {include}")

    print("\nMaterial Palettes:")
    for name, materials in material_palettes.items():
        print(f"Palette: {name}")
        for material in materials:
            print(f"  Material: {material}")

    print("\nDMSPRITEDEF2 Sections:")
    for dmspritedef2 in meshes:
        print(dmspritedef2)
    
    print("\nHIERARCHICALSPRITEDEF Sections:")
    print(armature_data)

    print("\nTRACKDEFINITION and TRACKINSTANCE Sections:")
    print(track_definitions)

    print("\nPOLYHEDRONDEFINITION Sections:")
    for polyhedron in polyhedrons:
        print(polyhedron)
