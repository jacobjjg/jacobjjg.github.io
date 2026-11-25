import os
import random
import shutil
import struct
import socket
import subprocess

import pytest

from swarmguard import sensors, simulate
from swarmguard.actuators import DryRunActuator, NftActuator
from swarmguard.cli import Monitor, run_simulation
from swarmguard.config import Config
from swarmguard.engine import Engine, Incident
from swarmguard.events import Event
from swarmguard.policy import Policy, enforcement_target


# ------------------------------------------------------------------ end to end
@pytest.mark.parametrize("seed", [1, 7, 42])
def test_scenario_blocks_hostile_and_spares_benign(seed):
    events, truth = simulate.scenario(seed=seed)
    rows = run_simulation(Monitor(Config(), DryRunActuator(), quiet=True), events, truth)
    for label, r in rows.items():
        if label in simulate.HOSTILE:
            assert r["blocked"] == r["sources"], label
        else:
            assert r["blocked"] == 0 and r["throttled"] == 0, label
    # the swarm is cut off early: most of its requests never get served
    assert rows["scraper"]["dropped"] > 10 * rows["scraper"]["served"]


def _swarm_events(rng, n, start_spread, assets=False, t_end=900.0):
    ev = []
    for i in range(n):
        src = f"203.0.113.{i + 1}"
        t = rng.uniform(0, start_spread)
        page = i * 1000
        while t < t_end:
            ev.append(Event(t, src, method="GET", path=f"/item/{page}", status=200))
            if assets:
                for a in ("/s/a.css", "/s/a.js", "/s/a.png"):
                    ev.append(Event(t + 0.1, src, method="GET", path=a, status=200))
            page += 1
            t += max(0.5, rng.gauss(5, 1.5))
    return sorted(ev, key=lambda e: e.ts)


def _run(events, cfg=None):
    mon = Monitor(cfg or Config(), DryRunActuator(), quiet=True)
    for e in events:
        mon.feed(e)
    return mon


def test_staggered_swarm_still_caught():
    # Agents join over 10 minutes instead of all at once: no arrival synchrony.
    mon = _run(_swarm_events(random.Random(3), 30, start_spread=600))
    assert len({s for d in mon.decisions for s in d.sources}) >= 25


def test_browser_like_staggered_swarm_still_caught():
    # Loads assets like a browser and staggers arrival; pacing and the partitioned
    # crawl still give it away.
    mon = _run(_swarm_events(random.Random(3), 30, start_spread=600, assets=True))
    assert len({s for d in mon.decisions for s in d.sources}) >= 25


def test_cold_start_does_not_fake_arrival_synchrony():
    # Everyone looks newly arrived when monitoring starts; that must not count as sync.
    eng = Engine(Config())
    incs = []
    for e in _swarm_events(random.Random(5), 10, start_spread=20, t_end=100):
        incs += eng.ingest(e)
    assert incs and all(i.detail["signals"]["sync"] == 0.5 for i in incs if i.kind == "swarm")


def test_small_group_is_not_a_swarm():
    mon = _run(_swarm_events(random.Random(1), 3, start_spread=10))
    assert mon.decisions == []


# ------------------------------------------------------------------ single source
def test_trap_and_flood_and_portscan():
    cfg = Config()
    eng = Engine(cfg)
    kinds = set()
    for i in range(700):
        for inc in eng.ingest(Event(i * 0.05, "192.0.2.1", path="/x", status=200)):
            kinds.add(inc.kind)
    eng.ingest(Event(36, "192.0.2.2", path="/.env", status=404))
    for p in range(20):
        eng.ingest(Event(37 + p * 0.01, "192.0.2.3", kind="conn", dport=1000 + p))
    kinds |= {i.kind for i in eng.evaluate(40)}
    assert {"flood", "trap", "portscan"} <= kinds


# ------------------------------------------------------------------ policy
def _inc(sources, score=0.9, kind="swarm"):
    return Incident(kind, score, sources, ["test"], 0.0)


def test_allowlist_never_actioned():
    cfg = Config(allowlist=["10.0.0.0/8", "2001:db8::/32"])
    pol = Policy(cfg, DryRunActuator())
    d = pol.handle(_inc(["10.1.2.3", "2001:db8::5", "203.0.113.5"]), 0, 5)
    assert d.sources == ["203.0.113.5"]


def test_circuit_breaker_downgrades_mass_block():
    act = DryRunActuator()
    pol = Policy(Config(), act)
    srcs = [f"203.0.113.{i}" for i in range(1, 96)]
    d = pol.handle(_inc(srcs), 0, visible_sources=100)  # 95% of visible clients
    assert d.level == "throttle" and "circuit breaker" in d.note
    assert {lvl for lvl, _, _ in act.log} == {"throttle"}


def test_ladder_throttle_then_block_with_longer_ttl():
    cfg = Config()
    act = DryRunActuator()
    pol = Policy(cfg, act)
    src = ["203.0.113.9"]
    assert pol.handle(_inc(src, 0.6), 0, 5).level == "throttle"
    assert pol.handle(_inc(src, 0.6), 10, 5) is None  # already throttled
    d2 = pol.handle(_inc(src, 0.6), 700, 5)  # came back after expiry
    assert d2.level == "throttle" and d2.ttl == 2 * cfg.base_ttl
    d3 = pol.handle(_inc(src, 0.6), 2000, 5)  # third strike
    assert d3.level == "block" and d3.ttl == 4 * cfg.base_ttl


def test_throttle_upgrades_to_block_when_score_rises():
    pol = Policy(Config(), DryRunActuator())
    pol.handle(_inc(["203.0.113.9"], 0.6), 0, 5)
    assert pol.handle(_inc(["203.0.113.9"], 0.9), 10, 5).level == "block"


def test_ipv6_enforced_as_slash64():
    assert enforcement_target("2001:db8:1:2:aaaa:bbbb:cccc:dddd") == "2001:db8:1:2::/64"
    assert enforcement_target("203.0.113.7") == "203.0.113.7"


def test_garbage_source_is_never_passed_to_firewall():
    act = DryRunActuator()
    assert Policy(Config(), act).handle(_inc(["1.2.3.4; rm -rf /"]), 0, 5) is None
    assert act.log == []


# ------------------------------------------------------------------ analyst
class _FakeAnalyst:
    def __init__(self):
        import queue
        self.results = queue.Queue()
        self.submitted = []

    def submit(self, inc, summary):
        self.submitted.append(summary)


def test_analyst_can_only_lift_actions():
    events = _swarm_events(random.Random(2), 12, start_spread=20, t_end=120)
    fake = _FakeAnalyst()
    act = DryRunActuator()
    mon = Monitor(Config(), act, analyst=fake, quiet=True)
    for e in events:
        mon.feed(e)
    assert fake.submitted and mon.policy.active
    inc = mon.decisions[0].incident
    # "hostile" verdict changes nothing...
    before = dict(mon.policy.active)
    fake.results.put((inc, {"assessment": "hostile_swarm", "confidence": "high", "summary": "x"}))
    mon._drain_analyst(200)
    assert mon.policy.active == before
    # ...a "benign" verdict releases exactly that incident's addresses
    fake.results.put((inc, {"assessment": "likely_benign", "confidence": "high", "summary": "x"}))
    mon._drain_analyst(200)
    assert not set(inc.sources) & set(mon.policy.active)
    assert any(lvl == "release" for lvl, _, _ in act.log)
    assert mon.policy.handle(inc, 210, 50) is None  # and they stay suppressed


# ------------------------------------------------------------------ sensors
def test_parse_combined_log_line():
    line = ('203.0.113.4 - - [25/Nov/2026:10:00:00 +0000] "POST /login?x=1 HTTP/1.1" 401 512 '
            '"-" "Mozilla/5.0 (X11)"')
    ev = sensors.parse_log_line(line)
    assert (ev.src, ev.method, ev.path, ev.status, ev.ua) == (
        "203.0.113.4", "POST", "/login", 401, "Mozilla/5.0 (X11)")
    assert sensors.parse_log_line("garbage") is None


def test_parse_syn_frame():
    eth = b"\x00" * 12 + struct.pack("!H", 0x0800)
    ip = bytes([0x45, 0, 0, 40, 0, 0, 0, 0, 64, 6, 0, 0]) + socket.inet_aton("203.0.113.8") + socket.inet_aton("10.0.0.1")
    syn = struct.pack("!HHIIBBHHH", 40000, 22, 0, 0, 5 << 4, 0x02, 1024, 0, 0)
    synack = struct.pack("!HHIIBBHHH", 40000, 22, 0, 0, 5 << 4, 0x12, 1024, 0, 0)
    ev = sensors.parse_frame(eth + ip + syn, 1.0)
    assert (ev.src, ev.dport, ev.kind) == ("203.0.113.8", 22, "conn")
    assert sensors.parse_frame(eth + ip + synack, 1.0) is None
    assert sensors.parse_frame(b"short", 1.0) is None


def test_config_rejects_unknown_and_mistyped_keys(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text("flood_rpm = 300\nallowlist = ['10.0.0.0/8']\n")
    cfg = Config.load(str(p))
    assert cfg.flood_rpm == 300.0 and cfg.allowlist == ["10.0.0.0/8"]
    p.write_text("nope = 1\n")
    with pytest.raises(ValueError):
        Config.load(str(p))
    p.write_text("allowlist = 'x'\n")
    with pytest.raises(ValueError):
        Config.load(str(p))


# ------------------------------------------------------------------ nftables (real)
def _nft_usable():
    if os.geteuid() != 0 or not shutil.which("nft"):
        return False
    return subprocess.run(["nft", "list", "tables"], capture_output=True).returncode == 0


@pytest.mark.skipif(not _nft_usable(), reason="needs root and nftables")
def test_nft_actuator_roundtrip():
    act = NftActuator()
    act.setup()
    try:
        act.apply("throttle", "203.0.113.50", 60)
        act.apply("block", "203.0.113.50", 60)  # supersedes the throttle
        act.apply("block", "2001:db8:1:2::/64", 60)
        out = subprocess.run(["nft", "list", "table", "inet", "swarmguard"],
                             capture_output=True, text=True, check=True).stdout
        block4 = out.split("set block4")[1].split("}")[0] + "}"
        throttle4 = out.split("set throttle4")[1].split("set ")[0]
        assert "203.0.113.50" in block4 and "203.0.113.50" not in throttle4
        assert "2001:db8:1:2::/64" in out
        act.release("203.0.113.50")
        out = subprocess.run(["nft", "list", "table", "inet", "swarmguard"],
                             capture_output=True, text=True, check=True).stdout
        assert "203.0.113.50" not in out
        with pytest.raises(ValueError):
            act.apply("block", "not-an-ip }; flush ruleset", 60)
    finally:
        act.teardown()
    assert subprocess.run(["nft", "list", "table", "inet", "swarmguard"],
                          capture_output=True).returncode != 0


# ------------------------------------------------------------------ red team
from swarmguard import redteam

_DEFENDED = ["naive", "hetero-pacing", "small-cells", "low-and-slow", "human-mimic",
             "stuff-naive", "stuff-low-slow"]
# Address rotation still wins against per-address firewalling; these pin how much it costs.
_KNOWN_EVASIONS = {"adaptive": 0.75, "rotate-3": 0.75, "stuff-rotate-3": 0.65, "mimic+adaptive": 0.95}


@pytest.mark.parametrize("name", _DEFENDED + list(_KNOWN_EVASIONS))
def test_redteam(name):
    st = next(s for s in redteam.STRATEGIES if s.name == name)
    r = redteam.run(st)
    assert r["benign_actioned"] == 0
    if name in _DEFENDED:
        assert r["yield"] < 0.25
    else:
        assert r["yield"] < _KNOWN_EVASIONS[name]  # no regression on the known gaps


def test_no_false_positives_without_an_attack():
    events, _ = simulate.scenario(seed=5, duration=1800, humans=700, swarm=0, stuffers=0, scanner=False)
    assert _run(events).decisions == []


def test_asset_signals_disabled_when_log_has_no_assets():
    # Assets served from a CDN never appear in the origin log; "loads no assets" must
    # then stop counting against clients.
    events, _ = simulate.scenario(seed=5, duration=900, humans=500, swarm=0, stuffers=0, scanner=False)
    pages_only = [e for e in events if not e.path.startswith(("/static/", "/favicon"))]
    mon = _run(pages_only)
    assert mon.engine.assets_visible is False
    assert not [d for d in mon.decisions if d.incident.kind in ("surge", "shield")]
