import os


def output_file_name_fx(input_file_name, encoding_decision, priority):
    """Generate output filename with .mkv extension if needed. Propagate priority."""
    name_without_ext = os.path.splitext(input_file_name)[0]
    current_ext = os.path.splitext(input_file_name)[1]
    if current_ext.lower() != '.mkv':
        output_file_name = name_without_ext + '.mkv'
        encoding_decision = True
        # Optionally adjust priority here if needed
    else:
        output_file_name = input_file_name
    return output_file_name, encoding_decision, priority
