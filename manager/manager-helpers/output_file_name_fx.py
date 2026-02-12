import os


def output_file_name_fx(input_file_name, encoding_decision):
    """Generate output filename with .mkv extension if needed."""
    # Get the current extension from the filename
    name_without_ext = os.path.splitext(input_file_name)[0]
    current_ext = os.path.splitext(input_file_name)[1]
    
    # Change extension to .mkv if it's not already
    if current_ext.lower() != '.mkv':
        output_file_name = name_without_ext + '.mkv'
        encoding_decision = True
    else:
        output_file_name = input_file_name
    
    # Return just the new filename without any directory path
    return output_file_name, encoding_decision
