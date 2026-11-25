from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone

from . import sensors, simulate
from .actuators import Actuator, DryRunActuator, NftActuator
from .config import Config
from .engine import Engine, Incident
from .events import Event
from .policy import Decision, Policy


class Monitor:
    """Wires engine -> policy -> actuator, plus audit log, webhook and analyst."""

    def __init__(self, cfg: Config, actuator: Actuator, analyst=None, quiet: bool = False):
        self.cfg = cfg
        self.engine = Engine(cfg)
        self.policy = Policy(cfg, actuator)
        self.analyst = analyst
        self.quiet = quiet
        self.decisions: list[Decision] = []
        self._audit = open(cfg.audit_log, "a") if cfg.audit_log else None

    def feed(self, ev: Event) -> list[Decision]:
        made = []
        for inc in self.engine.ingest(ev):
            d = self.policy.handle(inc, ev.ts, len(self.engine.sources))
            if d:
                made.append(d)
                self._record(d)
        if self.analyst:
            self._drain_analyst(ev.ts)
        self.decisions.extend(made)
        return made

    def _record(self, d: Decision) -> None:
        inc = d.incident
        rec = {
            "ts": d.ts, "action": d.level, "ttl": d.ttl, "detector": inc.kind,
            "score": inc.score, "sources": d.sources, "reasons": inc.reasons,
            "detail": inc.detail, "note": d.note,
        }
        self._emit(rec)
        if not self.quiet:
            when = datetime.fromtimestamp(d.ts, timezone.utc).strftime("%H:%M:%S")
            who = d.sources[0] if len(d.sources) == 1 else f"{len(d.sources)} addresses"
            print(f"[{when}] {d.level.upper():8} {who}  ({inc.kind}, score {inc.score:.2f}, ttl {d.ttl:.0f}s)")
            for r in inc.reasons:
                print(f"             - {r}")
            if d.note:
                print(f"             ! {d.note}")
        if self.analyst and inc.kind == "swarm":
            paths, uas = [], []
            for src in d.sources[:10]:
                st = self.engine.sources.get(src)
                if st:
                    paths.extend(e[2] for e in list(st.events)[-2:] if e[1])
                    uas.append(st.ua)
            from .analyst import summarize

            self.analyst.submit(inc, summarize(inc, d.level, paths, sorted(set(uas))))

    def _drain_analyst(self, now: float) -> None:
        while True:
            try:
                inc, verdict = self.analyst.results.get_nowait()
            except queue.Empty:
                return
            released = []
            if verdict.get("assessment") == "likely_benign":
                released = self.policy.release(inc.sources, now)
            self._emit({"ts": now, "action": "analyst", "verdict": verdict,
                        "released": released, "sources": len(inc.sources)})
            if not self.quiet:
                if "error" in verdict:
                    print(f"             analyst unavailable: {verdict['error']}")
                else:
                    print(f"             analyst: {verdict['assessment']} ({verdict['confidence']}) - {verdict['summary']}")
                    if released:
                        print(f"             analyst lifted the action on {len(released)} addresses")

    def _emit(self, rec: dict) -> None:
        if self._audit:
            self._audit.write(json.dumps(rec) + "\n")
            self._audit.flush()
        if self.cfg.webhook_url:
            req = urllib.request.Request(
                self.cfg.webhook_url, data=json.dumps(rec).encode(),
                headers={"Content-Type": "application/json"},
            )
            threading.Thread(target=_post, args=(req,), daemon=True).start()


def _post(req) -> None:
    try:
        urllib.request.urlopen(req, timeout=5).close()
    except OSError as exc:
        print(f"webhook failed: {exc}", file=sys.stderr)


def _make_analyst(args, cfg):
    if not getattr(args, "analyst", False):
        return None
    try:
        from .analyst import Analyst

        return Analyst(cfg.analyst_model)
    except ImportError:
        sys.exit('--analyst needs the Anthropic SDK: pip install "swarmguard[analyst]"')


# ----------------------------------------------------------------------------- run
def cmd_run(args) -> int:
    cfg = Config.load(args.config)
    if not args.log and not args.iface:
        sys.exit("give at least one sensor: --log FILE and/or --iface NAME")
    if args.enforce:
        actuator: Actuator = NftActuator(cfg.throttle_rate, cfg.throttle_burst)
        actuator.setup()
        print("ENFORCING via nftables table 'inet swarmguard' (remove with: swarmguard flush)")
    else:
        actuator = DryRunActuator()
        print("dry run: reporting what would be done; add --enforce to act")
    mon = Monitor(cfg, actuator, _make_analyst(args, cfg))

    q: queue.Queue = queue.Queue(maxsize=100_000)

    def pump(gen):
        for ev in gen:
            try:
                q.put_nowait(ev)
            except queue.Full:
                pass  # shed load rather than fall behind during a flood

    for path in args.log or []:
        threading.Thread(target=pump, args=(sensors.follow_log(path),), daemon=True).start()
    for iface in args.iface or []:
        threading.Thread(target=pump, args=(sensors.sniff(iface),), daemon=True).start()
    print(f"watching: {', '.join((args.log or []) + (args.iface or []))}")
    try:
        while True:
            try:
                mon.feed(q.get(timeout=1.0))
            except queue.Empty:
                if mon.analyst:
                    mon._drain_analyst(time.time())
    except KeyboardInterrupt:
        print("\nstopped; active firewall entries expire on their own (or run: swarmguard flush)")
    return 0


# -------------------------------------------------------------------------- replay
def cmd_replay(args) -> int:
    cfg = Config.load(args.config)
    mon = Monitor(cfg, DryRunActuator(), _make_analyst(args, cfg))
    n = 0
    for ev in sensors.read_log(args.file):
        mon.feed(ev)
        n += 1
    acted = {s for d in mon.decisions for s in d.sources}
    print(f"\n{n} events, {len(mon.decisions)} decisions, {len(acted)} addresses would be actioned")
    return 0


# ------------------------------------------------------------------------ simulate
def cmd_simulate(args) -> int:
    cfg = Config.load(args.config)
    events, truth = simulate.scenario(seed=args.seed)
    if args.write:
        with open(args.write, "w") as fh:
            for e in events:
                fh.write(json.dumps({"ts": e.ts, "src": e.src, "method": e.method,
                                     "path": e.path, "status": e.status, "ua": e.ua}) + "\n")
        print(f"wrote {len(events)} events to {args.write}")
        return 0
    mon = Monitor(cfg, DryRunActuator(), quiet=args.quiet)
    report = run_simulation(mon, events, truth)
    print_report(report)
    return 0


def run_simulation(mon: Monitor, events: list[Event], truth: dict[str, str]) -> dict:
    """Feed events through the monitor, dropping traffic from blocked sources as a
    firewall would. Returns per-label outcome counts."""
    served: Counter = Counter()
    dropped: Counter = Counter()
    worst: dict[str, str] = {}
    for ev in events:
        label = truth[ev.src]
        if mon.policy.level_of(ev.src, ev.ts) == "block":
            dropped[label] += 1
            continue
        served[label] += 1
        for d in mon.feed(ev):
            for s in d.sources:
                if worst.get(s) != "block":
                    worst[s] = d.level
    rows = {}
    for label in sorted(set(truth.values())):
        srcs = [s for s, l in truth.items() if l == label]
        rows[label] = {
            "sources": len(srcs),
            "throttled": sum(1 for s in srcs if worst.get(s) == "throttle"),
            "blocked": sum(1 for s in srcs if worst.get(s) == "block"),
            "served": served[label],
            "dropped": dropped[label],
        }
    return rows


def print_report(rows: dict) -> None:
    print("\nSimulation result (synthetic traffic, ground truth known):")
    print(f"  {'traffic':10} {'kind':8} {'addresses':>9} {'throttled':>9} {'blocked':>8} {'reqs served':>12} {'reqs dropped':>13}")
    for label, r in rows.items():
        kind = "HOSTILE" if label in simulate.HOSTILE else "benign"
        print(f"  {label:10} {kind:8} {r['sources']:>9} {r['throttled']:>9} {r['blocked']:>8} {r['served']:>12} {r['dropped']:>13}")


# --------------------------------------------------------------------------- flush
def cmd_flush(args) -> int:
    NftActuator().teardown()
    print("removed nftables table 'inet swarmguard'")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="swarmguard", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="monitor live traffic")
    r.add_argument("--log", action="append", help="web access log to tail (repeatable)")
    r.add_argument("--iface", action="append", help="interface to capture connection attempts on (root)")
    r.add_argument("--enforce", action="store_true", help="apply nftables actions (default: dry run)")
    r.add_argument("--analyst", action="store_true", help="have Claude review swarm incidents")
    r.add_argument("--config")
    r.set_defaults(fn=cmd_run)

    r = sub.add_parser("replay", help="analyse an existing access log (never enforces)")
    r.add_argument("file")
    r.add_argument("--analyst", action="store_true")
    r.add_argument("--config")
    r.set_defaults(fn=cmd_replay)

    r = sub.add_parser("simulate", help="run a synthetic attack scenario through the detector")
    r.add_argument("--seed", type=int, default=7)
    r.add_argument("--quiet", action="store_true", help="only print the summary table")
    r.add_argument("--write", metavar="FILE", help="write the scenario as a JSON-lines log instead")
    r.add_argument("--config")
    r.set_defaults(fn=cmd_simulate)

    r = sub.add_parser("flush", help="remove every SwarmGuard firewall rule")
    r.set_defaults(fn=cmd_flush)

    args = p.parse_args(argv)
    return args.fn(args)
