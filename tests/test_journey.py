from copy import deepcopy
from datetime import date, timedelta
import pytest
from solem_journey import JourneyStore, preferences, creator_progress, validate_creator
from solem_checkup import daily_checkup
from solem_progress import calculate_progress

TODAY = date(2026, 10, 10)


def setup_store():
    state = {}
    repo = JourneyStore(demo_state=state)
    channel = repo.save_item(dict(kind="channel", title="Canal principal · Gacha"))
    return repo, state, channel


def video(channel, **extra):
    return dict(kind="video", title="Episódio 1", channel_id=channel["id"],
                stage="Pronto", produced_on=str(TODAY), **extra)


def test_personal_targets_do_not_change_other_accounts_or_legacy_history():
    personal = preferences(personal=True)
    generic = preferences(generic=True)
    assert personal["targets"]["flexao"] == personal["targets"]["agachamento"] == 100
    assert personal["targets"]["cardio"] == 5
    assert personal["targets"]["created"] == personal["targets"]["published"] == 2
    assert not {"questions", "study"} & set(personal["enabled"])
    assert "mewing" not in generic["enabled"]
    assert generic["targets"]["flexao"] == 10
    assert {"questions", "study"} <= set(generic["enabled"])
    history = [dict(data=str(TODAY), grupo_muscular="Pernas", exercicio="Agachamento", repeticoes=60)]
    original = deepcopy(history)
    before = calculate_progress(history, TODAY)
    goals = {g["id"]: g for g in daily_checkup(history, [], TODAY, preferences=personal, creator_items=[])}
    assert goals["agachamento"]["value"] == 60 and not goals["agachamento"]["done"]
    assert calculate_progress(history, TODAY) == before and history == original


def test_video_lifecycle_edits_soft_delete_restore_and_two_channels():
    repo, _, channel = setup_store()
    first = repo.save_item(video(channel))
    second_channel = repo.save_item(dict(kind="channel", title="Outro canal"))
    second = repo.save_item(video(second_channel))
    stats = creator_progress(repo.load()["items"], TODAY)
    assert (stats["created"], stats["published"], stats["xp"]) == (2, 0, 40)
    published = repo.save_item(dict(first, stage="Publicado", published_on=str(TODAY)), first)
    renamed = repo.save_item(dict(published, title="Título revisado"), published)
    stats = creator_progress(repo.load()["items"], TODAY)
    assert (stats["created"], stats["published"], stats["xp"]) == (2, 1, 70)
    repo.archive(renamed)
    assert creator_progress(repo.load()["items"], TODAY)["xp"] == 20
    archived = next(r for r in repo.load()["items"] if r["id"] == renamed["id"])
    repo.archive(archived, False)
    assert creator_progress(repo.load()["items"], TODAY)["xp"] == 70
    assert next(r for r in repo.load()["items"] if r["id"] == second["id"])["revision"] == 1


def test_progress_ignores_future_rows_and_duplicate_ids():
    repo, _, channel = setup_store()
    row = repo.save_item(video(channel))
    assert creator_progress([row, row], TODAY)["xp"] == 20
    assert creator_progress([dict(row, produced_on=str(TODAY + timedelta(days=1)))], TODAY)["xp"] == 0
    assert creator_progress([dict(row, stage="Ideia", produced_on=None)], TODAY)["xp"] == 0
    assert creator_progress([row], TODAY + timedelta(days=1))["created"] == 0


def test_unavailable_creator_data_is_not_zero_and_custom_goals_apply():
    prefs = preferences(personal=True)
    prefs["targets"]["flexao"] = 120
    goals = {g["id"]: g for g in daily_checkup([], None, TODAY, preferences=prefs)}
    assert goals["created"]["value"] is None and not goals["created"]["done"]
    assert goals["water"]["value"] is None
    assert goals["flexao"]["target"] == 120
    assert "questions" not in goals and "study" not in goals


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf"), True, "100", 10001, 1.5])
def test_bad_targets_rejected(value):
    with pytest.raises(ValueError):
        preferences({"targets": {"flexao": value}})


def test_settings_persist_and_stale_writes_do_not_overwrite():
    repo, state, channel = setup_store()
    prefs = preferences(personal=True)
    repo.save_settings(prefs)
    snapshot = repo.load()["settings"]
    changed = deepcopy(prefs)
    changed["targets"]["flexao"] = 150
    repo.save_settings(changed, snapshot)
    with pytest.raises(ValueError):
        repo.save_settings(prefs, snapshot)
    assert JourneyStore(demo_state=state).load()["settings"]["preferences"]["targets"]["flexao"] == 150
    assert JourneyStore(demo_state=state, demo_owner="another").load() == dict(settings=None, items=[])
    row = repo.save_item(video(channel))
    repo.save_item(dict(row, title="Revisado"), row)
    with pytest.raises(ValueError):
        repo.save_item(dict(row, title="Antigo"), row)


def test_video_dates_links_and_channel_validation():
    repo, _, channel = setup_store()
    for changes in (dict(stage="Publicado"), dict(stage="Ideia"), dict(url="javascript:alert(1)"),
                    dict(stage="Publicado", published_on="2026-10-09"), dict(produced_on="invalid")):
        with pytest.raises(ValueError):
            validate_creator(dict(video(channel), **changes))
    with pytest.raises(ValueError):
        repo.save_item(dict(video(channel), channel_id="00000000-0000-4000-8000-000000000001"))


def test_settings_map_is_validated_and_unknown_goals_rejected():
    with pytest.raises(ValueError):
        preferences(dict(strategy="Canal\n   Indentação inválida"))
    with pytest.raises(ValueError):
        preferences(dict(enabled=["unknown"]))


def test_multi_channel_goal_is_aggregate_and_not_per_render():
    repo, _, channel = setup_store()
    repo.save_item(dict(video(channel), stage="Publicado", published_on=str(TODAY)))
    repo.save_item(dict(video(channel), title="Episódio 2", stage="Publicado", published_on=str(TODAY)))
    for _ in range(3):
        goals = {g["id"]: g for g in daily_checkup([], [], TODAY, preferences=preferences(personal=True), creator_items=repo.load()["items"])}
        assert goals["created"]["done"] and goals["published"]["done"]
        assert goals["created"]["value"] == goals["published"]["value"] == 2
