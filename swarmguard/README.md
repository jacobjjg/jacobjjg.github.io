# SwarmGuard

A network monitor that detects coordinated bot and AI-agent swarms and responds with
time-limited firewall actions.

Classic defences count requests per address. A swarm defeats that by spreading work
across many addresses that each look harmless: slow, jittered, with rotated browser
user agents. SwarmGuard looks for the coordination instead: groups of addresses that
behave like one actor.

Pure Python 3.11+, no dependencies. Linux for live packet capture and enforcement.

## Try it

```bash
cd swarmguard
python3 -m swarmguard simulate        # synthetic attack scenario, no network traffic
python3 -m pytest                     # test suite (pip install pytest)
```

The scenario mixes 300 ordinary visitors, an office behind one NAT address, an uptime
monitor and a benign flash crowd with a 60-address distributed scraper, a 40-address
credential-stuffing swarm and a lone secrets scanner. Every swarm member runs far below
the per-address flood limit.

## Run it

```bash
# watch, and report what would be done (the default: nothing is touched)
python3 -m swarmguard run --log /var/log/nginx/access.log

# add packet capture to see scans and floods on every port (root)
sudo python3 -m swarmguard run --log /var/log/nginx/access.log --iface eth0

# act: program nftables
sudo python3 -m swarmguard run --log /var/log/nginx/access.log --iface eth0 \
     --enforce --config swarmguard.example.toml

python3 -m swarmguard replay old-access.log   # what would it have done? never enforces
sudo python3 -m swarmguard flush              # remove every SwarmGuard firewall rule
```

Run in dry-run mode against your real traffic first, and put your own admin, office and
monitoring addresses in `allowlist` before using `--enforce`.

## How detection works

Sensors feed a sliding window (5 minutes by default) of activity per source address:

| Sensor | Sees |
| --- | --- |
| Access log (`--log`) | nginx/Apache combined format or JSON lines: method, path, status, user agent |
| Packet capture (`--iface`) | every inbound TCP connection attempt, on any port |

Single-address detectors: request flood, port scan, hits on decoy paths (`/.env`,
`/.git/config`, ...), and error-heavy probing.

The swarm detector profiles each address (page rate, share of asset requests, share of
new pages, error and POST ratios), clusters addresses with near-identical profiles
(DBSCAN), and scores each cluster for coordination:

| Signal | Meaning |
| --- | --- |
| Arrival synchrony | most members first appeared within the same two minutes |
| Cadence homogeneity | members pace their requests the same way; people do not |
| No assets | members never fetch CSS/JS/images, so they are not browsers |
| Distributed crawl | each member only visits new pages, and members barely overlap |
| Hammering | the whole group concentrates POSTs/errors on one endpoint |

## How it responds

Ladder: observe, then throttle (per-address limit on new connections), then block.

- Every action has a TTL enforced by the kernel, so it expires even if SwarmGuard dies.
- Repeat offenders get doubled TTLs and are promoted from throttle to block.
- IPv6 clients are actioned as their /64.
- Allowlisted networks are never touched.
- A circuit breaker refuses to block most of the visible client population at once; it
  throttles and flags the incident for a human instead.
- All rules live in one nftables table (`inet swarmguard`); `flush` removes it.
- Every decision goes to the console, and optionally to a JSON-lines audit log and a webhook.

Responses are limited to filtering traffic arriving at your own host. SwarmGuard never
sends anything back at a source.

## Optional AI analyst

`--analyst` asks Claude to review each swarm incident and explain it for the on-call
engineer (`pip install anthropic`, credentials via `ANTHROPIC_API_KEY`). It runs in the
background and never delays enforcement.

Logs contain attacker-chosen text, so the analyst's authority is deliberately narrow: it
can lift an action it judges a false positive, or leave it in place. It cannot escalate,
add targets or pick addresses.

## Limits

- Tested on synthetic traffic and unit tests only; not yet on production traffic. The
  simulator and the detector share an author, so treat its clean results as a
  demonstration, not a benchmark. Tune thresholds in dry-run mode on your own logs.
- A swarm whose members each convincingly imitate a different human (varied pacing,
  asset loading, overlapping navigation) will not cluster and is not detected.
- Behind a CDN or load balancer the access log must carry the real client address, and
  firewall actions on the origin host will not see it; enforce at the edge instead.
- Clients sharing one address (carrier NAT) are actioned together.
- Packet capture reads TCP connection attempts only: no UDP, no payload inspection.
- Detection runs on a tick (10 s by default), so the first requests always get through.
