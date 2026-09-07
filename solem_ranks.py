"""Personal game ranks, not competitive Elo or estimates of fitness."""
from datetime import date
from solem_progress import number, extras_of, record_date, category_of

NAMES = ['Ferro', 'Bronze', 'Prata', 'Ouro', 'Platina', 'Esmeralda', 'Diamante', 'Mestre']
REP_LIMITS = [0, 100, 500, 1500, 3500, 7000, 12000, 20000]
ACCURACY_LIMITS = [0, 40, 50, 60, 70, 80, 90, 95]
SAMPLE_LIMITS = [20, 20, 30, 40, 60, 80, 120, 200]

def ranks(records, topics, today=None):
    today = today or date.today()
    stats = {(d, t): [0, 0] for d, ts in topics.items() for t in ts if 'Simulado' not in t}
    reps = 0
    ignored = 0
    seen = set()
    for row in records:
        identity = row.get('id')
        if identity is not None:
            if identity in seen:
                continue
            seen.add(identity)
        day = record_date(row.get('data'))
        if day is None or day > today:
            continue
        if category_of(row) == 'treino':
            reps += int(number(row.get('repeticoes')))
        if row.get('grupo_muscular') != 'Estudos':
            continue
        extra = extras_of(row.get('dados_extras'))
        if extra.get('fonte_questoes') == 'Anki':
            continue
        correct = int(number(extra.get('q_certas')))
        wrong = int(number(extra.get('q_erradas')))
        key = (row.get('exercicio'), extra.get('topico_edital', extra.get('topico', '')))
        if key not in stats:
            ignored += correct + wrong
            continue
        stats[key][0] += correct
        stats[key][1] += wrong
    result = []
    for (discipline, topic), (correct, wrong) in stats.items():
        total = correct + wrong
        accuracy = correct * 100 / total if total else 0
        tier = max((i for i in range(8) if total >= SAMPLE_LIMITS[i] and accuracy >= ACCURACY_LIMITS[i]), default=-1)
        result.append(dict(discipline=discipline, topic=topic, correct=correct, total=total,
                           accuracy=accuracy, tier=tier, rank=NAMES[tier] if tier >= 0 else 'Em colocação'))
    tier = max(i for i, limit in enumerate(REP_LIMITS) if reps >= limit)
    return dict(reps=reps, physical_tier=tier, physical_rank=NAMES[tier], topics=result, ignored=ignored)
