import ast
from pathlib import Path

from solem_exercise_guide import guide_catalog, guide_payload

ROOT = Path(__file__).resolve().parents[1]


def test_all_preset_exercises_have_explicit_guide_or_pending_reason():
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf8"))
    presets = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "EXERCICIOS_PRESETADOS" for t in n.targets))
    for name in [name for group in presets.values() for name in group]:
        assert name in guide_catalog()["guides"]
        assert guide_payload(name)["guide"]["cues"]


def test_offline_assets_identical_and_lightweight():
    source = (ROOT / "assets/exercise_guides.json").read_bytes()
    assert len(source) < 350000
    for relative in ("main/assets", "test/resources"):
        assert source == (ROOT / f"android-app/app/src/{relative}/exercise_guides.json").read_bytes()


def test_grips_are_different_and_unknown_does_not_guess():
    pronated = guide_payload("Barra Fixa (Pronada)")
    supinated = guide_payload("Barra Fixa (Supinada)")
    assert pronated["grip"]["shapes"] != supinated["grip"]["shapes"]
    assert pronated["motion"] != supinated["motion"]
    assert "dorso" in pronated["grip"]["caption"].lower()
    assert "palmas" in supinated["grip"]["caption"].lower()
    assert guide_payload("Meu exercício <script>")["motion"] is None
    assert guide_payload("Abdominal Levantada")["guide"]["motion"] == "legraise"
    assert guide_payload("Remada em Pé na Polia")["guide"]["motion"] == "standingrow"
    assert guide_payload("Mewing com borracha")["motion"] is None


def test_vectors_valid_and_static_holds_static():
    data = guide_catalog()
    for guide in data["guides"].values():
        if guide["motion"]:
            assert guide["motion"] in data["motions"]
    for motion in data["motions"].values():
        assert len(motion["frames"]) in (1,9)
        for frame in motion["frames"]:
            assert len(frame) == len(motion["shapes"])
            for shape,coords in zip(motion["shapes"],frame):
                assert all(-10 <= value <= 450 for value in coords)
                if shape["kind"] == "ellipse":
                    assert len(coords)==4 and coords[2]>0 and coords[3]>0
                else:
                    expected=sum({"M":2,"L":2,"Q":4,"C":6,"Z":0}[c] for c in shape["commands"])
                    assert len(coords)==expected
        assert all([len(c) for c in frame]==[len(c) for c in motion["frames"][0]] for frame in motion["frames"])
    for exercise in ("Prancha", "L-Sit", "Handstand (Parada de Mãos)"):
        assert len(guide_payload(exercise)["motion"]["frames"]) == 1


def test_component_does_not_write_data_or_fetch_media():
    source = "\n".join((ROOT / f"assets/exercise_guide/{name}").read_text(encoding="utf8") for name in ("index.html","guide.js","figure.js"))
    for forbidden in ("fetch(", "XMLHttpRequest", "streamlit:setComponentValue", "innerHTML", "<video", "<iframe"):
        assert forbidden not in source
    assert 'document.hidden' in source
    assert 'prefers-reduced-motion' in source
    assert 'requestAnimationFrame' in source
    assert 'opacity' not in (ROOT / "assets/exercise_guide/guide.js").read_text(encoding="utf8")


def test_switching_guides_keeps_workout_records_unchanged():
    import os
    from copy import deepcopy
    from unittest.mock import patch
    from streamlit.testing.v1 import AppTest
    with patch.dict(os.environ, {"SOLEM_DEMO": "1", "SOLEM_DEMO_PROFILE": "personal"}):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        before = deepcopy(app.session_state["solem_demo_records"])
        app.radio(key="solem_page").set_value("Treino").run()
        for name in ("Barra Fixa (Pronada)", "Barra Fixa (Supinada)", "Prancha", "Abdominal Levantada"):
            app.selectbox(key="treino_exercicio").set_value(name).run()
            assert not app.exception
            assert app.session_state["solem_demo_records"] == before
