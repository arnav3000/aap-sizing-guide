# AAP Sizing Calculator - Project Summary

## Project Overview

A complete web-based sizing calculator application that helps plan migration from **Ansible Automation Platform 2.4** (RHEL-8 VMs) to **AAP 2.6** (containers).

**Created**: March 2026
**Purpose**: Calculate container resource requirements based on current AAP 2.4 VM utilization metrics

## What Was Built

### 1. Core Calculation Engine (`sizing_calculator.py`)

A comprehensive Python class `AAP26SizingCalculator` that:

- **Analyzes workload tier**: Determines if deployment should use Growth or Enterprise topology
- **Calculates resources per component**:
  - Platform Gateway
  - Automation Controller (Control Plane)
  - Automation Controller (Execution Plane)
  - Database (PostgreSQL)
  - Automation Hub
  - Event-Driven Ansible
  - Redis Cache
- **Includes intelligent headroom**: 30% CPU, 50% memory buffer
- **Ensures HA**: Minimum 2 replicas per service
- **Provides deployment notes**: Context-aware recommendations

**Key Methods**:
- `analyze_workload_tier()` - Scores workload against reference metrics
- `calculate_controller_resources()` - Sizes control plane
- `calculate_execution_node_resources()` - Sizes execution plane
- `calculate_database_resources()` - Sizes PostgreSQL with storage
- `generate_sizing_recommendation()` - Main orchestration method

### 2. Web Application (`app.py`)

Flask-based web server providing:

- **Main interface** at `/` - Web form for entering metrics
- **API endpoint** at `/api/calculate` - POST metrics, get sizing JSON
- **Example data** at `/api/example` - Pre-loaded sample scenario
- **RESTful design** - Can be used programmatically or via UI

### 3. User Interface

#### HTML Template (`templates/index.html`)
- Responsive form with sections for all AAP components
- "Load Example Data" button for quick testing
- Real-time calculation and results display
- Professional, clean design

#### CSS Styling (`static/css/style.css`)
- Red Hat color scheme (Red #ee0000, Purple gradient)
- Responsive grid layouts
- Component cards with clear visual hierarchy
- Mobile-friendly design

#### JavaScript (`static/js/app.js`)
- Form submission handling
- API communication
- Dynamic results rendering
- Example data loading

### 4. Documentation

#### README.md
- Complete usage guide
- Installation instructions
- API documentation
- Methodology explanation
- Based on Red Hat official docs

#### QUICKSTART.md
- Step-by-step quick start
- Example walkthrough
- Troubleshooting tips
- Next steps guidance

### 5. Supporting Files

- **requirements.txt**: Python dependencies (Flask, gunicorn, PyYAML)
- **run.sh**: One-command startup script
- **.gitignore**: Excludes Python cache, IDE files, etc.
- **docs/extracted-sizing-data.md**: All sizing specs extracted from Red Hat PDFs

## Based on Official Red Hat Documentation

All calculations derive from:

1. **Planning your Installation** (AAP 2.6)
2. **Performance Tuning** (AAP 2.6)
3. **Containerized Installation** (AAP 2.6)

### Reference Workloads Used

**Growth Topology**:
- 8 RPS, 1K hosts, 20 jobs/sec, 10K events/sec
- 30-day retention, 500 jobs/day

**Enterprise Topology**:
- 16 RPS, 10K hosts, 80 jobs/sec, 40K events/sec
- 7-day retention, 2000 jobs/day

## Example Calculation

### Input (Your AAP 2.4 Environment)
```
Controllers: 12 nodes (35% avg CPU, 50% peak, 20% memory)
Execution Nodes: 30 nodes (90% CPU, 50% memory, 165 forks)
Database: 16 vCPU, 128GB RAM (90% CPU, 35% memory)
Automation Hub: 2 nodes (25% CPU, 30% memory)

Workload:
- 70,000 playbooks/day
- 500 concurrent jobs
- 40,000 managed hosts
- 48-hour job retention
- 200GB/day database growth
```

### Output (AAP 2.6 Container Recommendation)
```
Topology: Enterprise

Summary:
- Total CPU: 115 vCPU
- Total Memory: 440 GB RAM
- Total Storage: 540 GB
- Total Pods: 32 containers

Components:
- Gateway: 3 pods (2 vCPU, 4GB each)
- Controller Control: 8 pods (4 vCPU, 16GB each)
- Controller Execution: 11 pods (4 vCPU, 16GB each)
- Database: 19 vCPU, 68GB RAM, 540GB storage
- Automation Hub: 2 pods (2 vCPU, 8GB each)
- Event-Driven Ansible: 2 pods (2 vCPU, 8GB each)
- Redis Cluster: 6 nodes (1 vCPU, 4GB each)

Notes:
- All values include 30-50% headroom
- Minimum 2 replicas for HA
- Separate PostgreSQL instances recommended
- Monitor and adjust post-migration
```

## Key Features

### Smart Workload Analysis
- Scores against 3 dimensions: job volume, concurrency, scale
- Auto-selects Growth vs Enterprise topology
- Considers current utilization patterns

### Component-Aware Sizing
Each component sized independently based on:
- Current resource usage
- Peak vs average loads
- Workload characteristics
- Red Hat best practices

### Container Efficiency
- Assumes 20-30% efficiency gain vs VMs
- Horizontal scaling (add pods, not resize)
- Resource requests = limits (avoid throttling)

### Database Intelligence
- Calculates storage: Event_Size × Events × Jobs × Retention
- Includes daily growth projection
- Recommends separation at scale

### HA by Default
- Minimum 2 replicas all services
- Clustered Redis for Enterprise
- Load balancer considerations

## How to Use

### Quick Start
```bash
./run.sh
# Open http://localhost:5000
# Click "Load Example Data"
# Click "Calculate Sizing"
```

### Programmatic Usage
```python
from sizing_calculator import AAP26SizingCalculator

calc = AAP26SizingCalculator()
result = calc.generate_sizing_recommendation(your_metrics)
```

### API Usage
```bash
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d @metrics.json
```

## Project Structure

```
aap-sizing-guide/
├── sizing_calculator.py       # Core calculation logic
├── app.py                      # Flask web application
├── requirements.txt            # Python dependencies
├── run.sh                      # Startup script
├── README.md                   # Full documentation
├── QUICKSTART.md              # Quick start guide
├── PROJECT_SUMMARY.md         # This file
├── .gitignore                 # Git ignore rules
│
├── templates/
│   └── index.html             # Web UI
│
├── static/
│   ├── css/
│   │   └── style.css          # Styling
│   └── js/
│       └── app.js             # Client-side logic
│
└── docs/
    ├── extracted-sizing-data.md  # Sizing specs from Red Hat
    └── *.pdf                      # Original Red Hat docs
```

## Technology Stack

- **Backend**: Python 3.8+, Flask
- **Frontend**: HTML5, CSS3 (Grid/Flexbox), Vanilla JavaScript
- **Styling**: Custom CSS with Red Hat color scheme
- **Dependencies**: Flask, gunicorn, PyYAML

## Calculation Methodology

### 1. Topology Selection
```
Score = 0
If jobs/day > 20K: score += 3
If concurrent > 200: score += 3
If hosts > 20K: score += 3

If score >= 5: Enterprise
Elif score >= 3: Enterprise Recommended
Else: Growth
```

### 2. CPU Sizing
```
Total Needed = Current_Nodes × vCPU × (Peak% / 100) × 1.3
Pods = ceil(Total Needed / vCPU_per_pod)
```

### 3. Memory Sizing
```
Total Needed = Current_Nodes × RAM × (Used% / 100) × 1.5
RAM per pod adjusted accordingly
```

### 4. Database Storage
```
Storage = 2KB × 500_events × Jobs_per_day × Retention_days
Storage += Daily_growth × Retention_days × 1.2
```

## Validation Against Red Hat Specs

All calculations validated against:
- ✅ Minimum system requirements (16-32GB RAM, 4 CPU, 60GB disk)
- ✅ Growth topology limits (1K hosts, 20 jobs/sec)
- ✅ Enterprise topology capacity (10K hosts, 80 jobs/sec)
- ✅ Resource headroom recommendations (30-50%)
- ✅ HA requirements (min 2 replicas)
- ✅ Database sizing formulas
- ✅ Redis standalone vs clustered guidance

## Benefits of This Tool

1. **Accurate Planning**: Based on real utilization, not guesswork
2. **Red Hat Validated**: Uses official reference architectures
3. **Component Breakdown**: Understand each service's needs
4. **Migration Guidance**: Notes and best practices included
5. **HA Built-in**: Automatic consideration of redundancy
6. **Easy to Use**: Web UI + API + CLI options
7. **Extensible**: Python module can be integrated into other tools

## Limitations & Disclaimers

- **Estimates only**: Actual needs vary by playbook complexity
- **Simplified network**: Doesn't deeply model mesh hop nodes
- **No custom plugins**: Assumes standard AAP components
- **Point-in-time**: Based on current usage, not future unknowns
- **Not official Red Hat tool**: For planning only, validate with Red Hat

## Next Steps for Users

1. ✅ Collect current AAP 2.4 metrics (2-4 weeks)
2. ✅ Run this calculator
3. ✅ Review and export results
4. Contact Red Hat support for validation
5. Deploy to test environment
6. Monitor actual usage
7. Tune resources based on real data
8. Plan production migration

## Maintenance & Updates

To update calculations for new AAP versions:
1. Update reference workloads in `AAP26SizingCalculator` class
2. Adjust `BASE_RESOURCES` if minimums change
3. Update topology thresholds if Red Hat guidance changes
4. Re-extract sizing data from new documentation PDFs

## Success Metrics

This tool successfully:
- ✅ Processes AAP 2.4 metrics
- ✅ Calculates AAP 2.6 container sizing
- ✅ Recommends appropriate topology
- ✅ Provides component breakdown
- ✅ Includes deployment notes
- ✅ Offers web UI and API access
- ✅ Based on official Red Hat documentation

## License & Support

- **Tool**: Provided as-is for planning
- **Documentation**: Based on Red Hat AAP 2.6 official docs
- **Support**: Use Red Hat support for production deployment validation

---

**Version**: 1.0
**Last Updated**: March 2026
**AAP Versions**: 2.4 (source) → 2.6 (target)
