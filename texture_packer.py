#!/usr/bin/env python
import sys
import re
import json

EXT_RES_PATTERN = '\[ext_resource path="(.*)" type="(.*)" id=(.*)\]'
SUB_RES_PATTERN = '\[sub_resource type="(.*)" id=(.*)\]'
ATLAS = '[ext_resource path="%s" type="Texture" id=%d]'
SUBRESOURCE = '[sub_resource type="AtlasTexture" id=%d]\n\natlas = ExtResource( %d )\nregion = Rect2( %d, %d, %d, %d )\nmargin = Rect2( 0, 0, 0, 0 )\n\n'

def read_file(path):
	with open(path, 'r') as file:
		data = file.readlines()
	file.close()
	return data

def decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = decode_list(item)
        elif isinstance(item, dict):
            item = decode_dict(item)
        rv.append(item)
    return rv

def decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = decode_list(value)
        elif isinstance(value, dict):
            value = decode_dict(value)
        rv[key] = value
    return rv

def read_json(path):
	with open(path, 'r') as file:
		dict = json.loads(file.read(), object_hook=decode_dict)
	file.close()
	return dict

def find_png(file):
	png_map = {}
	ext_res_count = 0
	ext_res_pattern = re.compile(EXT_RES_PATTERN)
	for line in file:
		match = ext_res_pattern.match(line)
		if match != None:
			ext_res_count = max(ext_res_count, int(match.group(3)))
			if match.group(2) == 'Texture':
				png_map[match.group(3)] = match.group(1)
	return [ext_res_count, png_map]

def get_sub_res_info(file):
	sub_res_count = 0
	insert_line = 0
	sub_res_pattern = re.compile(SUB_RES_PATTERN)
	for number, line in list(enumerate(file)):
		match = sub_res_pattern.match(line)
		if match != None:
			sub_res_count = max(sub_res_count, int(match.group(2)))
			if insert_line == 0:
				insert_line = number
	if insert_line == 0:
		for i in range(2, len(file)):
			if file[i] == "\n":
				insert_line = i
				break
	return [int(sub_res_count), int(insert_line)]

def replace_ext_res(file, ext_to_sub_map, atlas_ext_res):
	if not bool(ext_to_sub_map):
		return file
	new_file = []
	insert_line = 0
	ext_res_pattern = re.compile(EXT_RES_PATTERN)
	for number, line in list(enumerate(file)):
		match = ext_res_pattern.match(line)
		if match == None or not ext_to_sub_map.has_key(match.group(3)):
			new_file.append(line)
		if match != None:
			insert_line = len(new_file)
	new_file.insert(insert_line, atlas_ext_res)
	
	pattern = re.compile("ExtResource\( (.*) \)")
	for number, line in enumerate(new_file):
		if pattern.search(line):
			ext_res_id = pattern.search(line).group(1)
			if ext_to_sub_map.has_key(ext_res_id):
				new_file[number] = line.replace("ExtResource( %s )" % ext_res_id, "SubResource( %s )" % ext_to_sub_map[ext_res_id])
	return new_file
	

def rewrite_file(path, file_lines):
	with open(path, 'w') as file:
		file.writelines(file_lines)
	file.close()

def change_load_steps_count(file):
	steps_count = re.match(r"\[gd_scene load_steps=(.*) format=1\]", file[0]).group(1)
	file[0] = "[gd_scene load_steps=%d format=1]\n" % (int(steps_count) + 1)

if __name__ == "__main__":
	file_path = sys.argv[1]
	atlas_path = sys.argv[2].replace('\\', '/')
	atlas_description_path = atlas_path.split('.')[0] + '.json'
	atlas_description = read_json(atlas_description_path)

	file = read_file(file_path)
	[ext_res_count, png_map] = find_png(file)
	[sub_res_count, insert_line] = get_sub_res_info(file)	
	
	atlas_ext_res = ATLAS % ("res://" + atlas_path, ext_res_count + 1)
	
	ext_to_sub_map = {}
	for key in png_map.keys():
		png_filename = png_map[key].split('/')[-1]
		png_description = next((x for x in atlas_description["frames"] if x["filename"] == png_filename), None)
		if png_description != None:
			sub_res_count += 1
			frame = png_description["frame"]
			subresource_description = SUBRESOURCE % (sub_res_count, ext_res_count + 1, frame["x"], frame["y"], frame["w"], frame["h"])
			file.insert(insert_line, subresource_description)
			insert_line += 1
			ext_to_sub_map[key] = sub_res_count
	file = replace_ext_res(file, ext_to_sub_map, atlas_ext_res)
	if bool(ext_to_sub_map):
		change_load_steps_count(file)
	rewrite_file(file_path, file)