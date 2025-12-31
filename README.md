# StreamSaver by Budget Tech ITA 💚
Tracker abbonamenti **mobile-first** con:
- ✅ 30+ abbonamenti predefiniti (JSON remoto opzionale)
- 🔥 **Costo per utilizzo** (killer feature virale)
- 🏁 Challenge risparmio + streak gamification
- ⚡ Template setup “content-ready” (hook/script/hashtags)
- 🎯 Budget goal
- 📸 Export poster **1080×1920** (TikTok-ready)
- 🔐 Supabase (login + cloud save)
- 🆓 Freemium (3 abbonamenti) / ⭐ Premium (illimitati) via Patreon (key)

## Avvio locale
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Streamlit Cloud)
1. Carica questa repo su GitHub.
2. Streamlit Cloud → New app → seleziona repo e `app.py`.
3. Inserisci i secrets (Settings → Secrets) come nel file `.streamlit/secrets.toml`.

## Supabase setup (SQL)
Nel progetto Supabase (SQL Editor) esegui:

```sql
-- Necessario per uuid_generate_v4()
create extension if not exists "uuid-ossp";

-- Tabella abbonamenti
create table if not exists public.user_subscriptions (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references auth.users(id) on delete cascade,
  nome text not null,
  prezzo_mese numeric(10,2) not null,
  prezzo_anno_originale numeric(10,2),
  categoria text not null,
  icona text,
  tipo_pagamento text default 'mensile',
  data_rinnovo date,
  utilizzi_mese integer,
  custom boolean default false,
  data_aggiunto timestamp default now()
);

-- Profilo utente (PK = user_id per upsert semplice)
create table if not exists public.user_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  budget_mese numeric(10,2) default 0,
  xp integer default 0,
  created_at timestamp default now(),
  updated_at timestamp default now()
);

-- Challenge (PK = user_id per upsert semplice)
create table if not exists public.user_challenges (
  user_id uuid primary key references auth.users(id) on delete cascade,
  active boolean default false,
  challenge_id text,
  title text,
  days integer,
  started_at date,
  last_checkin date,
  streak_days integer default 0,
  created_at timestamp default now(),
  updated_at timestamp default now()
);

-- Row Level Security
alter table public.user_subscriptions enable row level security;
alter table public.user_profiles enable row level security;
alter table public.user_challenges enable row level security;

-- Policy: ogni utente vede/modifica solo le proprie righe
create policy "subs_select_own" on public.user_subscriptions
  for select using (auth.uid() = user_id);
create policy "subs_insert_own" on public.user_subscriptions
  for insert with check (auth.uid() = user_id);
create policy "subs_update_own" on public.user_subscriptions
  for update using (auth.uid() = user_id);
create policy "subs_delete_own" on public.user_subscriptions
  for delete using (auth.uid() = user_id);

create policy "profile_select_own" on public.user_profiles
  for select using (auth.uid() = user_id);
create policy "profile_upsert_own" on public.user_profiles
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "challenge_select_own" on public.user_challenges
  for select using (auth.uid() = user_id);
create policy "challenge_upsert_own" on public.user_challenges
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
```

### Nota Premium
Premium è gestito via **key condivisa** (Patreon). Nel codice è `PREMIUM_SHARED_KEY` in secrets.
Per fare qualcosa di più robusto, puoi integrare webhook Patreon e salvare un flag premium su `user_profiles`.

## JSON remoto abbonamenti
Puoi caricare `abbonamenti_predefiniti.json` su GitHub (raw) o Supabase Storage pubblico e impostare `PRESET_JSON_URL` nei secrets.
