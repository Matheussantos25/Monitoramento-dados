"""Convert our repository-owned SVG paths to an Android vector (no raster assets)."""
from pathlib import Path
from xml.etree import ElementTree as ET

android = Path(__file__).resolve().parents[1]
source = ET.parse(android.parent/'assets/character.svg').getroot()
ns = 'http://schemas.android.com/apk/res/android'
ET.register_namespace('android', ns)
def attr(key): return '{'+ns+'}'+key
vector = ET.Element('vector', {attr('width'):'240dp', attr('height'):'300dp', attr('viewportWidth'):'240', attr('viewportHeight'):'300'})
for e in source:
    tag = e.tag.split('}')[-1]
    if tag == 'path':
        path = e.attrib['d']
    elif tag in ('circle','ellipse'):
        x,y = float(e.attrib['cx']),float(e.attrib['cy'])
        rx = float(e.attrib.get('rx',e.attrib.get('r',0))); ry = float(e.attrib.get('ry',e.attrib.get('r',0)))
        path = f'M{x-rx},{y}a{rx},{ry} 0 1,0 {rx*2},0a{rx},{ry} 0 1,0 {-rx*2},0'
    elif tag == 'rect':
        x,y,w,h = [float(e.attrib[k]) for k in ('x','y','width','height')]
        path = f'M{x},{y}h{w}v{h}h{-w}Z'
    else:
        continue
    values = {attr('pathData'):path, attr('fillColor'):e.attrib.get('fill','#000000').replace('none','#00000000')}
    for source_name, target in [('stroke','strokeColor'),('stroke-width','strokeWidth'),('stroke-linecap','strokeLineCap')]:
        if source_name in e.attrib: values[attr(target)] = e.attrib[source_name]
    ET.SubElement(vector,'path',values)
output = android/'app/src/main/res/drawable/character.xml'
output.parent.mkdir(parents=True,exist_ok=True)
ET.indent(vector)
ET.ElementTree(vector).write(output,encoding='utf-8',xml_declaration=True)
print('Generated Android character from shared SVG.')
