"""
Gunicorn configuration for production deployment.

Uses Uvicorn workers for async support with multiple processes.
"""

import multiprocessing

# Server socket
bind = "0.0.0.0:8000"

# Worker processes
workers = min(multiprocessing.cpu_count() * 2, 12)
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
