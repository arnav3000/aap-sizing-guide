# AAP 2.6 Sizing Information Extracted from Red Hat Documentation

## Document Sources
- Planning Guide: /tmp/planning.txt
- Performance Tuning Guide: /tmp/performance.txt
- Containerized Installation Guide: /tmp/containerized.txt

---

## 1. MINIMUM SYSTEM REQUIREMENTS (Containerized Installation)

### 1.1 Virtual Machine Requirements (Table 4.2)
From: Containerized Installation Guide, Section 4.2.2

| Requirement | Minimum | Notes |
|------------|---------|-------|
| **RAM** | 16 GB | 32 GB required for growth topology bundled installations with hub_seed_collections=true |
| **CPUs** | 4 | - |
| **Total Disk Space** | 60 GB | - |
| **Installation Directory** | 15 GB | If on dedicated partition |
| **Disk IOPS** | 3000 | - |
| **/var/tmp (online)** | 1 GB | - |
| **/var/tmp (offline/bundled)** | 3 GB | - |
| **Temp directory (offline/bundled)** | 10 GB | Defaults to /tmp |

### 1.2 Supported Operating Systems
- RHEL 9.x (all minor versions)
- RHEL 10.x or later minor versions

### 1.3 CPU Architecture Support
- x86_64
- AArch64
- s390x (IBM Z)
- ppc64le (IBM Power)

### 1.4 Database Requirements
- PostgreSQL 15
- International Components for Unicode (ICU) support required for external databases
- Minimum disk: 60 GB (as specified for Database node)

---

## 2. DEPLOYMENT TOPOLOGIES

### 2.1 Topology Types

Red Hat tests two main topology patterns:

1. **Growth Topology (All-in-One)**
   - Intended for organizations getting started with AAP
   - Allows smaller footprint deployments
   - Single VM deployment possible
   - RAM requirement: 32 GB (with hub_seed_collections=true)

2. **Enterprise Topology**
   - Intended for production deployments requiring high uptime and scalability
   - Multi-node distributed architecture
   - Higher resource requirements
   - Separate nodes for different components

### 2.2 Installation Methods

| Method | Infrastructure | Tested Topologies |
|--------|---------------|-------------------|
| **Containers** | VMs and bare metal | Growth, Enterprise |
| **Operator** | Red Hat OpenShift | Growth, Enterprise |
| **RPM** (deprecated in 2.5) | VMs and bare metal | Growth, Enterprise |

---

## 3. REFERENCE WORKLOADS AND CAPACITY METRICS

### 3.1 Growth Topology Workloads (Table 1.1)
From: Performance Tuning Guide, Section 1.7

| Component/Feature | Metric | Value |
|------------------|--------|-------|
| **REST API** | Requests per second (RPS) | 8 RPS |
| **REST API** | 50th percentile latency @ 8 RPS | 500 milliseconds |
| **REST API** | 99th percentile latency @ 8 RPS | 1.5 seconds |
| **Automation Controller** | Hosts in inventory | 1,000 hosts |
| **Automation Controller** | Job start rate (max burst) | 20 jobs/second |
| **Automation Controller** | Concurrent jobs | 10 concurrent jobs (default 5 forks) + 100 with forks=1 |
| **Callback Receiver** | Event processing rate | 10,000 job events/second at peak |
| **Job History** | Retention | 30 days |
| **Job History** | Storage | 2KB event; 500 events/playbook run; 500 jobs/day = <60GB database disk |
| **Automation Hub** | (Certified) Sync time | <30 minutes |
| **Automation Hub** | (Validated) Sync time | <5 minutes |
| **Event-Driven Ansible** | Activation processing (6 activations) | 1 actionable event/minute with minimal payload (1 min job completion) |

### 3.2 Enterprise Topology Workloads (Table 1.2)
From: Performance Tuning Guide, Section 1.8

| Component/Feature | Metric | Value |
|------------------|--------|-------|
| **REST API** | Requests per second (RPS) | 16 RPS |
| **REST API** | 50th percentile latency @ 16 RPS | 500 milliseconds |
| **REST API** | 99th percentile latency @ 16 RPS | 1.5 seconds |
| **Automation Controller** | Hosts in inventory | 10,000 hosts |
| **Automation Controller** | Job start rate | 80 jobs/second |
| **Automation Controller** | Concurrent jobs | 40 concurrent jobs (default 5 forks) + 400 with forks=1 |
| **Callback Receiver** | Event rate | 40,000 events/second at peak |
| **Job History** | Retention | 7 days |
| **Job History** | Storage | 2KB event; 500 events/playbook run; 2000 jobs/day = <60GB database disk |
| **Automation Hub** | (Certified) Sync time | <30 minutes |
| **Automation Hub** | (Validated) Sync time | <5 minutes |
| **Event-Driven Ansible** | Processing events (6 activations) | 3 actionable events/minute with minimal payload (1 min job completion) |

---

## 4. COMPONENT ARCHITECTURE

### 4.1 Main Components

1. **Platform Gateway**
   - Acts as reverse proxy
   - Routes incoming requests to appropriate services
   - Handles authentication via gRPC service
   - Each pod includes its own authentication service

2. **Automation Controller**
   - Control plane components
   - Execution plane components (execution nodes)
   - Hybrid nodes (combination of control and execution)
   - Dispatcher (tasking system)
   - Callback Receiver (job event processing)

3. **Automation Hub**
   - API service
   - Content service
   - Worker service
   - Stores Ansible Collections and Execution Environments

4. **Event-Driven Ansible (EDA)**
   - API and WebSocket service
   - EventStream service
   - Activation workers
   - Runs ansible-rulebook instances

5. **Database (PostgreSQL)**
   - Separate database instances recommended per component at scale
   - Components: Gateway, Controller, Hub, EDA

6. **Redis**
   - Standalone Redis: Simple architecture, single point of failure
   - Clustered Redis: 3 primary nodes + 3 replica nodes, automatic failover

---

## 5. SCALING GUIDELINES

### 5.1 Vertical Scaling

**Definition:** Increasing physical resources (CPU, memory, disk, IOPS)

**Benefits:**
- Relieves resource contention
- Applications have access to more resources

**Limitations:**
- Instances >64 CPU cores and >128 GB RAM may not scale linearly
- Extensive testing required
- Resource overcommit leads to unpredictable performance
- CPU throttling issues in OpenShift if limits != requests

**Recommendation:** Always set CPU requests equal to CPU limits in OpenShift

### 5.2 Horizontal Scaling

**Definition:** Increasing number of replicas (pods or VMs)

**Benefits:**
- Improved availability
- Redundancy
- Increased authentication capacity (each gateway pod has auth service)
- Repeatable scaling procedure

**Limitations:**
- Increased database connections
- Health check overhead in mesh architecture
- More than 100 backlogged requests on OpenShift can be dropped by uWSGI

### 5.3 Key Performance Indicators for Scaling

Monitor these to determine when to scale:

1. **High API Latency**
   - 99th percentile >1500ms indicates need to scale
   - Monitor via Envoy proxy logs

2. **High CPU Utilization**
   - Consistently high CPU on API pods
   - Backlog of requests
   - Monitor: `container_cpu_cfs_throttled_seconds_total` metric

3. **Error Codes**
   - 502 UAEX: Authentication service overloaded
   - 503 UH: Upstream service unhealthy
   - 503 UF: Upstream connection failure

---

## 6. COMPONENT-SPECIFIC SCALING STRATEGIES

### 6.1 Platform Gateway

**When to Scale:**
- High latency on /api/gateway routes
- High CPU utilization on gateway pods/nodes
- 502 UAEX errors in Envoy logs

**How to Scale:**
- **OpenShift:** Adjust replicas in AnsibleAutomationPlatform CR
- **VM/Container:** Add more gateway nodes
- Horizontal scaling preferred over vertical

**Considerations:**
- Each pod increases database connections for WSGI and gRPC workers
- Scaling increases health check traffic to all components
- CPU bottleneck: Scale gRPC authentication service
- Use Token or Session auth (NOT Basic auth for high-frequency API calls)

### 6.2 Automation Controller

**When to Scale:**
- High latency on /api/controller routes
- High CPU utilization on API pods/nodes
- 503 errors from platform gateway

**How to Scale:**
- **OpenShift:**
  - Adjust `web_replicas` attribute on AutomationController CR
  - `replicas` attribute scales both task and web replicas
- **VM/Container:** Add control or hybrid nodes

**Considerations:**
- WSGI workers scale with machine's CPU count
- Control/hybrid nodes also scale Dispatcher and Callback Receiver
- More database connections than just scaling web deployment
- OpenShift allows separate scaling of web vs task components

**Database Connections:**
- Web replicas: Consume connections for WSGI workers and background services
- Control nodes: Additional connections for Dispatcher and Callback Receiver
- Worker pools scale with CPU availability

### 6.3 Automation Hub

**When to Scale:**
- High latency on /api/galaxy routes
- High CPU utilization on hub pods/nodes
- 503 errors when pod too busy for health checks
- Pulp worker saturation

**How to Scale:**
- **OpenShift:**
  - API pods: Increase `hub.api.replicas` in AnsibleAutomationPlatform CR
  - Content/Workers: Increase `hub.content.replicas` and `hub.worker.replicas`
- **VM/Container:** Add more hub nodes (scales all services)

**Considerations:**
- Content sync uses memory proportional to collections/versions synchronized
- Container image layer size impacts memory used by pulp workers
- Large execution environments increase memory requirements

### 6.4 Event-Driven Ansible

**When to Scale:**
- High latency on /api/eda or /api/eda-event-stream routes
- High CPU utilization on EDA pods/nodes

**How to Scale:**
- **OpenShift:**
  - API/WebSocket: Scale `eda-api` deployment
  - EventStream: Scale `eda-event-stream` worker deployment (separate from eda-api)
- **VM/Container:** Add hybrid nodes (increases all EDA component capacity)

**Considerations:**
- Scale `eda-api` deployment in proportion to number of activations
- Each activation needs dedicated worker capacity

### 6.5 Database (PostgreSQL)

**Scaling Considerations:**
- Vertical scaling increases potential connections and I/O utilization
- As you scale past tested models, deploy separate Postgres instances per component:
  - Platform Gateway DB
  - Automation Controller DB
  - Automation Hub DB
  - Event-Driven Ansible DB

**Connection Planning:**
- Connections scale with:
  - Number of web replicas
  - CPU count on VM/container installations
  - Number of control/hybrid nodes
  - Number of worker pools

---

## 7. MEMORY AND CPU ALLOCATION

### 7.1 Automation Controller Memory Capacity

**Variable:** `controller_percent_memory_capacity`

**Default:** `1.0` (allocates 100% of system memory to automation controller)

**Usage in Growth Topology:** `0.5` (allocates 50% of system memory)

**Purpose:** Controls memory allocation for automation controller on shared nodes

### 7.2 CPU and Memory Limits (OpenShift)

**Critical Setting:** Always set CPU requests equal to CPU limits

**Reason:** Prevents CPU throttling even when node has spare capacity

**Monitoring:** Use `container_cpu_cfs_throttled_seconds_total` metric

---

## 8. JOB CONCURRENCY AND THROUGHPUT

### 8.1 Job Concurrency Factors

**Default Fork Value:** 5 (forks per job)

**Concurrency Impact:**
- Growth: 10 concurrent jobs (default forks) OR 100 concurrent jobs (forks=1)
- Enterprise: 40 concurrent jobs (default forks) OR 400 concurrent jobs (forks=1)

**Fork Setting:** Lower forks = higher job concurrency possible

### 8.2 Job Event Processing

**Event Generation:**
- Single Ansible task on one host = 6 job events (verbosity 1)
- Same task = 34 job events (verbosity 3)
- Tasks: task start + host-specific details + task completion

**Event Size:** ~2KB per event (for capacity planning)

**Event Processing:**
- Dispatcher processes job events
- Callback receiver manages event transmission
- Events stored in database
- Processing occurs on control plane

### 8.3 Job Types

1. **Standard Jobs**
   - Execute Ansible playbook against inventory
   - Initiated by control node
   - Results streamed, processed, and stored

2. **Sliced Jobs**
   - Split jobs across inventory slices
   - Run in parallel

3. **Bulk Jobs**
   - Launch multiple jobs in single request

4. **Workflow Jobs**
   - Coordinate multiple job templates

5. **System Jobs**
   - Internal maintenance (cleanup, etc.)
   - Run on control plane
   - Frequency managed by schedules

---

## 9. DATABASE SIZING BASED ON JOB VOLUME

### 9.1 Database Growth Formula

**Base Formula:**
```
Storage = Event_Size × Events_Per_Run × Jobs_Per_Day × Retention_Days
```

**Example (Growth Topology - 30 day retention):**
```
Storage = 2KB × 500 events × 500 jobs/day × 30 days
Storage < 60 GB (as specified for Database node)
```

**Example (Enterprise Topology - 7 day retention):**
```
Storage = 2KB × 500 events × 2000 jobs/day × 7 days
Storage < 60 GB (as specified for Database node)
```

### 9.2 Retention Policies

**Growth Topology:** 30 days retention, 500 jobs/day
**Enterprise Topology:** 7 days retention, 2000 jobs/day

**Note:** Shorter retention with higher job volume keeps database size similar

---

## 10. AUTOMATION HUB STORAGE

### 10.1 Storage Backend Options

1. **Amazon S3**
   - Variable: `hub_storage_backend=s3`
   - Requires: `hub_s3_access_key`, `hub_s3_secret_key`, `hub_s3_bucket_name`
   - Bucket must exist before installation

2. **Azure Blob Storage**
   - Variable: `hub_storage_backend=azure`
   - Requires: `hub_azure_account_key`, `hub_azure_account_name`, `hub_azure_container`
   - Container must exist before installation

3. **Network File System (NFS)**
   - File-based storage option

### 10.2 Content Synchronization

**Memory Impact:** Proportional to number of collections and versions synchronized

**Execution Environment Impact:** Container image layer size affects memory used by pulp workers

---

## 11. REDIS CONFIGURATION

### 11.1 Standalone Redis

**Architecture:** Simple, single instance
**Use Case:** Resource-constrained deployments, non-production
**Limitation:** Single point of failure

### 11.2 Clustered Redis

**Architecture:**
- 3 primary nodes
- 3 replica nodes (one per primary)
- Automatic failover

**Features:**
- Data split across nodes automatically
- Enterprise-grade resilience
- Protection against node failures
- Automatic failover during system failures

**Use Case:** Production deployments requiring high availability

---

## 12. CONTAINER RESOURCE PLANNING

### 12.1 OpenShift Container Platform Specifics

**Scaling Operations (Table 2.1):**

| Operation | OpenShift | VM-based | Containerized (Podman) |
|-----------|-----------|----------|------------------------|
| Horizontal Scale Up | Adjust replicas independently; no platform disruption | Requires inventory update + reinstall (halts platform) | Requires inventory update + reinstall (halts platform) |
| Horizontal Scale Down | Reduce replicas via operator | Requires inventory update + reinstall | Requires inventory update + reinstall |
| Vertical Scaling | Edit resource requests/limits in CR | VM resize + reinstall to adapt settings | VM resize + reinstall to adapt settings |

**Advantages:**
- Most flexibility and customizability
- Fine-grained observability via built-in metrics
- Log aggregation from all pods
- Independent component scaling
- No platform downtime for most operations

### 12.2 Service Separation in OpenShift

**Control Plane vs Execution Plane:**
- Control plane: Scaling API/web services
- Execution plane: Scaling task execution capacity
- OpenShift allows independent scaling of each

**Benefit:** Conserve database connections by scaling only needed components

---

## 13. NETWORK AND CONNECTIVITY

### 13.1 Node Connection Types

1. **Control Nodes**
   - Run control plane services
   - API, scheduling, dispatching

2. **Execution Nodes**
   - Run playbook execution only
   - No control plane services

3. **Hybrid Nodes**
   - Combination of control and execution
   - Share connections of both types

4. **Hop Nodes**
   - Connect control and execution nodes
   - Minimal CPU and memory usage
   - Vertical scaling hop nodes does NOT impact system capacity

---

## 14. AUTHENTICATION PERFORMANCE

### 14.1 Authentication Methods (by performance)

1. **Token Authentication** - Most performant
2. **Session Authentication** - Performant
3. **Basic Authentication** - AVOID for high-frequency API automation

**Reason:** Basic auth with LDAP introduces:
- CPU-intensive password hashing
- Latency from LDAP service calls
- Limited LDAP service availability issues

**Recommendation:** Use OAuth Tokens for API automation

---

## 15. KEY VARIABLES FOR CAPACITY TUNING

### 15.1 Automation Controller Variables

| Variable | Purpose | Default | Notes |
|----------|---------|---------|-------|
| `controller_percent_memory_capacity` | Memory allocation percentage | 1.0 (100%) | Use 0.5 for shared all-in-one deployments |

### 15.2 Automation Hub Variables

| Variable | Purpose | Notes |
|----------|---------|-------|
| `hub_seed_collections` | Pre-seed collections during install | Requires 32GB RAM, takes 45+ minutes |
| `hub_storage_backend` | Storage type | Options: s3, azure, nfs |

### 15.3 Worker/Process Count Variables

From containerized installation documentation:

- Event workers count
- Hub workers count
- EDA workers count
- gRPC processes count

**Note:** These typically scale automatically with CPU count but can be overridden

---

## 16. LIMITATIONS AND CONSIDERATIONS

### 16.1 Vertical Scaling Limits

- **64 CPU cores / 128 GB RAM:** Beyond this, linear scaling not guaranteed
- Application-level limits exist
- System-level limits exist
- Testing required for each instance size

### 16.2 uWSGI Request Queue Limit

**Issue:** Maximum 100 backlogged requests on OpenShift

**Cause:** uWSGI backlog length tied to kernel parameter `somaxconn`

**Symptom:** `*** uWSGI listen queue of socket ":8000" (fd: 3) full !!! (101/100) ***`

**Impact:** Dropped requests, client timeouts

**Solution:** Horizontal scaling to prevent backlog

### 16.3 Database Connection Exhaustion

**Risk:** Scaling application increases database connections

**Factors:**
- WSGI web server connections (scale with CPU count)
- Background service connections
- Dispatcher connections
- Callback receiver connections
- Worker pool connections

**Mitigation:** Deploy separate PostgreSQL instances per component

### 16.4 Health Check Overhead

**Issue:** Each Envoy proxy sends health checks to every cluster member

**Impact:** Horizontal scaling increases baseline traffic

**Consideration:** Health checks share same queues as user requests

---

## 17. MONITORING AND METRICS

### 17.1 Key Metrics to Monitor

1. **API Latency**
   - 50th percentile
   - 99th percentile
   - Target: <1500ms for 99th percentile

2. **CPU Utilization**
   - Per pod/node
   - `container_cpu_cfs_throttled_seconds_total` for throttling

3. **Database Connections**
   - Active connections per component
   - Connection pool utilization

4. **Job Event Rate**
   - Events per second
   - Callback receiver capacity

5. **Error Rates**
   - 502 UAEX (authentication failures)
   - 503 UH (upstream unhealthy)
   - 503 UF (upstream connection failure)

### 17.2 Envoy Proxy Logs

**Routes to Monitor:**
- `/api/gateway` - Platform gateway
- `/api/controller` - Automation controller
- `/api/eda` - Event-Driven Ansible API
- `/eda-event-streams/api/eda/v1/external_event_stream/` - EDA Event Streams
- `/api/galaxy` - Automation hub

---

## 18. INVENTORY FILE EXAMPLES

### 18.1 Growth Topology (All-in-One)

**Single Host Deployment:**
```ini
[automationgateway]
aap.example.org ansible_connection=local

[automationcontroller]
aap.example.org ansible_connection=local

[automationhub]
aap.example.org ansible_connection=local

[automationedacontroller]
aap.example.org ansible_connection=local

[database]
aap.example.org ansible_connection=local

[all:vars]
gateway_admin_password=<set>
gateway_pg_host=aap.example.org
gateway_pg_password=<set>

controller_admin_password=<set>
controller_pg_host=aap.example.org
controller_pg_password=<set>
controller_percent_memory_capacity=0.5

hub_admin_password=<set>
hub_pg_host=aap.example.org
hub_pg_password=<set>

eda_admin_password=<set>
eda_pg_host=aap.example.org
eda_pg_password=<set>
```

### 18.2 Enterprise Topology (Multi-Node)

**Distributed Deployment:**
```ini
[automationgateway]
gateway1.example.org
gateway2.example.org

[automationcontroller]
controller1.example.org
controller2.example.org

[execution_nodes]
exec1.example.org
exec2.example.org

[automationhub]
hub1.example.org
hub2.example.org

[automationedacontroller]
eda1.example.org

[database]
db1.example.org

[all:vars]
# External database example
gateway_pg_host=externaldb.example.org
gateway_pg_database=<set>
gateway_pg_username=<set>
gateway_pg_password=<set>

controller_pg_host=externaldb.example.org
controller_pg_database=<set>
controller_pg_username=<set>
controller_pg_password=<set>

hub_pg_host=externaldb.example.org
hub_pg_database=<set>
hub_pg_username=<set>
hub_pg_password=<set>

eda_pg_host=externaldb.example.org
eda_pg_database=<set>
eda_pg_username=<set>
eda_pg_password=<set>
```

---

## 19. CONTAINER SERVICE NAMES (Podman-based Installation)

### 19.1 Gateway Services
- Platform gateway proxy service

### 19.2 Automation Controller Services
- automation-controller-task
- automation-controller-web
- automation-controller-dispatcher
- automation-controller-rsyslog

### 19.3 Automation Hub Services
- automation-hub-api
- automation-hub-content
- automation-hub-worker-<number>

### 19.4 Event-Driven Ansible Services
- automation-eda-api
- automation-eda-scheduler
- automation-eda-worker-<number>
- automation-eda-activation-worker-<number>

### 19.5 Database Service
- automation-postgresql

### 19.6 Redis Service
- automation-redis (standalone)
- automation-redis-cluster (clustered)

---

## 20. MIGRATION FROM AAP 2.4 TO 2.6 CONSIDERATIONS

### 20.1 RPM to Containerized Migration

**Key Changes:**
- RPM installer deprecated in 2.5, removed in 2.7
- RHEL 9 support continues during AAP 2.6 lifecycle
- Containerized installation uses Podman containers
- Same underlying services, different deployment method

### 20.2 Resource Translation Approach

**VM-based AAP 2.4 → Container-based AAP 2.6:**

1. **Baseline Metrics to Collect from AAP 2.4:**
   - CPU utilization per node (average and peak)
   - Memory utilization per node (average and peak)
   - Job concurrency (concurrent jobs at peak)
   - Job start rate (jobs/second)
   - API request rate (requests/second)
   - Database size and growth rate
   - Number of managed hosts

2. **Mapping to AAP 2.6 Container Resources:**
   - Use collected metrics to determine topology (growth vs enterprise)
   - Compare against reference workloads (Tables 1.1 and 1.2)
   - Calculate required replicas based on request rates and concurrency
   - Size CPU/memory per pod based on utilization patterns
   - Plan database resources based on job volume and retention

3. **Recommended Starting Point:**
   - If AAP 2.4 fits growth workload: Start with growth topology
   - If AAP 2.4 exceeds growth workload: Start with enterprise topology
   - Use `controller_percent_memory_capacity=0.5` for all-in-one deployments
   - Monitor and scale horizontally as needed

### 20.3 Component Mapping

| AAP 2.4 Component | AAP 2.6 Component | Notes |
|-------------------|-------------------|-------|
| Tower/Controller node | Automation Controller (control node) | Same functionality |
| Execution node | Execution node | Same functionality |
| Private Automation Hub | Automation Hub | Same functionality |
| - | Platform Gateway | New component in 2.6 |
| - | Event-Driven Ansible | New component (if using EDA) |

---

## 21. CAPACITY PLANNING WORKSHEET

### 21.1 Current AAP 2.4 Metrics to Gather

**Automation Controller:**
- [ ] Number of managed hosts: _______
- [ ] Peak concurrent jobs: _______
- [ ] Average jobs/day: _______
- [ ] Job start rate (jobs/second): _______
- [ ] Average events per job run: _______
- [ ] Job history retention period: _______ days
- [ ] API request rate (requests/second): _______
- [ ] CPU usage per node: _______% (avg), _______% (peak)
- [ ] Memory usage per node: _______ GB (avg), _______ GB (peak)

**Database:**
- [ ] Current database size: _______ GB
- [ ] Database growth rate: _______ GB/month
- [ ] Peak database connections: _______

**Automation Hub (if applicable):**
- [ ] Number of collections: _______
- [ ] Number of execution environments: _______
- [ ] Average EE size: _______ GB
- [ ] Sync frequency: _______

### 21.2 AAP 2.6 Sizing Recommendations

**Compare Against Reference Workloads:**

Growth Topology Thresholds:
- [ ] Hosts ≤ 1,000
- [ ] Job start rate ≤ 20/second
- [ ] Concurrent jobs ≤ 10 (default forks) or ≤ 100 (forks=1)
- [ ] Event rate ≤ 10,000/second
- [ ] API requests ≤ 8 RPS

Enterprise Topology Thresholds:
- [ ] Hosts ≤ 10,000
- [ ] Job start rate ≤ 80/second
- [ ] Concurrent jobs ≤ 40 (default forks) or ≤ 400 (forks=1)
- [ ] Event rate ≤ 40,000/second
- [ ] API requests ≤ 16 RPS

**Recommended Topology:** ________________

**Estimated Container Resources:**
- Platform Gateway replicas: _______
- Automation Controller web replicas: _______
- Automation Controller task replicas: _______
- Execution node VMs: _______
- Automation Hub replicas: _______
- Event-Driven Ansible replicas: _______
- Database instance sizing: _______ vCPU, _______ GB RAM
- Redis configuration: [ ] Standalone [ ] Clustered

---

## 22. ADDITIONAL NOTES

### 22.1 Installation Program Behavior

**Auto-tuning:**
- Installation program attempts to tune based on available CPU and RAM
- Not all components automatically scale with machine size
- Manual tuning may be required
- Extensive testing recommended for each instance size

**Recommendation:** After verifying instance size, use horizontal scaling with same-sized instances

### 22.2 Support and Testing

**Tested Topologies:**
- Red Hat fully tests published reference architectures
- Commercial support available for deployments meeting minimum requirements
- Custom topologies supported but not fully tested

**Best Practice:** Use tested topology for new deployments

### 22.3 High Availability

**Automation Hub HA:**
- Multiple nodes in active-active configuration
- Load balancer distributes workload
- No single point of failure
- Easy addition/removal of nodes

**Automation Controller HA:**
- Automation mesh architecture
- Peer-to-peer connections between nodes
- Dynamic cluster capacity
- Control/execution plane separation

**Database HA:**
- Clustered Redis for high availability
- PostgreSQL clustering recommended for production
- Automatic failover capabilities

---

## 23. SUMMARY OF KEY SIZING FACTORS

### 23.1 Primary Sizing Drivers

1. **Number of managed hosts** → Inventory size, memory requirements
2. **Job concurrency** → Execution node capacity
3. **Job start rate** → Controller capacity, database connections
4. **API request rate** → Gateway and API service replicas
5. **Job event rate** → Callback receiver capacity
6. **Retention period** → Database storage
7. **Number of collections/EEs** → Hub storage and memory

### 23.2 Scaling Triggers

**Scale UP when:**
- API latency >1500ms (99th percentile)
- CPU utilization consistently high (>80%)
- Error rates increasing (502, 503)
- Database connection pool exhaustion
- uWSGI request queue full errors

**Scale DOWN when:**
- Resource utilization consistently low (<30%)
- Over-provisioned for workload
- Cost optimization needed

### 23.3 Quick Reference: Growth vs Enterprise

| Metric | Growth | Enterprise | Scale Factor |
|--------|--------|------------|--------------|
| Managed Hosts | 1,000 | 10,000 | 10x |
| Job Start Rate | 20/sec | 80/sec | 4x |
| Concurrent Jobs (default forks) | 10 | 40 | 4x |
| Concurrent Jobs (forks=1) | 100 | 400 | 4x |
| Event Processing | 10K/sec | 40K/sec | 4x |
| API Request Rate | 8 RPS | 16 RPS | 2x |
| Jobs per Day | 500 | 2,000 | 4x |
| Retention Period | 30 days | 7 days | 0.23x |

---

## Document Version
- **Extracted:** 2026-03-04
- **Source Documentation:** Red Hat Ansible Automation Platform 2.6
- **Purpose:** Container resource sizing based on AAP 2.4 VM utilization metrics
