# Observability — P2-OBS

**Date:** 2026-08-16 · **Status:** **STACK LANDED & DRILL EXECUTED (local)**

`/metrics` already existed. What was missing was everything that turns metrics
into operations: a scraper, alert rules, an alert route and a dashboard. That is
now in the repo and was executed, not just written.

## What is in the repo

| Piece | File |
|---|---|
| Scrape config | `ops/observability/prometheus/prometheus.yml` |
| Alert rules (7) | `ops/observability/prometheus/alerts.yml` |
| Alert routing | `ops/observability/alertmanager/alertmanager.yml` (null receivers — honest default) |
| Pager overlay | `ops/observability/alertmanager/alertmanager.pager.yml` (`url_file` from a secret) |
| Grafana datasource | `ops/observability/grafana/provisioning/datasources/prometheus.yml` |
| Grafana dashboard provider | `ops/observability/grafana/provisioning/dashboards/dashboards.yml` |
| Dashboard (9 panels) | `ops/observability/grafana/dashboards/fitness-os-overview.json` |
| Alert-path drill | `ops/observability/alert_fire_drill.sh` |
| Stack overlay | `docker-compose.obs.yml` |

## Real pager (still UNVERIFIED)

**Status:** **UNVERIFIED** · P2-OBS-PROD

Index: `docs/ops/EXTERNAL_GATES.md`. The committed Alertmanager config
uses **null receivers** so local drills do not pretend to page a human.
The firing → Alertmanager path is already proven below. That is **not**
a pager.

### Close this gate (one command)

Owner: **A-OPS**.

```bash
# File contains a single https webhook URL. Never commit it.
umask 077
printf '%s\n' "$PAGERDUTY_OR_SLACK_WEBHOOK_URL" > "$HOME/.secrets/fitness-os-pager-url"

export PAGER_WEBHOOK_URL_FILE="$HOME/.secrets/fitness-os-pager-url"
export APPLY=1          # remount alertmanager with the pager overlay
export RUN_DRILL=1      # re-fire BackendTargetDown
# Set this ONLY after a human confirms the page arrived:
export PAGER_HUMAN_ACK=1
./ops/observability/pager_prove.sh
```

Without `PAGER_HUMAN_ACK=1` the script exits 2 even if Alertmanager
accepted the alert. A bot cannot acknowledge a pager.

Overlay: `ops/observability/docker-compose.pager.yml` replaces the null
receivers with `alertmanager.pager.yml` (`url_file` from the secret).
Do not put the webhook URL in compose, git, or this file.

### Evidence log

| Date | Destination (pager/slack, no URL) | Human who got the page | Result |
|---|---|---|---|
| — | — | — | **Never paged a human.** |

## Run it

```bash
docker compose -f docker-compose.yml -f docker-compose.obs.yml up -d
# Grafana http://localhost:3001 · Prometheus :9090 · Alertmanager :9093
```

## Alert rules

Every rule is bound to a metric the application actually exports
(`backend/app/core/metrics.py`). No rule references an invented metric.

| Alert | Severity | Condition |
|---|---|---|
| `BackendTargetDown` | critical | `up{job="fitness-os-backend"} == 0` for 2m |
| `DependencyDown` | critical | `fitness_network_os_dependency_up == 0` for 2m |
| `HighServerErrorRate` | critical | 5xx ratio > 5% for 5m |
| `HighRequestLatencyP95` | warning | route p95 > 1s for 10m |
| `AuthBruteForceSurge` | warning | login 429 rate > 1/s for 10m |
| `OutboxDispatchFailing` | critical | failed dispatch rate > 0 for 10m |
| `OutboxFailureRatioHigh` | warning | failure ratio > 10% for 15m |

## Executed evidence (2026-08-16)

Scrape targets, live from `/api/v1/targets`:

```
fitness-os-backend  http://fitness-os-backend:8000/metrics -> up
prometheus          http://localhost:9090/metrics          -> up
```

Live PromQL against the running stack:

```
up{job="fitness-os-backend"}                    = 1
fitness_network_os_dependency_up{postgresql}    = 1
fitness_network_os_dependency_up{redis}         = 1
```

Grafana provisioning verified through its API: datasource `Prometheus`
(default) and dashboard `fitness-os-overview` in folder "Fitness Network OS".

### Alert-path drill — `ops/observability/alert_fire_drill.sh`

The backend was stopped to induce a real scrape failure:

```
13:29:14  baseline rule state: inactive
13:29:35  rule state: pending
13:31:36  rule state: firing
13:31:36  PASS: BackendTargetDown is firing
13:31:36  PASS: BackendTargetDown present in Alertmanager
13:32:07  PASS: BackendTargetDown resolved after restore
```

The full path — scrape failure → rule evaluation → `for` duration → firing →
Alertmanager delivery → resolution — is proven, not assumed.

## What this does NOT close

- **Receivers are null by design.** Alerts fire, group and appear in the
  Alertmanager UI, but nothing is paged. Wire a real webhook (from a secret,
  via `url_file`) before relying on this in production.
- **No distributed tracing.** No OpenTelemetry spans are emitted; only metrics.
- **Local only.** This was executed against the dev compose stack, not a
  production deployment. In production `/metrics` requires `METRICS_BEARER_TOKEN`
  and the `authorization` block in `prometheus.yml` must be uncommented with the
  token mounted at `/etc/prometheus/metrics_token`.
- **No retention/HA story.** Single Prometheus, 15d local TSDB retention.
