import collections
import os.path as path
import re

import pandas as pd

from work_wikiAssistant import bot
import utils

logger = utils.getLogger('parse_po')


class SubTags:
    @staticmethod
    def strip_link(x):
        return re.sub(r'<link="(.+?)">(.*?)</link>', r'\g<1>', x)

    lang2col = {
        "en": "id",
        "zh": "string",
        "zh-hant": 'hant'
    }

    def __init__(self, df, site='oni'):
        self.site = site
        self.pages = {
            "en": bot.all_page_titles("en", site),
            "zh": bot.all_page_titles("zh", site),
            "zh-hant": bot.all_page_titles("zh", site),
        }
        self.cates = {
            "en": bot.all_cate_titles("en", site),
            "zh": bot.all_cate_titles("zh", site),
            "zh-hant": bot.all_cate_titles("zh", site),
        }
        self.df = df
        self.curr = None

        # set links
        self.links = {}
        for _, r_data in df.iterrows():
            for lang in ["en", "zh", "zh-hant"]:
                if lang not in self.links:
                    self.links[lang] = {}
                r_str = r_data[self.lang2col[lang]]
                if pd.isna(r_str):
                    continue
                # logger.debug(f"Processing link in {lang}: {r_str}")
                for r_match in re.finditer(r'<link="(.+?)">(.*?)</link>', r_str):
                    if r_match is None:
                        continue
                    # logger.debug(f"Found link: {r_match.group(1)} -> {r_match.group(2)}")
                    if r_match.group(1) not in self.links[lang]:
                        self.links[lang][r_match.group(1)] = r_match.group(2)
                    else:
                        # logger.info(
                        #     f"Duplicated link key detected: {r_match.group(1)} <- {r_match.group(2)}")
                        self.links[lang][r_match.group(1)] = False  # make sure to be unique
        # Use codex title if there is some duplications
        for _, r_data in df[df.context.str.match(r'^STRINGS\.CODEX\.\w+\.TITLE$')].iterrows():
            for lang in ["en", "zh", "zh-hant"]:
                r_str = r_data[self.lang2col[lang]]
                if pd.isna(r_str):
                    continue
                # logger.debug(f"Processing codex link in {lang}: {r_str}")
                for r_match in re.finditer(r'<link="(.+?)">(.*?)</link>', r_str):
                    if r_match is None:
                        continue
                    match_id = r_match.group(1)
                    if match_id in self.links[lang] and self.links[lang][match_id] is False:
                        # logger.info(f"Use codex title: {match_id} -> {r_match.group(2)}")
                        self.links[lang][match_id] = r_match.group(2)

    def link_page_or_cate(self, name, lang, text=None, force_type=None):
        name = re.sub(r'[\[\]]', '', name)  # prevent [/] in names
        auto_type = force_type == 'auto'
        if force_type == 'auto':
            force_type = None
        if name in self.pages[lang]:
            force_type = force_type or "page"
        elif name in self.cates[lang]:
            force_type = force_type or "cate"
        else:
            # logger.info(f"Cannot find page or category for {name} in {lang}")
            pass
        
        if auto_type:
            force_type = force_type or 'page'

        if force_type == "page":
            if text and text != name:
                return f"[[{name}|{text}]]"
            else:
                return f"[[{name}]]"
        elif force_type == "cate":
            return f"[[:Category:{name}|{text or name}]]"
        return None

    def repl_style(self, match: re.Match, lang, en_is_link):
        sty = match.group(1)

        if sty == "KKeyword":
            if lang == "en":
                linked = self.link_page_or_cate(match.group(2), lang)
                if linked is None:
                    en_is_link.append(None)
                elif linked.startswith("[[:Cate"):
                    en_is_link.append("cate")
                else:
                    en_is_link.append("page")

                if linked:
                    return linked

            elif lang.startswith("zh"):
                linked = self.link_page_or_cate(match.group(2), lang)
                if linked:
                    return linked
                if en_is_link:
                    islink = en_is_link.pop(0)
                    linked = self.link_page_or_cate(
                        match.group(2), lang, force_type=islink)
                    if linked:
                        return linked
        elif sty in ["logic_on", "logic_off", "hovercard_element"]:
            return f'<span class="ingame-{sty}">{match.group(2)}</span>'
        # if sty not in ["consumed", "produced"] and not match.group(2).startswith('{'):
        #     logging.warning(f'Cannot replace style "{match.group(0)}" in {self.curr[self.lang2col[lang]]}')
        return match.group(2)

    def repl_link(self, match: re.Match, lang, en_is_link):
        col = self.lang2col[lang]
        # g0 = match.group(0)  # full link
        g1 = match.group(1)  # link
        g2 = match.group(2)  # text
        # logger.debug(f"Replace link: {g1} -> {g2}, text is {g0}, lang is {lang}")

        if g1 in self.links[lang] and self.links[lang][g1]:
            # logger.info(f"Replace link: {g1} -> {self.links[lang][g1]}, text is {g2}, gonna find it in {lang}")
            return self.link_page_or_cate(self.links[lang][g1], lang, g2, 'auto')

        g1_trans = {
            "ATMOSUIT" : "EQUIPMENT.PREFABS.ATMO_SUIT",
            "BASICSINGLEHARVESTPLANT" : "CREATURES.SPECIES.BASICSINGLEHARVESTPLANT",
            "BLEACHSTONE" : "ELEMENTS.BLEACHSTONE",
            "BOOSTER": "CODEX.BIONICBOOSTER",
            "BULBPLANT" : "CREATURES.SPECIES.BULBPLANT",
            "CACTUSPLANT" : "CREATURES.SPECIES.CACTUSPLANT",
            "CARROTPLANT" : "CREATURES.SPECIES.CARROTPLANT",
            "CHECKPOINT" : "BUILDINGS.PREFABS.CHECKPOINT",
            "CLOTHING" : "DUPLICANTS.MODIFIERS.CLOTHING",
            "COLDBREATHER" : "CREATURES.SPECIES.COLDBREATHER",
            "COLDWHEAT" : "CREATURES.SPECIES.COLDWHEAT",
            "COMPOST" : "BUILDINGS.PREFABS.COMPOST",
            "CRITTERTRAPPLANT" : "CREATURES.SPECIES.CRITTERTRAPPLANT",
            "CYLINDRICA" : "CREATURES.SPECIES.CYLINDRICA",
            "DEWDRIPPERPLANT" : "CREATURES.SPECIES.DEWDRIPPERPLANT",
            "DINOFERN" : "CREATURES.SPECIES.DINOFERN",
            "ELECTROBANK" : "ITEMS.INDUSTRIAL_PRODUCTS.ELECTROBANK",
            "EQUIPMENT" : "UI.NEWBUILDCATEGORIES.EQUIPMENT",
            "EVILFLOWER" : "CREATURES.SPECIES.EVILFLOWER",
            "FILTERPLANT" : "CREATURES.SPECIES.FILTERPLANT",
            "FLUSHTOILET" : "BUILDINGS.PREFABS.FLUSHTOILET",
            "FLYTRAPPLANT" : "CREATURES.SPECIES.FLYTRAPPLANT",
            "FOOD" : "UI.BUILDCATEGORIES.FOOD",
            "GARDENDECORPLANT" : "CREATURES.SPECIES.GARDENDECORPLANT",
            "GARDENFOODPLANT" : "CREATURES.SPECIES.GARDENFOODPLANT",
            "GASGRASS" : "CREATURES.SPECIES.GASGRASS",
            "HARDSKINBERRYPLANT" : "CREATURES.SPECIES.HARDSKINBERRYPLANT",
            "HOSPITAL" : "ROOMS.TYPES.HOSPITAL",
            "ICE" : "ELEMENTS.ICE",
            "ICEFLOWER" : "CREATURES.SPECIES.ICEFLOWER",
            "JETSUIT" : "EQUIPMENT.PREFABS.JET_SUIT",
            "KELPPLANT" : "CREATURES.SPECIES.KELPPLANT",
            "LEADSUIT" : "EQUIPMENT.PREFABS.LEAD_SUIT",
            "LEAFYPLANT" : "CREATURES.SPECIES.LEAFYPLANT",
            "LIME" : "ELEMENTS.LIME",
            "MAGMA" : "ELEMENTS.MAGMA",
            "MEDICALCOT" : "BUILDINGS.PREFABS.MEDICALCOT",
            "METHANE" : "ELEMENTS.METHANE",
            "MUSHBAR" : "ITEMS.FOOD.MUSHBAR",
            "MUSHROOMPLANT" : "CREATURES.SPECIES.MUSHROOMPLANT",
            "NIOBIUM" : "ELEMENTS.NIOBIUM",
            "OXYFERN" : "CREATURES.SPECIES.OXYFERN",
            "OXYGENMASK" : "EQUIPMENT.PREFABS.OXYGEN_MASK",
            "POWERPLANT" : "ROOMS.TYPES.POWER_PLANT",
            "PRICKLEFLOWER" : "CREATURES.SPECIES.PRICKLEFLOWER",
            "PRICKLEGRASS" : "CREATURES.SPECIES.PRICKLEGRASS",
            "RAPTOR" : "CREATURES.SPECIES.RAPTOR",
            "RAWMETAL": "MISC.TAGS.METAL",
            "REFRIGERATOR" : "BUILDINGS.PREFABS.REFRIGERATOR",
            "ROCKCRUSHER" : "BUILDINGS.PREFABS.ROCKCRUSHER",
            "RUST" : "ELEMENTS.RUST",
            "SALTPLANT" : "CREATURES.SPECIES.SALTPLANT",
            "SEALETTUCE" : "CREATURES.SPECIES.SEALETTUCE",
            "SHOWER" : "BUILDINGS.PREFABS.SHOWER",
            "SPACETREE" : "CREATURES.SPECIES.SPACETREE",
            "STEAM" : "ELEMENTS.STEAM",
            "STORAGELOCKER" : "BUILDINGS.PREFABS.STORAGELOCKER",
            "SWAMPHARVESTPLANT" : "CREATURES.SPECIES.SWAMPHARVESTPLANT",
            "SWAMPLILY" : "CREATURES.SPECIES.SWAMPLILY",
            "TOEPLANT" : "CREATURES.SPECIES.TOEPLANT",
            "TRAVELTUBEENTRANCE" : "BUILDINGS.PREFABS.TRAVELTUBEENTRANCE",
            "VINEMOTHER" : "CODEX.VINEMOTHER",
            "WINECUPS" : "CREATURES.SPECIES.WINECUPS",
            "WORMPLANT" : "CREATURES.SPECIES.WORMPLANT",
        }
        if g1 in g1_trans:
            # logger.info(f"replace id: {g1}")
            g1 = g1_trans[g1]

        df = self.df
        candidates = df[df.context.str.endswith(f".{g1}.NAME")]
        if len(candidates) == 1: # if there is only one candidate, use it
            return self.link_page_or_cate(candidates.iloc[0][col], lang, g2, "page")
        if len(candidates) == 0:
            candidates = df[df.context.str.endswith(f".{g1}")]
            if len(candidates) == 1:
                return self.link_page_or_cate(candidates.iloc[0][col], lang, g2, "cate")
        if len(candidates) == 0:
            candidates = df[df.context.str.endswith(f".{g1}.TITLE")]
            if len(candidates) == 1:
                return self.link_page_or_cate(candidates.iloc[0][col], lang, g2, "cate")

        if lang in ['en', 'zh', 'zh-hant']:
            for _, c in candidates.iterrows():
                if (pd.isna(c[col]) or "link=" in c[col]): # No <link="..."> allowed in c[col]
                    continue
                linked = self.link_page_or_cate(
                    self.strip_link(self.simple_sub(c[col])), lang, g2)
                # logger.debug(f"Found candidate: {c[col]} -> {linked}, lang is {lang}")
                if linked:
                    return linked

        # if g1 not in ["HEAT"]:
        #     logging.warning(f'Can not find link "{g1}" in "{self.curr[self.lang2col[lang]]}"')
        return g2

    @staticmethod
    def simple_sub(s):
        if pd.isna(s):
            return s
        ori = s
        s = re.sub(r'\n+', '<br/>', s)
        s = re.sub(r'<color=#(.+?)>(.*?)</color>',
                   r'<span style="color:#\g<1>;">\g<2></span>', s)
        s = re.sub(r'<size=.+?>(.*?)</size>', r'\g<1>', s)
        s = re.sub(r'<smallcaps>(.*?)</smallcaps>',
                   r'<span class="ingame-smallcaps">\g<1></span>', s)
        if s.count('<link="') == 1:
            s = re.sub(r'^<link="\w+?">([^<]*?)</link>$', r'\g<1>', s)
        s = re.sub(r'<alpha=#(.+?)>((.|\n)*?)</color>',
                   lambda m: f"<span style='opacity:{int(m.group(1), 16) / int('ff', 16):.2f}'>"
                             f"{m.group(2)}</span>", s)
        s = re.sub(r'<indent=(.+?)>((.|\n)*?)</indent>',
                   lambda m: f"<span class='ingame-indent' "
                             f"style='padding-left:{m.group(1)}'>{m.group(2)}</span>", s)
        # again
        s = re.sub(r'<indent=(.+?)>((.|\n)*?)</indent>',
                   lambda m: f"<span class='ingame-indent' "
                             f"style='padding-left:{m.group(1)}'>{m.group(2)}</span>", s)

        # rollback unbalanced tags
        s = re.sub(r'<color=#(.+?)>(.*?)$',
                   r'<span style="color:#\g<1>;">\g<2></span>', s)
        s = re.sub(r'<size=.+?>(.*?)$', r'\g<1>', s)
        s = re.sub(r'<smallcaps>(.*?)$',
                   r'<span class="ingame-smallcaps">\g<1></span>', s)
        s = re.sub(r'<alpha=#(.+?)>((.|\n)*?)$',
                   lambda m: f"<span style='opacity:{int(m.group(1), 16) / int('ff', 16):.2f}'>"
                             f"{m.group(2)}</span>", s)
        s = re.sub(r'<indent=(.+?)>((.|\n)*?)$',
                   lambda m: f"<span class='ingame-indent' "
                             f"style='padding-left:{m.group(1)}'>{m.group(2)}</span>", s)
        s = re.sub(
            r'</color>|'
            r'</size>|'
            r'</indent>', "", s)

        def unbalanced(m):
            logger.warning(
                f"remove unbalanced tag \"{m.group(0)}\" from:\n{ori}")
            return ""

        s = re.sub(
            r'<color=#(\w+)>|'
            r'<size=.+?>|'
            r'<smallcaps>|'
            r'<alpha=#(\w\w)>|'
            r'</color>|'
            r'</size>|'
            r'</indent>', unbalanced, s)
        
        if '<i>' in s and '</i>' not in s:
            s += '</i>'
        return s

    def __call__(self, x):
        en_is_link = []
        self.curr = x
        # replace style to wikitext format in en / zh / zh-hant text
        for lang in ["en", "zh", "zh-hant"]:
            x_lang = x[self.lang2col[lang]]
            if not pd.isna(x_lang):
                x_lang = re.sub(r'<style="([^>]+?)">(.*?)</style>',
                                  lambda m: self.repl_style(m, lang, en_is_link), x_lang)
                x[self.lang2col[lang]] = x_lang

        # replace link to wikitext format in en / zh / zh-hant text
        for lang in ["en", "zh", "zh-hant"]:
            x_lang = x[self.lang2col[lang]]
            if not pd.isna(x_lang):
                # logger.info(f"Before: {x_lang}")
                x_lang = re.sub(r'<link="([^>]+?)">([^<]+?)</link>',
                            lambda m: str(self.repl_link(m, lang, en_is_link) or ""), x_lang)
                # logger.info(f"After: {x_lang}")
                x[self.lang2col[lang]] = x_lang

        return x


def main():
    df: pd.DataFrame = utils.get_str_data()
    df.dropna(inplace=True, subset=['context'])
    df = utils.sub_controls_str(df)

    sub_tags = SubTags(df, "oni")

    df["prefix"] = df.context.str.findall(
        r"(?<=STRINGS\.)\w+").apply(lambda x: utils.to_cap(x[0]))
    df.loc[df.prefix == "Ui", "prefix"] = "UI"

    df.id = df.id.apply(SubTags.simple_sub)
    df.string = df.string.apply(SubTags.simple_sub)
    df.hant = df.hant.apply(SubTags.simple_sub)

    df = pd.DataFrame(df.apply(sub_tags, axis="columns"))

    for prefix in df.prefix.unique():
        df_prefix = df[df.prefix == prefix]
        df_prefix = df_prefix.set_index("context")
        data = collections.OrderedDict()
        data["zh"] = df_prefix["string"].dropna().to_dict(
            collections.OrderedDict)
        data["zh-hant"] = df_prefix["hant"].dropna().to_dict(collections.OrderedDict)
        data["en"] = df_prefix["id"].dropna().to_dict(collections.OrderedDict)
        utils.save_lua(
            path.join(utils.DIR_OUT, f"i18n_strings_{prefix.lower()}"), data)

    # Generate OmegaT glossary_po.txt
    glossary_text = ""
    for row in df.itertuples():
        if row.id and row.string and "\n" not in str(row.id) and "\n" not in str(row.string):
            glossary_text += f"{row.id}\t{row.string}\n"
    with open(path.join(utils.DIR_OUT, "glossary_po.txt"), "wb") as text_file:
        text_file.write(glossary_text.encode("utf-8"))


if __name__ == '__main__':
    main()
