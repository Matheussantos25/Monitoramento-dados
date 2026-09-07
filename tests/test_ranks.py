import unittest
from datetime import date
from solem_ranks import ranks

class RankTests(unittest.TestCase):
    def test_reps_are_already_totals_and_deduplicated(self):
        row = dict(id=1, data='2026-09-01', grupo_muscular='Pernas', repeticoes=100, series=10)
        result = ranks([row, row, dict(row, id=2, data='2099-01-01')], {}, date(2026,9,7))
        self.assertEqual((result['reps'], result['physical_rank']), (100, 'Bronze'))

    def test_placement_and_sample_gate(self):
        def row(n):
            return dict(data='2026-09-01', grupo_muscular='Estudos', exercicio='Português', dados_extras={'topico_edital':'Sintaxe', 'q_certas':n})
        self.assertEqual(ranks([row(19)], {'Português':['Sintaxe']})['topics'][0]['rank'], 'Em colocação')
        self.assertEqual(ranks([row(20)], {'Português':['Sintaxe']})['topics'][0]['rank'], 'Bronze')
        self.assertEqual(ranks([row(200)], {'Português':['Sintaxe']})['topics'][0]['rank'], 'Mestre')

    def test_exact_topic_with_comma_and_ambiguous_session(self):
        row = dict(data='2026-09-01', grupo_muscular='Estudos', exercicio='P', dados_extras={'topico_edital':'A, B', 'q_certas':30})
        self.assertEqual(ranks([row], {'P':['A, B']})['topics'][0]['total'], 30)
        self.assertEqual(ranks([row], {'P':['A','B']})['ignored'], 30)
