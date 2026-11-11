"""AP5: connection pool starvation load test.

    uv run locust --headless -u 50 -r 10 -t 30s \\
        --host http://localhost:8000 \\
        --csv benchmarks/ap5-pool/locust-bad \\
        -f scripts/ap5_locustfile.py

Run once against the app started with POOL_MODE=bad, then again against
POOL_MODE=good, and compare the two --csv outputs.
"""

from locust import HttpUser, between, task


class OrdersApiUser(HttpUser):
    wait_time = between(0, 0.1)

    @task
    def slow_query(self):
        self.client.get("/demo/ap5/query")
