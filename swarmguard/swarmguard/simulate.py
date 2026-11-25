"""Synthetic traffic for demos and tests.

Generates in-memory events only (nothing is sent on the network). All addresses come
from ranges reserved for documentation and benchmarking, never real hosts.
"""
from __future__ import annotations

import random

from .events import Event

_BROWSER_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
]
_ASSETS = ["/static/app.css", "/static/app.js", "/static/logo.svg", "/static/hero.webp",
           "/static/font.woff2", "/static/vendor.js", "/favicon.ico"]
_POPULAR = ["/", "/products", "/pricing", "/about", "/blog", "/contact", "/login"]


def _human_ip(i: int) -> str:
    return f"198.18.{i // 250}.{i % 250 + 1}"  # 198.18.0.0/15: benchmarking range


def _bot_ip(i: int) -> str:
    nets = ["203.0.113", "192.0.2", "198.51.100"]  # documentation ranges
    return f"{nets[i % 3]}.{i // 3 + 1}"


def _human_session(rng, src, start, events, landing=None):
    ua = rng.choice(_BROWSER_UAS)
    t = start
    for page_no in range(1 + min(int(rng.expovariate(1 / 6)), 30)):
        if page_no == 0 and landing:
            path = landing
        elif rng.random() < 0.6:
            path = rng.choice(_POPULAR)
        else:
            path = f"/products/{int(rng.paretovariate(1.2)) % 400}"
        events.append(Event(t, src, method="GET", path=path, status=200, ua=ua))
        for a in rng.sample(_ASSETS, rng.randint(3, 6)):
            events.append(Event(t + rng.uniform(0.05, 1.2), src, method="GET", path=a, status=200, ua=ua))
        t += rng.lognormvariate(2.5, 0.9)  # think time, median ~12s, heavy tail


def scenario(seed: int = 7, duration: float = 900.0, humans: int = 300,
             swarm: int = 60, stuffers: int = 40,
             scanner: bool = True) -> tuple[list[Event], dict[str, str]]:
    """Return (events sorted by time, ground truth label per source address).

    Labels: human, office (many people behind one NAT), monitor (benign uptime bot),
    flash (benign crowd arriving together from a shared link), scraper (distributed AI
    crawl), stuffer (distributed credential stuffing), scanner (lone vulnerability probe).
    """
    rng = random.Random(seed)
    ev: list[Event] = []
    truth: dict[str, str] = {}
    n = 0

    def human(label="human"):
        nonlocal n
        n += 1
        truth[_human_ip(n)] = label
        return _human_ip(n)

    # Ordinary visitors arriving throughout.
    for _ in range(humans):
        _human_session(rng, human(), rng.uniform(0, duration), ev)

    # An office behind one NAT address: lots of traffic, all legitimate.
    office = human("office")
    for _ in range(40):
        _human_session(rng, office, rng.uniform(0, duration), ev)

    # Benign uptime monitor: perfectly regular, single address.
    mon = human("monitor")
    t = 0.0
    while t < duration:
        ev.append(Event(t, mon, method="GET", path="/health", status=200, ua="UptimeCheck/2.1"))
        t += 30

    # Benign flash crowd: 50 people follow the same link within a minute.
    t0 = duration * 0.25
    for _ in range(50):
        _human_session(rng, human("flash"), t0 + rng.uniform(0, 60), ev, landing="/blog/launch")

    # Hostile: distributed AI scraper. Each agent stays slow and jittery (well under any
    # per-address limit), rotates user agents, and takes its own slice of the catalogue.
    t0 = duration * 0.4
    for i in range(swarm):
        src = _bot_ip(i)
        truth[src] = "scraper"
        ua = rng.choice(_BROWSER_UAS)
        t = t0 + rng.uniform(0, 45)
        page = 1000 + i * 500
        while t < duration:
            ev.append(Event(t, src, method="GET", path=f"/products/{page}", status=200, ua=ua))
            page += 1
            t += max(0.5, rng.gauss(5.0, 1.8))

    # Hostile: distributed credential stuffing against /login.
    t0 = duration * 0.6
    for i in range(stuffers):
        src = _bot_ip(swarm + i)
        truth[src] = "stuffer"
        ua = rng.choice(_BROWSER_UAS)
        t = t0 + rng.uniform(0, 60)
        while t < duration:
            status = 200 if rng.random() < 0.02 else 401
            ev.append(Event(t, src, method="POST", path="/login", status=status, ua=ua))
            t += max(1.0, rng.gauss(9.0, 3.0))

    # Hostile: a lone scanner probing for secrets.
    src = _bot_ip(swarm + stuffers)
    t = duration * 0.5
    if scanner:
        truth[src] = "scanner"
    for path in [] if not scanner else ["/.env", "/.git/config", "/backup.zip", "/wp-login.php", "/admin", "/config.php"]:
        ev.append(Event(t, src, method="GET", path=path, status=404, ua="python-requests/2.32"))
        t += rng.uniform(0.2, 1.0)

    ev.sort(key=lambda e: e.ts)
    return ev, truth


HOSTILE = {"scraper", "stuffer", "scanner"}
