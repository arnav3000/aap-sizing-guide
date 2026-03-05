# Ansible Automation Platform 2.4 to 2.6 Sizing Calculator

A comprehensive sizing calculator that helps you plan your migration from **Ansible Automation Platform 2.4** (running on RHEL-8 VMs) to **AAP 2.6** (running as containers) using **official Red Hat Excel reference formulas**.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage Methods](#usage-methods)
- [Official Red Hat Formulas](#official-red-hat-formulas)
- [Required Input Parameters](#required-input-parameters)
- [Example Calculation](#example-calculation)
- [Understanding Your Results](#understanding-your-results)
- [API Documentation](#api-documentation)
- [Important Notes](#important-notes)
- [References](#references)

---

## Overview

This tool calculates the recommended container resources for AAP 2.6 based on your current AAP 2.4 VM utilization metrics. It uses **official Red Hat capacity planning formulas** from the Excel reference sheet (AAp-sizing-sheet-reference.xlsx).

### What It Does

- ✅ Analyzes your current AAP 2.4 resource utilization
- ✅ Calculates execution capacity using time-based concurrency
- ✅ Sizes control plane using AVERAGED event + job management formulas
- ✅ Provides accurate database storage requirements
- ✅ Recommends topology (Growth vs Enterprise)
- ✅ Shows all formulas and calculation breakdowns

### Formula Source

All calculations are based on:
- **Red Hat AAP Excel Reference Sheet** (`docs/AAp-sizing-sheet-reference.xlsx`)
- **48 benchmarked parameters** from Red Hat engineering tests
- **Field-tested formulas** from production deployments
- **AWX/Controller configuration parameters** (SYSTEM_TASK_FORKS_MEM, etc.)

**NOT based on estimates or assumptions** - these are official Red Hat formulas.

---

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux

# Install requirements
pip install -r requirements.txt
```

### 2. Run the Web Application

```bash
# Start the web server
python app.py

# Or use the convenience script
./run.sh
```

### 3. Open in Browser

Navigate to: **http://localhost:5001**

### 4. Use the Calculator

1. Click **"Load Example Data"** to see a pre-populated scenario
2. Or enter your own AAP 2.4 metrics
3. Click **"Calculate Sizing"** to get recommendations

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Web browser (for web interface)

### Step-by-Step Installation

```bash
# 1. Clone or download this repository
cd aap-sizing-guide

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Verify installation
python sizing_calculator.py
```

---

## Usage Methods

### Method 1: Web Interface (Recommended)

```bash
# Start the web server
python app.py

# Open in browser
open http://localhost:5001
```

**Features:**
- Interactive form for entering metrics
- Visual results with component breakdown
- Load example data with one click
- Shows calculation formulas and breakdowns

### Method 2: Command Line (Direct Execution)

```bash
# Run with example data
python sizing_calculator.py
```

**Output:** JSON with complete sizing recommendations

### Method 3: Python Module (Programmatic)

```python
from sizing_calculator import AAP26SizingCalculator

calculator = AAP26SizingCalculator()

metrics = {
    'managed_hosts': 40000,
    'playbooks_per_day_peak': 70000,
    'tasks_per_job': 100,
    'job_duration_hours': 0.25,  # 15 minutes
    'allowed_hours_per_day': 24,  # 24/7
    'job_retention_hours': 48,
    'forks_observed': 5,
    'database_vcpu': 16,
    'database_memory_gb': 128,
    'database_cpu_percent': 90,
    'database_memory_percent': 35,
    # ... other parameters
}

recommendation = calculator.generate_sizing_recommendation(metrics)
print(recommendation)
```

### Method 4: REST API

```bash
# POST to /api/calculate endpoint
curl -X POST http://localhost:5001/api/calculate \
  -H "Content-Type: application/json" \
  -d @your-metrics.json

# GET example data
curl http://localhost:5001/api/example
```

---

## Official Red Hat Formulas

### Core Principle: Time-Based Concurrency

The calculator uses **time-based concurrency calculations** that account for:
- How many jobs need to run over the operating period
- How long each job takes
- Whether you run 24/7 or only during business hours
- Realistic concurrency based on time constraints

### Benchmarked Constants (from Excel)

| Constant | Value | Description |
|----------|-------|-------------|
| Memory per Fork | 100 MB | Memory consumed per parallel fork |
| Forks per CPU Core | 4 | Number of forks one CPU core can handle |
| Events per Task | 10 | Average events generated per task (with loops) |
| Event Size | 2 KB | Event size in database (debug mode) |
| Facts Size per Host | 50 KB | Inventory facts storage per host |
| Controller Events/sec | 400 | Events processed per second |
| Memory per Event Fork | 0.0124 MB | Memory for event processing |
| CPU per Event Fork | 0.00011 | CPU for event processing |

---

### 1. Execution Plane Formulas

#### Calculate Needed Forks

```python
forks_needed = (
    number_of_hosts ×
    jobs_per_host_per_day ×
    job_duration_hours /
    allowed_hours_per_day
)
```

**Example:**
```
40,000 hosts × 1.75 jobs/host/day × 0.25 hrs / 24 hrs
= 729.17 forks needed
```

#### Calculate Memory

```python
memory_gb = (forks_needed × 100) / 1024  # MB to GB
memory_total_gb = memory_gb + (2 × number_of_nodes)
```

**Example:**
```
729 forks × 100 MB / 1024 = 71.2 GB
Plus 2 GB × 15 nodes = 30 GB base reservation
Total = 101.2 GB
```

#### Calculate CPU (AVERAGED)

**Use the AVG formula, NOT the MAX formula:**

```python
# AVG Formula (CORRECT - Use This)
cpu_avg = 2 × number_of_nodes + forks_needed / 4 / 10

# MAX Formula (TOO HIGH - Do Not Use)
cpu_max = forks_needed / 4  # Theoretical peak only
```

**Why the /10 divisor?** It accounts for average vs peak load. The MAX formula is theoretical capacity only.

**Example:**
```
AVG: 2 × 15 + 729 / 4 / 10 = 30 + 18.2 = 48.2 cores (REALISTIC)
MAX: 729 / 4 = 182 cores (TOO HIGH, IGNORE)
```

---

### 2. Control Plane Formulas

#### Critical Insight: AVERAGED Result Required

The control plane needs **BOTH**:
1. Event processing capacity
2. Job management capacity

Then it uses the **AVERAGE** of both (Excel row 54: "AVERAGED RESULT").

#### Calculate Event Forks

```python
event_forks = (
    hosts ×
    jobs_per_host_per_day ×
    tasks_per_job ×
    10  # events_per_task (benchmarked)
    × job_duration_hours /
    allowed_hours_per_day
)
```

**Example:**
```
40,000 × 1.75 × 100 × 10 × 0.25 / 24
= 729,166.67 event forks
```

#### Memory for Event Processing

```python
memory_events_mb = event_forks × 0.0124  # MB per event fork
memory_events_gb = memory_events_mb / 1024 + (2 × nodes)
```

#### CPU for Event Processing (AVERAGED)

```python
cpu_events = event_forks × 0.00011 / 10 + (1.6 × nodes)
```

#### Memory for Job Management

```python
concurrent_jobs = jobs_per_day × job_duration_hours / allowed_hours_per_day
forks_for_jobs = concurrent_jobs × average_forks_per_job
memory_jobs_gb = forks_for_jobs × 100 / 1024 + (2 × nodes)
```

#### CPU for Job Management (AVERAGED)

```python
cpu_jobs = 2 × nodes + forks_for_jobs / 4 / 10
```

#### Final Control Plane Sizing

```python
# Take the AVERAGE of both calculations
memory_control = (memory_events + memory_jobs) / 2
cpu_control = (cpu_events + cpu_jobs) / 2
```

**Example:**
```
Event processing: 13 GB memory, 11 CPU
Job management: 360 GB memory, 95 CPU
AVERAGED RESULT: 186 GB memory, 53 CPU
```

---

### 3. Database Storage Formula

```python
# Facts storage
db_facts_mb = hosts × 50 / 1024  # 50 KB per host

# Inventory storage
db_inventory_mb = hosts × 50 / 1024

# Jobs storage (MAIN COMPONENT)
db_jobs_mb = (
    hosts ×
    jobs_per_host_per_day ×
    tasks_per_job ×
    10  # events_per_task
    × days_to_keep_jobs ×
    2  # KB per event
) / 1024

# Total database size
db_total_gb = (db_facts_mb + db_inventory_mb + db_jobs_mb) / 1024
```

**Example:**
```
Facts: 1,953 MB
Inventory: 1,953 MB
Jobs: 273,437 MB (main component)
Total: 271 GB
```

---

## Required Input Parameters

### Core Workload Parameters

| Parameter | Description | Example | Notes |
|-----------|-------------|---------|-------|
| `managed_hosts` | Total managed hosts | 40,000 | Required |
| `playbooks_per_day_peak` | Peak daily job volume | 70,000 | Required |
| `tasks_per_job` | Average tasks per playbook | 100 | Default: 100 |
| `job_duration_hours` | Average job runtime | 0.25 | 0.25 = 15 minutes |
| `allowed_hours_per_day` | Operating window | 24 | 24 = 24/7, 8 = business hours |
| `forks_observed` | Average forks per job | 5 | Default: 5 |
| `job_retention_hours` | Job history retention | 48 | 48 hours = 2 days |

### Current Resource Utilization

| Parameter | Description | Example |
|-----------|-------------|---------|
| `num_controllers` | Number of controllers | 12 |
| `num_execution_nodes` | Number of execution nodes | 30 |
| `database_vcpu` | Database CPU cores | 16 |
| `database_memory_gb` | Database memory | 128 |
| `database_cpu_percent` | DB CPU utilization | 90 |
| `database_memory_percent` | DB memory utilization | 35 |

See the web UI for complete list of parameters.

---

## Example Calculation

### Input Scenario
```
Managed Hosts: 40,000
Jobs per Day: 70,000
Tasks per Job: 100
Job Duration: 0.25 hours (15 minutes)
Operating Hours: 24 (24/7)
Average Forks: 5
Retention: 48 hours
```

### Calculated Results

#### Execution Plane
```
Forks Needed: 729.17
- Calculation: 40,000 × (70,000/40,000) × 0.25 / 24 = 729.17

Memory: 102 GB
- Calculation: 729 × 100 / 1024 + 2 × 15 nodes = 102 GB

CPU: 49 vCPU
- Calculation: 2 × 15 + 729 / 4 / 10 = 49 cores

Execution Pods: 15
```

#### Control Plane
```
Event Forks: 729,167
- Calculation: 40,000 × 1.75 × 100 × 10 × 0.25 / 24 = 729,167

Job Forks: 3,646
- Calculation: (70,000 × 0.25 / 24) × 5 = 3,646

Event Processing: 13 GB / 11 CPU
Job Management: 360 GB / 95 CPU
AVERAGED: 187 GB / 54 CPU

Control Pods: 2
```

#### Database
```
Facts: 1,953 MB
Inventory: 1,953 MB
Jobs: 273,437 MB
Total Storage: 326 GB (with 20% buffer)
```

#### Summary
```
Total CPU: 142 vCPU
Total Memory: 425 GB
Total Storage: 326 GB
Total Pods: ~30
```

---

## Understanding Your Results

### Component Breakdown

Your results will show:

1. **Platform Gateway** - Authentication and routing (2-3 pods)
2. **Automation Controller - Control Plane** - Job orchestration and event processing
3. **Automation Controller - Execution Plane** - Job execution
4. **Database (PostgreSQL)** - Data storage with breakdown
5. **Automation Hub** - Content management
6. **Event-Driven Ansible** - Event processing
7. **Redis** - Cache layer

### Formulas Used Section

Shows the actual formulas used with your values:
```json
{
  "source": "Red Hat AAP Excel Reference Sheet",
  "execution_forks": "hosts × jobs_per_host_per_day × duration / allowed_hours",
  "control_plane": "AVERAGE of (event_processing + job_management) / 2",
  ...
}
```

### Calculation Breakdown

For control plane, you'll see:
```json
{
  "calculation_breakdown": {
    "event_processing": {"memory_gb": 13, "cpu": 11},
    "job_management": {"memory_gb": 360, "cpu": 95},
    "averaged_result": {"memory_gb": 187, "cpu": 54}
  }
}
```

---

## API Documentation

### POST /api/calculate

Calculate sizing recommendations.

**Request Body:**
```json
{
  "managed_hosts": 40000,
  "playbooks_per_day_peak": 70000,
  "tasks_per_job": 100,
  "job_duration_hours": 0.25,
  "allowed_hours_per_day": 24,
  "forks_observed": 5,
  "job_retention_hours": 48,
  "database_vcpu": 16,
  "database_memory_gb": 128,
  "database_cpu_percent": 90,
  "database_memory_percent": 35
}
```

**Response:**
```json
{
  "topology": "enterprise",
  "components": { ... },
  "summary": {
    "total_cpu": 142,
    "total_memory_gb": 425,
    "total_storage_gb": 326
  },
  "formulas_used": { ... },
  "deployment_notes": [ ... ]
}
```

### GET /api/example

Get example input data.

**Response:** Example metrics object

---

## Important Notes

### Formula Source Authority

⚠️ **Critical:** These formulas come from the official Red Hat AAP Excel reference sheet, **NOT** from estimated "capacity units" approaches.

Previous versions of this calculator used an incorrect "137 capacity units per node" formula that **does not exist** in official Red Hat documentation. This has been corrected.

See `FORMULA_CORRECTIONS_SUMMARY.md` for details on the corrections made.

### Time-Based Concurrency

The key innovation in the correct formulas is **time-based concurrency**:

```python
# Instead of: capacity = jobs × forks
# Correct: accounts for time window
forks = hosts × jobs_per_hostday × job_duration / allowed_hours
```

This provides accurate sizing based on:
- Actual job volume over time
- Job duration
- Operating window (24/7 vs business hours)

### Control Plane Averaging

The control plane calculation is **AVERAGED** between event processing and job management:

```python
# NOT just event processing
# NOT just job management
# AVERAGE of both!
result = (event_capacity + job_capacity) / 2
```

This is explicitly stated in the Excel reference (row 54: "AVERAGED RESULT").

### Deployment Recommendations

- ✅ All values include appropriate headroom for peaks and growth
- ✅ Minimum 2 replicas per service for high availability
- ✅ Container deployments typically 20-30% more efficient than VMs
- ✅ Test in non-production environment before migration
- ✅ Validate sizing with Red Hat support for production deployments

---

## References

### Official Red Hat Documentation

- Red Hat Ansible Automation Platform 2.6 Tested Deployment Models
- Performance Tuning for Ansible Automation Platform
- Planning Guide for Ansible Automation Platform
- Using Automation Execution Guide
- Configuring Automation Execution Guide

### Excel Reference

- `docs/AAp-sizing-sheet-reference.xlsx` - Official Red Hat sizing reference
- `docs/extracted_excel_parameters.json` - Extracted parameters and formulas

### Additional Documentation

- `CORRECT_FORMULAS_FROM_EXCEL.md` - Detailed formula documentation from Excel
- `FORMULA_CORRECTIONS_SUMMARY.md` - Summary of corrections made
- `ENHANCEMENT_PLAN.md` - Future enhancement plans

---

## Project Structure

```
aap-sizing-guide/
├── sizing_calculator.py          # Core calculation engine
├── app.py                         # Flask web application
├── templates/
│   └── index.html                 # Web UI
├── static/
│   ├── css/style.css             # Styles
│   └── js/app.js                 # Client-side JavaScript
├── docs/
│   ├── AAp-sizing-sheet-reference.xlsx
│   └── extracted_excel_parameters.json
├── requirements.txt
└── README.md
```

---

## Support

For issues or questions:
1. Check the documentation in `docs/`
2. Review `CORRECT_FORMULAS_FROM_EXCEL.md` for formula details
3. Consult Red Hat AAP 2.6 official documentation
4. Contact Red Hat support for production sizing validation

---

## License

This tool is provided as-is for AAP sizing planning. Always validate sizing recommendations with Red Hat support before production deployment.

---

**Last Updated:** 2024
**Formula Source:** Red Hat AAP Excel Reference Sheet (AAp-sizing-sheet-reference.xlsx)
**Status:** ✅ Production-ready with official Red Hat formulas
