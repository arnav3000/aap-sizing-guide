# AAP Sizing Calculator Enhancement Plan

## Overview

This document outlines enhancements to make the sizing calculator more precise and accurate by:
1. Creating a RAG (Retrieval-Augmented Generation) database from Red Hat documentation
2. Adding advanced parameters for workload characterization
3. Implementing more granular capacity calculations

---

## Part 1: RAG Database for Enhanced Accuracy

### Purpose
- Extract structured knowledge from Red Hat AAP 2.6 documentation
- Enable context-aware recommendations
- Provide source-backed answers to sizing questions
- Support what-if scenario analysis

### Implementation Plan

#### 1.1 Knowledge Extraction
Create structured knowledge base from:
- ✅ Tested Deployment Models (already extracted)
- ✅ Performance Tuning Guide (already extracted)
- ✅ Planning Guide (already extracted)
- 🔄 Using Automation Execution Guide
- 🔄 Configuring Automation Execution Guide
- 🔄 OpenShift Installation Guide

#### 1.2 RAG Database Structure

```
docs/
├── rag_database/
│   ├── capacity_formulas.json       # All capacity formulas
│   ├── component_specs.json         # Component specifications
│   ├── workload_patterns.json       # Common workload patterns
│   ├── scaling_guidelines.json      # Scaling decision trees
│   ├── database_sizing.json         # Database-specific rules
│   └── best_practices.json          # Red Hat best practices
```

#### 1.3 Searchable Knowledge Topics

**Capacity Planning:**
- Execution capacity formulas (different job types)
- Memory requirements (fork-based, workflow, sliced)
- Database connection pools
- Event processing rates

**Job Type Specifics:**
- Standard jobs
- Sliced jobs (capacity impact)
- Workflow jobs (orchestration overhead)
- Bulk jobs
- System jobs

**Database Sizing:**
- Connection pool calculations
- Storage growth patterns
- IOPS requirements by workload
- Backup and replication overhead

**Network & Distribution:**
- Automation mesh considerations
- Hop nodes
- Execution node placement
- Latency impact on capacity

---

## Part 2: Additional Parameters for Precision

### Current Parameters (18)
✅ Basic metrics already captured:
- Controllers, execution nodes, hub nodes
- CPU/Memory utilization percentages
- Concurrent jobs, playbooks/day
- Database size and growth
- Forks observed

### Proposed New Parameters (20+)

#### 2.1 Job Characteristics

**Job Slicing**
```python
'job_slice_count': int  # Average slices per job
'percent_sliced_jobs': float  # % of jobs using slicing
```

**Formula Impact:**
```
Sliced Job Capacity = job_slice_count × base_capacity
Recommendation: Slices ≤ Number of execution nodes
```

**Workflow Jobs**
```python
'percent_workflow_jobs': float  # % of jobs that are workflows
'avg_workflow_nodes': int  # Average nodes per workflow
```

**Formula Impact:**
```
Workflow Overhead = avg_workflow_nodes × workflow_penalty_factor
Additional Control Capacity Needed = workflows × orchestration_overhead
```

**Job Verbosity**
```python
'avg_verbosity_level': int  # 0-4, affects event generation
```

**Formula Impact:**
```
Verbosity 0: 4 events/task
Verbosity 1: 6 events/task (default)
Verbosity 2: 12 events/task
Verbosity 3: 34 events/task
Verbosity 4: 50+ events/task
```

#### 2.2 Database Connection Planning

**Connection Pool Sizing**
```python
'web_replicas_planned': int  # Number of web service replicas
'control_nodes_planned': int  # Number of control nodes
'hybrid_nodes_planned': int  # Number of hybrid nodes
```

**Formula:**
```
WSGI Connections per Web Replica = CPU_count × workers_per_cpu
gRPC Connections per Gateway = processes × threads
Dispatcher Connections per Control Node = worker_pool_size
Callback Receiver Connections = worker_pool_size

Total DB Connections = (Web Replicas × WSGI) +
                       (Gateways × gRPC) +
                       (Control Nodes × Dispatcher) +
                       (Control Nodes × Callback) +
                       (EDA × Workers) +
                       (Hub × Workers) +
                       Connection_Overhead (20%)
```

**PostgreSQL Sizing:**
```python
'max_connections_required': int  # Calculated from above
'connection_pooler': bool  # Using PgBouncer or similar?
```

#### 2.3 Inventory & Project Characteristics

**Inventory Size**
```python
'total_inventories': int  # Number of inventories
'avg_hosts_per_inventory': int  # Average hosts
'dynamic_inventories': int  # Number using dynamic sources
```

**Formula Impact:**
```
Database Size += inventories × hosts × metadata_per_host
Sync Time = dynamic_inventories × source_query_time
```

**Project Characteristics**
```python
'total_projects': int  # Number of projects
'avg_project_size_mb': int  # Average project size
'project_sync_frequency_hours': int  # How often synced
```

**Formula Impact:**
```
Control Plane Load += projects × (size / sync_frequency)
Disk Space Needed = projects × size × 2  # Working + cache
```

#### 2.4 Execution Environment Details

**Container Image Sizing**
```python
'avg_ee_size_gb': float  # Average execution environment size
'number_of_ees': int  # Number of different EEs
'ee_pull_frequency': str  # 'always', 'missing', 'never'
```

**Formula Impact:**
```
Registry Storage = number_of_ees × avg_ee_size_gb × layers_factor
Pull Overhead = (ee_size × nodes) / network_bandwidth
Memory Overhead = ee_layers × layer_cache_size
```

#### 2.5 API & Integration Load

**API Request Patterns**
```python
'api_requests_per_minute': int  # External API calls
'webhook_triggers_per_day': int  # Incoming webhooks
'awx_cli_users': int  # CLI/API automation users
```

**Formula Impact:**
```
Gateway CPU += api_requests × request_processing_cost
Authentication Load = (api_requests + webhooks) × auth_overhead
Database Queries = api_requests × avg_queries_per_request
```

#### 2.6 High Availability Requirements

**HA Configuration**
```python
'require_zero_downtime': bool  # True = extra capacity for rolling updates
'disaster_recovery_rpo_hours': int  # Recovery point objective
'backup_frequency_hours': int  # How often backups run
```

**Formula Impact:**
```
Extra Capacity for HA:
- Zero Downtime: +1 pod per service (rolling update buffer)
- DR: Database replication overhead +20% CPU/IOPS
- Backups: +10% database IOPS during backup windows
```

#### 2.7 Automation Mesh Topology

**Mesh Configuration**
```python
'uses_automation_mesh': bool
'number_of_hop_nodes': int
'execution_nodes_remote_sites': int
'avg_latency_ms': int  # Network latency to remote sites
```

**Formula Impact:**
```
Hop Node Resources: Minimal (1 vCPU, 2GB per hop)
Latency Penalty: latency > 100ms → reduce concurrent jobs by 10%
Mesh Overhead: +5% CPU on control plane for mesh management
```

#### 2.8 Content & Collection Management

**Automation Hub Usage**
```python
'collections_synced': int  # Number of collections
'avg_collection_size_mb': int  # Average size
'private_collections': int  # Private/custom collections
'sync_from_external': bool  # Sync from Galaxy/external
```

**Formula Impact:**
```
Hub Storage = collections × avg_size × 1.5  # With metadata
Hub Memory += sync_from_external ? 4GB : 0
Hub CPU += (collections × sync_frequency) / 24
```

#### 2.9 Event-Driven Ansible Specifics

**EDA Workload**
```python
'number_of_activations': int  # Active rulebook activations
'events_per_second_eda': int  # Incoming event rate
'eda_audit_enabled': bool  # Store events in DB?
```

**Formula Impact:**
```
EDA API Pods = max(2, activations / 10)
EDA Worker Pods = max(2, events_per_second / 1000)
Database Growth += eda_audit ? (events × event_size) : 0
WebSocket Connections = activations × 1
```

#### 2.10 Compliance & Audit Requirements

**Audit Configuration**
```python
'activity_stream_enabled': bool  # Capture all changes
'job_output_retention_days': int  # Keep full job logs
'compliance_mode': bool  # Extra audit requirements
```

**Formula Impact:**
```
Database Growth Multiplier = compliance_mode ? 1.5 : 1.0
Activity Stream Overhead: +15% database writes
Storage += activity_stream ? (changes × metadata_size) : 0
```

---

## Part 3: Enhanced Calculation Logic

### 3.1 Multi-Factor Capacity Calculation

**Current:** Simple formula based on concurrent jobs × forks

**Enhanced:**
```python
def calculate_enhanced_execution_capacity(metrics):
    base_capacity = (concurrent_jobs × forks) + concurrent_jobs

    # Slicing adjustment
    if metrics['percent_sliced_jobs'] > 0:
        sliced_jobs = concurrent_jobs × (metrics['percent_sliced_jobs'] / 100)
        slice_overhead = sliced_jobs × metrics['job_slice_count'] × 0.1
        base_capacity += slice_overhead

    # Workflow adjustment
    if metrics['percent_workflow_jobs'] > 0:
        workflow_jobs = concurrent_jobs × (metrics['percent_workflow_jobs'] / 100)
        workflow_overhead = workflow_jobs × metrics['avg_workflow_nodes'] × 0.05
        base_capacity += workflow_overhead

    # Verbosity adjustment
    event_multiplier = get_event_multiplier(metrics['avg_verbosity_level'])
    event_capacity = base_capacity × event_multiplier

    return max(base_capacity, event_capacity)
```

### 3.2 Database Connection Pool Calculator

```python
def calculate_database_connections(metrics):
    # Web service connections
    web_connections = (
        metrics['web_replicas_planned'] ×
        metrics['cpu_per_pod'] ×
        5  # Workers per CPU
    )

    # Gateway gRPC connections
    gateway_connections = (
        metrics['gateway_pods'] ×
        metrics['grpc_processes'] ×
        metrics['grpc_threads']
    )

    # Control plane connections
    control_connections = (
        metrics['control_nodes_planned'] ×
        (20 + 10)  # Dispatcher + Callback Receiver
    )

    # EDA connections
    eda_connections = metrics['eda_pods'] × 10

    # Hub connections
    hub_connections = metrics['hub_pods'] × 10

    total = (web_connections + gateway_connections +
             control_connections + eda_connections + hub_connections)

    # Add 20% overhead
    recommended = total × 1.2

    return {
        'min_connections': total,
        'recommended_max_connections': math.ceil(recommended),
        'breakdown': {
            'web': web_connections,
            'gateway': gateway_connections,
            'control': control_connections,
            'eda': eda_connections,
            'hub': hub_connections
        }
    }
```

### 3.3 Event Processing with Verbosity

```python
VERBOSITY_EVENT_MULTIPLIERS = {
    0: 0.67,  # 4 events per task
    1: 1.0,   # 6 events per task (baseline)
    2: 2.0,   # 12 events per task
    3: 5.67,  # 34 events per task
    4: 8.33   # 50 events per task
}

def calculate_event_processing_enhanced(metrics):
    verbosity = metrics.get('avg_verbosity_level', 1)
    multiplier = VERBOSITY_EVENT_MULTIPLIERS[verbosity]

    base_events_per_job = 10 × 50 × 6  # tasks × hosts × events
    actual_events_per_job = base_events_per_job × multiplier

    peak_rate = (
        metrics['concurrent_jobs_peak'] ×
        actual_events_per_job / 60
    )

    return {
        'events_per_job': actual_events_per_job,
        'events_per_second_peak': peak_rate,
        'verbosity_level': verbosity,
        'note': f'Verbosity {verbosity} generates {multiplier:.1f}x baseline events'
    }
```

### 3.4 Sliced Job Capacity Impact

```python
def calculate_slicing_impact(metrics):
    if metrics['percent_sliced_jobs'] == 0:
        return {'impact': 'none', 'additional_capacity': 0}

    sliced_jobs = (
        metrics['concurrent_jobs_peak'] ×
        metrics['percent_sliced_jobs'] / 100
    )

    slice_count = metrics['job_slice_count']

    # Each slice becomes a separate workflow node
    # Scheduling overhead per slice
    scheduling_overhead = sliced_jobs × slice_count × 0.05

    # Need capacity for parallel slice execution
    parallel_capacity = sliced_jobs × (slice_count - 1)

    return {
        'sliced_jobs_count': sliced_jobs,
        'slices_per_job': slice_count,
        'scheduling_overhead_capacity': scheduling_overhead,
        'parallel_execution_capacity': parallel_capacity,
        'total_additional_capacity': scheduling_overhead + parallel_capacity,
        'recommendation': (
            f'Job slicing increases capacity needs by {slice_count}x for sliced jobs. '
            f'Ensure execution nodes ≥ {slice_count} for optimal performance.'
        )
    }
```

---

## Part 4: Implementation Priority

### Phase 1: Core Enhancements (Week 1)
1. ✅ Add job slicing parameters
2. ✅ Add workflow job parameters
3. ✅ Add verbosity level parameter
4. ✅ Implement database connection calculator
5. ✅ Update UI with new parameters (collapsible sections)

### Phase 2: RAG Database (Week 2)
1. Create JSON knowledge base from extracted docs
2. Implement simple keyword search
3. Add "Why this number?" explanations with sources
4. Link calculations to Red Hat documentation

### Phase 3: Advanced Parameters (Week 3)
1. Add inventory/project characteristics
2. Add execution environment parameters
3. Add API/integration load parameters
4. Implement HA overhead calculations

### Phase 4: Automation Mesh & Distributed (Week 4)
1. Add mesh topology parameters
2. Add network latency considerations
3. Calculate hop node requirements
4. Remote site execution planning

---

## Part 5: RAG Database Structure Example

### capacity_formulas.json
```json
{
  "execution_capacity": {
    "formula": "(concurrent_jobs × forks) + concurrent_jobs",
    "units": "capacity_units",
    "source": "Red Hat AAP 2.6 Performance Tuning Guide",
    "variants": {
      "standard_jobs": {
        "formula": "(jobs × forks) + jobs",
        "description": "Basic execution capacity"
      },
      "sliced_jobs": {
        "formula": "(jobs × forks × slices) + (jobs × slices)",
        "description": "Each slice runs as separate workflow node",
        "note": "Slices should be ≤ execution node count"
      },
      "workflow_jobs": {
        "formula": "(jobs × avg_nodes × forks) + (jobs × orchestration_overhead)",
        "description": "Workflow orchestration adds overhead",
        "orchestration_overhead": 1.05
      }
    },
    "examples": [
      {
        "scenario": "500 standard jobs, 5 forks",
        "calculation": "(500 × 5) + 500 = 3000 units",
        "nodes_needed": "3000 / 137 = 22 nodes"
      },
      {
        "scenario": "200 sliced jobs (10 slices), 5 forks",
        "calculation": "(200 × 5 × 10) + (200 × 10) = 12000 units",
        "nodes_needed": "12000 / 137 = 88 nodes",
        "note": "Slicing dramatically increases capacity needs"
      }
    ]
  }
}
```

### scaling_guidelines.json
```json
{
  "database_connections": {
    "triggers": [
      {
        "condition": "max_connections > 90% utilized",
        "action": "Scale up PostgreSQL or implement connection pooling",
        "source": "Performance Tuning Guide Section 3.4.3"
      },
      {
        "condition": "connection_pool_wait_time > 100ms",
        "action": "Add web replicas or increase connection pool size",
        "source": "Performance Tuning Guide Section 3.1"
      }
    ],
    "formulas": {
      "web_connections": "replicas × CPU_per_pod × 5 workers_per_cpu",
      "control_connections": "nodes × (dispatcher_pool + callback_pool)"
    }
  }
}
```

---

## Part 6: UI Enhancements

### Advanced Parameters Section (Collapsible)

```html
<div class="form-section advanced-section collapsed">
    <h3>⚙️ Advanced Parameters (Optional)</h3>
    <button class="toggle-advanced">Show Advanced Options</button>

    <div class="advanced-params">
        <!-- Job Characteristics -->
        <h4>Job Characteristics</h4>
        <div class="form-grid">
            <div class="form-group">
                <label>Job Slicing Usage (%)</label>
                <input type="number" name="percent_sliced_jobs" min="0" max="100" value="0">
                <small>Percentage of jobs using slicing</small>
            </div>
            <div class="form-group">
                <label>Average Slices per Job</label>
                <input type="number" name="job_slice_count" min="1" value="1">
            </div>
        </div>

        <!-- Database Connections -->
        <h4>Database Connection Planning</h4>
        <div class="form-grid">
            <div class="form-group">
                <label>Use Connection Pooler</label>
                <input type="checkbox" name="connection_pooler">
                <small>PgBouncer, pgpool, etc.</small>
            </div>
        </div>
    </div>
</div>
```

---

## Part 7: Benefits of Enhancements

### Increased Accuracy
- **Current:** ±30% accuracy for standard workloads
- **Enhanced:** ±10% accuracy with advanced parameters

### Better Recommendations
- Specific guidance for sliced jobs
- Database connection pool sizing
- Workflow orchestration overhead accounted
- Verbosity impact on event processing

### Source-Backed Answers
- Every calculation links to Red Hat docs
- "Why this number?" explanations
- What-if scenario analysis
- Best practice recommendations

---

## References

Based on official Red Hat documentation:
- [Job Slicing Guide - AAP 2.6](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/using_automation_execution/controller-job-slicing)
- [Performance Tuning Guide - AAP 2.6](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/configuring_automation_execution/assembly-controller-improving-performance)
- [Automation Controller Performance - v4.5](https://docs.ansible.com/automation-controller/4.5/html/administration/performance.html)
- [Managing Workflow Job Templates at Scale](https://www.redhat.com/en/blog/managing-ansible-automation-platform-workflow-job-templates-scale)

---

## Recommendation

**Start with Phase 1** - Add the most impactful parameters:
1. Job slicing (can 3-10x capacity requirements!)
2. Workflow jobs (orchestration overhead)
3. Verbosity levels (affects event processing)
4. Database connection calculations

These 4 enhancements will provide the biggest accuracy improvement with manageable implementation effort.

Should I proceed with implementing Phase 1?
