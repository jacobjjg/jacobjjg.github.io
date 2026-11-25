"""Response policy: turns incidents into graduated, time-limited actions.

Ladder: observe -> throttle -> block. Every action carries a TTL, so a mistake heals
itself. Guard rails: allowlist, hard cap on active blocks, and a circuit breaker that
refuses to block most of the visible client population in one go.
"""
from __future__ import annotations

import ipaddress
from collections import Counter
from dataclasses import dataclass

from .actuators import Actuator
from .config import Config
from .engine import Incident

_LEVEL = {"throttle": 1, "block": 2}


@dataclass
class Decision:
    ts: float
    level: str  # throttle | block
    sources: list[str]
    ttl: float
    incident: Incident
    note: str = ""


def enforcement_target(src: str) -> str:
    """IPv4: the address. IPv6: its /64, since one client controls the whole prefix."""
    ip = ipaddress.ip_address(src)
    if ip.version == 6:
        return str(ipaddress.ip_network(f"{src}/64", strict=False))
    return str(ip)


class Policy:
    def __init__(self, cfg: Config, actuator: Actuator):
        self.cfg = cfg
        self.actuator = actuator
        self.allow = [ipaddress.ip_network(n, strict=False) for n in cfg.allowlist]
        self.active: dict[str, tuple[str, float]] = {}  # src -> (level, expires)
        self.strikes: Counter = Counter()
        self.suppressed: dict[str, float] = {}  # src -> until (analyst said benign)

    def is_allowed(self, src: str) -> bool:
        try:
            ip = ipaddress.ip_address(src)
        except ValueError:
            return True  # never act on something that is not an address
        return any(ip.version == n.version and ip in n for n in self.allow)

    def level_of(self, src: str, now: float) -> str | None:
        cur = self.active.get(src)
        if cur and cur[1] > now:
            return cur[0]
        return None

    def _expire(self, now: float) -> None:
        for src in [s for s, (_, exp) in self.active.items() if exp <= now]:
            del self.active[src]
        for src in [s for s, until in self.suppressed.items() if until <= now]:
            del self.suppressed[src]

    def handle(self, inc: Incident, now: float, visible_sources: int) -> Decision | None:
        cfg = self.cfg
        self._expire(now)
        if inc.score >= cfg.block_score:
            level = "block"
        elif inc.score >= cfg.throttle_score:
            level = "throttle"
        else:
            return None

        note = ""
        targets: list[tuple[str, str]] = []  # (src, level)
        for src in inc.sources:
            if self.is_allowed(src) or src in self.suppressed:
                continue
            want = level
            if want == "throttle" and self.strikes[src] >= cfg.strikes_to_block:
                want = "block"  # repeat offender
            cur = self.level_of(src, now)
            if cur and _LEVEL[cur] >= _LEVEL[want]:
                continue
            targets.append((src, want))
        if not targets:
            return None

        blocked = sum(1 for lvl, _ in self.active.values() if lvl == "block")
        new_blocks = sum(1 for _, lvl in targets if lvl == "block")
        if new_blocks:
            population = visible_sources + blocked
            if blocked + new_blocks > cfg.max_active_blocks:
                note = "block cap reached; throttling instead"
            elif population >= 20 and blocked + new_blocks > cfg.max_block_fraction * population:
                note = "circuit breaker: would block most visible clients; throttling instead, needs human review"
            if note:
                targets = [
                    (s, "throttle") for s, _ in targets
                    if self.level_of(s, now) != "throttle"
                ]
                if not targets:
                    return None

        applied = []
        ttl_max = 0.0
        final_level = "throttle"
        for src, lvl in targets:
            ttl = min(cfg.max_ttl, cfg.base_ttl * (2 ** self.strikes[src]))
            self.actuator.apply(lvl, enforcement_target(src), ttl)
            self.active[src] = (lvl, now + ttl)
            self.strikes[src] += 1
            applied.append(src)
            ttl_max = max(ttl_max, ttl)
            if lvl == "block":
                final_level = "block"
        return Decision(now, final_level, applied, ttl_max, inc, note)

    def release(self, sources: list[str], now: float, suppress_for: float = 900.0) -> list[str]:
        """Lift actions on sources (analyst judged them benign) and leave them alone for a while."""
        released = []
        for src in sources:
            if src in self.active:
                self.actuator.release(enforcement_target(src))
                del self.active[src]
                self.strikes[src] = max(0, self.strikes[src] - 1)
                released.append(src)
            self.suppressed[src] = now + suppress_for
        return released
