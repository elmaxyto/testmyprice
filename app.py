from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any, Optional

import requests
import streamlit as st

import config
from calculator import (
    biggest_waste,
    cost_per_use,
    euro,
    level_from_xp,
    monthly_cost,
    total_monthly,
    xp_for_action,
)
from export_image import build_social_card
from supabase_client import (
    delete_subscription,
    fetch_challenge,
    fetch_profile,
    fetch_subscriptions,
    sign_in,
    sign_out,
    sign_up,
    supabase_enabled,
    upsert_challenge,
    upsert_profile,
    upsert_subscription,
)

st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="Budget Tech ITA.png",
    layout="centered",
    initial_sidebar_state="collapsed",
)

MOBILE_CSS = """
<style>
.block-container { max-width: 760px; padding-top: 1.0rem; padding-bottom: 5rem; }
header[data-testid="stHeader"] { height: 0px; }
div[data-testid="stToolbar"] { visibility: hidden; height: 0px; }

.ss-card {
  background: #0F1B2E;
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 18px;
  padding: 14px 14px;
  margin: 10px 0;
}
.ss-row { display: flex; gap: 12px; justify-content: space-between; align-items: center; }
.ss-muted { color: rgba(229,231,235,.75); font-size: 0.92rem; }
.ss-big { font-size: 1.35rem; font-weight: 750; }
.ss-pill {
  display:inline-block; padding: 4px 10px; border-radius: 999px;
  background: rgba(34,197,94,.12); border: 1px solid rgba(34,197,94,.25);
  color: #A7F3D0; font-size: 0.84rem;
}
.ss-warn { background: rgba(245,158,11,.12); border: 1px solid rgba(245,158,11,.25); color: #FDE68A; }
.ss-bad { background: rgba(239,68,68,.12); border: 1px solid rgba(239,68,68,.25); color: #FCA5A5; }
</style>
"""
st.markdown(MOBILE_CSS, unsafe_allow_html=True)

HEADER_CSS = """
<style>
/* Remove default streamlit top padding */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
}

/* Title Styling with Gradient */
.header-title {
    font-family: 'Source Sans Pro', sans-serif;
    font-size: 3rem; /* Adjusted for horizontal layout */
    font-weight: 800;
    background: -webkit-linear-gradient(45deg, #22c55e, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    line-height: 1.1;
}
.header-subtitle {
    font-size: 1rem;
    color: #94a3b8;
    margin-top: 5px;
}
/* Fix top padding to pull title up slightly if needed */
.header-text-box {
    padding-top: 10px; 
}
</style>
"""
st.markdown(HEADER_CSS, unsafe_allow_html=True)


def ss_init():
    st.session_state.setdefault("mode", "guest")  # guest | authed
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("access_token", None)

    st.session_state.setdefault("is_premium", True)

    st.session_state.setdefault("subs_local", [])
    st.session_state.setdefault("profile_local", {"budget_mese": 0.0, "xp": 0})
    st.session_state.setdefault(
        "challenge_local",
        {
            "active": False,
            "challenge_id": None,
            "title": "",
            "days": 0,
            "started_at": None,
            "last_checkin": None,
            "streak_days": 0,
        },
    )


ss_init()


@st.cache_data(ttl=3600)
def load_presets() -> dict[str, Any]:
    url = st.secrets.get("PRESET_JSON_URL")
    if url:
        try:
            r = requests.get(url, timeout=6)
            r.raise_for_status()
            return r.json()
        except Exception:
            pass

    try:
        with open("abbonamenti_predefiniti.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"items": []}


PRESETS = load_presets()
PRESET_ITEMS: list[dict[str, Any]] = PRESETS.get("items", [])


def preset_names() -> list[str]:
    return sorted({i.get("nome", "") for i in PRESET_ITEMS if i.get("nome")})


def preset_by_name(name: str) -> Optional[dict[str, Any]]:
    for it in PRESET_ITEMS:
        if it.get("nome") == name:
            return it
    return None


def is_authed() -> bool:
    return bool(st.session_state.mode == "authed" and st.session_state.user and st.session_state.access_token)


def get_subs() -> list[dict]:
    if is_authed():
        return fetch_subscriptions(st.session_state.access_token, st.session_state.user["id"])
    return st.session_state.subs_local


def set_subs_local(subs: list[dict]) -> None:
    st.session_state.subs_local = subs


def get_profile() -> dict:
    if is_authed():
        prof = fetch_profile(st.session_state.access_token, st.session_state.user["id"])
        if not prof:
            prof = {"user_id": st.session_state.user["id"], "budget_mese": 0, "xp": 0}
            upsert_profile(st.session_state.access_token, prof)
        return prof
    return st.session_state.profile_local


def save_profile(profile: dict) -> None:
    if is_authed():
        profile["user_id"] = st.session_state.user["id"]
        upsert_profile(st.session_state.access_token, profile)
    else:
        st.session_state.profile_local = profile


def get_challenge() -> dict:
    if is_authed():
        ch = fetch_challenge(st.session_state.access_token, st.session_state.user["id"])
        return ch or {}
    return st.session_state.challenge_local


def save_challenge(ch: dict) -> None:
    if is_authed():
        ch["user_id"] = st.session_state.user["id"]
        upsert_challenge(st.session_state.access_token, ch)
    else:
        st.session_state.challenge_local = ch


def award_xp(profile: dict, action: str) -> dict:
    profile = dict(profile or {})
    profile["xp"] = int(profile.get("xp") or 0) + xp_for_action(action)
    return profile


def check_premium_key(k: str) -> bool:
    secret = st.secrets.get("PREMIUM_SHARED_KEY")
    if not secret:
        return False
    return (k or "").strip() == str(secret).strip()


def free_limit() -> int:
    return config.DEFAULT_FREE_LIMIT


col_logo, col_text = st.columns([1, 5])

with col_logo:
    st.image("Budget Tech ITA.png", width=85)

with col_text:
    st.markdown("""
    <div class="header-text-box">
        <div class="header-title">StreamSaver</div>
        <div class="header-subtitle">by Budget Tech ITA</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"<div style='text-align: center; color: #94a3b8; font-size: 1.1rem;'>{config.TAGLINE}</div>", unsafe_allow_html=True)


with st.expander("🔐 Login & Cloud Save (Supabase)", expanded=False):
    if not supabase_enabled():
        st.info("Supabase non configurato nei secrets. Puoi usare Guest Mode (salvataggio locale).")
    else:
        if is_authed():
            st.success(f"Loggato come: {st.session_state.user.get('email')}")
            if st.button("Esci (logout)", use_container_width=True):
                try:
                    sign_out(st.session_state.access_token)
                except Exception:
                    pass
                st.session_state.mode = "guest"
                st.session_state.user = None
                st.session_state.access_token = None
                st.rerun()
        else:
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("Email", placeholder="tuo@email.it")
            with col2:
                password = st.text_input("Password", type="password", placeholder="••••••••")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Login", use_container_width=True):
                    try:
                        res = sign_in(email.strip(), password)
                        session = res.get("session")
                        user = res.get("user")
                        if session and user:
                            st.session_state.mode = "authed"
                            st.session_state.user = {"id": user.id, "email": user.email}
                            st.session_state.access_token = session.access_token
                            st.rerun()
                        else:
                            st.error("Login fallito.")
                    except Exception as e:
                        st.error(f"Errore login: {e}")
            with c2:
                if st.button("Crea account", use_container_width=True):
                    try:
                        sign_up(email.strip(), password)
                        st.success("Account creato. Ora fai Login.")
                    except Exception as e:
                        st.error(f"Errore signup: {e}")

    st.caption("Guest Mode = niente cloud save. Per tracking serio + cross-device, consigliato login.")


st.divider()
col_kofi_1, col_kofi_2 = st.columns([3, 1])
with col_kofi_1:
    st.markdown("### ☕ Ti piace StreamSaver?")
    st.caption(
        "Quest'app è **100% gratuita** e open source. "
        "Se ti ho aiutato a risparmiare, puoi offrirmi un caffè simbolico!"
    )
with col_kofi_2:
    ko_fi_url = "https://ko-fi.com/budgettechita"
    st.markdown(
        f"""
        <a href="{ko_fi_url}" target="_blank">
            <img src="[https://storage.ko-fi.com/cdn/kofi2.png?v=3](https://storage.ko-fi.com/cdn/kofi2.png?v=3)"
                alt="Buy Me a Coffee"
                style="height: 45px; width: auto; margin-top: 10px;" >
        </a>
        """,
        unsafe_allow_html=True
    )


subs = get_subs()
profile = get_profile()
challenge = get_challenge()

monthly = total_monthly(subs)
budget = float(profile.get("budget_mese") or 0.0)
remaining = float(budget) - float(monthly) if budget else None

xp = int(profile.get("xp") or 0)
lvl, to_next = level_from_xp(xp)

is_premium = bool(st.session_state.is_premium)
limit_reached = False

tab_subs, tab_chal, tab_templates, tab_export = st.tabs(
    ["📋 Abbonamenti", "🏁 Challenge", "⚡ Setup", "📸 Export Poster"]
)

with tab_subs:
    st.markdown(
        f"""
<div class="ss-card">
  <div class="ss-row">
    <div>
      <div class="ss-muted">Spesa mensile totale</div>
      <div class="ss-big">{euro(monthly)}</div>
      <div class="ss-muted">Obiettivo: {euro(budget) if budget else "n/a"} • Rimanente: {euro(remaining) if remaining is not None else "n/a"}</div>
    </div>
    <div style="text-align:right">
      <div class="ss-muted">Livello</div>
      <div class="ss-pill">Lv {lvl} • {xp} XP</div>
      <div class="ss-muted">Next: {to_next} XP</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("### 🎯 Budget Goal")
    new_budget = st.number_input("Budget mensile (€)", min_value=0.0, value=float(budget), step=5.0)
    if st.button("Salva budget", use_container_width=True):
        profile["budget_mese"] = float(new_budget)
        profile = award_xp(profile, "set_budget")
        save_profile(profile)
        st.success("Budget salvato ✅")
        st.rerun()

    if budget and remaining is not None:
        ratio = min(max(float(monthly) / float(budget), 0.0), 1.0) if budget > 0 else 0.0
        st.progress(ratio)
        pill_class = "ss-pill" if remaining >= 0 else "ss-pill ss-bad"
        st.markdown(f"<span class='{pill_class}'>Rimanente: {euro(remaining)}</span>", unsafe_allow_html=True)

    st.divider()

    st.markdown("### ➕ Aggiungi abbonamento")
    mode = st.radio("Scegli tipo", ["Predefinito", "Custom"], horizontal=True, disabled=limit_reached)

    if mode == "Predefinito":
        chosen = st.selectbox("Seleziona abbonamento", options=[""] + preset_names(), disabled=limit_reached)
        preset = preset_by_name(chosen) if chosen else None
        nome = (preset or {}).get("nome", "")
        categoria = (preset or {}).get("categoria", "Altro")
        icona = (preset or {}).get("icona", "💳")
        prezzo_mese = float((preset or {}).get("prezzo_mese") or 0.0)
        prezzo_anno_originale = (preset or {}).get("prezzo_anno_originale")
    else:
        nome = st.text_input("Nome", disabled=limit_reached)
        categoria = st.selectbox("Categoria", config.CATEGORIES, disabled=limit_reached)
        icona = st.text_input("Icona (emoji)", value="💳", disabled=limit_reached)
        prezzo_mese = st.number_input("Prezzo mensile (€)", min_value=0.0, value=0.0, step=1.0, disabled=limit_reached)
        prezzo_anno_originale = None

    tipo_pagamento = st.selectbox("Pagamento", ["mensile", "annuale"], disabled=limit_reached)

    if tipo_pagamento == "annuale":
        prezzo_anno = st.number_input(
            "Prezzo annuo (€)",
            min_value=0.0,
            value=float(prezzo_anno_originale or 0.0),
            step=5.0,
            disabled=limit_reached,
        )
    else:
        prezzo_anno = float(prezzo_anno_originale or 0.0)

    utilizzi_mese = st.number_input("Utilizzi al mese (reali)", min_value=0, value=4, step=1, disabled=limit_reached)
    data_rinnovo = st.date_input("Data rinnovo (opzionale)", value=None)

    preview = {
        "nome": nome,
        "categoria": categoria,
        "icona": icona,
        "prezzo_mese": prezzo_mese,
        "prezzo_anno_originale": prezzo_anno,
        "tipo_pagamento": tipo_pagamento,
        "utilizzi_mese": int(utilizzi_mese),
    }
    cpu = cost_per_use(preview)
    st.markdown(
        f"""
<div class="ss-card">
  <div class="ss-muted">🔥 COSTO PER UTILIZZO</div>
  <div class="ss-big">{euro(cpu) if cpu is not None else "n/a"} per utilizzo</div>
  <div class="ss-muted">Tip: imposta utilizzi reali → “reality check” virale.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if st.button("Aggiungi", use_container_width=True, disabled=limit_reached):
        if not nome:
            st.error("Inserisci un nome.")
        else:
            row = {
                "nome": nome,
                "categoria": categoria,
                "icona": icona,
                "tipo_pagamento": tipo_pagamento,
                "prezzo_mese": float(prezzo_mese),
                "prezzo_anno_originale": float(prezzo_anno) if prezzo_anno else None,
                "utilizzi_mese": int(utilizzi_mese),
                "data_rinnovo": data_rinnovo.isoformat() if isinstance(data_rinnovo, date) else None,
                "custom": mode == "Custom",
            }

            if is_authed():
                row["user_id"] = st.session_state.user["id"]
                upsert_subscription(st.session_state.access_token, row)
            else:
                local = list(st.session_state.subs_local)
                local.insert(0, row)
                set_subs_local(local)

            profile = award_xp(profile, "add_subscription")
            save_profile(profile)
            st.success("Aggiunto ✅")
            st.rerun()

    st.divider()

    st.markdown("### 📋 I tuoi abbonamenti")
    if not subs:
        st.info("Nessun abbonamento ancora. Aggiungine uno per vedere il costo/uso.")
    else:
        waste = biggest_waste(subs)
        if waste:
            w_cpu = cost_per_use(waste)
            badge = "ss-pill ss-bad" if (w_cpu is not None and float(w_cpu) >= 2.0) else "ss-pill ss-warn"
            st.markdown(
                f"""
<div class="ss-card">
  <div class="ss-row">
    <div>
      <div class="ss-muted">🧨 Peggior spreco</div>
      <div class="ss-big">{waste.get("icona","💳")} {waste.get("nome","")}</div>
      <div class="ss-muted">Costo/uso: {euro(w_cpu) if w_cpu else "n/a"} • Costo/mese: {euro(monthly_cost(waste))}</div>
    </div>
    <div><span class="{badge}">Viral metric</span></div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )

        for idx, s in enumerate(subs):
            name = s.get("nome", "")
            icon = s.get("icona", "💳")
            cat = s.get("categoria", "Altro")
            mc = monthly_cost(s)
            cpu = cost_per_use(s)
            cpu_txt = euro(cpu) if cpu is not None else "n/a"
            pill = "ss-pill" if cpu is not None and float(cpu) < 1.0 else "ss-pill ss-warn" if cpu is not None else "ss-pill ss-bad"

            st.markdown(
                f"""
<div class="ss-card">
  <div class="ss-row">
    <div>
      <div class="ss-big">{icon} {name}</div>
      <div class="ss-muted">{cat} • {euro(mc)}/mese</div>
      <div class="ss-muted">🔥 Costo/uso: <span class="{pill}">{cpu_txt}</span></div>
    </div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )

            c1, c2, c3 = st.columns([1.2, 1.2, 1.0])
            with c1:
                new_uses = st.number_input(
                    f"Utilizzi/mese — {name}",
                    min_value=0,
                    value=int(s.get("utilizzi_mese") or 0),
                    step=1,
                    key=f"uses_{idx}",
                )
            with c2:
                new_price = st.number_input(
                    f"Prezzo mensile — {name}",
                    min_value=0.0,
                    value=float(s.get("prezzo_mese") or 0.0),
                    step=1.0,
                    key=f"price_{idx}",
                )
            with c3:
                if st.button("🗑️ Elimina", key=f"del_{idx}", use_container_width=True):
                    if is_authed() and s.get("id"):
                        delete_subscription(st.session_state.access_token, s["id"], st.session_state.user["id"])
                    else:
                        local = list(st.session_state.subs_local)
                        if 0 <= idx < len(local):
                            local.pop(idx)
                        set_subs_local(local)

                    profile = award_xp(profile, "delete_subscription")
                    save_profile(profile)
                    st.rerun()

            if st.button("Salva modifiche", key=f"save_{idx}", use_container_width=True):
                s2 = dict(s)
                s2["utilizzi_mese"] = int(new_uses)
                s2["prezzo_mese"] = float(new_price)
                if is_authed():
                    s2["user_id"] = st.session_state.user["id"]
                    upsert_subscription(st.session_state.access_token, s2)
                else:
                    local = list(st.session_state.subs_local)
                    if 0 <= idx < len(local):
                        local[idx] = s2
                    set_subs_local(local)
                st.success("Salvato ✅")
                st.rerun()


with tab_chal:
    st.markdown("### 🏁 Challenge Risparmio")

    ch = challenge or {}
    active = bool(ch.get("active"))

    if active:
        title = ch.get("title") or "Challenge attiva"
        days = int(ch.get("days") or 0)
        started_at = ch.get("started_at")
        last_checkin = ch.get("last_checkin")
        streak = int(ch.get("streak_days") or 0)

        st.markdown(
            f"""
<div class="ss-card">
  <div class="ss-muted">Challenge attiva</div>
  <div class="ss-big">🏁 {title}</div>
  <div class="ss-muted">Streak: <b>{streak} giorni</b> • Durata: {days} giorni</div>
</div>
""",
            unsafe_allow_html=True,
        )

        if started_at:
            try:
                start_d = date.fromisoformat(str(started_at))
                elapsed = (date.today() - start_d).days
                if days > 0:
                    st.progress(min(max(elapsed / days, 0.0), 1.0))
                    st.caption(f"Giorno {min(elapsed+1, days)}/{days}")
            except Exception:
                pass

        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Check-in di oggi", use_container_width=True):
                today = date.today()
                prev = None
                try:
                    if last_checkin:
                        prev = date.fromisoformat(str(last_checkin))
                except Exception:
                    prev = None

                if prev == today:
                    st.info("Hai già fatto check-in oggi.")
                else:
                    if prev == today - timedelta(days=1):
                        streak = streak + 1
                    else:
                        streak = 1

                    ch["streak_days"] = streak
                    ch["last_checkin"] = today.isoformat()
                    save_challenge(ch)

                    profile = award_xp(profile, "checkin")
                    save_profile(profile)
                    st.success("Check-in fatto ✅")
                    st.rerun()

        with c2:
            if st.button("🛑 Termina challenge", use_container_width=True):
                ch = {
                    "active": False,
                    "challenge_id": None,
                    "title": "",
                    "days": 0,
                    "started_at": None,
                    "last_checkin": None,
                    "streak_days": 0,
                }
                save_challenge(ch)
                st.success("Challenge terminata.")
                st.rerun()

        st.divider()

        st.markdown("### 🧨 Suggerimento rapido: cosa tagliare")
        subs_now = get_subs()
        w = biggest_waste(subs_now)
        if not w:
            st.info("Aggiungi almeno 1 abbonamento per avere suggerimenti.")
        else:
            w_cpu = cost_per_use(w)
            st.markdown(
                f"""
<div class="ss-card">
  <div class="ss-muted">Candidato #1</div>
  <div class="ss-big">{w.get("icona","💳")} {w.get("nome","")}</div>
  <div class="ss-muted">Costo/uso: {euro(w_cpu) if w_cpu else "n/a"} • Risparmio stimato: {euro(monthly_cost(w))}/mese</div>
</div>
""",
                unsafe_allow_html=True,
            )

    else:
        st.info("Nessuna challenge attiva. Avviane una per lo streak e la gamification.")
        preset_titles = [f"{p['title']} ({p['days']}g)" for p in config.CHALLENGE_PRESETS]
        idx = st.selectbox("Scegli challenge", range(len(preset_titles)), format_func=lambda i: preset_titles[i])
        preset = config.CHALLENGE_PRESETS[int(idx)]

        st.markdown(f"**Descrizione:** {preset.get('description')}")

        if st.button("🚀 Avvia challenge", use_container_width=True):
            today = date.today().isoformat()
            ch = {
                "active": True,
                "challenge_id": preset["id"],
                "title": preset["title"],
                "days": int(preset.get("days") or 0),
                "started_at": today,
                "last_checkin": None,
                "streak_days": 0,
            }
            save_challenge(ch)
            profile = award_xp(profile, "start_challenge")
            save_profile(profile)
            st.success("Challenge avviata ✅")
            st.rerun()


with tab_templates:
    st.markdown("### ⚡ Setup (Content Ready)")

    tpl_titles = [t["title"] for t in config.TEMPLATES]
    t_idx = st.selectbox("Scegli template", range(len(tpl_titles)), format_func=lambda i: tpl_titles[i])
    tpl = config.TEMPLATES[int(t_idx)]

    st.markdown(
        f"""
<div class="ss-card">
  <div class="ss-muted">Hook (Incipit video)</div>
  <div class="ss-big">🎬 {tpl['hook']}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("**Script (voce):**")
    st.code("\n".join(tpl["script"]), language="text")

    st.markdown("**Hashtags:**")
    st.code(" ".join(tpl["hashtags"]), language="text")

    if st.button("➕ Importa abbonamenti del template", use_container_width=True):
        subs_now = get_subs()
        remaining_slots = 10**9 if is_premium else max(0, free_limit() - len(subs_now))
        to_add = tpl.get("items", [])[:remaining_slots]

        added = 0
        for item in to_add:
            name = item.get("nome")
            uses = int(item.get("utilizzi_mese") or 0)
            p = preset_by_name(name) or {
                "nome": name,
                "categoria": "Altro",
                "icona": "💳",
                "prezzo_mese": 0.0,
                "prezzo_anno_originale": None,
            }
            row = {
                "nome": p.get("nome"),
                "categoria": p.get("categoria", "Altro"),
                "icona": p.get("icona", "💳"),
                "tipo_pagamento": "mensile",
                "prezzo_mese": float(p.get("prezzo_mese") or 0.0),
                "prezzo_anno_originale": p.get("prezzo_anno_originale"),
                "utilizzi_mese": uses,
                "data_rinnovo": None,
                "custom": False if preset_by_name(name) else True,
            }

            if is_authed():
                row["user_id"] = st.session_state.user["id"]
                upsert_subscription(st.session_state.access_token, row)
            else:
                local = list(st.session_state.subs_local)
                local.insert(0, row)
                set_subs_local(local)

            added += 1

        profile = award_xp(profile, "import_template")
        save_profile(profile)
        st.success(f"Import completato ✅ (+{added} abbonamenti)")
        st.rerun()

    st.caption("Tip virale: registra schermo mentre sistemi “costo/uso” e fai il reveal dello spreco.")


with tab_export:
    st.markdown("### 📸 Export Poster (9:16)")
    subs_now = get_subs()

    if not subs_now:
        st.info("Aggiungi almeno 1 abbonamento per generare il poster.")
    else:
        cpus = []
        for s in subs_now:
            c = cost_per_use(s)
            if c is not None:
                cpus.append((float(c), s))
        best_cpu_txt = None
        worst_cpu_txt = None
        if cpus:
            cpus.sort(key=lambda x: x[0])
            best = cpus[0]
            worst = cpus[-1]
            best_cpu_txt = f"{best[1].get('nome','')} • {euro(best[0])}"
            worst_cpu_txt = f"{worst[1].get('nome','')} • {euro(worst[0])}"

        ch = get_challenge() or {}
        challenge_title = ch.get("title") if ch.get("active") else "Nessuna challenge attiva"
        streak = int(ch.get("streak_days") or 0) if ch.get("active") else 0

        payload = {
            "title": "StreamSaver",
            "subtitle": "Quanto ti costa OGNI utilizzo?",
            "monthly_total": float(total_monthly(subs_now)),
            "budget": float(get_profile().get("budget_mese") or 0.0),
            "remaining": float(remaining) if remaining is not None else None,
            "best_cpu": best_cpu_txt,
            "worst_cpu": worst_cpu_txt,
            "challenge_title": challenge_title,
            "streak_days": streak,
            "footer": "Condividi questo poster sui social: #BudgetTech #Risparmio",
        }

        img_bytes = build_social_card(payload, size=config.EXPORT_SIZE)

        st.image(img_bytes, caption="Anteprima poster (1080×1920)", use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "⬇️ Scarica PNG",
                data=img_bytes,
                file_name="streamsaver_social_poster.png",
                mime="image/png",
                use_container_width=True,
            )
        with c2:
            if st.button("✅ Segna Export (XP)", use_container_width=True):
                profile = award_xp(get_profile(), "export")
                save_profile(profile)
                st.success("XP aggiunti ✅")
                st.rerun()

        st.markdown("**Caption pronta (copia/incolla):**")
        caption = (
            "Ho scoperto quanto mi costa OGNI utilizzo dei miei abbonamenti. "
            "Spoiler: c'era uno spreco assurdo. 💸🔥\n\n"
            "#risparmio #abbonamenti #budget #tech #italia"
        )
        st.code(caption, language="text")
        st.caption("Tip: usa la preview + hook del template e fai un 'reveal' del peggior costo/uso.")


st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #6b7280; font-size: 0.8rem;'>
        <p>
            <strong>Disclaimer:</strong> StreamSaver è un tool a scopo informativo e di intrattenimento.
            I calcoli si basano sui dati inseriti dall'utente.
            L'autore non si assume responsabilità per decisioni finanziarie, cancellazioni di abbonamenti o perdite di dati.
            <br>
            Non condividiamo i tuoi dati con terze parti.
        </p>
        <p>Made with 💚 by Budget Tech ITA</p>
    </div>
    """,
    unsafe_allow_html=True
)
