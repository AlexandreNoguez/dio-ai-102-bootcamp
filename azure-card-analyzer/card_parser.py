from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CardExtraction:
    last4: str | None
    brand: str | None
    expiry: str | None
    holder_name: str | None
    luhn_ok: bool
    expiry_ok: bool
    format_valid: bool


def _luhn_check(number: str) -> bool:
    # number must contain only digits
    total = 0
    reverse_digits = list(map(int, reversed(number)))
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _detect_brand(pan: str) -> str | None:
    # Basic BIN/IIN patterns (not exhaustive).
    if pan.startswith("4"):
        return "Visa"
    if re.match(r"^5[1-5]", pan):
        return "Mastercard"
    if re.match(r"^3[47]", pan):
        return "American Express"
    if re.match(r"^6(?:011|5)", pan):
        return "Discover"
    if re.match(r"^(?:35)", pan):
        return "JCB"
    return None


def _find_expiry(text: str) -> str | None:
    # Look for MM/YY or MM/YYYY
    m = re.search(r"\b(0[1-9]|1[0-2])\s*[/\-]\s*(\d{2}|\d{4})\b", text)
    if not m:
        return None
    mm = int(m.group(1))
    yy_raw = m.group(2)
    yy = int(yy_raw[-2:])  # take last 2 digits
    return f"{mm:02d}/{yy:02d}"


def _expiry_is_future(expiry_mm_yy: str) -> bool:
    try:
        mm, yy = expiry_mm_yy.split("/")
        mm_i = int(mm)
        yy_i = int(yy)
        now = datetime.utcnow()
        # interpret YY as 2000-2099
        year = 2000 + yy_i
        # valid until end of expiry month
        if mm_i < 1 or mm_i > 12:
            return False
        if year < now.year:
            return False
        if year == now.year and mm_i < now.month:
            return False
        return True
    except Exception:
        return False


def _mask_last4(pan: str) -> str:
    return pan[-4:]


def extract_from_ocr_text(ocr_text: str) -> CardExtraction:
    # Find candidate PANs: 13-19 digits, allowing spaces or hyphens
    candidates = []
    for m in re.finditer(r"\b(?:\d[ -]?){13,19}\b", ocr_text):
        raw = m.group(0)
        pan = re.sub(r"[ -]", "", raw)
        if 13 <= len(pan) <= 19 and pan.isdigit():
            candidates.append(pan)

    best_pan = None
    for pan in candidates:
        if _luhn_check(pan):
            best_pan = pan
            break

    expiry = _find_expiry(ocr_text)
    expiry_ok = _expiry_is_future(expiry) if expiry else False

    brand = _detect_brand(best_pan) if best_pan else None
    luhn_ok = _luhn_check(best_pan) if best_pan else False
    last4 = _mask_last4(best_pan) if best_pan else None

    # Optional: try to guess holder name (very heuristic)
    holder_name = None
    # Many cards show the name in uppercase; pick a reasonable-looking line.
    lines = [ln.strip() for ln in ocr_text.splitlines() if ln.strip()]
    for ln in lines:
        if re.match(r"^[A-Z][A-Z\s\.\-]{5,}$", ln) and "VALID" not in ln:
            holder_name = ln[:40]
            break

    format_valid = bool(best_pan) and luhn_ok and expiry_ok

    return CardExtraction(
        last4=last4,
        brand=brand,
        expiry=expiry,
        holder_name=holder_name,
        luhn_ok=luhn_ok,
        expiry_ok=expiry_ok,
        format_valid=format_valid,
    )