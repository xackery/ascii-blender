import re

def simplespritedef_parse(lines):
    textures = {}
    current_texture = None
    current_frames = []
    sleep_time = None
    animated_frame_count = 0
    tiled_frame_count = 0  # Variable to keep track of the number of "tiled" frames

    # Regular expression to check for a number before the file extension
    animated_frame_regex = re.compile(r'.*\d(?=\.[a-zA-Z]+$)')

    for line in lines:
        line = line.strip()
        print(f"Processing line: {line}")

        if line.startswith("SIMPLESPRITETAG"):
            # Store the previous texture data if any
            if current_texture:
                current_texture['num_tiled_frames'] = tiled_frame_count  # Save the count of tiled frames
                textures[current_texture['name']] = current_texture
                print(f"Added texture to dictionary: {current_texture['name']}")

            # Initialize new texture data
            current_texture = {
                'name': line.split('"')[1],
                'frames': [],
                'animated': False,
                'sleep': 'NULL',
                'number_frames': 0,
                'frame_files': [],
                'properties': [],
                'num_tiled_frames': 0,  # Initialize num_tiled_frames for the new texture
                'palette_mask_file': None  # Initialize the palette_mask_file key
            }
            print(f"Started new SIMPLESPRITEDEF: {current_texture['name']}")
            current_frames = []
            animated_frame_count = 0
            tiled_frame_count = 0  # Reset tiled frame count for new texture
            sleep_time = 'NULL'

        elif line.startswith("SLEEP?"):
            sleep_value = line.split('?')[1].strip()
            if sleep_value == "NULL":
                sleep_time = "NULL"
                current_texture['animated'] = False
            elif sleep_value.isdigit():
                sleep_time = float(sleep_value) / 1000.0
                current_texture['sleep'] = sleep_time
                # Set animated to True only if sleep_time is greater than 0
                current_texture['animated'] = sleep_time > 0
            else:
                sleep_time = "NULL"
                current_texture['animated'] = False
            print(f"Set sleep time for {current_texture['name']}: {sleep_time}")

        elif line.startswith("FRAME"):
            parts = line.split('"')
            if len(parts) > 3:
                frame_file = parts[1].strip()
                frame_data = {'file': frame_file}

                if "_LAYER" in frame_file:
                    frame_data['type'] = 'layer'
                    frame_data['file'] = frame_file.replace("_LAYER", "").strip()
                elif "_DETAIL" in frame_file:
                    detail_value = frame_file.split('_DETAIL_')[1]
                    frame_data['type'] = 'detail'
                    frame_data['detail_value'] = float(detail_value)
                    frame_data['file'] = frame_file.split('_DETAIL_')[0].strip()
                elif "PAL.BMP" in frame_file:
                    previous_file = current_frames[-1]['file'] if current_frames else ''
                    if previous_file.split('.')[0] == frame_file.replace("PAL.BMP", "").strip():
                        frame_data['type'] = 'palette_mask'
                        frame_data['file'] = frame_file

                        # Save the palette mask file name separately in the current texture
                        current_texture['palette_mask_file'] = frame_file
                elif "," in frame_file:
                    num_values, file_name = frame_file.split(", ", 3)[-1], frame_file.split(", ", 3)[-1]
                    numbers = frame_file.split(", ")[:3]
                    frame_data['type'] = 'tiled'
                    frame_data['color_index'] = int(numbers[0]) - 1
                    frame_data['scale'] = int(numbers[1]) * 10
                    frame_data['blend'] = int(numbers[2])
                    frame_data['file'] = file_name.strip()
                    tiled_frame_count += 1  # Increment tiled frame count
                else:
                    if sleep_time != "NULL" and sleep_time > 0 and animated_frame_regex.match(frame_file):
                        animated_frame_count += 1
                        frame_data['animation_frame'] = animated_frame_count

                current_frames.append(frame_data)
                current_texture['frame_files'].append(frame_data['file'])
                current_texture['frames'].append(frame_data)
                print(f"Added frame for {current_texture['name']}: {frame_data}")

        elif line.startswith("ENDSIMPLESPRITEDEF"):
            if current_texture:
                current_texture['number_frames'] = animated_frame_count
                current_texture['num_tiled_frames'] = tiled_frame_count  # Save the count of tiled frames
                textures[current_texture['name']] = current_texture
                print(f"Added texture to dictionary: {current_texture['name']}")
                current_texture = None

    # After all lines are processed, add any remaining texture
    if current_texture:
        current_texture['number_frames'] = animated_frame_count
        current_texture['num_tiled_frames'] = tiled_frame_count  # Save the count of tiled frames
        textures[current_texture['name']] = current_texture
        print(f"Added final texture to dictionary: {current_texture['name']}")

    print("Textures inside simplespritedef_parse function:")
    for key, value in textures.items():
        print(f"Texture Name: {key}")
        for k, v in value.items():
            print(f"  {k}: {v}")
    
    return textures