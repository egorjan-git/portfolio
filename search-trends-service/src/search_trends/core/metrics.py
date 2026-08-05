from prometheus_client import Counter, Gauge, Histogram

EVENTS_TOTAL = Counter(
    "search_events_total",
    "Search events processed by outcome",
    labelnames=("outcome",),
)
CONSUMER_LAG = Gauge(
    "search_consumer_lag",
    "Kafka consumer lag by topic partition",
    labelnames=("topic", "partition"),
)
TOP_REQUEST_SECONDS = Histogram(
    "search_top_request_seconds",
    "Time spent building or reading the search top",
)
TOP_RESULT_SIZE = Histogram(
    "search_top_result_size",
    "Number of items returned by top requests",
    buckets=(0, 1, 5, 10, 20, 50, 100),
)
