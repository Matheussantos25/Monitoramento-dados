from datetime import date
from io import BytesIO

import pytest
from PIL import Image

from solem_health import (base_record, daily_water_ml, private_weight_history, sleep_minutes,
                          training_category_stats, training_measure_stats, training_recommendation, training_stats)
from solem_photos_ui import normalized_jpeg


def test_water_accumulates_only_valid_entries():
    day = date(2026, 9, 23)
    rows = [base_record(day, "10:00:00", "Nutrição", "Água", extras={"volume_ml":750,"quantidade":5}),
            base_record(day, "13:00:00", "Nutrição", "Água", extras={"volume_ml":250,"quantidade":1}),
            base_record(day, "14:00:00", "Nutrição", "Refeição Diária", alimentacao_saudavel="Banana")]
    assert daily_water_ml(rows, day) == 4000
    assert daily_water_ml(rows, date(2026, 9, 22)) == 0


def test_sleep_crosses_midnight_and_rejects_invalid_duration():
    assert sleep_minutes("23:00", "07:00") == 480
    with pytest.raises(ValueError):
        sleep_minutes("07:00", "07:00")


def test_training_summary_and_recovery_suggestion():
    rows = [base_record("2026-09-20", "08:00:00", "Peitoral", "Flexão", repeticoes=30),
            base_record("2026-09-20", "09:00:00", "Peitoral", "Flexão", repeticoes=20),
            base_record("2026-09-22", "08:00:00", "Peitoral", "Flexão", repeticoes=40)]
    stats = training_stats(rows, "Flexão")
    assert stats["days"] == 2
    assert stats["average_reps_per_day"] == 45
    assert stats["best"]["repeticoes"] == 40
    category = training_category_stats(rows, "Peitoral")
    assert category["days"] == 2
    assert category["average_reps_per_day"] == 45
    assert training_recommendation(rows, date(2026, 9, 23))["group"] == "Costas"


def test_training_measure_is_specific_to_exercise_and_cardio_unit():
    rows = [base_record("2026-09-20", "08:00:00", "Peitoral", "Flexão", repeticoes=30),
            base_record("2026-09-21", "08:00:00", "Peitoral", "Flexão", repeticoes=40),
            base_record("2026-09-22", "08:00:00", "Cardio", "Caminhada", distancia_km=2.5),
            base_record("2026-09-23", "08:00:00", "Cardio", "Caminhada", distancia_km=3.5)]
    flexao = training_measure_stats(rows, "Flexão")
    caminhada = training_measure_stats(rows, "Caminhada")
    assert (flexao["unit"], flexao["record"], flexao["average_per_day"]) == ("rep", 40, 35)
    assert (caminhada["unit"], caminhada["record"], caminhada["average_per_day"]) == ("km", 3.5, 3)
    assert caminhada["last_day"] == date(2026, 9, 23)


def test_weight_chart_only_uses_private_weight_entries():
    rows = [{"kind": "meal", "day": "2026-09-23", "details": {"kg": 80}},
            {"kind": "weight", "day": "2026-09-23", "details": {"kg": 68.1}},
            {"kind": "weight", "day": "2026-09-20", "details": {"kg": 68.5}},
            {"kind": "weight", "day": "invalid", "details": {"kg": 70}}]
    assert private_weight_history(rows) == [(date(2026, 9, 20), 68.5), (date(2026, 9, 23), 68.1)]


def test_photo_reencoding_strips_metadata():
    image = Image.new("RGB", (10, 10), "red")
    source = BytesIO()
    image.save(source, format="JPEG", exif=b"Exif\x00\x00GPS fake metadata")
    processed = normalized_jpeg(source.getvalue())
    assert processed.startswith(b"\xff\xd8\xff")
    assert b"GPS fake metadata" not in processed
