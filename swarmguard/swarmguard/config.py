from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, fields


@dataclass
class Config:
    # --- observation ---
    window: float = 300.0  # seconds of history kept per source
    tick: float = 10.0  # how often (in event time) detectors run
    max_sources: int = 50_000
    max_events_per_source: int = 400

    # --- single-source detectors ---
    flood_rpm: float = 600.0  # sustained requests/min from one address
    portscan_ports: int = 15  # distinct destination ports in the window
    probe_min_requests: int = 20
    probe_error_ratio: float = 0.7
    trap_paths: list[str] = field(
        default_factory=lambda: [
            "/.env",
            "/.git/config",
            "/wp-login.php",
            "/xmlrpc.php",
            "/phpmyadmin",
        ]
    )

    # --- swarm detector ---
    swarm_min_sources: int = 6
    swarm_min_pages: int = 5  # page requests a source needs before it is profiled
    swarm_eps: float = 0.2  # behaviour-space neighbourhood radius
    swarm_sync_span: float = 120.0  # arrival-synchrony window, seconds
    swarm_max_profiled: int = 800

    # --- population-level detectors (catch rotation, low-and-slow and mimicry) ---
    surge_min_sources: int = 20  # asset-less addresses on one target before it counts as a surge
    surge_factor: float = 4.0  # ...and this many times the learned baseline
    coverage_min_paths: int = 40  # pages only one address asked for, across a group
    novel_share: float = 0.5  # share of an address's pages that nobody else requested
    shield_ttl: float = 600.0  # heightened alert on a target after an attack on it
    shield_requests: int = 2  # asset-less requests a new address gets on a shielded target

    # --- response policy ---
    throttle_score: float = 0.55
    block_score: float = 0.75
    base_ttl: float = 600.0
    max_ttl: float = 86_400.0
    strikes_to_block: int = 2  # throttles before a repeat offender is blocked
    max_active_blocks: int = 10_000
    max_block_fraction: float = 0.8  # of recently seen sources; above it, throttle instead
    allowlist: list[str] = field(default_factory=lambda: ["127.0.0.0/8", "::1/128"])

    # --- enforcement / output ---
    throttle_rate: str = "30/minute"
    throttle_burst: int = 10
    audit_log: str = ""
    webhook_url: str = ""

    # --- optional LLM analyst ---
    analyst_model: str = "claude-opus-5-5"

    @classmethod
    def load(cls, path: str | None) -> "Config":
        cfg = cls()
        if not path:
            return cfg
        with open(path, "rb") as fh:
            data = tomllib.load(fh)
        known = {f.name: f for f in fields(cls)}
        for key, value in data.items():
            if key not in known:
                raise ValueError(f"unknown config key: {key}")
            default = getattr(cfg, key)
            if isinstance(default, float) and isinstance(value, int):
                value = float(value)
            if type(value) is not type(default):
                raise ValueError(
                    f"config key {key}: expected {type(default).__name__}, got {type(value).__name__}"
                )
            setattr(cfg, key, value)
        return cfg
