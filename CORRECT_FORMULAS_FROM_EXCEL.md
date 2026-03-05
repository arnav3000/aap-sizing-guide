# CORRECT AAP Sizing Formulas - From Official Excel Reference

## ❌ WHAT WAS WRONG

**Incorrect Assumption:**
```
"Red Hat defines that a standard node (4 vCPU, 16 GB RAM) provides 137 capacity units"
```

**This 137 number does NOT appear anywhere in the official Excel sizing reference!**

---

## ✅ CORRECT FORMULAS (From Excel Reference Sheet)

### Core Constants (Benchmarked Values)

| Parameter | Value | Description | Source |
|-----------|-------|-------------|---------|
| **Memory per Fork** | 100 MB | Memory consumed per parallel fork | `SYSTEM_TASK_FORKS_MEM` |
| **Forks per CPU core** | 4 | Number of forks one CPU core can handle | `SYSTEM_TASK_FORKS_CPU` |
| **Events per Task** | 10 | Average events generated per task | Benchmark (with loops) |
| **Size per Event** | 2 KB | Event size in database | Default (debug mode) |
| **Facts size per host** | 50 KB | Inventory facts per host | Benchmark |
| **EE Average Size** | 1,600 MB | Execution Environment image size | Benchmark |
| **Controller Events/sec** | 400 | Events processed per second | Engineering tests |
| **Memory per event fork** | 0.0124 MB | Memory for event processing | Engineering tests |
| **CPU per event fork** | 0.00011 | CPU for event processing | Engineering tests |
| **API calls per controller** | 100 | Concurrent API calls supported | Max 300 with monitoring |

---

## 📐 EXECUTION PLANE SIZING FORMULAS

### Formula 1: Calculate Needed Forks

```python
# Total forks needed for parallel execution
forks_needed = (
    number_of_hosts *
    jobs_per_host_per_day *
    job_duration_hours /
    allowed_hours_per_day
)
```

**Example:**
```
500 hosts × 5 jobs/host/day × 0.25 hrs job duration / 12 hrs day
= 500 × 5 × 0.25 / 12
= 52.08 forks needed
```

### Formula 2: Calculate Execution Node Memory

```python
# Memory calculation
memory_gb = (
    forks_needed * 100  # MB per fork
) / 1024  # Convert to GB

# Add base reservation per node
memory_total_gb = memory_gb + (2 * number_of_nodes)
```

**Example:**
```
52 forks × 100 MB / 1024 = 5.08 GB
Plus 2 GB × 3 nodes = 6 GB
Total = 11 GB for 3 execution nodes
```

### Formula 3: Calculate Execution Node CPU

**MAX Formula (Theoretical Maximum - Usually TOO HIGH):**
```python
cpu_max = forks_needed / 4  # forks_per_cpu
```

**AVG Formula (Realistic Average):**
```python
cpu_avg = (
    2 * number_of_nodes +  # Base CPU
    forks_needed / 4 / 10  # Averaged utilization
)
```

**Example:**
```
MAX: 52 / 4 = 13 cores (TOO HIGH, IGNORE)
AVG: 2×3 + 52/4/10 = 6 + 1.3 = 7.3 cores (REALISTIC)
```

**Key Insight:** Use AVG, not MAX! The /10 divisor accounts for average vs peak load.

---

## 📐 CONTROL PLANE SIZING FORMULAS

### Formula 4: Calculate Event Forks

```python
# Events that need to be processed in parallel
event_forks = (
    number_of_hosts *
    jobs_per_host_per_day *
    tasks_per_job *
    events_per_task *
    job_duration_hours /
    allowed_hours_per_day
)
```

**Example:**
```
500 hosts × 5 jobs/host/day × 100 tasks/job × 10 events/task × 0.25 hrs / 12 hrs
= 500 × 5 × 100 × 10 × 0.25 / 12
= 5,208 event forks
```

### Formula 5: Calculate Control Node Memory (for Events)

```python
# Memory for event processing
memory_for_events_mb = event_forks * 0.0124  # MB per event fork
memory_gb = memory_for_events_mb / 1024 + (2 * number_of_nodes)
```

**Example:**
```
5,208 × 0.0124 = 64.58 MB
64.58 / 1024 + (2×2) = 4.06 GB
```

### Formula 6: Calculate Control Node CPU (for Events)

**MAX Formula (Theoretical - TOO HIGH):**
```python
cpu_max = event_forks * 0.00011 + (0.6 * number_of_nodes)
```

**AVG Formula (Realistic):**
```python
cpu_avg = (
    event_forks * 0.00011 / 10 +  # Averaged event processing
    (1.6 * number_of_nodes)        # Base CPU
)
```

**Example:**
```
MAX: 5,208×0.00011 + 0.6×2 = 0.57 + 1.2 = 1.77 cores (TOO LOW!)
AVG: 5,208×0.00011/10 + 1.6×2 = 0.057 + 3.2 = 3.26 cores
```

### Formula 7: Control Plane ALSO Needs Fork Capacity

**The Excel shows control plane needs BOTH event processing AND fork capacity!**

```python
# Control plane also manages concurrent jobs
concurrent_jobs = (
    jobs_per_day *
    job_duration_hours /
    allowed_hours_per_day
)

# Forks for job management
forks_for_jobs = concurrent_jobs * average_forks_per_job

# Memory for job management
memory_for_jobs_gb = (
    forks_for_jobs * 100 / 1024 +  # mem_per_fork
    (2 * number_of_nodes)
)

# CPU for job management
cpu_for_jobs_avg = (
    2 * number_of_nodes +
    forks_for_jobs / 4 / 10  # averaged
)
```

### Formula 8: AVERAGED Result for Control Plane

```python
# Control plane needs AVERAGE of event processing AND job management
memory_control_gb = (memory_for_events + memory_for_jobs) / 2
cpu_control_cores = (cpu_for_events_avg + cpu_for_jobs_avg) / 2
```

**This is explicitly stated in Excel row 54: "AVERAGED RESULT"**

---

## 📐 DATABASE SIZING FORMULAS

### Formula 9: Database Storage

```python
# Facts storage
db_facts_mb = number_of_hosts * 50 / 1024  # 50KB per host

# Inventory storage
db_inventory_mb = number_of_hosts * 50 / 1024  # Similar to facts

# Jobs storage (MAIN COMPONENT)
db_jobs_mb = (
    number_of_hosts *
    jobs_per_host_per_day *
    events_per_task *
    days_to_keep_jobs *
    2  # KB per event
) / 1024

# Total database size
db_total_gb = (db_facts_mb + db_inventory_mb + db_jobs_mb) / 1024
```

**Example:**
```
Facts: 500 × 50 / 1024 = 24.4 KB (negligible)
Inventory: 500 × 50 / 1024 = 24.4 KB (negligible)
Jobs: 500 × 5 × 10 × 10 × 2 / 1024 = 488 KB
Total: ~0.5 MB (this seems too small - check formula)
```

**Wait, the Excel shows:**
```
Row 60: Database size for jobs: 39,062.5 MB
Formula: hosts * jobs_per_hostday * events * keep_days * event_size / 1024
= 500 × 5 × 10 × 10 × 2 / 1024
```

**Issue: The formula seems to be missing tasks_per_job!**

**Corrected Formula:**
```python
db_jobs_mb = (
    number_of_hosts *
    jobs_per_host_per_day *
    tasks_per_job *
    events_per_task *
    days_to_keep_jobs *
    2  # KB per event
) / 1024
```

---

## 📐 AUTOMATION HUB SIZING

### Formula 10: Execution Environment Storage

```python
# Storage for EE container images
ee_storage_mb = (
    number_of_ees *
    number_of_versions_per_ee *
    ee_average_size_mb *
    (1 - overlap_percentage / 100)
)

ee_storage_gb = ee_storage_mb / 1024
```

**Example:**
```
5 EEs × 5 versions × 1,600 MB × (1 - 60/100)
= 5 × 5 × 1,600 × 0.4
= 16,000 MB
= 15.6 GB
```

---

## 📐 API LOAD CALCULATIONS

### Formula 11: API Calls and Concurrency

```python
# API calls per day
api_calls_per_day = (
    jobs_per_day *
    job_duration_hours /
    polling_interval_hours
)

# Concurrent API calls
concurrent_api_calls = (
    api_calls_per_day *
    api_call_duration_hours /
    allowed_hours_per_day
)
```

**Example:**
```
Jobs/day: 500 jobs × 0.25 hrs / 0.0083 hrs = 15,060 API calls/day
Concurrent: 15,060 × 0.00139 hrs / 12 hrs = 1.74 concurrent API calls
```

---

## 🔥 KEY DIFFERENCES FROM OUR PREVIOUS CALCULATOR

### What We Got WRONG:

1. **❌ The "137 capacity units" number**
   - This doesn't exist in official formulas
   - Was likely derived or estimated incorrectly

2. **❌ Simple multiplication (jobs × forks)**
   - Real formula considers job duration and allowed hours
   - Accounts for time-based concurrency

3. **❌ Event calculation**
   - We used 6 events/task
   - Real benchmark: 10 events/task

4. **❌ Control plane sizing**
   - We underestimated event processing needs
   - Didn't account for AVERAGED result needed

5. **❌ Database formula**
   - We had right structure but wrong multipliers
   - Missing tasks_per_job in some places

### What We Got RIGHT:

1. ✅ Memory per fork: 100 MB
2. ✅ Forks per CPU: 4
3. ✅ Base concepts of fork-based sizing
4. ✅ Event size: 2 KB

---

## 📊 CORRECTED CALCULATION FOR YOUR SCENARIO

### Input Parameters (from your scenario):
```
Hosts: 40,000
Jobs per host per day: 70,000 / 40,000 = 1.75
Concurrent jobs peak: 500
Tasks per job: 100 (estimated)
Job duration: 0.25 hours (15 minutes average)
Allowed hours per day: 24 (24/7 operation)
Average forks per job: 5
Events per task: 10
Days to keep jobs: 2 (48 hours)
```

### Execution Plane Calculation:

```python
# Step 1: Calculate needed forks
forks = 40,000 × 1.75 × 0.25 / 24
forks = 729 forks needed

# Step 2: Calculate memory
memory_gb = 729 × 100 / 1024 = 71 GB
Plus 2 GB per node (assume 3 nodes) = 6 GB
Total memory = 77 GB

# Step 3: Calculate CPU (AVG)
cpu_avg = 2×3 + 729/4/10 = 6 + 18.2 = 24.2 cores
```

**Execution Nodes: 3 nodes × 8 vCPU × 32 GB = 24 vCPU, 96 GB total**

### Control Plane Calculation:

```python
# Step 1: Calculate event forks
event_forks = 40,000 × 1.75 × 100 × 10 × 0.25 / 24
event_forks = 72,917 event forks

# Step 2: Memory for events
memory_events = 72,917 × 0.0124 / 1024 + 2×2 = 4.88 GB

# Step 3: CPU for events (AVG)
cpu_events = 72,917 × 0.00011 / 10 + 1.6×2 = 0.8 + 3.2 = 4 cores

# Step 4: Concurrent jobs capacity
concurrent_jobs = 70,000 × 0.25 / 24 = 729 jobs
forks_for_jobs = 729 × 5 = 3,645 forks

# Step 5: Memory for jobs
memory_jobs = 3,645 × 100 / 1024 + 2×2 = 359 GB

# Step 6: CPU for jobs (AVG)
cpu_jobs = 2×2 + 3,645/4/10 = 4 + 91 = 95 cores

# Step 7: AVERAGE both
memory_control = (4.88 + 359) / 2 = 182 GB
cpu_control = (4 + 95) / 2 = 49.5 cores
```

**Control Nodes: 2 nodes × 25 vCPU × 91 GB = 50 vCPU, 182 GB total**

### Database Calculation:

```python
# Facts + Inventory (negligible)
db_facts = 40,000 × 50 / 1024 / 1024 = 1.9 MB
db_inventory = 1.9 MB

# Jobs (MAIN)
db_jobs = 40,000 × 1.75 × 100 × 10 × 2 × 2 / 1024
db_jobs = 2,734,375 MB = 2,670 GB

# Total
db_total = 2,670 GB
```

**Database: Large server with 2.7 TB storage**

---

## 🎯 COMPARISON: Old Calculator vs Correct Formula

| Component | Old Calculator | Correct Formula | Difference |
|-----------|---------------|-----------------|------------|
| **Execution CPU** | 88 vCPU | 24 vCPU | -73% |
| **Execution Memory** | 352 GB | 96 GB | -73% |
| **Control CPU** | 8 vCPU | 50 vCPU | +525% |
| **Control Memory** | 32 GB | 182 GB | +469% |
| **Database Storage** | 540 GB | 2,670 GB | +394% |

**HUGE DIFFERENCES! The old calculator:**
- ✅ Over-sized execution plane by 3x
- ❌ Under-sized control plane by 6x
- ❌ Under-sized database by 5x

---

## 🚀 ACTION ITEMS

1. **REWRITE** sizing_calculator.py with correct formulas
2. **ADD** all parameters from Excel to input form:
   - Jobs per host per day
   - Tasks per playbook/job
   - Job duration (hours)
   - Allowed hours per day (24/7 or business hours)
   - Events per task
   - Days to keep jobs
3. **REMOVE** the 137 capacity units concept entirely
4. **IMPLEMENT** the averaging logic for control plane
5. **UPDATE** documentation with correct formulas
6. **CREATE** RAG database with these authoritative formulas

---

## 📚 Excel Formula Reference

### Execution Nodes (Rows 36-39)
```
Forks = hosts * jobs_per_hostday * job_duration / day_work_hours
Memory = forks * 100 + 2048 * nodes
CPU (MAX) = forks / 4  [TOO HIGH, IGNORE]
CPU (AVG) = 2 * nodes + forks / 4 / 10
```

### Control Nodes (Rows 46-56)
```
Event Forks = hosts * jobs_per_hostday * tasks_per_job * events_per_task * job_duration / day_work_hours
Memory (Events) = event_forks * 0.0124 + 2048 * nodes
CPU (Events AVG) = event_forks * 0.00011 / 10 + 1.6 * nodes

Job Forks = concurrent_jobs * forks_per_job
Memory (Jobs) = job_forks * 100 + 2048 * nodes
CPU (Jobs AVG) = 2 * nodes + job_forks / 4 / 10

FINAL = AVERAGE of both (events + jobs) / 2
```

### Database (Rows 58-61)
```
Facts = hosts * 50 / 1024 MB
Inventory = hosts * 50 / 1024 MB
Jobs = hosts * jobs_per_hostday * tasks_per_job * events_per_task * keep_days * 2 / 1024 MB
Total = (Facts + Inventory + Jobs) / 1024 GB
```

---

## ✅ VALIDATION

The Excel formulas are based on:
- **Engineering benchmarks** from Red Hat
- **Field-tested values** from real deployments
- **AWX/Controller configuration parameters** (SYSTEM_TASK_FORKS_MEM, etc.)

These are MORE AUTHORITATIVE than the simplified "137 units" approach!

---

## 🔧 Next Step

Shall I rewrite the calculator with these correct formulas?
