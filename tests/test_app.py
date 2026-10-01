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

    def test_training_and_study_show_scoped_edit_delete_controls(self):
        for page, is_study in (("Treino", False), ("Estudar", True)):
            with self.subTest(page=page):
                self.app.radio(key="solem_page").set_value(page).run()
                self.assertFalse(self.app.exception)
                self.assertFalse(any(x.key == f"manage_{page}" for x in self.app.toggle))
                records = [r for r in self.app.session_state["solem_demo_records"]
                           if (r["grupo_muscular"] == "Estudos") == is_study
                           and (is_study or r["grupo_muscular"] not in ("Nutrição", "Métricas"))]
                record_id = max(r["id"] for r in records)
                self.assertTrue(self.app.button(key=f"manage_edit_{page}_{record_id}"))
                self.assertTrue(self.app.button(key=f"manage_delete_button_{page}_{record_id}"))
                self.app.button(key=f"manage_edit_{page}_{record_id}").click().run()
                self.assertEqual(self.app.session_state[f"manage_selected_{page}"], record_id)
                self.assertTrue(any(x.label == "Salvar Alterações" or "Salvar Alterações" in x.label for x in self.app.button))
                self.assertFalse(any(x.label == "Excluir registro permanentemente" for x in self.app.button))
        self.app.session_state["solem_demo_records"] = []
        for page in ("Treino", "Estudar"):
            self.app.radio(key="solem_page").set_value(page).run()
            self.assertFalse(self.app.exception)

    def test_same_exercise_sessions_can_be_edited_and_deleted_individually(self):
        from solem_health import now_local
        day = str(now_local().date())
        def session(record_id, hour):
            return dict(id=record_id, data=day, horario=hour, grupo_muscular="Pernas",
                        exercicio="Agachamento", series=1, repeticoes=20, carga_kg=0.0,
                        descanso_seg=0, duracao_min=0, distancia_km=0.0,
                        alimentacao_saudavel="", alimentacao_besteirol="", peso_corporal=0.0,
                        dados_extras={})
        self.app.session_state["solem_demo_records"] = [session(101, "08:00:00"), session(102, "18:00:00")]
        self.app.radio(key="solem_page").set_value("Treino").run()
        self.assertFalse(self.app.exception)
        self.assertTrue(self.app.button(key="manage_edit_Treino_101"))
        self.assertTrue(self.app.button(key="manage_edit_Treino_102"))
        self.app.button(key="manage_edit_Treino_101").click().run()
        next(x for x in self.app.number_input if x.label == "Repetições").set_value(25)
        next(x for x in self.app.button if "Salvar Alterações" in x.label).click().run()
        self.assertEqual([(r["id"], r["repeticoes"]) for r in self.app.session_state["solem_demo_records"]],
                         [(101, 25), (102, 20)])
        self.app.button(key="manage_delete_button_Treino_102").click().run()
        self.assertTrue(self.app.button(key="manage_confirm_Treino_102"))
        self.app.button(key="manage_confirm_Treino_102").click().run()
        self.assertEqual([(r["id"], r["repeticoes"]) for r in self.app.session_state["solem_demo_records"]],
                         [(101, 25)])

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

    def test_overview_checkup_uses_private_water_and_links_to_source_tabs(self):
        self.app.session_state["demo_health_entries"] = [{
            "id": "water-test", "day": str(self.app.session_state["solem_demo_records"][-1]["data"]),
            "logged_at": "09:00:00", "kind": "water",
            "details": {"volume_ml": 750, "quantidade": 4}}]
        self.app.run()
        self.assertFalse(self.app.exception)
        self.assertTrue(self.app.button(key="checkup_go_water"))
        self.app.button(key="checkup_go_water").click().run()
        self.assertEqual(self.app.radio(key="solem_page").value, "Saúde")

    def test_checkup_shortcuts_prefill_the_matching_exercise(self):
        for key, exercise in (("mewing", "Mewing com borracha"), ("flexao", "Flexão"),
                              ("agachamento", "Agachamento"), ("caminhada", "Caminhada"),
                              ("corrida", "Corrida")):
            with self.subTest(exercise=exercise):
                self.app.radio(key="solem_page").set_value("Visão geral").run()
                self.app.button(key=f"checkup_go_{key}").click().run()
                self.assertEqual(self.app.radio(key="solem_page").value, "Treino")
                self.assertEqual(self.app.selectbox(key="treino_exercicio").value, exercise)
                self.assertEqual(self.app.radio(key="treino_formato").value, "🏋️ Exercício Isolado (Convencional)")

    def test_overview_call_survives_stale_ui_module_during_hot_reload(self):
        # Streamlit Cloud can keep a previously imported two-argument function
        # in memory after app.py changes; the call site must remain compatible.
        with patch("solem_ui.overview", side_effect=lambda progress, records=None: None) as old_overview:
            self.app.run()
        self.assertFalse(self.app.exception)
        self.assertEqual(len(old_overview.call_args.args), 2)

    def test_health_saved_meal_and_water_can_be_edited(self):
        from solem_health import now_local
        day = str(now_local().date())
        self.app.session_state["demo_health_entries"] = [
            {"id": "meal-test", "day": day, "logged_at": "12:30:00", "kind": "meal",
             "details": {"tipo_refeicao": "Almoço", "saudaveis": ["Arroz"], "ocasionais": []}},
            {"id": "water-test", "day": day, "logged_at": "10:00:00", "kind": "water",
             "details": {"recipiente": "Garrafa", "volume_ml": 750, "quantidade": 1}},
        ]
        self.app.radio(key="solem_page").set_value("Saúde").run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.selectbox(key="new_meal_type").value, "Café da manhã")
        self.app.selectbox(key="new_meal_type").set_value("Almoço").run()
        self.assertIn("Feijão", next(w for w in self.app.multiselect
                                     if w.label == "Alimentos habituais" and w.key is None).options)
        self.app.multiselect(key="meal_good_meal-test").set_value(["Arroz", "Feijão"]).run()
        next(b for b in self.app.button if b.label == "Salvar edição").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.session_state["demo_health_entries"][0]["details"]["saudaveis"], ["Arroz", "Feijão"])
        self.app.number_input(key="water_amount_water-test").set_value(2).run()
        [b for b in self.app.button if b.label == "Salvar edição"][1].click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.session_state["demo_health_entries"][1]["details"]["quantidade"], 2)

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
