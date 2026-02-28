from prometheus_client import Counter, Gauge, Histogram

# --- COUNTERS ---
# Counters only go UP. Perfect for counting events over time.
# In Grafana you use rate() to get "per minute" values.

incidents_created_total = Counter(
    name="incidents_created_total",
    documentation="Total number of incidents created",
    labelnames=["severity", "source"]  # allows filtering by severity/source in Grafana
)

incidents_resolved_total = Counter(
    name="incidents_resolved_total",
    documentation="Total number of incidents resolved",
    labelnames=["severity"]
)

alertmanager_webhooks_total = Counter(
    name="alertmanager_webhooks_total",
    documentation="Total number of webhooks received from Alertmanager",
    labelnames=["status"]  # firing or resolved
)


# --- GAUGES ---
# Gauges go UP and DOWN. Perfect for current state.

incidents_open_gauge = Gauge(
    name="incidents_open_total",
    documentation="Current number of open incidents",
    labelnames=["severity"]
)


# --- HISTOGRAMS ---
# Histograms track distributions. Perfect for measuring time durations.
# This is how you calculate MTTR (Mean Time To Resolve).

incident_resolution_duration = Histogram(
    name="incident_resolution_duration_seconds",
    documentation="Time taken to resolve an incident in seconds",
    labelnames=["severity"],
    # Buckets: 5min, 15min, 30min, 1hr, 2hr, 4hr, 8hr, 24hr
    buckets=[300, 900, 1800, 3600, 7200, 14400, 28800, 86400]
)