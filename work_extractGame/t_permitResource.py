from os import path
import json
import constant
import utils

output = {"allPermits": {}, "displayedPermits": [], "permitSortedByPrefabs": {}}
blueprints = {}
def main():
    #db_permitResources
    with open(constant.dict_PATH_EXTRACT_FILE['db_'], 'r', encoding='utf-8') as file:
        data = json.load(file)
        output["allPermits"].update({permit['Id']: permit for permit in data.get("permitResources", [])})
        
        # delete unneeded field in each permit
        for permit in output["allPermits"].values():
            keys_to_remove = ['facadeFor']
            for key in keys_to_remove:
                permit.pop(key, None)

        # print permits with specific requiredDlcIds
        # for permit in output["allPermits"].values():
        #     if "requiredDlcIds" in permit and permit["requiredDlcIds"] == ["COSMETIC1_ID"]:
        #         print(f"{permit['Name']}, {permit['requiredDlcIds']}")
        
    with open(constant.dict_PATH_EXTRACT_FILE['spritesInfo'], 'r', encoding='utf-8') as file:
        sorted_blueprints = json.load(file)
    if 'categoryIdToSubcategoryIdsMap' in sorted_blueprints:
        for categoryId, subcategoryIds in sorted_blueprints['categoryIdToSubcategoryIdsMap'].items():
            output["displayedPermits"].append(dict(categoryId=categoryId, subcategoryIds=list(subcategoryIds)))
            if 'subcategoryIdToPermitIdsMap' in sorted_blueprints:
                for subcategoryId in subcategoryIds:
                    permitIds = sorted_blueprints['subcategoryIdToPermitIdsMap'].get(subcategoryId, [])
                    output["displayedPermits"][-1][subcategoryId] =list(permitIds)
                    for permitId in permitIds:
                        if permitId in output['allPermits']:
                            if sort_key := output['allPermits'][permitId].get('PrefabID') or \
                                output['allPermits'][permitId].get('prefabId') or \
                                output['allPermits'][permitId].get('Part'):
                                if sort_key in ['Bottom', 'Middle', 'Top']:
                                    sort_key = f'Monument{sort_key}'
                                if sort_key not in output["permitSortedByPrefabs"]:
                                    output["permitSortedByPrefabs"][sort_key] = []
                                output["permitSortedByPrefabs"][sort_key].append(permitId)

    utils.save_lua(path.join(utils.DIR_OUT, "PermitResources.lua"), output)
if __name__ == '__main__':
    main()