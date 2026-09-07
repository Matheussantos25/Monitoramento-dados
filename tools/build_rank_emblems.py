"""Generate original faceted rank emblems for web and Android from identical paths."""
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PALETTES = [('#796D69','#D0BCB0','#352F34'),('#B07655','#F0C49B','#493139'),
 ('#819AA8','#E4F2FA','#354B60'),('#C29648','#FFF0AA','#5D4028'),
 ('#3FADBA','#ADF8EF','#174B66'),('#44AD81','#B4FFD9','#1B4B43'),
 ('#658CE5','#C8F2FF','#34366E'),('#B66CDB','#FFD6FF','#572A71')]

def paths(tier):
    main, light, dark = PALETTES[tier]
    result = []
    for mirror in (False, True):
        def add(points, color):
            points = [(240-x if mirror else x,y) for x,y in points]
            result.append(('M'+' L'.join(f'{x},{y}' for x,y in points)+' Z',color))
        add([(119,139),(88,126),(43,111),(18,54),(57,86),(98,100)],dark)
        add([(22,60),(59,89),(96,102),(115,132),(85,114),(48,103)],main)
        add([(22,60),(57,83),(99,98),(113,119),(96,104),(55,92)],light)
        add([(37,85),(51,102),(89,115),(112,133),(87,121),(43,109)],light)
        if tier >= 2:
            add([(91,102),(68,77),(47,28),(48,74),(66,99),(111,134)],dark)
            add([(47,28),(72,76),(95,97),(111,125),(82,96),(59,66)],main)
            add([(47,28),(65,65),(84,85),(100,106),(74,84)],light)
        if tier >= 4:
            add([(34,103),(10,110),(42,119),(96,142),(116,143),(77,123)],main)
            add([(10,110),(39,108),(83,133),(46,115)],light)
        if tier >= 6:
            add([(85,91),(82,49),(104,72),(115,113)],dark)
            add([(82,49),(103,78),(107,104),(93,85)],light)
    result.extend([('M120,78 L147,102 L138,126 L120,151 L102,126 L93,102 Z',dark),
                   ('M120,84 L142,104 L120,143 L98,104 Z',main),
                   ('M120,84 L120,143 L98,104 Z',light),
                   ('M120,96 L133,107 L120,130 L107,107 Z',dark),
                   ('M120,98 L128,108 L120,126 L112,108 Z',light)])
    if tier >= 3:
        result.append(('M120,57 L128,68 L120,80 L112,68 Z',light))
    return result

if __name__ == '__main__':
    ns = 'http://schemas.android.com/apk/res/android'
    ET.register_namespace('android',ns)
    for tier in range(8):
        art = paths(tier)
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 170">'+''.join(f'<path d="{d}" fill="{c}"/>' for d,c in art)+'</svg>'
        target = ROOT/'assets/ranks'/f'rank_{tier}.svg'
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(svg,encoding='utf-8')
        vector = ET.Element('vector', {f'{{{ns}}}{k}':v for k,v in dict(width='240dp',height='170dp',viewportWidth='240',viewportHeight='170').items()})
        for d,c in art:
            ET.SubElement(vector,'path',{f'{{{ns}}}pathData':d,f'{{{ns}}}fillColor':c})
        ET.indent(vector)
        ET.ElementTree(vector).write(ROOT/'android-app/app/src/main/res/drawable'/f'rank_{tier}.xml',encoding='utf-8',xml_declaration=True)
    print('Generated 8 matching web/Android emblems.')
