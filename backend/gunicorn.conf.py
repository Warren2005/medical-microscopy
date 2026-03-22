"""
Gunicorn configuration for production deployment.

Uses Uvicorn workers for async support with multiple processes.
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"

# Worker processes — default to 2 in Docker to avoid OOM from CLIP model copies.
# Set GUNICORN_WORKERS env var to override.
workers = int(os.environ.get("GUNICORN_WORKERS", min(multiprocessing.cpu_count(), 2)))
worker_class = "uvicorn.workers.UvicornWorker"

# Timeouts
timeout = 120  # CLIP inference can take a few seconds
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "medical-microscopy"

# Preload app for shared memory (CLIP model loaded once)
preload_app = True
