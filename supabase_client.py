from __future__ import annotations

from typing import Any

import streamlit as st
from supabase import create_client, Client


def supabase_enabled() -> bool:
    return bool(st.secrets.get("SUPABASE_URL")) and bool(st.secrets.get("SUPABASE_ANON_KEY"))


def _base_client() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])


def _authed_client(access_token: str) -> Client:
    sb = _base_client()
    # Important: imposta JWT per PostgREST (RLS)
    sb.postgrest.auth(access_token)
    return sb


def sign_up(email: str, password: str) -> dict[str, Any]:
    sb = _base_client()
    res = sb.auth.sign_up({"email": email, "password": password})
    return {"user": res.user, "session": res.session}


def sign_in(email: str, password: str) -> dict[str, Any]:
    sb = _base_client()
    res = sb.auth.sign_in_with_password({"email": email, "password": password})
    return {"user": res.user, "session": res.session}


def sign_out(access_token: str) -> None:
    sb = _authed_client(access_token)
    sb.auth.sign_out()


def fetch_subscriptions(access_token: str, user_id: str) -> list[dict]:
    sb = _authed_client(access_token)
    res = (
        sb.table("user_subscriptions")
        .select("*")
        .eq("user_id", user_id)
        .order("data_aggiunto", desc=True)
        .execute()
    )
    return res.data or []


def upsert_subscription(access_token: str, row: dict) -> dict:
    sb = _authed_client(access_token)
    res = sb.table("user_subscriptions").upsert(row).execute()
    return (res.data or [{}])[0]


def delete_subscription(access_token: str, sub_id: str, user_id: str) -> None:
    sb = _authed_client(access_token)
    sb.table("user_subscriptions").delete().eq("id", sub_id).eq("user_id", user_id).execute()


def fetch_profile(access_token: str, user_id: str) -> dict:
    sb = _authed_client(access_token)
    res = sb.table("user_profiles").select("*").eq("user_id", user_id).maybe_single().execute()
    return res.data or {}


def upsert_profile(access_token: str, row: dict) -> dict:
    sb = _authed_client(access_token)
    res = sb.table("user_profiles").upsert(row).execute()
    return (res.data or [{}])[0]


def fetch_challenge(access_token: str, user_id: str) -> dict:
    sb = _authed_client(access_token)
    res = sb.table("user_challenges").select("*").eq("user_id", user_id).maybe_single().execute()
    return res.data or {}


def upsert_challenge(access_token: str, row: dict) -> dict:
    sb = _authed_client(access_token)
    res = sb.table("user_challenges").upsert(row).execute()
    return (res.data or [{}])[0]
