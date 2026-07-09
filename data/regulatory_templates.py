"""Regulatory document templates for industrial compliance.

Generates reference documents for OISD, DGMS, and Factory Act standards.
These are synthetic but realistic regulatory document templates.
"""

from pathlib import Path
from loguru import logger


# --- OISD Standards Templates ---

OISD_DOCUMENTS = [
    {
        "doc_id": "OISD-116",
        "title": "OISD-116: Safety Guidelines for Petroleum Refineries",
        "content": """
OISD-116 SAFETY GUIDELINES FOR PETROLEUM REFINERIES

Section 1: Scope and Applicability
This standard applies to all petroleum refinery operations, including crude oil
distillation, catalytic cracking, hydroprocessing, and product finishing units.
Compliance is mandatory for all refineries under the Ministry of Petroleum.

Section 2: Equipment Inspection Requirements
2.1 Pressure vessels, including storage tanks TNK-T01 through TNK-T03, must
undergo annual internal inspection per OISD-116 guidelines.
2.2 Heat exchangers HX-D01 and HX-D02 require semi-annual tube inspection
and leak testing.
2.3 All pumps (PUMP-A01, PUMP-A02, PUMP-B01) must be monitored monthly for
vibration, temperature, and seal integrity.
2.4 Compressors COMP-C01 and COMP-C02 require weekly safety valve checks
and quarterly bearing inspection.

Section 3: Permit Requirements
3.1 Hot work permits are mandatory for any work involving open flames, sparks,
or temperatures exceeding 30°C above ambient in hazardous areas.
3.2 Confined space entry permits must be issued before entering any vessel,
tank, or enclosed space.
3.3 Line breaking permits are required for opening any pressurized piping system.

Section 4: Emergency Response
4.1 Each plant must maintain a minimum of 2 emergency response teams per shift.
4.2 Fire fighting equipment must be inspected monthly per OISD-116 standards.
4.3 Emergency shutdown procedures must be posted at all control rooms.
""",
    },
    {
        "doc_id": "OISD-117",
        "title": "OISD-117: Storage Tank Integrity Management",
        "content": """
OISD-117 STORAGE TANK INTEGRITY MANAGEMENT

Section 1: Tank Classification
1.1 Tanks TNK-T01 and TNK-T02 are classified as Group A (hazardous materials).
1.2 Tank TNK-T03 is classified as Group B (flammable liquids).
1.3 Classification determines inspection frequency and maintenance protocols.

Section 2: Inspection Schedule
2.1 Group A tanks: Annual internal inspection, biennial external inspection.
2.2 Group B tanks: Biennial internal inspection, annual external inspection.
2.3 All tanks require visual inspection of foundations quarterly.
2.4 Tank bottoms must be scanned using ultrasonic testing every 5 years.

Section 3: Maintenance Requirements
3.1 Corrosion monitoring coupons must be installed in all tanks storing
corrosive materials.
3.2 Cathodic protection systems must be tested annually.
3.3 Tank shell thickness measurements must be taken during every internal
inspection.
""",
    },
    {
        "doc_id": "OISD-118",
        "title": "OISD-118: Process Safety Management",
        "content": """
OISD-118 PROCESS SAFETY MANAGEMENT

Section 1: Process Safety Information
1.1 All process equipment must have complete technical specifications documented.
1.2 Equipment tags EQ-1001 through EQ-4002 must be registered in the
Process Safety Information database.
1.3 Chemical inventory and hazard data must be maintained for all process
units.

Section 2: Process Hazard Analysis
2.1 HAZOP studies must be conducted for all new installations and
modifications to existing units.
2.2 Revalidation of HAZOP studies must occur every 5 years.
2.3 Action items from PHA studies must be tracked to completion.

Section 3: Operating Procedures
3.1 Written operating procedures must be available for all process units.
3.2 Deviation procedures must be documented and approved.
3.3 Operators must be trained on emergency shutdown procedures.
""",
    },
    {
        "doc_id": "OISD-119",
        "title": "OISD-119: Inspection and Maintenance of Piping Systems",
        "content": """
OISD-119 INSPECTION AND MAINTENANCE OF PIPING SYSTEMS

Section 1: Piping Classification
1.1 High-pressure piping (>15 bar) requires annual thickness measurement.
1.2 Medium-pressure piping (5-15 bar) requires biennial inspection.
1.3 Low-pressure piping (<5 bar) requires triennial inspection.

Section 2: Corrosion Management
2.1 Corrosion rates must be calculated and documented for all piping systems.
2.2 Remaining life calculations must be updated at each inspection.
2.3 Replacement must be planned when remaining life falls below 5 years.

Section 3: Documentation Requirements
3.1 All inspection results must be recorded in the piping database.
3.2 Repair and replacement records must be maintained for each pipe segment.
3.3 Inspection reports must be reviewed by a qualified inspector.
""",
    },
    {
        "doc_id": "OISD-130",
        "title": "OISD-130: Safety in Electrical Systems",
        "content": """
OISD-130 SAFETY IN ELECTRICAL SYSTEMS

Section 1: Electrical Safety Standards
1.1 All electrical equipment in hazardous areas must be certified for the
appropriate zone classification.
1.2 Electrical isolation procedures must be followed before any maintenance
work on electrical equipment.
1.3 Lockout/tagout procedures must be implemented per OISD-130 guidelines.

Section 2: Electrical Inspection
2.1 Transformer oil testing must be conducted quarterly.
2.2 Switchgear must be inspected annually for signs of wear or damage.
2.3 Grounding systems must be tested annually for compliance.
2.4 Circuit breakers must be tested for proper operation every 6 months.

Section 3: Emergency Procedures
3.1 Emergency shutdown procedures for electrical systems must be documented.
3.2 Arc flash analysis must be conducted for all switchgear and panel boards.
3.3 Personal protective equipment requirements must be posted at all
electrical work areas.
""",
    },
]


# --- DGMS Circulars ---

DGMS_DOCUMENTS = [
    {
        "doc_id": "DGMS-2023-01",
        "title": "DGMS Circular 2023-01: Safety in Mining Operations",
        "content": """
DGMS CIRCULAR 2023-01: SAFETY IN MINING OPERATIONS

Subject: Mandatory safety equipment and procedures in mining operations.

1. Personal Protective Equipment (PPE)
1.1 All workers entering mining areas must wear mandatory PPE including
hard hats, safety boots, high-visibility vests, and safety glasses.
1.2 Respiratory protection must be provided for workers in dusty environments.
1.3 Hearing protection must be mandatory in areas exceeding 85 dB.

2. Equipment Safety
2.1 All underground equipment must undergo safety inspection before each shift.
2.2 Emergency communication systems must be installed at 100m intervals.
2.3 Gas monitoring equipment must be checked daily for calibration.

3. Training Requirements
3.1 All new workers must complete 40 hours of safety induction training.
3.2 Refresher training must be conducted every 6 months.
3.3 Emergency response drills must be conducted monthly.
""",
    },
    {
        "doc_id": "DGMS-2022-05",
        "title": "DGMS Circular 2022-05: Ventilation Requirements",
        "content": """
DGMS CIRCULAR 2022-05: VENTILATION REQUIREMENTS IN UNDERGROUND MINES

Subject: Minimum ventilation standards for underground mining operations.

1. General Requirements
1.1 Fresh air supply must be maintained at a minimum of 0.1 m³/s per worker.
1.2 Air quality must be monitored continuously for methane and carbon monoxide.
1.3 Ventilation systems must have backup power supply.

2. Monitoring Requirements
2.1 Gas monitoring must be conducted at the working face every 2 hours.
2.2 Ventilation surveys must be completed weekly.
2.3 Records must be maintained for all monitoring activities.
""",
    },
    {
        "doc_id": "DGMS-TC-15",
        "title": "DGMS Technical Circular 15: Ground Control Management",
        "content": """
DGMS TECHNICAL CIRCULAR 15: GROUND CONTROL MANAGEMENT

Subject: Roof support and ground control in underground mines.

1. Roof Support Design
1.1 Ground conditions must be assessed before establishing support design.
1.2 Support systems must be designed for worst-case geological conditions.
1.3 Changes in ground conditions require reassessment of support adequacy.

2. Inspection Requirements
2.1 Daily visual inspection of roof conditions is mandatory.
2.2 Instrumentation monitoring must be conducted weekly.
2.3 Any signs of instability must be reported immediately.
""",
    },
]


# --- Factory Act Sections ---

FACTORY_ACT_DOCUMENTS = [
    {
        "doc_id": "FA-SEC-7A",
        "title": "Factory Act Section 7A: Safety Officers",
        "content": """
FACTORY ACT - SECTION 7A: APPOINTMENT OF SAFETY OFFICERS

1. Every factory having 1000 or more workers must employ a qualified
safety officer.
2. The safety officer must hold a degree or diploma in industrial safety.
3. The safety officer's duties include:
   a) Advising on prevention of accidents and occupational diseases.
   b) Investigating accidents and near-miss incidents.
   c) Conducting safety audits and inspections.
   d) Organizing safety training programs.
4. The safety officer must report directly to the occupier of the factory.
""",
    },
    {
        "doc_id": "FA-SEC-36",
        "title": "Factory Act Section 36: Fire Precautions",
        "content": """
FACTORY ACT - SECTION 36: PRECAUTIONS AGAINST FIRE

1. Every factory must take adequate precautions against fire.
2. Fire extinguishers must be provided and maintained in efficient condition.
3. At least two exits must be provided for every enclosed workspace.
4. Fire escapes must be provided in every factory with more than 10 workers
above ground level.
5. All exits must be clearly marked and well illuminated.
6. Fire drills must be conducted at least once every quarter.
""",
    },
    {
        "doc_id": "FA-SEC-38",
        "title": "Factory Act Section 38: Fencing of Machinery",
        "content": """
FACTORY ACT - SECTION 38: FENCING OF MACHINERY

1. Every dangerous part of any machinery must be securely fenced.
2. The following must be fenced:
   a) All moving parts including flywheels, gears, and pulleys.
   b) Parts in motion when the machinery is running.
   c) Fixed parts which may move to create a danger.
3. Guards must not be removed for maintenance without proper isolation.
4. Fencing must comply with approved standards.
""",
    },
    {
        "doc_id": "FA-SEC-40A",
        "title": "Factory Act Section 40A: Accident Reporting",
        "content": """
FACTORY ACT - SECTION 40A: ACCIDENT REPORTING AND INVESTIGATION

1. All accidents resulting in death or serious injury must be reported
to the factory inspector within 12 hours.
2. The investigation must establish root cause and contributing factors.
3. Corrective actions must be implemented and documented.
4. An accident register must be maintained at the factory.
5. Annual accident statistics must be submitted to the Chief Inspector.
""",
    },
    {
        "doc_id": "FA-SEC-41B",
        "title": "Factory Act Section 41B: Hazardous Processes",
        "content": """
FACTORY ACT - SECTION 41B: SAFETY MEASURES FOR HAZARDOUS PROCESSES

1. Factories must provide the following for hazardous processes:
   a) Adequate and suitable PPE for all workers.
   b) Medical examination of workers before and during employment.
   c) Safety showers and eye wash stations.
2. Workers must be trained on hazardous material handling.
3. Emergency plans must be developed and tested.
4. Exposure monitoring must be conducted regularly.
""",
    },
    {
        "doc_id": "FA-SEC-41C",
        "title": "Factory Act Section 41C: Right to Workers",
        "content": """
FACTORY ACT - SECTION 41C: RIGHTS OF WORKERS

1. Workers have the right to:
   a) Be informed about hazards at their workplace.
   b) Receive training on safety procedures.
   c) Report unsafe conditions without fear of retaliation.
   d) Refuse to work in immediate danger to life or health.
2. Workers may form safety committees with employer participation.
3. Safety committee meetings must be held at least quarterly.
""",
    },
]


def generate_regulatory_documents():
    """Write all regulatory documents to the corpus/real directory."""
    output_dir = Path(__file__).parent / "corpus" / "real"
    output_dir.mkdir(parents=True, exist_ok=True)

    all_docs = OISD_DOCUMENTS + DGMS_DOCUMENTS + FACTORY_ACT_DOCUMENTS

    for doc in all_docs:
        filepath = output_dir / f"{doc['doc_id']}.txt"
        content = f"{doc['title']}\n{'=' * len(doc['title'])}\n{doc['content']}"
        filepath.write_text(content.strip(), encoding="utf-8")
        logger.info(f"Wrote regulatory document: {filepath.name}")

    logger.info(f"Generated {len(all_docs)} regulatory documents in {output_dir}")
    return len(all_docs)


if __name__ == "__main__":
    count = generate_regulatory_documents()
    print(f"Generated {count} regulatory document templates.")
