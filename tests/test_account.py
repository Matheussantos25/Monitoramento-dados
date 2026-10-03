from datetime import date
from solem_account import DEFAULTS, generic_account, activity_table
from solem_checkup import daily_checkup


def test_owner_is_preserved_even_if_creation_time_is_missing_or_recent():
    for created in (None, "2026-12-01T00:00:00Z", "2026-09-01T12:00:00Z"):
        assert not generic_account(" MSDOF25@GMAIL.COM ", created)


def test_only_new_accounts_get_generic_defaults_and_private_activities():
    assert not generic_account("existing@example.test", "2026-10-03T22:59:59Z")
    assert generic_account("new@example.test", "2026-10-03T23:00:00Z")
    assert generic_account("new@example.test", "2026-10-03T20:00:00-03:00")
    assert generic_account("new@example.test", None)
    assert activity_table(False) == "treinos"
    assert activity_table(True) == "solem_activities"


def test_generic_content_does_not_expose_personal_presets():
    content = str({k: v for k, v in DEFAULTS.items() if k not in ("preserved_email", "new_accounts_since")}).casefold()
    for personal in ("mewing", "massagem facial", "planche", "fgv", "dataprev", "concurso"):
        assert personal not in content
    assert len(DEFAULTS["prompts"]) >= 8
    assert "Programação" in DEFAULTS["TOPICOS_EDITAL"]


def test_legacy_goals_remain_identical_and_generic_has_no_mewing():
    original = {x["id"]: x for x in daily_checkup([], [], date.today())}
    generic = {x["id"]: x for x in daily_checkup([], [], date.today(), generic=True)}
    assert original["mewing"]["target"] == 400
    assert original["water"]["target"] == 3000
    assert original["questions"]["target"] == 150
    assert "mewing" not in generic
    assert generic["questions"]["target"] == 10


def test_custom_study_topics_do_not_mutate_defaults():
    from solem_account import personal_study_topics
    result = personal_study_topics(DEFAULTS["TOPICOS_EDITAL"], [
        {"grupo_muscular": "Estudos", "exercicio": "Design", "dados_extras": {"topico_edital": "Tipografia"}},
        {"grupo_muscular": "Peitoral", "exercicio": "Flexão"},
    ])
    assert result["Design"] == ["Tipografia"]
    assert "Design" not in DEFAULTS["TOPICOS_EDITAL"]
    assert "Flexão" not in result
