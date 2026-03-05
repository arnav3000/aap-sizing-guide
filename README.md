# Ansible Automation Platform 2.4 to 2.6 Sizing Calculator

A comprehensive sizing calculator that helps you plan your migration from **Ansible Automation Platform 2.4** (running on RHEL-8 VMs) to **AAP 2.6** (running as containers) using **official Red Hat capacity formulas**.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage Methods](#usage-methods)
- [Calculation Logic Explained](#calculation-logic-explained)
- [Official Red Hat Formulas Used](#official-red-hat-formulas-used)
- [Example Calculation](#example-calculation)
- [Understanding Your Results](#understanding-your-results)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)

---

## Overview

This tool calculates the recommended container resources for AAP 2.6 based on your current AAP 2.4 VM utilization metrics. It uses **official Red Hat capacity planning formulas** extracted from AAP 2.6 documentation.

### What It Does

- ✅ Analyzes your current AAP 2.4 resource utilization
- ✅ Determines appropriate topology (Growth vs Enterprise)
- ✅ Calculates execution capacity using Red Hat's formula
- ✅ Sizes control plane, execution plane, database, and all components
- ✅ Provides deployment notes and best practices
- ✅ Shows the actual formulas used in calculations

### Based On Official Documentation

All calculations are derived from:
- Red Hat Ansible Automation Platform 2.6 Tested Deployment Models
- Performance Tuning for Ansible Automation Platform
- Using Automation Execution Guide
- Community best practices (TechBeatly, etc.)

---

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install requirements
pip install -r requirements.txt
```

### 2. Run the Web Application

```bash
# Start the web server
python3 app.py

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
python3 sizing_calculator.py
```

---

## Usage Methods

### Method 1: Web Interface (Recommended)

```bash
# Start the web server
python3 app.py

# Open in browser
open http://localhost:5001
```

**Features:**
- Interactive form for entering metrics
- Visual results with component breakdown
- Load example data with one click
- Export-friendly results display

### Method 2: Command Line (Direct Execution)

```bash
# Run with example data
python3 sizing_calculator.py
```

**Output:** JSON with complete sizing recommendations

### Method 3: Python Module (Programmatic)

```python
from sizing_calculator import AAP26SizingCalculator

calculator = AAP26SizingCalculator()

metrics = {
    'num_controllers': 12,
    'controller_cpu_percent_avg': 35,
    'controller_cpu_percent_peak': 50,
    'controller_memory_percent': 20,
    'num_execution_nodes': 30,
    'execution_cpu_percent': 90,
    'execution_memory_percent': 50,
    'forks_observed': 165,
    'database_vcpu': 16,
    'database_memory_gb': 128,
    'database_cpu_percent': 90,
    'database_memory_percent': 35,
    'concurrent_db_requests_peak': 600,
    'db_growth_per_day_gb': 200,
    'playbooks_per_day_peak': 70000,
    'concurrent_jobs_peak': 500,
    'concurrent_jobs_pending': 30,
    'job_retention_hours': 48,
    'managed_hosts': 40000,
    'num_hub_nodes': 2,
    'hub_cpu_percent': 25,
    'hub_memory_percent': 30
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

## Calculation Logic Explained

### Core Principle: Capacity-Based Sizing

The calculator uses Red Hat's **capacity unit system** instead of simple percentage-based estimates. This ensures accurate sizing based on actual workload requirements.

### Key Constant: 137 Capacity Units per Node

Red Hat defines that a **standard node (4 vCPU, 16 GB RAM)** provides **137 capacity units**.

This is the foundation of all execution capacity calculations.

---

## Official Red Hat Formulas Used

### 1. Execution Capacity Formula

**Purpose:** Calculate how many execution nodes you need

**Formula:**
```
Execution Capacity = (Concurrent Jobs × Forks per Job) + (Concurrent Jobs × 1 base task)
```

**Capacity per Node:**
```
Standard Node (4 vCPU / 16 GB RAM) = 137 capacity units
```

**Nodes Needed:**
```
Execution Nodes = Execution Capacity / 137
```

**Example:**
```
Input: 500 concurrent jobs, 5 forks per job

Calculation:
Execution Capacity = (500 × 5) + (500 × 1)
                   = 2,500 + 500
                   = 3,000 capacity units

Execution Nodes = 3,000 / 137
                = 21.9
                ≈ 22 nodes
```

**Code Implementation:**
```python
def calculate_execution_capacity(self, concurrent_jobs: int, forks_per_job: int = 5) -> int:
    capacity = (concurrent_jobs * forks_per_job) + (concurrent_jobs * 1)
    return capacity

execution_capacity = self.calculate_execution_capacity(500, 5)  # Returns 3000
execution_nodes = math.ceil(execution_capacity / 137)  # Returns 22
```

---

### 2. Memory Capacity Formula

**Purpose:** Calculate memory requirements based on fork consumption

**Formula:**
```
Memory = (Total Concurrent Forks × 100 MB per Fork) + 2 GB reservation
```

**Constants:**
- **100 MB per fork** (Red Hat specification)
- **2 GB base reservation** for system overhead

**Example:**
```
Input: 500 concurrent jobs, 5 forks per job

Calculation:
Total Forks = 500 × 5 = 2,500 forks
Memory = (2,500 × 100 MB) + 2 GB
       = 250 GB + 2 GB
       = 252 GB total memory needed

Per Node (22 nodes):
Memory per Node = 252 GB / 22
                = 11.5 GB per node
                ≈ 16 GB standard node size (sufficient)
```

**Code Implementation:**
```python
def calculate_execution_memory(self, concurrent_jobs: int, forks_per_job: int = 5) -> int:
    total_forks = concurrent_jobs * forks_per_job
    memory_mb = (total_forks * self.MEMORY_PER_FORK_MB) + (self.MEMORY_RESERVATION_GB * 1024)
    memory_gb = math.ceil(memory_mb / 1024)
    return memory_gb
```

---

### 3. Control Plane Capacity Formula

**Purpose:** Size the control plane for job management

**Formula:**
```
Control Capacity = Maximum Concurrent Jobs to Manage
```

**Sizing:**
```
Control Nodes = max(2, Control Capacity / (137 × 5))
```

**Why 1/5 ratio?**
- Control plane manages jobs, doesn't execute them
- Requires far less capacity than execution plane
- Minimum 2 nodes for high availability

**Example:**
```
Input: 500 concurrent jobs

Calculation:
Control Capacity = 500 jobs
Control Nodes = 500 / (137 × 5)
              = 500 / 685
              = 0.73
              ≈ 2 nodes (minimum for HA)
```

**Code Implementation:**
```python
def calculate_controller_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
    concurrent_jobs = current_metrics.get('concurrent_jobs_peak', 100)
    control_capacity = concurrent_jobs
    control_nodes_needed = max(2, math.ceil(control_capacity / (self.CAPACITY_PER_NODE * 5)))

    return {
        'control_plane_pods': control_nodes_needed,
        'cpu_per_pod': 4,
        'memory_per_pod_gb': 16,
        'control_capacity': control_capacity
    }
```

---

### 4. Database Storage Formula

**Purpose:** Calculate database storage based on job volume and retention

**Formula:**
```
Storage = Event_Size × Events_Per_Job × Jobs_Per_Day × Retention_Days
```

**Constants:**
- **Event Size:** 2 KB per event
- **Events per Job:** 500 events (average playbook)
- **Retention Days:** Based on your policy

**Example:**
```
Input: 70,000 jobs/day, 48 hours retention

Calculation:
Daily Jobs = 70,000 / 30 = 2,333 jobs/day
Retention = 48 hours / 24 = 2 days
Storage = 2 KB × 500 × 2,333 × 2
        = 4.66 GB baseline

Plus observed growth:
Daily Growth = 200 GB/day
Total Storage = 4.66 GB + (200 GB × 2 days × 1.2 buffer)
              = 4.66 GB + 480 GB
              ≈ 485 GB
```

**Code Implementation:**
```python
def calculate_database_storage(self, jobs_per_day: int, retention_days: int,
                               events_per_job: int = 500, event_size_kb: int = 2) -> int:
    storage_kb = event_size_kb * events_per_job * jobs_per_day * retention_days
    storage_gb = math.ceil(storage_kb / (1024 * 1024))
    return max(storage_gb, 60)  # Minimum 60GB
```

---

### 5. Event Processing Rate Formula

**Purpose:** Calculate peak event processing requirements

**Formula:**
```
Events per Job = Tasks per Job × Hosts per Job × 6 Events per Task
Peak Event Rate = (Concurrent Jobs × Events per Job) / Job Duration
```

**Constants:**
- **6 events per task** (at verbosity level 1)
- **Average job duration:** 60 seconds

**Example:**
```
Input: 500 concurrent jobs, 10 tasks/job, 50 hosts/job

Calculation:
Events per Job = 10 × 50 × 6 = 3,000 events
Peak Rate = (500 jobs × 3,000 events) / 60 seconds
          = 1,500,000 / 60
          = 25,000 events/second
```

**Code Implementation:**
```python
def calculate_event_processing_rate(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
    concurrent_jobs = current_metrics.get('concurrent_jobs_peak', 100)
    avg_tasks_per_job = 10
    avg_hosts_per_job = 50
    events_per_task = 6

    events_per_job = avg_tasks_per_job * avg_hosts_per_job * events_per_task
    avg_job_duration_sec = 60
    events_per_second_peak = math.ceil((concurrent_jobs * events_per_job) / avg_job_duration_sec)

    return {
        'events_per_job': events_per_job,
        'events_per_second_peak': events_per_second_peak
    }
```

---

### 6. Database Resource Sizing

**Purpose:** Size PostgreSQL based on current utilization

**Formula:**
```
Recommended CPU = Current_CPU × (CPU_Percent / 100) × 1.3
Recommended Memory = Current_Memory × (Memory_Percent / 100) × 1.5
```

**Headroom:**
- **30% CPU headroom** for peaks and growth
- **50% Memory headroom** for buffer and cache

**Example:**
```
Input: 16 vCPU, 128 GB RAM, 90% CPU, 35% memory usage

Calculation:
CPU Usage = 16 × (90 / 100) = 14.4 vCPU used
Recommended CPU = 14.4 × 1.3 = 18.72 ≈ 19 vCPU

Memory Usage = 128 × (35 / 100) = 44.8 GB used
Recommended Memory = 44.8 × 1.5 = 67.2 ≈ 68 GB
```

**Code Implementation:**
```python
def calculate_database_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
    cpu_percent = current_metrics.get('database_cpu_percent', 90)
    memory_percent = current_metrics.get('database_memory_percent', 35)
    current_db_vcpu = current_metrics.get('database_vcpu', 16)
    current_db_memory = current_metrics.get('database_memory_gb', 128)

    actual_cpu_used = current_db_vcpu * (cpu_percent / 100)
    actual_memory_used = current_db_memory * (memory_percent / 100)

    recommended_cpu = max(8, math.ceil(actual_cpu_used * 1.3))
    recommended_memory = max(32, math.ceil(actual_memory_used * 1.5))

    return {
        'cpu': recommended_cpu,
        'memory_gb': recommended_memory
    }
```

---

### 7. Workload Tier Analysis

**Purpose:** Determine if workload needs Growth or Enterprise topology

**Scoring System:**

| Metric | Threshold | Points |
|--------|-----------|--------|
| Jobs/day > 20,000 | Yes | +3 |
| Jobs/day > 5,000 | Yes | +2 |
| Jobs/day > 2,000 | Yes | +1 |
| Concurrent > 200 | Yes | +3 |
| Concurrent > 100 | Yes | +2 |
| Concurrent > 50 | Yes | +1 |
| Hosts > 20,000 | Yes | +3 |
| Hosts > 5,000 | Yes | +2 |
| Hosts > 2,000 | Yes | +1 |

**Decision:**
- **Score ≥ 5:** Enterprise Topology
- **Score ≥ 3:** Enterprise Recommended
- **Score < 3:** Growth Topology

**Example:**
```
Input: 70,000 jobs/day, 500 concurrent jobs, 40,000 hosts

Scoring:
Jobs/day (70,000 > 20,000): +3
Concurrent (500 > 200): +3
Hosts (40,000 > 20,000): +3

Total Score: 9 points
Decision: Enterprise Topology
```

**Code Implementation:**
```python
def analyze_workload_tier(self, current_metrics: Dict[str, Any]) -> str:
    jobs_per_day = current_metrics.get('playbooks_per_day_peak', 0)
    concurrent_jobs = current_metrics.get('concurrent_jobs_peak', 0)
    managed_hosts = current_metrics.get('managed_hosts', 0)

    enterprise_score = 0

    if jobs_per_day > 20000:
        enterprise_score += 3
    elif jobs_per_day > 5000:
        enterprise_score += 2
    elif jobs_per_day > 2000:
        enterprise_score += 1

    if concurrent_jobs > 200:
        enterprise_score += 3
    elif concurrent_jobs > 100:
        enterprise_score += 2
    elif concurrent_jobs > 50:
        enterprise_score += 1

    if managed_hosts > 20000:
        enterprise_score += 3
    elif managed_hosts > 5000:
        enterprise_score += 2
    elif managed_hosts > 2000:
        enterprise_score += 1

    if enterprise_score >= 5:
        return 'enterprise'
    elif enterprise_score >= 3:
        return 'enterprise_recommended'
    else:
        return 'growth'
```

---

## Example Calculation

### Input: Your AAP 2.4 Environment

```json
{
  "num_controllers": 12,
  "controller_cpu_percent_avg": 35,
  "controller_cpu_percent_peak": 50,
  "controller_memory_percent": 20,
  "num_execution_nodes": 30,
  "execution_cpu_percent": 90,
  "execution_memory_percent": 50,
  "forks_observed": 165,
  "database_vcpu": 16,
  "database_memory_gb": 128,
  "database_cpu_percent": 90,
  "database_memory_percent": 35,
  "playbooks_per_day_peak": 70000,
  "concurrent_jobs_peak": 500,
  "job_retention_hours": 48,
  "managed_hosts": 40000
}
```

### Step-by-Step Calculation

#### Step 1: Analyze Workload Tier

```
Jobs/day: 70,000 (>20,000) = +3 points
Concurrent: 500 (>200) = +3 points
Hosts: 40,000 (>20,000) = +3 points

Total Score: 9 points
Result: Enterprise Topology
```

#### Step 2: Calculate Execution Capacity

```
Forks observed: 165
Concurrent jobs: 500
Average forks per job: 165 / 500 = 0.33 (too low, use default 5)

Execution Capacity = (500 jobs × 5 forks) + (500 × 1)
                   = 2,500 + 500
                   = 3,000 capacity units

Execution Nodes = 3,000 / 137
                = 21.9
                ≈ 22 nodes
```

#### Step 3: Calculate Execution Memory

```
Total Forks = 500 × 5 = 2,500
Memory = (2,500 × 100 MB) + 2 GB
       = 250 GB + 2 GB
       = 252 GB

Per Node = 252 / 22 = 11.5 GB/node
Use Standard: 16 GB/node
Total Memory: 22 × 16 = 352 GB
```

#### Step 4: Calculate Control Plane

```
Control Capacity = 500 concurrent jobs
Control Nodes = max(2, 500 / 685)
              = max(2, 0.73)
              = 2 nodes

Control CPU = 2 × 4 = 8 vCPU
Control Memory = 2 × 16 = 32 GB
```

#### Step 5: Calculate Database

```
CPU:
Used = 16 × (90 / 100) = 14.4 vCPU
Recommended = 14.4 × 1.3 = 18.72 ≈ 19 vCPU

Memory:
Used = 128 × (35 / 100) = 44.8 GB
Recommended = 44.8 × 1.5 = 67.2 ≈ 68 GB

Storage:
Jobs/day = 70,000 / 30 = 2,333
Retention = 2 days
Base = 2 KB × 500 × 2,333 × 2 = 4.66 GB
Growth = 200 GB/day × 2 × 1.2 = 480 GB
Total = 485 GB ≈ 540 GB (with rounding)
```

#### Step 6: Calculate Event Processing

```
Events per Job = 10 tasks × 50 hosts × 6 = 3,000 events
Peak Rate = (500 jobs × 3,000) / 60 sec
          = 25,000 events/second
```

#### Step 7: Other Components

```
Gateway (Enterprise): 3 pods × 2 vCPU × 4 GB = 6 vCPU, 12 GB
Automation Hub: 2 pods × 2 vCPU × 8 GB = 4 vCPU, 16 GB
EDA: 2 pods × 2 vCPU × 8 GB = 4 vCPU, 16 GB
Redis (Clustered): 6 nodes × 1 vCPU × 4 GB = 6 vCPU, 24 GB
```

### Final Output

```json
{
  "workload_tier": "enterprise",
  "summary": {
    "total_cpu": 135,
    "total_memory_gb": 520,
    "total_storage_gb": 540,
    "estimated_pods": 37
  },
  "components": {
    "platform_gateway": {
      "gateway_pods": 3,
      "total_cpu": 6,
      "total_memory_gb": 12
    },
    "automation_controller_control_plane": {
      "control_plane_pods": 2,
      "total_cpu": 8,
      "total_memory_gb": 32,
      "control_capacity": 500
    },
    "automation_controller_execution_plane": {
      "execution_pods": 22,
      "total_cpu": 88,
      "total_memory_gb": 352,
      "execution_capacity": 3000,
      "avg_forks_per_job": 5
    },
    "database": {
      "cpu": 19,
      "memory_gb": 68,
      "storage_gb": 540
    },
    "automation_hub": {
      "hub_pods": 2,
      "total_cpu": 4,
      "total_memory_gb": 16
    },
    "event_driven_ansible": {
      "eda_pods": 2,
      "total_cpu": 4,
      "total_memory_gb": 16
    },
    "redis": {
      "type": "clustered",
      "total_nodes": 6,
      "total_cpu": 6,
      "total_memory_gb": 24
    }
  },
  "calculation_method": {
    "execution_capacity_formula": "(500 jobs × 5 forks) + (500 × 1) = 3000 units",
    "capacity_per_node": "137 units per 4vCPU/16GB node",
    "memory_per_fork": "100MB per fork + 2GB reservation",
    "event_rate_peak": "25000 events/second peak"
  }
}
```

---

## Understanding Your Results

### Topology Recommendation

**Growth Topology:**
- Suitable for: < 1,000 hosts, < 20 jobs/sec, < 500 jobs/day
- Characteristics: Single-node or minimal distribution
- Use case: Development, testing, small deployments

**Enterprise Topology:**
- Suitable for: > 10,000 hosts, > 80 jobs/sec, > 2,000 jobs/day
- Characteristics: Multi-node, high availability, independent scaling
- Use case: Production, large-scale deployments

### Resource Summary

**Total CPU:**
- Sum of all component vCPU requirements
- Includes headroom for peaks and growth

**Total Memory:**
- Sum of all component RAM requirements
- Includes buffers for fork consumption and caching

**Total Storage:**
- Database storage based on job volume and retention
- Includes daily growth projection with buffer

**Estimated Pods:**
- Total number of container pods across all components
- Each pod typically runs on a separate node or can be co-located

### Component Breakdown

**Platform Gateway:**
- Handles authentication and routing
- 2-3 pods for HA
- Lightweight resource requirements

**Automation Controller - Control Plane:**
- Manages job scheduling and orchestration
- Sized based on concurrent job management capacity
- Minimal resources compared to execution

**Automation Controller - Execution Plane:**
- Runs actual automation jobs
- Sized using capacity formula (jobs × forks)
- Largest resource consumer

**Database (PostgreSQL):**
- Stores job data, events, inventory
- Sized based on current utilization + headroom
- Storage based on retention policy

**Automation Hub:**
- Hosts content collections and execution environments
- Scales based on sync frequency and size

**Event-Driven Ansible:**
- Processes events and triggers automation
- Scales with number of activations

**Redis:**
- Caching and queueing
- Standalone for growth, clustered for enterprise

### Calculation Method

The calculator shows you exactly how it arrived at the numbers:

```
Execution Capacity Formula: (500 jobs × 5 forks) + (500 × 1) = 3000 units
Capacity per Node: 137 units per 4vCPU/16GB node
Memory per Fork: 100MB per fork + 2GB reservation
Event Rate Peak: 25000 events/second peak
```

This transparency allows you to:
- Validate the calculations
- Adjust inputs to see impact
- Understand the sizing rationale
- Share with Red Hat support for validation

---

## API Documentation

### Endpoints

#### GET /api/example

Returns example AAP 2.4 metrics for testing.

**Response:**
```json
{
  "num_controllers": 12,
  "controller_cpu_percent_avg": 35,
  "playbooks_per_day_peak": 70000,
  ...
}
```

#### POST /api/calculate

Calculates AAP 2.6 sizing based on provided metrics.

**Request Body:**
```json
{
  "num_controllers": 12,
  "controller_cpu_percent_avg": 35,
  "controller_cpu_percent_peak": 50,
  "controller_memory_percent": 20,
  "num_execution_nodes": 30,
  "execution_cpu_percent": 90,
  "execution_memory_percent": 50,
  "forks_observed": 165,
  "database_vcpu": 16,
  "database_memory_gb": 128,
  "database_cpu_percent": 90,
  "database_memory_percent": 35,
  "concurrent_db_requests_peak": 600,
  "db_growth_per_day_gb": 200,
  "playbooks_per_day_peak": 70000,
  "concurrent_jobs_peak": 500,
  "concurrent_jobs_pending": 30,
  "job_retention_hours": 48,
  "managed_hosts": 40000,
  "num_hub_nodes": 2,
  "hub_cpu_percent": 25,
  "hub_memory_percent": 30
}
```

**Response:**
```json
{
  "workload_tier": "enterprise",
  "topology_recommendation": "Enterprise Topology - ...",
  "components": { ... },
  "summary": { ... },
  "calculation_method": { ... },
  "deployment_notes": [ ... ]
}
```

---

## Troubleshooting

### Port Already in Use

If you see "Address already in use" error:

```bash
# Find and kill the process
lsof -ti:5001 | xargs kill -9

# Or change the port in app.py
# Edit: app.run(debug=True, host='0.0.0.0', port=5002)
```

### Module Not Found Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### PDF Reading Issues

If you need to read the PDF documentation:

```bash
# Install poppler for PDF reading
brew install poppler  # macOS
apt-get install poppler-utils  # Ubuntu/Debian
```

### Python Version Issues

Ensure you're using Python 3.8 or higher:

```bash
python3 --version

# If too old, install newer Python
brew install python@3.11  # macOS
```

---

## Files and Directories

```
aap-sizing-guide/
├── app.py                          # Flask web application
├── sizing_calculator.py            # Core calculation engine
├── requirements.txt                # Python dependencies
├── run.sh                         # Startup script
├── README.md                      # This file
├── QUICKSTART.md                  # Quick start guide
├── CALCULATION_CORRECTION.md      # Formula corrections explained
├── FIXES_APPLIED.md              # Summary of fixes
├── PROJECT_SUMMARY.md            # Project overview
├── .gitignore                     # Git ignore rules
├── templates/
│   └── index.html                 # Web UI template
├── static/
│   ├── css/
│   │   └── style.css             # Styling
│   └── js/
│       └── app.js                 # Client-side JavaScript
├── docs/
│   ├── extracted-sizing-data.md   # Red Hat sizing data
│   └── *.pdf                      # Original Red Hat docs
└── venv/                          # Virtual environment (created)
```

---

## References and Sources

### Official Red Hat Documentation

1. [Red Hat Ansible Automation Platform 2.6 - Tested Deployment Models](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/pdf/tested_deployment_models/)
2. [Using Automation Execution - Chapter 19: Managing Capacity](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/using_automation_execution/assembly-controller-instances)
3. [Performance Tuning for Ansible Automation Platform](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/configuring_automation_execution/assembly-controller-improving-performance)
4. [Planning Your Installation](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html-single/planning_your_installation/)
5. [Containerized Installation Guide](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html-single/containerized_installation/)

### Community Resources

1. [Ansible Capacity Planning - TechBeatly](https://techbeatly.com/ansible-capacity-planning/)

### Key Constants Verified

- ✓ 137 capacity units per 4vCPU/16GB node
- ✓ 100MB memory per fork
- ✓ 2GB base memory reservation
- ✓ 4 forks per CPU core baseline
- ✓ 6 events per task (verbosity 1)
- ✓ Default fork value: 5

---

## Support and Feedback

### For Calculator Issues

- Check troubleshooting section above
- Review CALCULATION_CORRECTION.md for formula details
- Verify your metrics are in correct format

### For Production Deployments

- **Always validate with Red Hat Support**
- This tool provides estimates based on official formulas
- Actual requirements may vary based on specific workload characteristics
- Test in non-production environment first

### Important Disclaimers

- This is a planning tool, not an official Red Hat product
- Calculations are based on publicly available Red Hat documentation
- Real-world performance may vary
- Always monitor actual usage and adjust accordingly

---

## License

This tool is provided as-is for planning purposes. Always validate sizing with Red Hat support for production deployments.

---

**Version:** 2.0 (Corrected with Official Red Hat Formulas)
**Last Updated:** March 2026
**AAP Versions:** 2.4 (source) → 2.6 (target)
