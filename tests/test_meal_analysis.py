import json
from io import BytesIO

import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest

from solem_meal_analysis import catalog, nutrition, meal_details, day_nutrition
from solem_photos_ui import normalized_jpeg

RICE = {"name": "Arroz", "food_id": "169757", "grams": 150, "confidence": "high"}


def test_verified_catalog_and_platform_parity():
    foods = catalog()
    assert len(foods) == 24
    assert all(food["name"] and food["source_url"].startswith("https://fdc.nal.usda.gov/") for food in foods)
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    for file in ("android-app/app/src/main/assets/nutrition_catalog.json", "android-app/app/src/test/resources/nutrition_catalog.json"):
        assert json.loads((root/file).read_text(encoding="utf-8")) == foods


def test_nutrition_uses_source_not_model_numbers():
    result=nutrition([RICE])
    assert result["totals"]["kcal"] == 195
    assert result["totals"]["protein_g"] == 4
    assert result["complete"]
    assert nutrition([{**RICE,"grams":50}])["totals"]["kcal"] == 65
    for missing in ({**RICE,"food_id":"unknown"},{**RICE,"grams":0}):
        result=nutrition([RICE,missing])
        assert result["totals"]["kcal"] == 195
        assert result["missing"] == 1 and not result["complete"]


@pytest.mark.parametrize("grams", [-1,2001,float("nan"),float("inf"),"100",True])
def test_bad_portions(grams):
    with pytest.raises(ValueError): nutrition([{**RICE,"grams":grams}])


def test_private_payload_and_daily_partial():
    details=meal_details("Almoço",[RICE])
    assert "image" not in json.dumps(details) and "google" not in json.dumps(details)
    assert len(json.dumps(details,ensure_ascii=False).encode()) < 3800
    result=day_nutrition([{"details":details},{"details":{"tipo_refeicao":"Jantar"}}])
    assert result["totals"]["kcal"] == 195 and result["partial"] and result["counted"] == 1
    assert not day_nutrition([])["counted"]


def test_progress_photo_exif_still_stripped():
    picture=Image.new("RGB",(20,20),"white")
    exif=Image.Exif(); exif[270]="private metadata"
    raw=BytesIO();picture.save(raw,"JPEG",exif=exif)
    jpeg=normalized_jpeg(raw.getvalue())
    assert not Image.open(BytesIO(jpeg)).getexif()


def test_recognition_removed_from_clients():
    from pathlib import Path
    import solem_meal_analysis as module
    root = Path(__file__).resolve().parents[1]
    health = (root / "solem_health_ui.py").read_text(encoding="utf-8")
    interface = (root / "solem_meal_photo_ui.py").read_text(encoding="utf-8")
    android = (root / "android-app/app/src/main/java/com/matheussantos/solem/ui/HealthPage.kt").read_text(encoding="utf-8")
    assert "photo_meal(" not in health
    assert "Analisar foto" not in interface and "OpenRouter" not in interface
    assert "MealPhotoForm(" not in android
    assert not hasattr(module, "invoke") and not hasattr(module, "recognize")
    assert not hasattr(module, "httpx")
    assert not (root / "android-app/app/src/main/java/com/matheussantos/solem/data/repository/MealAnalysisRepository.kt").exists()
    assert not (root / "android-app/app/src/main/java/com/matheussantos/solem/viewmodel/MealAnalysisViewModel.kt").exists()


def test_review_save_edit_recalculate_and_confirmation():
    code='''
import streamlit as st
from datetime import date
from solem_meal_analysis import nutrition
from solem_meal_photo_ui import review_meal
def save(client,day,time,kind,details,message,old=None,demo=False):
    st.session_state.saved=details
review_meal(None,date(2026,10,4),nutrition([{"name":"Arroz","food_id":"169757","grams":150,"confidence":"high"}]),save,"review",demo=True)
'''
    app=AppTest.from_string(code).run()
    assert not app.exception
    assert app.button(key="review_save").disabled
    app.number_input(key="review_grams_0").set_value(50).run()
    app.checkbox(key="review_confirmed").check().run()
    app.button(key="review_save").click().run()
    assert not app.exception
    assert app.session_state.saved["nutrition"]["totals"]["kcal"] == 65
