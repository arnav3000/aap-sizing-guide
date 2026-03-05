# Quick Start Guide

## 1. Start the Application

### Option A: Using the run script (Recommended)
```bash
./run.sh
```

### Option B: Manual start
```bash
pip3 install -r requirements.txt
python3 app.py
```

## 2. Open in Browser

Navigate to: **http://localhost:5000**

## 3. Enter Your Metrics or Load Example

### Load Example Data
Click the **"Load Example Data"** button to populate the form with a realistic large-scale AAP 2.4 environment.

### Or Enter Your Own Metrics

Fill in the following sections:

#### Automation Controllers
- **Number of Controllers**: How many controller nodes in your current setup
- **CPU % (Average)**: Average CPU utilization (e.g., 35)
- **CPU % (Peak)**: Peak CPU utilization (e.g., 50)
- **Memory % (Used)**: Current memory usage percentage

#### Automation Hub
- **Number of Hub Nodes**: Count of automation hub instances
- **CPU/Memory %**: Current utilization metrics

#### Execution Nodes
- **Number of Execution Nodes**: Total execution node count
- **CPU/Memory %**: Current resource utilization
- **Forks Observed**: Typical fork count during peak times

#### Database
- **vCPU**: Number of virtual CPUs allocated
- **Memory (GB)**: RAM allocated to database
- **CPU/Memory %**: Current utilization percentages
- **Peak Concurrent DB Requests**: Maximum concurrent database connections
- **DB Growth per Day (GB)**: Daily database size increase

#### Workload Metrics
- **Playbooks/Day (Peak)**: Maximum playbooks executed per day
- **Concurrent Jobs (Peak)**: Maximum jobs running simultaneously
- **Job Retention (Hours)**: How long job data is kept
- **Managed Hosts**: Total number of servers managed by AAP

## 4. Calculate Sizing

Click **"Calculate Sizing"** button

## 5. Review Results

The calculator will show:

### Topology Recommendation
- **Growth** or **Enterprise** topology selection
- Explanation of what this means for your deployment

### Resource Summary
- **Total CPU**: Total vCPU cores needed
- **Total Memory**: Total RAM in GB
- **Storage**: Database storage requirements
- **Total Pods**: Number of container pods

### Component Breakdown
Detailed sizing for each component:
- Platform Gateway
- Automation Controller (Control & Execution)
- Database
- Automation Hub
- Event-Driven Ansible
- Redis Cache

### Deployment Notes
- Best practices
- Warnings about resource constraints
- Migration recommendations

## Example Results

Using the example data (70K playbooks/day, 40K hosts, 500 concurrent jobs), you should see:

```
Topology: Enterprise
Total CPU: ~115 vCPU
Total Memory: ~440 GB RAM
Total Storage: ~540 GB
Total Pods: ~32 containers
```

This represents approximately:
- **60% reduction in node count** (from 44 VMs to ~32 pods)
- **20-30% better efficiency** due to containerization
- **Horizontal scaling capability** across all components

## Next Steps

1. **Save/Export Results**: Screenshot or copy the recommendations
2. **Validate with Red Hat**: Contact Red Hat support for official validation
3. **Test in Non-Production**: Deploy to test environment first
4. **Monitor Actual Usage**: Track metrics for 2-4 weeks before migration
5. **Plan Migration**: Create migration plan based on recommendations

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, edit `app.py` and change:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Use different port
```

### Missing Dependencies
```bash
pip3 install flask gunicorn pyyaml
```

### Python Version Issues
Ensure Python 3.8+ is installed:
```bash
python3 --version
```

## Command Line Usage

For automated/scripted usage:

```python
from sizing_calculator import AAP26SizingCalculator
import json

calculator = AAP26SizingCalculator()

metrics = {
    'num_controllers': 12,
    'controller_cpu_percent_avg': 35,
    # ... other metrics
}

result = calculator.generate_sizing_recommendation(metrics)
print(json.dumps(result, indent=2))
```

## Understanding Your Results

### If you get "Growth Topology"
- Your workload fits within tested limits for smaller deployments
- You can deploy on fewer resources
- Suitable for development, test, or smaller production environments
- Can be migrated to Enterprise later if needed

### If you get "Enterprise Topology"
- Your workload requires production-grade architecture
- High availability is critical
- Independent scaling of components
- Multiple replicas for all services

### Resource Headroom
All calculations include:
- **30% CPU headroom** over peak usage
- **50% Memory headroom** over current usage
- **Minimum 2 replicas** for high availability

This ensures:
- Handle traffic spikes
- Allow for workload growth
- Maintain performance during pod failures/updates

## Support

For questions about:
- **This Tool**: See README.md
- **AAP 2.6 Official Documentation**: [Red Hat Docs](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/)
- **Production Deployment**: Contact Red Hat Support
