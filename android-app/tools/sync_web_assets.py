"""Export literal catalogs/assets and parity fixtures without starting Streamlit.

Run from any directory: python android-app/tools/sync_web_assets.py
Fixture generation uses pandas (already a Streamlit project dependency).
"""
import ast
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

android = Path(__file__).resolve().parents[1]
repo = android.parent
tree = ast.parse((repo / "app.py").read_text(encoding="utf-8"))
names = {"EXERCICIOS_PRESETADOS", "ALIMENTOS_SAUDAVEIS", "ALIMENTOS_BESTEIROL", "DISCIPLINAS_ESTUDO", "DECKS_ANKI", "FONTES_QUESTOES", "TOPICOS_EDITAL", "ROTA_ESTRATEGICA", "PESOS_DISCIPLINA", "PERIODOS_DASHBOARD"}
catalog = {}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in names:
                catalog[target.id] = ast.literal_eval(node.value)
assert set(catalog) == names
health_tree = ast.parse((repo / "solem_health.py").read_text(encoding="utf-8"))
profile_names = {"WORKOUT_FIELD_PROFILES", "WORKOUT_EXERCISE_PROFILES"}
for node in health_tree.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in profile_names:
                catalog[target.id] = ast.literal_eval(node.value)
assert profile_names <= set(catalog)

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

assets = android / "app/src/main/assets"
save(assets / "catalog.json", catalog)
shutil.copytree(repo / "prompts", assets / "prompts", dirs_exist_ok=True)
edital = next(n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and "**MATEMÁTICA E ESTATÍSTICA APLICADA:**" in n.value)
(assets / "edital.txt").write_text(edital.strip(), encoding="utf-8")
raw = android / "app/src/main/res/raw"
raw.mkdir(parents=True, exist_ok=True)
for video in (repo / "edits_motivacionais").glob("*.mp4"):
    shutil.copy2(video, raw / video.name.lower())

# Execute only these pure existing functions, never the app module/network setup.
selected = {"converter_tempo_para_segundos", "formatar_segundos", "preparar_importacao_simulado"}
module = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in selected], type_ignores=[])
scope = dict(catalog, pd=pd, datetime=datetime, timedelta=timedelta)
exec(compile(module, "app.py (pure functions only)", "exec"), scope)
fixtures = []
for schema in ("solem_simulado_v1", "solem_simulado_ce_v1"):
    subjects = catalog["DISCIPLINAS_ESTUDO"][:3]
    questions = []
    for index, seconds in enumerate([30, 30, 30, 60.5, "01:31", "01:00:02", 0]):
        subject = subjects[index % 3]
        questions.append(dict(numero=index+1, disciplina=subject,
            topico_edital=catalog["TOPICOS_EDITAL"][subject][0],
            resultado=["certo", "erro", "anulada"][index % 3],
            tempo_segundos=seconds, tempo_informado=index != 6,
            confianca=None if index % 2 else 3, resposta_usuario=" a ", gabarito="B", tipo_erro="conteúdo"))
    payload = dict(schema=schema, simulado_id="Teste-" + schema, data="06/09/2026", questoes=questions)
    result = scope["preparar_importacao_simulado"](payload)
    assert not result["erros"], result["erros"]
    for row in result["registros"]:
        row["horario"] = "12:00:00"
    fixtures.append(dict(input=payload, expected=result["registros"]))
resources = android / "app/src/test/resources"
save(resources / "catalog.json", catalog)
save(resources / "import-parity.json", fixtures)
print("Exported web catalogs and workout profiles, original prompts/videos and 2 Python import parity fixtures.")
