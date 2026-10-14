"""Exercise the actual entrypoint assignment even with a stale imported helper."""
import ast
from pathlib import Path
from types import SimpleNamespace
import pytest

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.mark.parametrize("personal,demo,expected", [
    (True, False, "treinos"),
    (False, False, "solem_activities"),
    (False, True, "treinos"),
])
def test_entrypoint_does_not_call_old_cached_boolean_helper(personal, demo, expected):
    tree = ast.parse(APP.read_text(encoding="utf-8"))
    statement = next(node for node in tree.body if isinstance(node, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "ACTIVITY_TABLE" for t in node.targets))
    # Exactly the old helper retained by a running worker before the deployment.
    old_helper = lambda generic: "solem_activities" if generic else "treinos"
    assert old_helper("msdof25@gmail.com") == "solem_activities"
    scope = dict(IS_DEMO=demo, PERSONAL_JOURNEY=personal, activity_table=old_helper,
                 account_user=SimpleNamespace(email="msdof25@gmail.com" if personal else "new@example.test"))
    exec(compile(ast.Module(body=[statement], type_ignores=[]), str(APP), "exec"), scope)
    assert scope["ACTIVITY_TABLE"] == expected
