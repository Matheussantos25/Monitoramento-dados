import unittest
from datetime import date
from solem_calendar import monthly_activity, latest_weight

class CalendarTests(unittest.TestCase):
    def test_calendar_handles_leap_year_and_monday_offset(self):
        days = monthly_activity([],2024,2,date(2024,3,1))
        self.assertEqual(len(days),29)
        self.assertEqual(next(iter(days)).weekday(),3)

    def test_time_and_days_are_not_estimated_from_repetitions(self):
        rows = [dict(data='2026-09-02',grupo_muscular='Peitoral',exercicio='Flexão',repeticoes=20),
            dict(data='2026-09-02',grupo_muscular='Estudos',exercicio='Anki',duracao_min=60,dados_extras={'tempo_segundos_exato':90,'tempo_video':10})]
        day = monthly_activity(rows,2026,9,date(2026,9,7))[date(2026,9,2)]
        self.assertTrue(day['study'] and day['workout'])
        self.assertEqual(day['study_minutes'],11.5)
        self.assertEqual(day['workout_minutes'],0)
        self.assertEqual(day['reps'],20)

    def test_empty_future_and_weight_only_do_not_mark_activity(self):
        rows = [dict(data='2026-09-02',grupo_muscular='Estudos'),dict(data='2026-09-08',grupo_muscular='Pernas',repeticoes=20),dict(data='2026-09-02',grupo_muscular='Métricas',peso_corporal=70)]
        days=monthly_activity(rows,2026,9,date(2026,9,7))
        self.assertFalse(any(d['study'] or d['workout'] for d in days.values()))

    def test_latest_weight_is_dated_not_guessed(self):
        rows = [dict(data='2026-09-02',peso_corporal=70),dict(data='2026-09-03',peso_corporal=0),dict(data='2026-10-01',peso_corporal=90),dict(data='invalid',peso_corporal=100)]
        self.assertEqual(latest_weight(rows,date(2026,9,7)),(70,date(2026,9,2)))
        self.assertIsNone(latest_weight([],date(2026,9,7)))
