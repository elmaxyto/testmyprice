from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Optional


def _d(x: Any) -> Decimal:
    if x is None or x == "":
        return Decimal("0")
    try:
        return Decimal(str(x))
    except Exception:
        return Decimal("0")


def euro(amount: Any) -> str:
    val = _d(amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    s = f"{val:.2f}".replace(".", ",")
    return f"€{s}"


def monthly_cost(sub: dict) -> Decimal:
    tipo = (sub.get("tipo_pagamento") or "mensile").lower()
    pm = _d(sub.get("prezzo_mese"))
    pa = _d(sub.get("prezzo_anno_originale"))
    if tipo == "annuale":
        if pa > 0:
            return (pa / Decimal("12"))
        if pm > 0:
            return pm
        return Decimal("0")
    return pm


def yearly_cost(sub: dict) -> Decimal:
    tipo = (sub.get("tipo_pagamento") or "mensile").lower()
    pm = _d(sub.get("prezzo_mese"))
    pa = _d(sub.get("prezzo_anno_originale"))
    if tipo == "annuale":
        if pa > 0:
            return pa
        return pm * Decimal("12")
    return pm * Decimal("12")


def cost_per_use(sub: dict) -> Optional[Decimal]:
    uses = sub.get("utilizzi_mese")
    try:
        uses_i = int(uses) if uses not in (None, "") else 0
    except Exception:
        uses_i = 0
    if uses_i <= 0:
        return None
    return monthly_cost(sub) / Decimal(str(uses_i))


def total_monthly(subs: Iterable[dict]) -> Decimal:
    tot = Decimal("0")
    for s in subs:
        tot += monthly_cost(s)
    return tot


def biggest_waste(subs: list[dict]) -> Optional[dict]:
    with_cpu = []
    zero_use = []
    for s in subs:
        cpu = cost_per_use(s)
        if cpu is None:
            zero_use.append(s)
        else:
            with_cpu.append((cpu, s))

    if with_cpu:
        with_cpu.sort(key=lambda x: x[0], reverse=True)
        return with_cpu[0][1]

    if zero_use:
        zero_use.sort(key=lambda x: monthly_cost(x), reverse=True)
        return zero_use[0]

    return None


def xp_for_action(action: str) -> int:
    table = {
        "checkin": 10,
        "add_subscription": 5,
        "delete_subscription": 50,
        "cancel_high_waste": 120,
        "set_budget": 20,
        "export": 10,
        "import_template": 20,
        "start_challenge": 20,
    }
    return table.get(action, 0)


def level_from_xp(xp: int) -> tuple[int, int]:
    if xp < 0:
        xp = 0
    lvl = xp // 250 + 1
    next_threshold = (lvl * 250)
    return lvl, max(0, next_threshold - xp)
