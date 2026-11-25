"""Red-team harness: an adaptive simulated attacker versus SwarmGuard.

Everything here is in-memory simulation. No packets are sent; addresses come from
reserved ranges. The point is to find out which evasion strategies beat the detector,
so the detector can be improved and its limits stated honestly.

The attacker runs a campaign of workers that share a job (scrape a catalogue, or try
stolen credentials against /login). Each worker speaks from one address at a time and
gets realistic feedback: when its address is blocked its requests fail, and an adaptive
campaign reacts by moving to a fresh address. The attacker's cost is the number of
addresses it burns; its yield is how much of the job gets done.
"""
from __future__ import annotations

import heapq
import random
from collections import Counter, deque
from dataclasses import dataclass

from . import simulate
from .actuators import DryRunActuator
from .config import Config
from .events import Event

DURATION = 1200.0
ATTACK_START = 360.0


@dataclass
class Strategy:
    name: str
    idea: str
    mode: str = "scrape"  # scrape | stuff
    workers: int = 60
    pool: int = 60  # addresses the attacker can afford
    gap: float = 5.0  # mean seconds between a worker's requests
    jitter: float = 0.35  # per-request jitter (fraction of gap)
    hetero: float = 0.0  # spread of per-worker mean gap (lognormal sigma)
    assets: float = 0.0  # probability a worker behaves like a browser and loads assets
    noise: float = 0.0  # share of requests spent on popular pages as camouflage
    spread: float = 45.0  # seconds over which workers start
    per_ip: int = 0  # rotate to a fresh address after this many requests (0 = never)
    adaptive: bool = False  # rotate when blocked
    cells: int = 0  # split workers into this many differently-behaving cells


STRATEGIES = [
    Strategy("naive", "control: uniform slow crawl, no camouflage"),
    Strategy("adaptive", "naive, but swap to a fresh address whenever one is blocked",
             adaptive=True, pool=1500),
    Strategy("hetero-pacing", "every worker paces itself differently", hetero=0.9),
    Strategy("small-cells", "12 cells of 5, each cell with its own behaviour (under the group minimum)",
             cells=12),
    Strategy("low-and-slow", "300 addresses, one request per 75s each (too little to profile)",
             workers=300, pool=300, gap=75.0, spread=75.0),
    Strategy("rotate-3", "discard every address after 3 requests", per_ip=3, pool=6000),
    Strategy("human-mimic", "load assets, browse popular pages, varied pacing, drift in over 10 min",
             assets=1.0, noise=0.4, hetero=0.9, spread=600.0, jitter=0.8),
    Strategy("mimic+adaptive", "human-mimic plus rotation on block",
             assets=1.0, noise=0.4, hetero=0.9, spread=600.0, jitter=0.8, adaptive=True, pool=1500),
    Strategy("stuff-naive", "control: credential stuffing from 40 addresses",
             mode="stuff", workers=40, pool=40, gap=9.0),
    Strategy("stuff-rotate-3", "credential stuffing, 3 guesses per address",
             mode="stuff", workers=40, gap=9.0, per_ip=3, pool=6000),
    Strategy("stuff-low-slow", "credential stuffing, 400 addresses, one guess per 80s each",
             mode="stuff", workers=400, pool=400, gap=80.0, spread=80.0),
]


def _attacker_ip(i: int) -> str:
    return f"203.{i // 62500 % 4}.{i // 250 % 250}.{i % 250 + 1}"  # simulation-only labels


class Campaign:
    def __init__(self, st: Strategy, rng: random.Random):
        self.st = st
        self.rng = rng
        self.next_ip = 0
        self.next_page = 100_000
        self.workers = []
        self.owner: dict[str, int] = {}
        for w in range(st.workers):
            gap, assets, noise = st.gap, rng.random() < st.assets, st.noise
            if st.cells:
                cell = random.Random(w % st.cells)
                gap = st.gap * cell.uniform(0.4, 3.0)
                assets = cell.random() < 0.5
                noise = cell.uniform(0.0, 0.6)
            if st.hetero:
                gap *= rng.lognormvariate(0, st.hetero)
            self.workers.append({
                "gap": gap, "assets": assets, "noise": noise, "ip": None, "used": 0,
                "ua": rng.choice(simulate._BROWSER_UAS), "dead": False, "blocked": False,
            })

    def start_times(self):
        return [(ATTACK_START + self.rng.uniform(0, self.st.spread), w) for w in range(self.st.workers)]

    def _fresh_ip(self, w) -> bool:
        if self.next_ip >= self.st.pool:
            w["dead"] = True
            return False
        w["ip"] = _attacker_ip(self.next_ip)
        self.owner[w["ip"]] = id(w)
        self.next_ip += 1
        w["used"] = 0
        w["blocked"] = False
        w["ua"] = self.rng.choice(simulate._BROWSER_UAS)
        return True

    def act(self, wi: int, t: float) -> tuple[list[Event], float | None]:
        """Return the requests worker wi sends at time t and when it acts next."""
        st, rng, w = self.st, self.rng, self.workers[wi]
        if w["dead"]:
            return [], None
        need_new = w["ip"] is None or (st.per_ip and w["used"] >= st.per_ip) \
            or (st.adaptive and w["blocked"])
        if need_new and not self._fresh_ip(w):
            return [], None
        w["used"] += 1
        ev = []
        if st.mode == "stuff":
            ok = rng.random() < 0.02
            ev.append(Event(t, w["ip"], method="POST", path="/login", status=200 if ok else 401, ua=w["ua"]))
        else:
            if rng.random() < w["noise"]:
                path = rng.choice(simulate._POPULAR)
            else:
                path = f"/products/{self.next_page}"
                self.next_page += 1
            ev.append(Event(t, w["ip"], method="GET", path=path, status=200, ua=w["ua"]))
            if w["assets"]:
                for a in rng.sample(simulate._ASSETS, rng.randint(3, 6)):
                    ev.append(Event(t + rng.uniform(0.05, 1.2), w["ip"], method="GET", path=a, status=200, ua=w["ua"]))
        if st.jitter >= 0.8:
            nxt = t + rng.lognormvariate(0, st.jitter) * w["gap"]
        else:
            nxt = t + max(0.3, rng.gauss(w["gap"], st.jitter * w["gap"]))
        return ev, nxt

    def blocked(self, wi: int) -> None:
        self.workers[wi]["blocked"] = True


def run(st: Strategy, cfg: Config | None = None, seed: int = 11, monitor_factory=None) -> dict:
    from .cli import Monitor

    rng = random.Random(seed)
    benign, truth = simulate.scenario(seed=seed, duration=DURATION, humans=400,
                                      swarm=0, stuffers=0, scanner=False)
    mon = (monitor_factory or (lambda: Monitor(cfg or Config(), DryRunActuator(), quiet=True)))()
    camp = Campaign(st, rng)
    heap = camp.start_times()
    heapq.heapify(heap)
    recent: dict[str, deque] = {}
    bi = 0
    goal_attempted = goal_served = 0
    hostile_ips: set[str] = set()
    actioned: dict[str, str] = {}
    first_block: float | None = None

    def deliver(ev: Event) -> bool:
        """Apply the firewall, then let the monitor see what got through."""
        nonlocal first_block
        level = mon.policy.level_of(ev.src, ev.ts)
        if level == "block":
            return False
        if level == "throttle":  # 30 new connections/min per address
            q = recent.setdefault(ev.src, deque())
            while q and q[0] < ev.ts - 60:
                q.popleft()
            if len(q) >= 30:
                return False
            q.append(ev.ts)
        for d in mon.feed(ev):
            for s in d.sources:
                if actioned.get(s) != "block":
                    actioned[s] = d.level
                if d.level == "block" and s in hostile_ips and first_block is None:
                    first_block = d.ts
        return True

    while heap or bi < len(benign):
        t_att = heap[0][0] if heap else float("inf")
        if bi < len(benign) and benign[bi].ts <= t_att:
            deliver(benign[bi])
            bi += 1
            continue
        t, wi = heapq.heappop(heap)
        if t >= DURATION:
            continue
        events, nxt = camp.act(wi, t)
        for i, ev in enumerate(events):
            hostile_ips.add(ev.src)
            ok = deliver(ev)
            if i == 0:
                is_goal = ev.path.startswith("/products/") or ev.path == "/login"
                goal_attempted += is_goal
                goal_served += is_goal and ok
                if not ok:
                    camp.blocked(wi)
        if nxt is not None:
            heapq.heappush(heap, (nxt, wi))

    benign_hit = Counter(truth[s] for s in actioned if s in truth)
    return {
        "strategy": st.name,
        "ips_used": len(hostile_ips),
        "ips_blocked": sum(1 for s in hostile_ips if actioned.get(s) == "block"),
        "ips_throttled": sum(1 for s in hostile_ips if actioned.get(s) == "throttle"),
        "attempted": goal_attempted,
        "served": goal_served,
        "yield": goal_served / goal_attempted if goal_attempted else 0.0,
        "first_block_after": None if first_block is None else round(first_block - ATTACK_START),
        "benign_actioned": sum(benign_hit.values()),
        "benign_detail": dict(benign_hit),
        "benign_sources": len(truth),
    }


def print_results(rows: list[dict]) -> None:
    print(f"{'strategy':16} {'IPs used':>8} {'blocked':>8} {'throttled':>9} {'job done':>9} "
          f"{'first block':>11} {'benign hit':>10}   verdict")
    for r in rows:
        y = r["yield"]
        verdict = "DEFENDED" if y < 0.2 else "partial" if y < 0.6 else "EVADED"
        fb = "-" if r["first_block_after"] is None else f"{r['first_block_after']}s"
        print(f"{r['strategy']:16} {r['ips_used']:>8} {r['ips_blocked']:>8} {r['ips_throttled']:>9} "
              f"{r['served']:>5}/{r['attempted']:<5}".ljust(60)
              + f"{y:>5.0%} {fb:>11} {r['benign_actioned']:>10}   {verdict}")
