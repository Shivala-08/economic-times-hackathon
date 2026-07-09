"""Faker-based synthetic data generator for industrial documents.

Generates realistic work orders, permits, and inspection logs as CSV files.
"""

import csv
import random
from pathlib import Path
from datetime import datetime, timedelta

from faker import Faker
from loguru import logger

fake = Faker()
Faker.seed(42)
random.seed(42)

# Domain-specific constants
EQUIPMENT_TAGS = [
    "EQ-1001", "EQ-1002", "EQ-2001", "EQ-2002", "EQ-2003",
    "EQ-3001", "EQ-3002", "EQ-3003", "EQ-4001", "EQ-4002",
    "PUMP-A01", "PUMP-A02", "PUMP-B01", "COMP-C01", "COMP-C02",
    "HX-D01", "HX-D02", "VAN-V01", "VAN-V02", "VAL-V03",
    "TNK-T01", "TNK-T02", "TNK-T03", "FIL-F01", "MTR-M01",
]

DEPARTMENTS = ["Maintenance", "Operations", "Engineering", "Safety", "Quality"]
PLANTS = ["Refinery Unit A", "Power Plant B", "Chemical Plant C", "Steel Mill D"]
SHIFT_TYPES = ["Day Shift", "Night Shift", "Swing Shift"]
PRIORITIES = ["Critical", "High", "Medium", "Low"]
PERMIT_TYPES = ["Hot Work", "Confined Space Entry", "Work at Height", "Electrical Isolation", "Line Breaking", "Excavation"]
SAFETY_HAZARDS = ["Fire hazard", "Confined space", "Working at height", "Electrical", "Chemical exposure", "Noise", "Falling objects"]
INCIDENT_TYPES = ["Near Miss", "First Aid", "Recordable", "Lost Time"]
OISD_SECTIONS = ["OISD-116", "OISD-117", "OISD-118", "OISD-119", "OISD-130"]
DGMS_REFS = ["DGMS Circular 2023-01", "DGMS Circular 2022-05", "DGMS Technical Circular 15"]
FACTORY_ACT_SECTIONS = ["Section 7A", "Section 36", "Section 38", "Section 40A", "Section 41B", "Section 41C"]


def generate_work_orders(n: int = 50) -> list[dict]:
    """Generate synthetic work orders."""
    work_orders = []
    for i in range(n):
        start_date = fake.date_between(start_date="-90d", end_date="today")
        due_date = start_date + timedelta(days=random.randint(1, 14))
        status = random.choice(["Open", "In Progress", "Completed", "On Hold"])
        work_orders.append({
            "work_order_id": f"WO-{2026}-{1000 + i:04d}",
            "title": fake.sentence(nb_words=6),
            "description": fake.paragraph(nb_sentences=3),
            "equipment_tag": random.choice(EQUIPMENT_TAGS),
            "plant": random.choice(PLANTS),
            "department": random.choice(DEPARTMENTS),
            "priority": random.choice(PRIORITIES),
            "status": status,
            "assigned_to": fake.name(),
            "requested_by": fake.name(),
            "start_date": start_date.isoformat(),
            "due_date": due_date.isoformat(),
            "completion_date": due_date.isoformat() if status == "Completed" else "",
            "estimated_hours": random.randint(1, 40),
            "actual_hours": random.randint(1, 50) if status == "Completed" else "",
            "safety_hazard": random.choice(SAFETY_HAZARDS),
            "regulation_ref": random.choice(OISD_SECTIONS),
        })
    return work_orders


def generate_permits(n: int = 30) -> list[dict]:
    """Generate synthetic work permits."""
    permits = []
    for i in range(n):
        issue_date = fake.date_between(start_date="-60d", end_date="today")
        expiry_date = issue_date + timedelta(days=random.randint(1, 30))
        permits.append({
            "permit_id": f"PRM-{2026}-{5000 + i:04d}",
            "permit_type": random.choice(PERMIT_TYPES),
            "work_description": fake.sentence(nb_words=8),
            "location": fake.address(),
            "plant": random.choice(PLANTS),
            "equipment_tag": random.choice(EQUIPMENT_TAGS),
            "issued_to": fake.name(),
            "issued_by": fake.name(),
            "issue_date": issue_date.isoformat(),
            "expiry_date": expiry_date.isoformat(),
            "status": random.choice(["Active", "Expired", "Cancelled", "Closed"]),
            "safety_measures": "; ".join(random.sample(SAFETY_HAZARDS, k=2)),
            "regulation_ref": random.choice(OISD_SECTIONS),
        })
    return permits


def generate_inspection_logs(n: int = 40) -> list[dict]:
    """Generate synthetic inspection logs."""
    inspections = []
    for i in range(n):
        insp_date = fake.date_between(start_date="-90d", end_date="today")
        finding_count = random.randint(0, 5)
        inspections.append({
            "inspection_id": f"INS-{2026}-{8000 + i:04d}",
            "inspection_type": random.choice(["Routine", "Pre-Startup", "Post-Maintenance", "Emergency", "Regulatory"]),
            "plant": random.choice(PLANTS),
            "equipment_tag": random.choice(EQUIPMENT_TAGS),
            "inspector": fake.name(),
            "inspection_date": insp_date.isoformat(),
            "shift": random.choice(SHIFT_TYPES),
            "findings": fake.paragraph(nb_sentences=finding_count + 1),
            "findings_count": finding_count,
            "severity": random.choice(["None", "Minor", "Major", "Critical"]),
            "corrective_action_required": random.choice([True, False]),
            "regulation_ref": random.choice(OISD_SECTIONS + DGMS_REFS),
        })
    return inspections


def generate_incident_reports(n: int = 20) -> list[dict]:
    """Generate synthetic incident reports."""
    incidents = []
    for i in range(n):
        incidents.append({
            "incident_id": f"INC-{2026}-{9000 + i:04d}",
            "incident_type": random.choice(INCIDENT_TYPES),
            "date": fake.date_between(start_date="-180d", end_date="today").isoformat(),
            "time": f"{random.randint(0,23):02d}:{random.randint(0,59):02d}",
            "plant": random.choice(PLANTS),
            "location": fake.address(),
            "equipment_tag": random.choice(EQUIPMENT_TAGS),
            "description": fake.paragraph(nb_sentences=4),
            "root_cause": fake.sentence(nb_words=10),
            "injury_severity": random.choice(["None", "First Aid", "Medical Treatment", "Lost Time"]),
            "worker_name": fake.name(),
            "department": random.choice(DEPARTMENTS),
            "corrective_actions": fake.paragraph(nb_sentences=2),
            "regulation_ref": random.choice(OISD_SECTIONS + DGMS_REFS + FACTORY_ACT_SECTIONS),
            "status": random.choice(["Open", "Closed", "Under Investigation"]),
        })
    return incidents


def write_csv(data: list[dict], filepath: Path):
    """Write a list of dicts to CSV."""
    if not data:
        return
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    logger.info(f"Wrote {len(data)} records to {filepath}")


def generate_all():
    """Generate all synthetic data and save to CSV files."""
    output_dir = Path(__file__).parent / "corpus" / "synthetic"

    work_orders = generate_work_orders(50)
    write_csv(work_orders, output_dir / "work_orders.csv")

    permits = generate_permits(30)
    write_csv(permits, output_dir / "permits.csv")

    inspections = generate_inspection_logs(40)
    write_csv(inspections, output_dir / "inspection_logs.csv")

    incidents = generate_incident_reports(20)
    write_csv(incidents, output_dir / "incident_reports.csv")

    total = len(work_orders) + len(permits) + len(inspections) + len(incidents)
    logger.info(f"Generated {total} total synthetic records")
    return total


if __name__ == "__main__":
    generate_all()
