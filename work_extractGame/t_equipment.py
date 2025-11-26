import json

import constant as constant
from work_extractGame.model.EntityInfo import EntityInfo
from work_extractGame.util.DataUtils import save_lua_by_schema

def convert_data_2_lua(entityInfo: EntityInfo):
    dict_equipmentDefs = {}
    dict_output = {}
    # 读取装备
    with open(constant.dict_PATH_EXTRACT_FILE['item'], 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data['EquipmentDefs']:
            dict_equipmentDefs[item['Id']] = item
        for item in data['equipments']:
            # 装备
            entityId = item.get('name', None)
            if entityId is None:
                continue
            item['id'] = entityId
            item['requiredDlcIds'] = item['kPrefabID'].get('requiredDlcIds', None)
            item['forbiddenDlcIds'] = item['kPrefabID'].get('forbiddenDlcIds', None)
            if item.get('tags', None):
                item['tags'] = [mItem['Name'] for mItem in item['tags']]
            equipDef = dict_equipmentDefs.get(entityId, None)
            if equipDef:
                item['slot'] = equipDef['Slot']
                item['wornID'] = equipDef['wornID']
                # 防护属性
                AttributeModifiers = equipDef.get('AttributeModifiers', None)
                if AttributeModifiers and len(AttributeModifiers) > 0:
                    item['attribute'] = AttributeModifiers
                # 免疫效果
                EffectImmunites = equipDef.get('EffectImmunites', None)
                if EffectImmunites and len(EffectImmunites) > 0:
                    item['effectImmunites'] = [effect for effect in EffectImmunites]
                # 装备效果
                OnEquipCallBack = equipDef.get('OnEquipCallBack', None)
                if OnEquipCallBack:
                    target0 = OnEquipCallBack.get('target0', None)
                    if target0:
                        clothingInfo = target0.get('clothingInfo', None)
                        if clothingInfo:
                            item['onEquipEffect'] = clothingInfo
            else:
                # 定义损坏物品
                item['isWorn'] = True

            dict_output[item['name']] = item
    save_lua_by_schema(entityInfo, dict_output)
    return True


if __name__ == '__main__':
    convert_data_2_lua(constant.EntityType.Equipment.value)
