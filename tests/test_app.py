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


if __name__ == "__main__":
    unittest.main()
