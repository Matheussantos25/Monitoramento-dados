"""Browser-owned persistent Supabase session, server-validated short-lived access.

No password/refresh token is stored by Python, in URLs, cookies or launchers.
The browser SDK handles refresh-token rotation and cross-tab locking.
"""
import base64
import json
import time
from pathlib import Path
from uuid import uuid4
import streamlit as st
import streamlit.components.v1 as components

browser_component = components.declare_component(
    "solem_browser_login", path=str(Path(__file__).parent / "assets/auth_login"))


def access_expiry(token):
    """Untrusted parsing only for expiry routing, NEVER proof of authentication."""
    if not isinstance(token, str) or len(token) > 16000:
        return 0
    try:
        pieces = token.split(".")
        if len(pieces) != 3:
            return 0
        body = json.loads(base64.urlsafe_b64decode(pieces[1] + "=" * (-len(pieces[1]) % 4)))
        if not isinstance(body, dict):
            return 0
        exp = body.get("exp", 0)
        return int(exp) if type(exp) in (int, float) else 0
    except (ValueError, TypeError, KeyError, OverflowError):
        return 0


def clear_account_state():
    # Preserve only this iframe's handshake while changing authenticated users.
    for key in list(st.session_state):
        if not str(key).startswith("_auth_"):
            del st.session_state[key]
    for key in ("_auth_verified_access", "_auth_user_id"):
        st.session_state.pop(key, None)


def queue_command(action):
    st.session_state["_auth_command"] = dict(action=action, id=str(uuid4()))


def request_logout():
    clear_account_state()
    queue_command("signout")


def require_browser_login(client, url, public_key):
    command = st.session_state.get("_auth_command")
    event = browser_component(url=url, public_key=public_key, command=command,
                              key="_auth_bridge", default=None)
    if not isinstance(event, dict) or event.get("ready") is not True:
        st.stop()
    if command:
        # Never accept a stale signed-in component value while logout is pending.
        if event.get("ack") != command["id"]:
            st.stop()
        st.session_state.pop("_auth_command", None)
    token = event.get("access_token")
    if not token:
        clear_account_state()
        st.stop()
    if access_expiry(token) <= time.time() + 90:
        queue_command("refresh")
        st.rerun()
    if token != st.session_state.get("_auth_verified_access"):
        try:
            # Supabase Python calls get_user(access_token) here. The decoded JWT
            # above and all browser-provided identity claims are untrusted.
            verified = client.auth.set_session(token, "")
            if not verified.user or not verified.session:
                raise ValueError("Unverified session")
        except Exception as error:
            status = getattr(error, "status", None)
            if status in (400, 401, 403) or isinstance(error, ValueError):
                request_logout()
                st.rerun()
            st.error("Não foi possível validar sua sessão. Confira a conexão e tente novamente; seu acesso salvo não foi apagado.")
            st.button("Tentar validar novamente", key="_auth_retry")
            st.stop()
        previous = st.session_state.get("_auth_user_id")
        if previous and previous != str(verified.user.id):
            clear_account_state()
        st.session_state["private_client"] = client
        st.session_state["_auth_user_id"] = str(verified.user.id)
        st.session_state["_auth_verified_access"] = token
    if event.get("storage_blocked"):
        st.warning("Este navegador não permitiu salvar o acesso. Você entrou, mas poderá precisar entrar novamente ao fechar a página.")
    return client
