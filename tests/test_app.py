"""Run every existing page and a save lifecycle against demo data only."""
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


class AppTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"SOLEM_DEMO":"1"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.app = AppTest.from_file(str(APP), default_timeout=30).run()

    def test_all_pages_with_records_and_empty_history(self):
        pages = self.app.radio(key="solem_page").options
        self.assertNotIn("Login", pages)
        for empty in (False, True):
            if empty:
                self.app.session_state["solem_demo_records"] = []
            for page in pages:
                with self.subTest(page=page, empty=empty):
                    self.app.radio(key="solem_page").set_value(page).run()
                    self.assertFalse(self.app.exception, [e.message for e in self.app.exception])

    def test_quick_action_and_save_recalculates_xp(self):
        from solem_progress import calculate_progress
        before = calculate_progress(self.app.session_state["solem_demo_records"])["xp"]
        self.app.button(key="go_treino").click().run()
        self.assertEqual(self.app.radio(key="solem_page").value, "Treino")
        next(w for w in self.app.number_input if w.label == "Repetições (Total)").set_value(12)
        next(b for b in self.app.button if b.label == "Salvar treino").click().run()
        self.assertFalse(self.app.exception)
        after = calculate_progress(self.app.session_state["solem_demo_records"])["xp"]
        self.assertEqual(after - before, 45)  # first workout + body/mind bonus
        self.assertTrue(self.app.toast)
        self.app.radio(key="solem_page").set_value("Visão geral").run()
        self.assertFalse(self.app.exception)

    def test_workout_history_updates_when_exercise_changes(self):
        self.app.session_state["solem_demo_records"].extend([
            {"id": 1001, "data": "2026-09-20", "horario": "08:00:00", "grupo_muscular": "Cardio",
             "exercicio": "Caminhada", "repeticoes": 0, "distancia_km": 2.5, "duracao_min": 30,
             "carga_kg": 0.0, "dados_extras": {}},
            {"id": 1002, "data": "2026-09-21", "horario": "08:00:00", "grupo_muscular": "Cardio",
             "exercicio": "Caminhada", "repeticoes": 0, "distancia_km": 3.5, "duracao_min": 40,
             "carga_kg": 0.0, "dados_extras": {}},
        ])
        self.app.radio(key="solem_page").set_value("Treino").run()
        self.app.selectbox(key="treino_exercicio").set_value("Caminhada").run()
        self.assertFalse(self.app.exception)
        values = {metric.label: metric.value for metric in self.app.metric}
        self.assertEqual(values["Recorde registrado"], "3.50 km")
        self.app.selectbox(key="treino_exercicio").set_value("Flexão").run()
        self.assertFalse(self.app.exception)
        values = {metric.label: metric.value for metric in self.app.metric}
        self.assertTrue(values["Recorde registrado"].endswith("rep"))

    def test_workout_fields_change_with_selected_exercise(self):
        self.app.radio(key="solem_page").set_value("Treino").run()
        self.app.selectbox(key="treino_exercicio").set_value("Prancha").run()
        self.assertFalse(self.app.exception)
        labels = {widget.label for widget in self.app.number_input}
        self.assertIn("Tentativas / repetições", labels)
        self.assertIn("Tempo sustentado (seg)", labels)
        self.assertNotIn("Duração (min)", labels)
        self.assertNotIn("Distância (km)", labels)
        next(w for w in self.app.number_input if w.label == "Tentativas / repetições").set_value(5)
        next(w for w in self.app.number_input if w.label == "Tempo sustentado (seg)").set_value(45)
        self.app.selectbox(key="treino_exercicio").set_value("Caminhada").run()
        self.assertFalse(self.app.exception)
        labels = {widget.label for widget in self.app.number_input}
        self.assertIn("Duração (min)", labels)
        self.assertIn("Distância (km)", labels)
        self.assertNotIn("Carga (kg)", labels)
        self.assertNotIn("Repetições (Total)", labels)
        self.app.number_input(key="treino_distancia").set_value(2.5)
        next(w for w in self.app.number_input if w.label == "Duração (min)").set_value(30)
        next(b for b in self.app.button if b.label == "Salvar treino").click().run()
        self.assertFalse(self.app.exception)
        saved = self.app.session_state["solem_demo_records"][-1]
        self.assertEqual(saved["exercicio"], "Caminhada")
        self.assertEqual(saved["repeticoes"], 0)
        self.assertEqual(saved["dados_extras"]["isometria_segundos"], 0)
        self.assertEqual(saved["distancia_km"], 2.5)

    def test_workout_history_reads_beyond_first_supabase_page(self):
        self.app.session_state["solem_demo_records"] = [
            {"id": index, "data": "2026-09-20", "horario": "08:00:00", "grupo_muscular": "Peitoral",
             "exercicio": "Flexão", "repeticoes": 1, "distancia_km": 0.0, "duracao_min": 0,
             "carga_kg": 0.0, "dados_extras": {}}
            for index in range(1, 502)
        ]
        self.app.radio(key="solem_page").set_value("Treino").run()
        self.app.selectbox(key="treino_exercicio").set_value("Flexão").run()
        self.assertFalse(self.app.exception)
        values = {metric.label: metric.value for metric in self.app.metric}
        self.assertEqual(values["Média por dia treinado"], "501 rep")


if __name__ == "__main__":
    unittest.main()
