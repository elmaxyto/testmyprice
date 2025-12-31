from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from calculator import euro


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = (text or "").split()
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def build_tiktok_card(payload: dict[str, Any], size=(1080, 1920)) -> bytes:
    W, H = size
    img = Image.new("RGB", size, (11, 18, 32))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("DejaVuSans.ttf", 64)
        big_font = ImageFont.truetype("DejaVuSans.ttf", 54)
        mid_font = ImageFont.truetype("DejaVuSans.ttf", 36)
        small_font = ImageFont.truetype("DejaVuSans.ttf", 28)
    except Exception:
        title_font = ImageFont.load_default()
        big_font = ImageFont.load_default()
        mid_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    draw.rounded_rectangle((60, 60, W - 60, 220), radius=36, fill=(15, 27, 46))
    draw.text((90, 95), payload.get("title", "StreamSaver"), font=title_font, fill=(229, 231, 235))

    subtitle = payload.get("subtitle", "Costo per utilizzo = realtà.")
    sub_lines = _wrap(draw, subtitle, mid_font, W - 180)
    y = 170
    for line in sub_lines[:1]:
        draw.text((90, y), line, font=mid_font, fill=(156, 163, 175))

    draw.rounded_rectangle((60, 260, W - 60, 1180), radius=46, fill=(10, 20, 36))
    y = 300

    def metric(label: str, value: str, emoji: str = "✅"):
        nonlocal y
        draw.text((90, y), f"{emoji}  {label}", font=mid_font, fill=(156, 163, 175))
        y += 46
        draw.text((90, y), value, font=big_font, fill=(229, 231, 235))
        y += 86

    metric("Spesa mensile", euro(payload.get("monthly_total", 0)), "💸")
    metric("Budget mensile", euro(payload.get("budget", 0)), "🎯")

    remaining = payload.get("remaining")
    if remaining is not None:
        metric("Rimanente", euro(remaining), "🧠")

    best_cpu = payload.get("best_cpu")
    if best_cpu:
        metric("Miglior affare (€/uso)", best_cpu, "🔥")

    worst_cpu = payload.get("worst_cpu")
    if worst_cpu:
        metric("Peggior spreco (€/uso)", worst_cpu, "🧨")

    draw.rounded_rectangle((60, 1230, W - 60, 1520), radius=46, fill=(15, 27, 46))
    draw.text((90, 1260), "🏁 Challenge", font=mid_font, fill=(156, 163, 175))
    draw.text((90, 1320), payload.get("challenge_title", "Nessuna challenge attiva"), font=big_font, fill=(229, 231, 235))

    streak = int(payload.get("streak_days", 0) or 0)
    draw.text((90, 1400), f"Streak: {streak} giorni", font=mid_font, fill=(34, 197, 94))

    draw.rounded_rectangle((60, 1580, W - 60, 1860), radius=46, fill=(10, 20, 36))
    footer = payload.get("footer", "Salva soldi. Condividi il poster. Ripeti.")
    lines = _wrap(draw, footer, mid_font, W - 180)
    yy = 1620
    for line in lines[:3]:
        draw.text((90, yy), line, font=mid_font, fill=(229, 231, 235))
        yy += 46

    stamp = datetime.now().strftime("%d/%m/%Y")
    draw.text((90, 1810), f"StreamSaver • {stamp}", font=small_font, fill=(156, 163, 175))

    out = BytesIO()
    img.save(out, format="PNG", optimize=True)
    return out.getvalue()
