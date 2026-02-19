"""
Prometheus metrics middleware and instrumentation.

Exposes /metrics endpoint for Prometheus scraping with:
- search_latency_histogram: Histogram of search endpoint latency
- search_requests_total: Counter of total search requests
- cache_hit_total / cache_miss_total: Counters for embedding cache performance
- active_searches: Gauge of currently in-flight searches
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# Metrics
search_latency_histogram = Histogram(
    "search_latency_seconds",
    "Search endpoint latency in seconds",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
)

search_requests_total = Counter(
    "search_requests_total",
    "Total number of search requests",
    ["endpoint", "status"],
)

cache_hit_total = Counter(
    "cache_hit_total",
    "Total embedding cache hits",
)

cache_miss_total = Counter(
    "cache_miss_total",
    "Total embedding cache misses",
)

active_searches = Gauge(
    "active_searches",
    "Number of currently active search requests",
)

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP request metrics."""

    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path

        # Track active searches
        is_search = "/search/" in path
        if is_search:
            active_searches.inc()

        start_time = time.time()
        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Record metrics
            status = str(response.status_code)
            http_requests_total.labels(method=method, path=path, status=status).inc()
            http_request_duration_seconds.labels(method=method, path=path).observe(duration)

            if is_search:
                search_latency_histogram.observe(duration)
                search_requests_total.labels(endpoint=path, status=status).inc()

            return response
        finally:
            if is_search:
                active_searches.dec()


async def metrics_endpoint(request: Request) -> Response:
    """Expose Prometheus metrics at /metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
