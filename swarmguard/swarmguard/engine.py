"""Detection engine.

Keeps a sliding window of activity per source address and, on every tick, runs:

* single-source detectors (flood, port scan, decoy-path hit, error-heavy probing), and
* the swarm detector, which looks for *groups* of addresses that are individually
  unremarkable but behave like one coordinated actor.

The engine runs on event time (timestamps carried by events), so live traffic, log
replay and simulation all behave identically.
"""
from __future__ import annotations

import math
import random
from collections import Counter, deque
from dataclasses import dataclass, field

from .config import Config
from .events import Event

_ASSET_EXT = (
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".webp", ".map", ".ttf", ".mp4",
)


@dataclass
class Incident:
    kind: str  # swarm | surge | coverage | shield | flood | portscan | trap | probing
    score: float  # 0..1 confidence that this is hostile automation
    sources: list[str]
    reasons: list[str]
    ts: float
    detail: dict = field(default_factory=dict)


@dataclass
class Features:
    src: str
    first_seen: float
    n: int = 0
    rpm: float = 0.0  # all requests / connection attempts per minute
    pages: int = 0  # non-asset HTTP requests
    asset_ratio: float = 0.0
    err_ratio: float = 0.0
    post_ratio: float = 0.0
    breadth: float = 0.0  # distinct pages / page requests
    mean_gap: float = 0.0  # seconds between page requests
    trap_hits: int = 0
    ports: int = 0
    ua: str = ""
    paths: frozenset = frozenset()
    top_path: str = ""
    top_target: str = ""
    targets: frozenset = frozenset()
    novel: float = 0.0  # share of its pages that no other address requested
    age: float = 0.0  # seconds since its first request in the window


class _Source:
    __slots__ = ("first_seen", "last_seen", "events", "ua", "has_asset", "shield_hits")

    def __init__(self, ts: float, maxlen: int):
        self.first_seen = ts
        self.last_seen = ts
        # (ts, is_http, path, is_error, is_asset, is_post, is_trap, dport)
        self.events: deque = deque(maxlen=maxlen)
        self.ua = ""
        self.has_asset = False
        self.shield_hits = 0


def _target(path: str, is_post: bool) -> str:
    """What a request is aimed at: the exact endpoint for POSTs, the site section otherwise."""
    if is_post:
        return "POST " + path
    return "/" + path.split("/", 2)[1] if path.startswith("/") else path


def _clamp(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


class Engine:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.sources: dict[str, _Source] = {}
        self._traps = tuple(p.lower() for p in cfg.trap_paths)
        self._last_tick: float | None = None
        self._started: float | None = None
        self._base: dict[str, float] = {}  # learned normal levels for population detectors
        self._base_ready = False
        self.shields: dict[str, tuple[float, float]] = {}  # target -> (since, until)
        self.assets_visible = False  # until traffic shows the log carries asset requests
        self._seen_pages = 0
        self._seen_assets = 0
        self._rng = random.Random(0)

    # ------------------------------------------------------------------ ingest
    def ingest(self, ev: Event) -> list[Incident]:
        """Record an event; returns incidents when a detection tick falls due."""
        st = self.sources.get(ev.src)
        if st is None:
            if len(self.sources) >= self.cfg.max_sources:
                self._evict()
            st = self.sources[ev.src] = _Source(ev.ts, self.cfg.max_events_per_source)
        st.last_seen = ev.ts
        fast: list[Incident] = []
        if ev.kind == "http":
            path = ev.path or "/"
            low = path.lower()
            is_asset = low.endswith(_ASSET_EXT)
            is_post = ev.method == "POST"
            st.events.append((
                ev.ts, True, path, 400 <= ev.status < 500, is_asset,
                is_post, low.startswith(self._traps) if self._traps else False, 0,
            ))
            if not self.shields:  # learn the normal mix only while not under attack
                if is_asset:
                    self._seen_assets += 1
                else:
                    self._seen_pages += 1
                if self._seen_pages > 100_000:
                    self._seen_pages //= 2
                    self._seen_assets //= 2
            if is_asset:
                st.has_asset = True
            elif self.shields and not st.has_asset:
                # Heightened alert: a target is under distributed attack, so an address
                # that turned up after the attack began and behaves like the attackers
                # (no browser assets) is cut off after a couple of requests instead of
                # being given time to build a full profile.
                target = _target(path, is_post)
                sh = self.shields.get(target)
                if sh and sh[1] > ev.ts and st.first_seen >= sh[0]:
                    st.shield_hits += 1
                    if st.shield_hits == self.cfg.shield_requests:
                        fast.append(Incident(
                            "shield", 0.8, [ev.src],
                            [f"new address joined the ongoing attack on {target} "
                             f"({st.shield_hits} requests, no browser assets)"],
                            ev.ts, {"target": target},
                        ))
            if ev.ua:
                st.ua = ev.ua
        else:
            st.events.append((ev.ts, False, "", False, False, False, False, ev.dport))

        if self._last_tick is None:
            self._last_tick = self._started = ev.ts
        if ev.ts - self._last_tick >= self.cfg.tick:
            self._last_tick = ev.ts
            return fast + self.evaluate(ev.ts)
        return fast

    def _evict(self) -> None:
        oldest = sorted(self.sources, key=lambda s: self.sources[s].last_seen)
        for src in oldest[: max(1, len(oldest) // 10)]:
            del self.sources[src]

    # ---------------------------------------------------------------- features
    def _features(self, src: str, st: _Source, now: float) -> Features | None:
        cutoff = now - self.cfg.window
        ev = st.events
        while ev and ev[0][0] < cutoff:
            ev.popleft()
        if not ev:
            return None
        f = Features(src=src, first_seen=st.first_seen, ua=st.ua, n=len(ev))
        f.age = now - ev[0][0]
        span = max(30.0, min(self.cfg.window, f.age))
        f.rpm = f.n / span * 60.0
        http = errors = assets = posts = 0
        page_ts: list[float] = []
        page_paths: Counter = Counter()
        targets: Counter = Counter()
        ports: set[int] = set()
        for ts, is_http, path, is_err, is_asset, is_post, is_trap, dport in ev:
            if not is_http:
                ports.add(dport)
                continue
            http += 1
            errors += is_err
            posts += is_post
            f.trap_hits += is_trap
            if is_asset:
                assets += 1
            else:
                page_ts.append(ts)
                page_paths[path] += 1
                targets[_target(path, is_post)] += 1
        f.ports = len(ports)
        if http:
            f.asset_ratio = assets / http
            f.err_ratio = errors / http
            f.post_ratio = posts / http
        f.pages = len(page_ts)
        if f.pages:
            f.breadth = len(page_paths) / f.pages
            f.paths = frozenset(page_paths)
            f.top_path = page_paths.most_common(1)[0][0]
            f.targets = frozenset(targets)
            f.top_target = targets.most_common(1)[0][0]
        if f.pages > 1:
            f.mean_gap = (page_ts[-1] - page_ts[0]) / (f.pages - 1)
        return f

    # ---------------------------------------------------------------- evaluate
    def evaluate(self, now: float) -> list[Incident]:
        cfg = self.cfg
        feats: list[Features] = []
        for src in list(self.sources):
            st = self.sources[src]
            f = self._features(src, st, now)
            if f is None:
                del self.sources[src]
            else:
                feats.append(f)

        incidents: list[Incident] = []
        for f in feats:
            if f.trap_hits:
                incidents.append(Incident(
                    "trap", _clamp(0.8 + 0.05 * (f.trap_hits - 1)), [f.src],
                    [f"requested {f.trap_hits} decoy path(s) no legitimate client uses"], now,
                    {"trap_hits": f.trap_hits},
                ))
            if f.ports >= cfg.portscan_ports:
                incidents.append(Incident(
                    "portscan", 0.9, [f.src],
                    [f"connection attempts to {f.ports} distinct ports"], now, {"ports": f.ports},
                ))
            if f.rpm >= cfg.flood_rpm:
                incidents.append(Incident(
                    "flood", _clamp(0.6 + 0.2 * (f.rpm / cfg.flood_rpm - 1)), [f.src],
                    [f"{f.rpm:.0f} requests/min sustained (limit {cfg.flood_rpm:.0f})"], now,
                    {"rpm": round(f.rpm)},
                ))
            if f.n >= cfg.probe_min_requests and f.err_ratio >= cfg.probe_error_ratio and f.pages:
                incidents.append(Incident(
                    "probing", 0.7, [f.src],
                    [f"{f.err_ratio:.0%} of {f.n} requests were client errors"], now,
                    {"err_ratio": round(f.err_ratio, 2)},
                ))
        incidents.extend(self._swarms(feats, now))
        incidents.extend(self._population(feats, now))
        return incidents

    # -------------------------------------------------------------- population
    def _shield(self, target: str, now: float) -> None:
        since = self.shields.get(target, (now, 0.0))
        if since[1] <= now:
            since = (now, 0.0)
        self.shields[target] = (since[0], now + self.cfg.shield_ttl)

    def _population(self, feats: list[Features], now: float) -> list[Incident]:
        """Detectors that look at the whole client population rather than at addresses.

        Rotating through single-use addresses, going very slow, or imitating a browser
        all keep each address unremarkable. What they cannot hide is the aggregate:
        the target suddenly has far more asset-less clients than it normally does, or
        a group of clients is working through pages nobody else ever asks for.
        """
        cfg = self.cfg
        for t in [t for t, (_, until) in self.shields.items() if until <= now]:
            del self.shields[t]
        warm = self._started is not None and now - self._started >= cfg.window
        # If the log carries hardly any asset requests (assets on a CDN), "loads no
        # assets" says nothing about a client, so every signal built on it stays off.
        # The mix is learned from traffic seen while no attack is in progress, so a
        # flood of asset-less requests cannot switch these signals off.
        self.assets_visible = (
            self._seen_pages >= 200 and self._seen_assets >= 0.5 * self._seen_pages
        )
        out: list[Incident] = []
        observed: dict[str, float] = {}
        firing: set[str] = set()

        # --- surge of asset-less clients on one target
        thin: dict[str, list[str]] = {}
        if self.assets_visible:
            for f in feats:
                # (a browser's assets trail its page request, so give new arrivals a moment)
                if f.pages and f.asset_ratio == 0 and f.age >= 5.0:
                    for t in f.targets:
                        thin.setdefault(t, []).append(f.src)
        for target, srcs in thin.items():
            key = "thin:" + target
            observed[key] = len(srcs)
            base = self._base.get(key, 0.0)
            if self._base_ready and len(srcs) >= max(cfg.surge_min_sources, cfg.surge_factor * base):
                firing.add(key)
                self._shield(target, now)
                out.append(Incident(
                    "surge", 0.8, sorted(srcs),
                    [f"{len(srcs)} addresses that load no browser assets are working on {target} "
                     f"(normal level: {base:.0f})",
                     "each stays too quiet to stand out alone (rotation or low-and-slow)"],
                    now, {"target": target, "sources": len(srcs), "baseline": round(base, 1)},
                ))

        # --- coverage: a group working through pages nobody else requests
        owners: Counter = Counter()
        for f in feats:
            owners.update(f.paths)
        group, novel_paths = [], 0
        for f in feats:
            if len(f.paths) < cfg.swarm_min_pages:
                continue
            mine = sum(1 for p in f.paths if owners[p] == 1)
            f.novel = mine / len(f.paths)
            if f.novel >= cfg.novel_share:
                group.append(f)
                novel_paths += mine
        key = "novel"
        observed[key] = novel_paths
        base = self._base.get(key, 0.0)
        if (self._base_ready and len(group) >= cfg.swarm_min_sources
                and novel_paths >= max(cfg.coverage_min_paths, cfg.surge_factor * base)):
            firing.add(key)
            target = Counter(f.top_target for f in group).most_common(1)[0][0]
            out.append(Incident(
                "coverage", 0.8, sorted(f.src for f in group),
                [f"{len(group)} addresses fetched {novel_paths} pages that no other client asked for "
                 f"(normal level: {base:.0f})",
                 "systematic harvesting of the long tail, whatever the clients look like"],
                now, {"target": target, "sources": len(group), "novel_paths": novel_paths,
                      "baseline": round(base, 1)},
            ))

        # --- learn what normal looks like (never from a level that is raising an alarm)
        if warm and not self._base_ready:
            self._base = dict(observed)  # first full window: take it as the starting normal
            self._base_ready = True
        elif self._base_ready:
            alpha = min(1.0, cfg.tick / 1800.0)
            for key in set(self._base) | set(observed):
                if key in firing or key.removeprefix("thin:") in self.shields:
                    continue
                cur = self._base.get(key, 0.0)
                self._base[key] = cur + alpha * (observed.get(key, 0.0) - cur)
        return out

    # ------------------------------------------------------------------ swarms
    def _swarms(self, feats: list[Features], now: float) -> list[Incident]:
        cfg = self.cfg
        cand = [f for f in feats if f.pages >= cfg.swarm_min_pages]
        if len(cand) < cfg.swarm_min_sources:
            return []
        if len(cand) > cfg.swarm_max_profiled:
            cand = sorted(cand, key=lambda f: -f.pages)[: cfg.swarm_max_profiled]
        vecs = [
            (
                math.log10(1 + f.pages / max(1.0, f.mean_gap * f.pages) * 60) / 2,
                f.asset_ratio,
                f.breadth,
                f.err_ratio,
                f.post_ratio,
            )
            for f in cand
        ]
        out = []
        for members in _dbscan(vecs, cfg.swarm_eps, cfg.swarm_min_sources):
            inc = self._score_cluster([cand[i] for i in members], now)
            if inc:
                out.append(inc)
        return out

    def _score_cluster(self, group: list[Features], now: float) -> Incident | None:
        cfg = self.cfg
        m = len(group)

        # 1. Arrival synchrony: did most members first appear in one short burst?
        #    Addresses already present when monitoring began have no known arrival time
        #    (right after start-up everyone looks "new"), so they are left out; without
        #    enough known arrivals the signal stays neutral.
        warm = (self._started or 0.0) + cfg.swarm_sync_span
        firsts = sorted(f.first_seen for f in group if f.first_seen > warm)
        sync = 0.5
        if len(firsts) >= max(3, m // 2):
            best = j = 0
            for i in range(len(firsts)):
                while firsts[i] - firsts[j] > cfg.swarm_sync_span:
                    j += 1
                best = max(best, i - j + 1)
            sync = best / len(firsts)

        # 2. Cadence homogeneity: do members pace themselves the same way?
        gaps = [f.mean_gap for f in group if f.mean_gap > 0]
        homog = 0.0
        if len(gaps) >= 3:
            mu = sum(gaps) / len(gaps)
            sd = math.sqrt(sum((g - mu) ** 2 for g in gaps) / len(gaps))
            homog = _clamp(1 - (sd / mu) / 0.6) if mu else 0.0

        # 3. Clients that never fetch page assets are not browsers.
        noasset = 1 - sum(f.asset_ratio for f in group) / m

        # 4a. Divide-and-conquer crawl: every member visits new pages only, and
        #     members barely overlap with each other.
        pairs = [(a, b) for a in range(m) for b in range(a + 1, m)]
        if len(pairs) > 300:
            pairs = self._rng.sample(pairs, 300)
        jac = 0.0
        for a, b in pairs:
            pa, pb = group[a].paths, group[b].paths
            union = len(pa | pb)
            jac += len(pa & pb) / union if union else 0.0
        jac /= len(pairs)
        breadth = sum(f.breadth for f in group) / m
        crawl = _clamp((breadth * (1 - jac) - 0.6) / 0.35)

        # 4b. Hammering: the whole group concentrates on one endpoint with POSTs/errors.
        tops = Counter(f.top_path for f in group)
        top_path, top_n = tops.most_common(1)[0]
        err = sum(f.err_ratio for f in group) / m
        post = sum(f.post_ratio for f in group) / m
        hammer = (top_n / m) * max(err, post)

        score = 0.30 * sync + 0.25 * homog + 0.20 * noasset + 0.25 * max(crawl, hammer)
        if score < cfg.throttle_score:
            return None

        reasons = [f"{m} addresses share one behaviour profile"]
        if sync >= 0.6:
            reasons.append(f"{sync:.0%} of them first appeared within {cfg.swarm_sync_span:.0f}s of each other")
        if homog >= 0.5:
            reasons.append("near-identical request pacing across addresses")
        if noasset >= 0.8:
            reasons.append("none of them load page assets (not browsers)")
        if crawl >= 0.5:
            reasons.append("they split the site between them with almost no overlap (distributed crawl)")
        if hammer >= 0.5:
            reasons.append(f"they concentrate on {top_path} with {max(err, post):.0%} POST/error traffic")
        uas = Counter(f.ua for f in group if f.ua)
        if uas and uas.most_common(1)[0][1] / m >= 0.6:
            reasons.append("one user-agent string reused across addresses")
        rpm = sum(f.rpm for f in group)
        if noasset >= 0.8 and self.assets_visible:
            self._shield(Counter(f.top_target for f in group).most_common(1)[0][0], now)
        return Incident(
            "swarm", round(score, 3), sorted(f.src for f in group), reasons, now,
            {
                "size": m,
                "combined_rpm": round(rpm),
                "per_source_rpm": round(rpm / m, 1),
                "signals": {
                    "sync": round(sync, 2), "cadence": round(homog, 2),
                    "no_assets": round(noasset, 2), "crawl": round(crawl, 2),
                    "hammer": round(hammer, 2),
                },
                "top_path": top_path,
            },
        )


def _dbscan(vecs: list[tuple], eps: float, min_pts: int) -> list[list[int]]:
    """Plain DBSCAN; returns clusters as lists of indices (noise omitted)."""
    n = len(vecs)
    eps2 = eps * eps
    neigh: list[list[int]] = [[] for _ in range(n)]
    for i in range(n):
        vi = vecs[i]
        for j in range(i + 1, n):
            vj = vecs[j]
            d = 0.0
            for a, b in zip(vi, vj):
                d += (a - b) * (a - b)
                if d > eps2:
                    break
            else:
                neigh[i].append(j)
                neigh[j].append(i)
    label = [-1] * n
    clusters: list[list[int]] = []
    for i in range(n):
        if label[i] != -1 or len(neigh[i]) + 1 < min_pts:
            continue
        cid = len(clusters)
        members = [i]
        label[i] = cid
        stack = list(neigh[i])
        while stack:
            k = stack.pop()
            if label[k] != -1:
                continue
            label[k] = cid
            members.append(k)
            if len(neigh[k]) + 1 >= min_pts:
                stack.extend(neigh[k])
        clusters.append(members)
    return clusters
