from os import path
import json
import constant
import utils

output = {"allOutfits": {}, "displayedOutfits": []}

def main():

    with open(constant.dict_PATH_EXTRACT_FILE['db_'], 'r', encoding='utf-8') as file:
        data = json.load(file)
        if "clothingOutfits" in data:
            # extract clothing outfits, keyed by their Id
            output["allOutfits"] = {outfit['Id']: outfit for outfit in data.get("clothingOutfits", [])}
            # extract displayed clothing outfits
            for outfit in data.get("clothingOutfits", []):
                output["displayedOutfits"].append(outfit['Id'])
    utils.save_lua(path.join(utils.DIR_OUT, "ClothingOutfits.lua"), output)

if __name__ == '__main__':
    main()