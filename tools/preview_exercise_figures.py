"""Write an isolated visual-QA gallery with only public vector assets.

Run this script, then serve the printed directory locally for browser review.
No production session, keys, account data or workout records are included.
"""
import json
import tempfile
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "assets/exercise_guides.json").read_text(encoding="utf8"))
renderer = (ROOT / "assets/exercise_guide/figure.js").read_text(encoding="utf8")
folder = Path(tempfile.mkdtemp(prefix="solem-figures-"))
html = """<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Revisão vetorial · Solem</title>
<style>body{margin:20px;background:#0b1422;color:#daeaf4;font:15px system-ui}header{position:sticky;top:0;background:#0b1422;padding:8px;z-index:2}input{width:300px}main{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}article{background:#142538;padding:10px;border-radius:10px}svg{width:100%;aspect-ratio:1}h2{font-size:15px;margin:0}@media(max-width:600px){main{grid-template-columns:repeat(2,1fr)}}</style>
<header><h1>Revisão de poses · sem dados pessoais</h1><label>Posição de todos os exercícios <input id="range" type="range" min="0" max="100" value="50"></label></header><main id="grid"></main>
<script>""" + renderer + "</script><script>const catalog=" + json.dumps(data, ensure_ascii=False) + """;
const paints=[];for(const[name,motion]of Object.entries(catalog.motions)){const card=document.createElement('article'),title=document.createElement('h2'),svg=document.createElementNS('http://www.w3.org/2000/svg','svg');title.textContent=name;svg.setAttribute('viewBox','0 0 440 440');card.append(title,svg);document.getElementById('grid').appendChild(card);const paint=ExerciseFigure.mount(svg,motion);paint(.5);paints.push(paint)}
document.getElementById('range').oninput=e=>paints.forEach(paint=>paint(e.target.value/100));</script></html>"""
(folder / "index.html").write_text(html, encoding="utf8")
shutil.copytree(ROOT / "assets/exercise_guide", folder / "component")
guide = data["guides"]["Barra Fixa (Supinada)"]
payload = dict(exercise="Barra Fixa (Supinada)", guide=guide,
               motion=data["motions"][guide["motion"]], grip=data["grips"][guide["grip"]], notice=data["notice"])
mobile = '''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Guia · teste de 390 px</title>
<style>body{background:#0b1422;color:#daeaf4;font:16px system-ui;margin:16px}iframe{display:block;width:390px;max-width:100%;border:0}</style>
<h1>Guia em largura de celular · 390 px</h1><iframe title="Guia mobile" src="component/index.html"></iframe>
<script>const frame=document.querySelector('iframe');const args=''' + json.dumps(payload, ensure_ascii=False) + ''';
window.addEventListener('message',e=>{if(e.source!==frame.contentWindow)return;if(e.data.type==='streamlit:componentReady')frame.contentWindow.postMessage({type:'streamlit:render',args},'*');if(e.data.type==='streamlit:setFrameHeight')frame.height=e.data.height});</script></html>'''
(folder / "mobile.html").write_text(mobile, encoding="utf8")
print(folder)
