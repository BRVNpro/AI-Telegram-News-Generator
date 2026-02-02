import hashlib
import re
from typing import Iterable


def make_hash(*parts: str) -> str:
    s = "||".join([p.strip() for p in parts if p is not None])
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def normalize_text(s: str) -> str:
    s = s or ""
    s = re.sub(r"\s+", " ", s).strip()
    return s


def matches_keywords(text: str, keywords: Iterable[str]) -> bool:
    text_l = (text or "").lower()
    keys = [k.strip().lower() for k in keywords if k and k.strip()]
    if not keys:
        return True
    return any(k in text_l for k in keys)