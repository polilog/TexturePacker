#!/usr/bin/env python
import subprocess
import os
import sys
import fnmatch

scenes = []
atlases = []

def run_script(scene_path, atlas_path):
	cmd = ['python', 'texture_packer.py', scene_path, atlas_path]
	subprocess.check_call(cmd)

def files_within(directory_path, extension, pattern="*"):
    for dirpath, dirnames, filenames in os.walk(directory_path):
        for file_name in fnmatch.filter(filenames, pattern):
			file, file_extension = os.path.splitext(file_name)
			if file_extension == extension:
				yield os.path.normpath(os.path.join(dirpath, file_name))
	
if __name__ == "__main__":
	scenes_dir = sys.argv[1]
	atlases_dir = sys.argv[2]
	scenes = list(files_within(scenes_dir, ".tscn"))
	atlases = list(files_within(atlases_dir, ".png"))
	for scene_path in scenes:
		for atlas_path in atlases:
			run_script(scene_path, atlas_path)