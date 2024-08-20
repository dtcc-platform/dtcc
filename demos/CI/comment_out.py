# Simple script to comment out .view() calls (mainly useful for monitorless machines like for CI) 

import os
import re

def comment_out_view_lines(directory):
    # Walk through the directory and its subdirectories
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    lines = f.readlines()

                with open(file_path, 'w') as f:
                    for line in lines:
                        if '.view()' in line:
                            line = '# ' + line
                        f.write(line)

                print(f"Processed file: {file_path}")

# Define the root directory to start the search
root_directory = '../'  # Replace with the path to your directory
comment_out_view_lines(root_directory)

print("Completed commenting out lines containing .view() in all .py files.")
