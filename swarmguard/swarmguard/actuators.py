"""Enforcement back-ends.

DryRunActuator only records what would be done. NftActuator programs a dedicated
nftables table; set elements carry kernel-side timeouts, so actions expire on their own
even if SwarmGuard crashes, and removing the table undoes everything.
"""
from __future__ import annotations

import ipaddress
import subprocess

TABLE = "swarmguard"


class Actuator:
    def setup(self) -> None: ...
    def apply(self, level: str, target: str, ttl: float) -> None: ...
    def release(self, target: str) -> None: ...
    def teardown(self) -> None: ...


class DryRunActuator(Actuator):
    def __init__(self):
        self.log: list[tuple[str, str, float]] = []

    def apply(self, level: str, target: str, ttl: float) -> None:
        self.log.append((level, target, ttl))

    def release(self, target: str) -> None:
        self.log.append(("release", target, 0.0))


def _ruleset(rate: str, burst: int) -> str:
    limit = f"limit rate over {rate} burst {burst} packets"
    return f"""
table inet {TABLE} {{
  set block4 {{ type ipv4_addr; flags timeout; }}
  set block6 {{ type ipv6_addr; flags interval, timeout; }}
  set throttle4 {{ type ipv4_addr; flags timeout; }}
  set throttle6 {{ type ipv6_addr; flags interval, timeout; }}
  set meter4 {{ type ipv4_addr; flags dynamic, timeout; timeout 2m; }}
  set meter6 {{ type ipv6_addr; flags dynamic, timeout; timeout 2m; }}
  chain input {{
    type filter hook input priority -10; policy accept;
    ip saddr @block4 counter drop
    ip6 saddr @block6 counter drop
    ip saddr @throttle4 ct state new add @meter4 {{ ip saddr {limit} }} counter drop
    ip6 saddr @throttle6 ct state new add @meter6 {{ ip6 saddr & ffff:ffff:ffff:ffff:: {limit} }} counter drop
  }}
}}
"""


class NftActuator(Actuator):
    def __init__(self, rate: str = "30/minute", burst: int = 10):
        self.rate = rate
        self.burst = burst

    @staticmethod
    def _nft(*args: str, stdin: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["nft", *args], input=stdin, text=True, capture_output=True, check=check
        )

    @staticmethod
    def _family(target: str) -> str:
        # Validates the target: only a real address/prefix ever reaches nft.
        return "6" if ipaddress.ip_network(target, strict=False).version == 6 else "4"

    def setup(self) -> None:
        self._nft("delete", "table", "inet", TABLE, check=False)
        self._nft("-f", "-", stdin=_ruleset(self.rate, self.burst))

    def apply(self, level: str, target: str, ttl: float) -> None:
        fam = self._family(target)
        if level not in ("throttle", "block"):
            raise ValueError(level)
        if level == "block":  # a block supersedes a throttle
            self._nft("delete", "element", "inet", TABLE, f"throttle{fam}", f"{{ {target} }}", check=False)
        self._nft(
            "add", "element", "inet", TABLE, f"{level}{fam}",
            f"{{ {target} timeout {max(1, int(ttl))}s }}",
        )

    def release(self, target: str) -> None:
        fam = self._family(target)
        for name in ("block", "throttle"):
            self._nft("delete", "element", "inet", TABLE, f"{name}{fam}", f"{{ {target} }}", check=False)

    def teardown(self) -> None:
        self._nft("delete", "table", "inet", TABLE, check=False)
