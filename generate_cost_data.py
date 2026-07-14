"""
Synthetic AWS cost data generator.

Since LocalStack can't return real Cost Explorer usage data, this script
simulates realistic daily spend per service, with normal day-to-day
fluctuation and occasional injected spikes (anomalies). The output feeds
the same pipeline that a real Cost Explorer API call would later feed.
"""

import random
import csv
from datetime import date, timedelta

SERVICES = ["EC2", "S3", "RDS", "Lambda", "CloudWatch"]

BASE_DAILY_COST = {
    "EC2": 40.0,
    "S3": 5.0,
    "RDS": 25.0,
    "Lambda": 2.0,
    "CloudWatch": 1.5,
}

NUM_DAYS = 30
ANOMALY_CHANCE = 0.08
ANOMALY_MULTIPLIER_RANGE = (2.5, 5.0)

def generate_row(day, service):
    base = BASE_DAILY_COST[service]
    fluctuation = random.uniform(0.85, 1.15)
    cost = base * fluctuation

    is_anomaly = random.random() < ANOMALY_CHANCE
    if is_anomaly:
        cost *= random.uniform(*ANOMALY_MULTIPLIER_RANGE)

    return {
        "date": day.isoformat(),
        "service": service,
        "cost_usd": round(cost, 2),
        "is_injected_anomaly": is_anomaly,
    }

def main():
    start_day = date.today() - timedelta(days=NUM_DAYS)
    rows = []

    for i in range(NUM_DAYS):
        current_day = start_day + timedelta(days=i)
        for service in SERVICES:
            rows.append(generate_row(current_day, service))

    with open("synthetic_costs.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "service", "cost_usd", "is_injected_anomaly"])
        writer.writeheader()
        writer.writerows(rows)

    anomaly_count = sum(1 for r in rows if r["is_injected_anomaly"])
    print(f"Generated {len(rows)} rows across {NUM_DAYS} days for {len(SERVICES)} services.")
    print(f"Injected {anomaly_count} anomalies for later detection testing.")
    print("Saved to synthetic_costs.csv")

if __name__ == "__main__":
    main()