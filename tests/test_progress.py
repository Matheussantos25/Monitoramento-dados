import unittest
from datetime import date
from solem_progress import calculate_progress


class ProgressTests(unittest.TestCase):
    today = date(2026, 9, 4)

    def row(self, group="Peitoral", day="2026-09-04", **values):
        return dict(data=day, grupo_muscular=group, repeticoes=values.pop("repeticoes", 10), **values)

    def calc(self, records):
        return calculate_progress(records, self.today)

    def test_empty_history(self):
        p = self.calc([])
        self.assertEqual((p["xp"], p["level"], p["streak"], p["week_days"]), (0, 1, 0, 0))

    def test_daily_cap_and_dual_bonus(self):
        p = self.calc([self.row()] * 6 + [self.row("Estudos")] * 4)
        self.assertEqual(p["xp"], 75)
        self.assertEqual(p["week_workouts"], 1)

    def test_food_earns_same_points_regardless_of_group(self):
        p = self.calc([self.row("Nutrição", alimentacao_besteirol="Pizza")])
        self.assertEqual(p["xp"], 10)

    def test_weight_empty_and_future_do_not_score(self):
        p = self.calc([self.row("Métricas", peso_corporal=70), self.row(day="2027-01-01"),
                       self.row(repeticoes=0), self.row(day="invalid"), self.row("Nutrição")])
        self.assertEqual(p["xp"], 0)

    def test_yesterday_keeps_streak(self):
        p = self.calc([self.row(day="2026-09-03"), self.row(day="2026-09-02")])
        self.assertEqual(p["streak"], 2)

    def test_pause_keeps_xp_but_resets_streak(self):
        p = self.calc([self.row(day="2026-09-02")])
        self.assertEqual((p["streak"], p["xp"]), (0, 30))

    def test_json_anki_video_and_exact_duration(self):
        p = self.calc([
            self.row("Estudos", repeticoes=0, dados_extras='{"tempo_video": 25}'),
            self.row("Estudos", repeticoes=50, duracao_min=12, dados_extras={"fonte_questoes":"Anki"}),
            self.row("Estudos", duracao_min=1, dados_extras={"tempo_segundos_exato":90,"q_certas":8,"q_erradas":2}),
        ])
        self.assertEqual(p["study_minutes"], 38.5)
        self.assertEqual(p["questions"], 10)
        self.assertEqual(p["xp"], 30)

    def test_week_starts_on_monday(self):
        p = self.calc([self.row(day="2026-08-30"), self.row(day="2026-08-31")])
        self.assertEqual(p["week_workouts"], 1)
        self.assertEqual(p["week"][0], date(2026, 8, 31))

    def test_levels_and_recalculation_after_delete(self):
        records = [self.row(day=f"2026-08-{i:02}") for i in range(1, 11)]
        self.assertEqual(self.calc(records)["level"], 2)
        self.assertEqual(self.calc(records[:1])["level"], 1)

    def test_malformed_values_are_ignored(self):
        p = self.calc([self.row(repeticoes=float("nan"), dados_extras="not json"),
                       self.row("Estudos", repeticoes=-10, dados_extras={"tempo_video":float("inf")})])
        self.assertEqual(p["xp"], 0)


if __name__ == "__main__":
    unittest.main()
