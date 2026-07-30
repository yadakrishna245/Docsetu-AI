# Load Testing - DocSetu AI

Load tests using [Locust](https://locust.io/) to simulate realistic user traffic against the DocSetu AI backend.

## Setup

```bash
pip install -r tests/load/requirements.txt
```

## Run Locally (Web UI)

```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089 in your browser to configure and start the test.

## Run Headless (CI/CD)

```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
  --headless -u 100 -r 10 --run-time 5m
```

### Parameters

| Flag | Description |
|------|-------------|
| `-u 100` | 100 concurrent users |
| `-r 10` | Spawn 10 users per second |
| `--run-time 5m` | Run for 5 minutes |
| `--csv=results` | Export results to CSV |
| `--html=report.html` | Generate HTML report |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TARGET_HOST` | `http://localhost:8000` | Target server URL |

## Performance Targets

| Metric | Target |
|--------|--------|
| Concurrent users | 100 |
| p95 latency (non-LLM endpoints) | < 500ms |
| Error rate | < 1% |
| Daily document capacity | 3,000 docs/day (simulated) |

## Test Scenarios

The load test simulates users performing weighted actions:

| Task | Weight | Description |
|------|--------|-------------|
| List documents | 5 | Most common - fetching document list |
| Health check | 3 | Lightweight availability probe |
| Compliance rules | 3 | Fetching compliance rule sets |
| Upload document | 2 | Uploading a small test PDF |
| View profile | 1 | Viewing user profile |

Each simulated user registers, logs in, then performs tasks with 1-5 second waits between actions.

## Generating Reports

```bash
# CSV output
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
  --headless -u 100 -r 10 --run-time 5m --csv=results

# HTML report
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
  --headless -u 100 -r 10 --run-time 5m --html=report.html
```

## Distributed Mode

For higher load, run Locust in distributed mode:

```bash
# Master
locust -f tests/load/locustfile.py --master

# Workers (run on multiple machines)
locust -f tests/load/locustfile.py --worker --master-host=<MASTER_IP>
```
