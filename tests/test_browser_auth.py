import base64
import json
import time
from types import SimpleNamespace
from unittest.mock import Mock, patch
import pytest
import solem_browser_auth as auth


class Halt(Exception): pass
class Rerun(Exception): pass


def jwt(payload=None):
    data = payload if payload is not None else {"exp": int(time.time()) + 3600}
    body = base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")
    return f"header.{body}.signature-fixture"


def gate(event, state=None, result=None, error=None):
    state = {} if state is None else state
    fake_st = SimpleNamespace(session_state=state, stop=Mock(side_effect=Halt),
                              rerun=Mock(side_effect=Rerun), error=Mock(), button=Mock(), warning=Mock())
    client = SimpleNamespace(auth=SimpleNamespace(set_session=Mock(side_effect=error,
        return_value=result or SimpleNamespace(user=SimpleNamespace(id="verified-user"), session=object()))))
    return fake_st, client, patch.object(auth, "st", fake_st), patch.object(auth, "browser_component", return_value=event)


@pytest.mark.parametrize("token", [None, 5, "not-a-token", "x." + "a"*17000 + ".x", jwt([]), jwt({"exp": "tomorrow"}), jwt({"exp": True})])
def test_untrusted_payloads_cannot_authenticate(token):
    assert auth.access_expiry(token) == 0


def test_no_content_until_component_initializes():
    st, client, p1, p2 = gate(None)
    with p1, p2, pytest.raises(Halt):
        auth.require_browser_login(client, "https://example.supabase.co", "public")
    client.auth.set_session.assert_not_called()


def test_valid_browser_token_is_verified_by_auth_not_merely_decoded():
    token=jwt()
    st, client, p1, p2=gate(dict(ready=True, access_token=token))
    with p1, p2:
        assert auth.require_browser_login(client, "https://example.supabase.co", "public") is client
        assert auth.require_browser_login(client, "https://example.supabase.co", "public") is client
    client.auth.set_session.assert_called_once_with(token, "")
    assert st.session_state["_auth_user_id"] == "verified-user"
    assert "refresh_token" not in st.session_state


def test_expired_access_requests_browser_refresh_without_using_server_refresh_token():
    st, client, p1, p2=gate(dict(ready=True, access_token=jwt({"exp":1})))
    with p1, p2, pytest.raises(Rerun):
        auth.require_browser_login(client,"https://example.supabase.co","public")
    assert st.session_state["_auth_command"]["action"] == "refresh"
    client.auth.set_session.assert_not_called()


def test_logout_waits_for_browser_ack_and_never_accepts_stale_access():
    state={"_auth_command":dict(action="signout",id="logout-one"),"private_note":"draft"}
    st, client, p1, p2=gate(dict(ready=True,access_token=jwt(),ack=None),state)
    with p1, p2, pytest.raises(Halt):
        auth.require_browser_login(client,"https://example.supabase.co","public")
    client.auth.set_session.assert_not_called()
    st, client, p1, p2=gate(dict(ready=True,access_token=None,ack="logout-one"),state)
    with p1, p2, pytest.raises(Halt):
        auth.require_browser_login(client,"https://example.supabase.co","public")
    assert "private_note" not in state and "_auth_command" not in state


def test_account_switch_clears_previous_account_drafts_and_caches():
    state={"_auth_user_id":"other-user","journey_data":{"secret":"old"},"draft":"old","_auth_bridge":{}}
    st, client, p1, p2=gate(dict(ready=True,access_token=jwt()),state)
    with p1, p2:
        auth.require_browser_login(client,"https://example.supabase.co","public")
    assert "journey_data" not in state and "draft" not in state
    assert state["_auth_user_id"] == "verified-user"


def test_forged_but_unexpired_token_is_rejected_by_provider():
    error=RuntimeError("invalid signature"); error.status=401
    st, client, p1, p2=gate(dict(ready=True,access_token=jwt()),error=error)
    with p1, p2, pytest.raises(Rerun):
        auth.require_browser_login(client,"https://example.supabase.co","public")
    assert st.session_state["_auth_command"]["action"] == "signout"
    assert "_auth_verified_access" not in st.session_state


def test_network_failure_does_not_erase_remembered_session():
    st, client, p1, p2=gate(dict(ready=True,access_token=jwt()),error=ConnectionError("offline"))
    with p1, p2, pytest.raises(Halt):
        auth.require_browser_login(client,"https://example.supabase.co","public")
    assert "_auth_command" not in st.session_state
    assert st.error.called


def test_signout_clears_private_data_and_queues_browser_removal():
    st, client, p1, p2=gate(None,{"private_client":object(),"journey_data":{},"_auth_verified_access":jwt(),"_auth_bridge":{}})
    with p1:
        auth.request_logout()
    assert "private_client" not in st.session_state and "journey_data" not in st.session_state
    assert "_auth_verified_access" not in st.session_state
    assert st.session_state["_auth_command"]["action"] == "signout"
