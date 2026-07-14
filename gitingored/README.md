# Cost Monitor — AWS Cost & Resource Anomaly Monitor

A Django-based monitoring dashboard that tracks cloud spend, flags unusual cost spikes using a rolling-average anomaly detector, and sends automated email alerts — inspired by real FinOps tooling used to catch cloud overspend before it becomes a surprise bill.

![Dashboard screenshot](./screenshots/dashboard-overview.png)

## The problem this solves

Cloud bills are easy to lose track of. A misconfigured resource, a forgotten instance, or a runaway process can quietly rack up cost for days before anyone notices. This project simulates a lightweight cost-monitoring tool that checks daily spend per service, compares it against a rolling baseline, and proactively alerts when something looks abnormal — rather than waiting for a monthly invoice to reveal the damage.

## Features

- **Dashboard** — spend-by-service breakdown (doughnut chart) and a 30-day daily spend trend line, built with Chart.js
- **Anomaly detection** — rule-based rolling-average detector: flags any day where a service's cost exceeds 1.5x its trailing 7-day average
- **Email alerts** — automatically emails a summary whenever anomalies are detected, listing the specific service/date/cost
- **Automated scheduling** — runs daily without manual intervention (Windows Task Scheduler locally; `django-crontab` config included for Linux deployment)
- **Admin panel** — Django admin for browsing raw cost records

## Screenshots

| Dashboard overview | Anomaly panel |
|---|---|
| ![overview](./screenshots/dashboard-overview.png) | ![anomalies](./screenshots/anomaly-panel.png) |

## Tech stack

- **Backend:** Django 5.2, Python 3.10
- **Database:** SQLite (dev)
- **AWS interaction:** `boto3` + `moto` (mocked AWS services — see note below)
- **Frontend:** Chart.js, vanilla HTML/CSS/JS (Django templates)
- **Email:** Django's SMTP backend via Gmail app password
- **Scheduling:** Windows Task Scheduler (dev) / `django-crontab` (prod-ready config included)

## Architecture decisions (and honest trade-offs)

**Why Moto instead of LocalStack.** LocalStack was the original plan for emulating AWS locally. During development, a Docker/WSL2 networking conflict on the dev machine consistently blocked outbound HTTPS to LocalStack's licensing server (`api.localstack.cloud`), even after DNS and firewall fixes. Rather than lose more time on infrastructure plumbing unrelated to the actual project, the AWS interaction layer was switched to `moto`, a pure-Python AWS mocking library with no external service dependency. This kept development unblocked without touching real AWS billing.

**Why synthetic cost data instead of live Cost Explorer.** Real AWS Cost Explorer data requires a funded AWS account and doesn't exist in a locally mocked environment. A synthetic data generator (`generate_cost_data.py`) produces realistic daily costs per service with injected anomalies, so the detection and alerting logic could be built and tested against known ground truth. The architecture is designed so swapping in a real Cost Explorer API call later requires no changes to the database, dashboard, detection, or alerting layers.

**Why Windows Task Scheduler instead of cron.** `django-crontab` depends on the Unix `fcntl` module, which doesn't exist on Windows. Rather than fight the platform, scheduling was implemented via a `.bat` script triggered by Windows Task Scheduler for local development. The `django-crontab` configuration remains in `settings.py` for when this is deployed to a Linux host, where it will work natively.

## Anomaly detection logic

For each service, the detector looks at the average cost over the preceding 7 days. If a given day's cost exceeds 1.5x that rolling average, it's flagged. Days without enough prior history (fewer than 3 preceding records) are skipped rather than judged unfairly. This is deliberately a transparent, explainable rule rather than a black-box model — appropriate for a first version, and easy to tune via command-line flags:

```bash
python manage.py detect_anomalies --window 10 --threshold 2.0 --dry-run
```

## Project structure

```
cost-monitor/
├── costmonitor/          # Django project settings
├── monitor/               # Main app
│   ├── models.py          # CostSnapshot model
│   ├── views.py            # Dashboard view
│   ├── management/commands/
│   │   ├── load_costs.py       # CSV -> database loader
│   │   └── detect_anomalies.py # Rolling-average anomaly detector + email alerts
│   └── templates/monitor/dashboard.html
├── generate_cost_data.py  # Synthetic cost data generator
├── run_detection.bat      # Windows Task Scheduler entry point
└── synthetic_costs.csv    # Generated sample data
```

## Running it locally

```bash
# clone and enter the project
git clone https://github.com/YOUR_USERNAME/cost-monitor.git
cd cost-monitor

# set up virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # macOS/Linux

# install dependencies
pip install -r requirements.txt

# create your .env file (see .env.example)

# generate sample data and set up the database
python generate_cost_data.py
python manage.py migrate
python manage.py load_costs
python manage.py detect_anomalies

# run the server
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` for the dashboard.

## What I'd build next

- Swap synthetic data for real AWS Cost Explorer once deployed with a funded account
- Move from a rolling-average rule to a statistical baseline (mean + standard deviation) for more nuanced detection
- Deploy to Render/Railway with hosted Postgres for a live, publicly viewable instance

## Author

Built by Rajamanikandan -- Information Technology student, exploring cloud/data engineering.
