from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Event:
    """One observation of inbound traffic from a source address."""

    ts: float
    src: str
    kind: str = "http"  # "http" (from an access log) or "conn" (from packet capture)
    method: str = ""
    path: str = ""
    status: int = 0
    ua: str = ""
    dport: int = 0
