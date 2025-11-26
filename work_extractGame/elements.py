import collections
import os.path as path

import yaml
import json

import constant as constant
import utils

elements_base = path.join(
    utils.ONI_ROOT, "OxygenNotIncluded_Data", "StreamingAssets", "elements")
element_states = [
    "solid",
    "liquid",
    "gas",
    "special",
]

def get_substance_colours():
    with open(constant.dict_PATH_EXTRACT_FILE['element'], 'r', encoding='utf-8') as file_elem:
        data_elem = json.load(file_elem).get("elementTable", None)
    dict_colours = {}
    for _, ele in data_elem.items():
        dict_colours[ele['tag']['Name']] = {}
        substance = ele.get('substance', None)
        if substance:
            for colour_key in ['colour', 'uiColour', 'conduitColour']:
                if colour_key in substance:
                    colour_rgba = substance[colour_key]
                    colour_hex = "#{:02x}{:02x}{:02x}{:02x}".format(colour_rgba['r'], colour_rgba['g'], colour_rgba['b'], colour_rgba['a'])
                    dict_colours[ele['tag']['Name']][colour_key] = colour_hex
        # utils.save_lua(path.join(utils.DIR_OUT, "Elements.lua"), dict_colours)
    return dict_colours
    
    
def main():
    data = []
    for state in element_states:
        with open(path.join(elements_base, f"{state}.yaml"), 'r') as f:
            data.extend(yaml.safe_load(f)["elements"])
    data = collections.OrderedDict({ele["elementId"]: ele for ele in data})
    # 添加颜色信息
    with open(constant.dict_PATH_EXTRACT_FILE['element'], 'r', encoding='utf-8') as file_elem:
        data_elem = json.load(file_elem).get("elementTable", None)
    for _, ele in data_elem.items():
        if 'tag' in ele and 'Name' in ele['tag'] and ele['tag']['Name'] in data and 'substance' in ele:
            substance = ele['substance']
            if substance:
                for colour_key in ['colour', 'uiColour', 'conduitColour']:
                    if colour_key in substance:
                        colour_rgba = substance[colour_key]
                        colour_hex = "#{:02x}{:02x}{:02x}{:02x}".format(colour_rgba['r'], colour_rgba['g'], colour_rgba['b'], colour_rgba['a'])
                        data[ele['tag']['Name']][colour_key] = colour_hex

    utils.save_lua(path.join(utils.DIR_OUT, "Elements.lua"), data)


if __name__ == '__main__':
    main()
