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
python3 -m swarmguard redteam         # adaptive simulated attacker tries to evade it
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

Three population-level detectors cover attackers who keep every address unremarkable:

| Detector | Catches |
| --- | --- |
| Surge | far more asset-less addresses on one target than its learned normal level (rotation, low-and-slow) |
| Coverage | a group fetching pages no other client asks for (browser-imitating scrapers) |
| Heightened alert | once a target is under attack, a new asset-less address is cut off after 2 requests |

If the log carries no asset requests (assets on a CDN), the asset-based signals switch
themselves off rather than misfire.

## Red-team results

`swarmguard redteam` runs a simulated attacker that shares a job across workers, gets
feedback when an address is blocked, and adapts. "Job done" is the share of its requests
that got through; background traffic is 400 visitors plus an office NAT, a monitor and
a flash crowd. Seed 11; three seeds give the same picture.

| Strategy | Addresses burned | Job done, first version | Job done, now | Benign hit |
| --- | ---: | ---: | ---: | ---: |
| naive (control) | 60 | 7% | 3% | 0 |
| hetero-pacing | 60 | 5% | 2% | 0 |
| small-cells (12 groups of 5) | 60 | 42% | 7% | 0 |
| low-and-slow (300 addresses) | 300 | 58% | 18% | 0 |
| human-mimic (assets, noise, drift-in) | 60 | 93% | 8% | 0 |
| stuff-naive (control) | 40 | 12% | 4% | 0 |
| stuff-low-slow (400 addresses) | 400 | 70% | 19% | 0 |
| adaptive (new address when blocked) | 1500 | 85% | 66% | 0 |
| rotate-3 (3 requests per address) | 3296 | 100% | 65% | 0 |
| stuff-rotate-3 | 1228 | 100% | 54% | 0 |
| mimic+adaptive | 763 | 100% | 89% | 0 |

The last four still beat it. An attacker with a large pool of single-use addresses gets
about two requests per address before being cut off (five when it also imitates a
browser), and a firewall that acts per address cannot do better: it only sees a request
after it has been served. Stopping those needs a check before the response, such as a
login rate limit per account or a proof-of-work/JavaScript challenge at the web tier,
switched on when SwarmGuard reports a target under attack.

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
  simulator, the attacker and the detector share an author, so treat the results as a
  demonstration, not a benchmark. Tune thresholds in dry-run mode on your own logs.
- Address rotation still wins (see the red-team results).
- The population detectors learn "normal" from the first five minutes after start-up, so
  an attack already running at start-up is taken as normal, and a very slow ramp can
  drag the baseline up with it.
- During heightened alert a real visitor whose browser has every asset cached can be
  blocked after two page views on the attacked section (`shield_requests` tunes this).
- Behind a CDN or load balancer the access log must carry the real client address, and
  firewall actions on the origin host will not see it; enforce at the edge instead.
- Clients sharing one address (carrier NAT) are actioned together.
- Packet capture reads TCP connection attempts only: no UDP, no payload inspection.
- Detection runs on a tick (10 s by default), so the first requests always get through.
