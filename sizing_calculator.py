"""
AAP 2.4 to 2.6 Sizing Calculator
Calculates recommended container resources for AAP 2.6 based on AAP 2.4 VM metrics
Using Official Red Hat Capacity Formulas
"""

import math
from typing import Dict, Any


class AAP26SizingCalculator:
    """
    Calculates sizing recommendations for AAP 2.6 container deployment
    based on AAP 2.4 VM metrics and workload characteristics.

    Uses official Red Hat formulas:
    - Execution Capacity = (Concurrent Jobs × Forks) + (Concurrent Jobs × 1)
    - Capacity per Node (4 vCPU/16GB) = 137 units
    - Memory per Fork = 100MB
    - Control Capacity = Maximum concurrent jobs to manage
    """

    # Red Hat official capacity constants
    CAPACITY_PER_NODE = 137  # Capacity units for 4 vCPU / 16GB node
    MEMORY_PER_FORK_MB = 100  # MB per fork
    MEMORY_RESERVATION_GB = 2  # Base memory reservation
    FORKS_PER_CPU = 4  # Baseline forks per CPU core
    DEFAULT_FORKS = 5  # Default fork value for jobs

    # Reference workload metrics from Red Hat documentation
    GROWTH_TOPOLOGY = {
        'rps': 8,
        'hosts': 1000,
        'job_start_rate': 20,
        'concurrent_jobs_default_forks': 10,
        'concurrent_jobs_fork1': 100,
        'events_per_second': 10000,
        'jobs_per_day': 500,
        'retention_days': 30
    }

    ENTERPRISE_TOPOLOGY = {
        'rps': 16,
        'hosts': 10000,
        'job_start_rate': 80,
        'concurrent_jobs_default_forks': 40,
        'concurrent_jobs_fork1': 400,
        'events_per_second': 40000,
        'jobs_per_day': 2000,
        'retention_days': 7
    }

    # Standard node specifications
    STANDARD_NODE_SPEC = {
        'cpu': 4,
        'memory_gb': 16,
        'disk_gb': 128,
        'iops': 3000
    }

    def __init__(self):
        pass

    def calculate_database_storage(self, jobs_per_day: int, retention_days: int,
                                   events_per_job: int = 500, event_size_kb: int = 2) -> int:
        """
        Calculate database storage requirements in GB.
        Formula: Event_Size × Events_Per_Run × Jobs_Per_Day × Retention_Days
        """
        storage_kb = event_size_kb * events_per_job * jobs_per_day * retention_days
        storage_gb = math.ceil(storage_kb / (1024 * 1024))
        return max(storage_gb, 60)  # Minimum 60GB

    def analyze_workload_tier(self, current_metrics: Dict[str, Any]) -> str:
        """
        Determine if workload fits growth or enterprise topology based on metrics.
        """
        jobs_per_day = current_metrics.get('playbooks_per_day_peak', 0)
        concurrent_jobs = current_metrics.get('concurrent_jobs_peak', 0)
        managed_hosts = current_metrics.get('managed_hosts', 0)

        # Score against enterprise topology
        enterprise_score = 0

        if jobs_per_day > 20000:  # Exceeds growth capacity significantly
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

    def calculate_execution_capacity(self, concurrent_jobs: int, forks_per_job: int = None) -> int:
        """
        Calculate execution capacity using Red Hat's official formula.

        Formula: Capacity = (Concurrent Jobs × Forks) + (Concurrent Jobs × 1 base task)

        Returns: Required capacity units
        """
        if forks_per_job is None:
            forks_per_job = self.DEFAULT_FORKS

        capacity = (concurrent_jobs * forks_per_job) + (concurrent_jobs * 1)
        return capacity

    def calculate_execution_memory(self, concurrent_jobs: int, forks_per_job: int = None) -> int:
        """
        Calculate memory needed for execution using Red Hat's fork-based formula.

        Formula: Memory = (Total Forks × 100MB) + 2GB reservation

        Returns: Memory in GB
        """
        if forks_per_job is None:
            forks_per_job = self.DEFAULT_FORKS

        total_forks = concurrent_jobs * forks_per_job
        memory_mb = (total_forks * self.MEMORY_PER_FORK_MB) + (self.MEMORY_RESERVATION_GB * 1024)
        memory_gb = math.ceil(memory_mb / 1024)

        return memory_gb

    def calculate_controller_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate automation controller resources based on control capacity needs.

        Control Capacity = Maximum concurrent jobs to manage
        """
        concurrent_jobs = current_metrics.get('concurrent_jobs_peak', 100)

        # Control capacity equals max concurrent jobs
        control_capacity = concurrent_jobs

        # Calculate nodes needed (using 137 capacity units per 4vCPU/16GB node)
        # Control plane needs less capacity than execution, roughly 1:5 ratio
        control_nodes_needed = max(2, math.ceil(control_capacity / (self.CAPACITY_PER_NODE * 5)))

        # Use standard 4 vCPU / 16GB spec
        cpu_per_pod = self.STANDARD_NODE_SPEC['cpu']
        memory_per_pod = self.STANDARD_NODE_SPEC['memory_gb']

        return {
            'control_plane_pods': control_nodes_needed,
            'cpu_per_pod': cpu_per_pod,
            'memory_per_pod_gb': memory_per_pod,
            'total_cpu': control_nodes_needed * cpu_per_pod,
            'total_memory_gb': control_nodes_needed * memory_per_pod,
            'control_capacity': control_capacity,
            'note': f'Sized for {concurrent_jobs} concurrent job management capacity'
        }

    def calculate_execution_node_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate execution node resources using Red Hat's capacity formula.

        Formula: Capacity = (Concurrent Jobs × Forks) + (Concurrent Jobs × 1)
        Capacity per Node = 137 units (for 4 vCPU/16GB node)
        """
        concurrent_jobs = current_metrics.get('concurrent_jobs_peak', 100)
        forks_observed = current_metrics.get('forks_observed', self.DEFAULT_FORKS)

        # Calculate average forks per job
        # If user provided forks_observed, use it; otherwise use default
        avg_forks = forks_observed if forks_observed > 0 else self.DEFAULT_FORKS

        # If forks_observed seems like total forks, derive avg per job
        if avg_forks > 50:  # Likely total concurrent forks
            avg_forks = max(self.DEFAULT_FORKS, math.ceil(avg_forks / concurrent_jobs))

        # Calculate execution capacity needed
        execution_capacity = self.calculate_execution_capacity(concurrent_jobs, avg_forks)

        # Calculate nodes needed (137 capacity units per 4vCPU/16GB node)
        execution_nodes = max(2, math.ceil(execution_capacity / self.CAPACITY_PER_NODE))

        # Calculate memory using fork-based formula
        total_memory_needed = self.calculate_execution_memory(concurrent_jobs, avg_forks)

        # Distribute memory across nodes
        memory_per_pod = max(16, math.ceil(total_memory_needed / execution_nodes))

        # Use standard 4 vCPU spec
        cpu_per_pod = self.STANDARD_NODE_SPEC['cpu']

        # Adjust if memory per pod exceeds standard
        if memory_per_pod > 16:
            # Need to add more nodes to distribute memory
            execution_nodes = max(execution_nodes, math.ceil(total_memory_needed / 16))
            memory_per_pod = 16  # Keep standard size

        return {
            'execution_pods': execution_nodes,
            'cpu_per_pod': cpu_per_pod,
            'memory_per_pod_gb': memory_per_pod,
            'total_cpu': execution_nodes * cpu_per_pod,
            'total_memory_gb': execution_nodes * memory_per_pod,
            'execution_capacity': execution_capacity,
            'avg_forks_per_job': avg_forks,
            'note': f'Sized for {execution_capacity} capacity units ({concurrent_jobs} jobs × {avg_forks} forks)'
        }

    def calculate_database_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate database resources based on workload and current utilization.
        Accounts for connection scaling with worker counts.
        """
        cpu_percent = current_metrics.get('database_cpu_percent', 90)
        memory_percent = current_metrics.get('database_memory_percent', 35)
        current_db_vcpu = current_metrics.get('database_vcpu', 16)
        current_db_memory = current_metrics.get('database_memory_gb', 128)
        concurrent_db_requests = current_metrics.get('concurrent_db_requests_peak', 600)
        db_growth_per_day_gb = current_metrics.get('db_growth_per_day_gb', 200)
        retention_days = current_metrics.get('job_retention_hours', 48) / 24
        jobs_per_day = current_metrics.get('playbooks_per_day_peak', 70000)

        # Calculate actual used resources
        actual_cpu_used = current_db_vcpu * (cpu_percent / 100)
        actual_memory_used = current_db_memory * (memory_percent / 100)

        # Add headroom for growth and peaks
        recommended_cpu = max(8, math.ceil(actual_cpu_used * 1.3))  # 30% headroom
        recommended_memory = max(32, math.ceil(actual_memory_used * 1.5))  # 50% headroom

        # Calculate storage needs
        storage_gb = self.calculate_database_storage(
            jobs_per_day=math.ceil(jobs_per_day / 30) if jobs_per_day > 10000 else jobs_per_day,
            retention_days=math.ceil(retention_days)
        )

        # Add observed daily growth
        storage_with_buffer = math.ceil(storage_gb + (db_growth_per_day_gb * retention_days * 1.2))

        # Calculate connection requirements
        # Connections scale with number of workers and replicas
        # Rough estimate: 10 connections per web worker, workers scale with CPU
        estimated_connections = concurrent_db_requests if concurrent_db_requests > 0 else 200

        return {
            'cpu': recommended_cpu,
            'memory_gb': recommended_memory,
            'storage_gb': storage_with_buffer,
            'iops': 3000,  # Minimum required
            'max_connections': max(200, estimated_connections),
            'note': 'Consider separate PostgreSQL instances for each component at scale'
        }

    def calculate_automation_hub_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate automation hub resources.
        Hub is less resource intensive but needs capacity for content sync.
        """
        cpu_percent = current_metrics.get('hub_cpu_percent', 25)
        memory_percent = current_metrics.get('hub_memory_percent', 30)
        num_hub_nodes = current_metrics.get('num_hub_nodes', 2)

        # Hub is less resource intensive, minimum 2 pods for HA
        hub_pods = max(2, num_hub_nodes)

        # Adjust based on utilization
        if cpu_percent > 50:
            cpu_per_pod = 4
        else:
            cpu_per_pod = 2

        if memory_percent > 50:
            memory_per_pod = 16
        else:
            memory_per_pod = 8

        return {
            'hub_pods': hub_pods,
            'cpu_per_pod': cpu_per_pod,
            'memory_per_pod_gb': memory_per_pod,
            'total_cpu': hub_pods * cpu_per_pod,
            'total_memory_gb': hub_pods * memory_per_pod,
            'note': 'Add 32GB extra if seeding collections (hub_seed_collections=true)'
        }

    def calculate_gateway_resources(self, workload_tier: str) -> Dict[str, Any]:
        """
        Calculate platform gateway resources.
        Gateway handles authentication and routing.
        """
        if workload_tier == 'enterprise':
            gateway_pods = 3  # HA configuration
            cpu_per_pod = 2
            memory_per_pod = 4
        else:
            gateway_pods = 2  # Basic HA
            cpu_per_pod = 2
            memory_per_pod = 4

        return {
            'gateway_pods': gateway_pods,
            'cpu_per_pod': cpu_per_pod,
            'memory_per_pod_gb': memory_per_pod,
            'total_cpu': gateway_pods * cpu_per_pod,
            'total_memory_gb': gateway_pods * memory_per_pod
        }

    def calculate_eda_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Event-Driven Ansible resources.
        Scale based on number of activations.
        """
        # Basic EDA setup for growth, can be scaled later
        eda_pods = 2  # Minimum for HA
        cpu_per_pod = 2
        memory_per_pod = 8

        return {
            'eda_pods': eda_pods,
            'cpu_per_pod': cpu_per_pod,
            'memory_per_pod_gb': memory_per_pod,
            'total_cpu': eda_pods * cpu_per_pod,
            'total_memory_gb': eda_pods * memory_per_pod,
            'note': 'Scale based on number of activations and event rates'
        }

    def calculate_redis_resources(self, workload_tier: str) -> Dict[str, Any]:
        """
        Calculate Redis resources.
        Clustered for enterprise, standalone for growth.
        """
        if workload_tier == 'enterprise':
            # Clustered Redis: 3 primary + 3 replica
            return {
                'type': 'clustered',
                'primary_nodes': 3,
                'replica_nodes': 3,
                'cpu_per_node': 1,
                'memory_per_node_gb': 4,
                'total_nodes': 6,
                'total_cpu': 6,
                'total_memory_gb': 24
            }
        else:
            # Standalone Redis
            return {
                'type': 'standalone',
                'nodes': 1,
                'cpu': 1,
                'memory_gb': 2
            }

    def calculate_event_processing_rate(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate event processing requirements.

        Event generation: 6 events per task per host (at verbosity 1)
        Formula: Jobs × Average Tasks × Average Hosts × 6 Events
        """
        jobs_per_day = current_metrics.get('playbooks_per_day_peak', 500)
        concurrent_jobs = current_metrics.get('concurrent_jobs_peak', 100)

        # Estimate events per job
        # Assume ~10 tasks per playbook, ~50 hosts per job on average
        avg_tasks_per_job = 10
        avg_hosts_per_job = 50
        events_per_task = 6  # At verbosity 1

        # Events per job
        events_per_job = avg_tasks_per_job * avg_hosts_per_job * events_per_task

        # Peak event rate (when all concurrent jobs are running)
        # Assume each job takes ~60 seconds on average
        avg_job_duration_sec = 60
        events_per_second_peak = math.ceil((concurrent_jobs * events_per_job) / avg_job_duration_sec)

        # Daily event volume
        events_per_day = jobs_per_day * events_per_job

        return {
            'events_per_job': events_per_job,
            'events_per_second_peak': events_per_second_peak,
            'events_per_day': events_per_day,
            'note': f'Assumes {avg_tasks_per_job} tasks/job, {avg_hosts_per_job} hosts/job, {events_per_task} events/task'
        }

    def generate_sizing_recommendation(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate complete sizing recommendation for AAP 2.6 based on AAP 2.4 metrics.
        Uses official Red Hat capacity formulas.
        """
        # Determine workload tier
        workload_tier = self.analyze_workload_tier(current_metrics)

        # Calculate resources for each component
        gateway = self.calculate_gateway_resources(workload_tier)
        controller = self.calculate_controller_resources(current_metrics)
        execution = self.calculate_execution_node_resources(current_metrics)
        database = self.calculate_database_resources(current_metrics)
        hub = self.calculate_automation_hub_resources(current_metrics)
        eda = self.calculate_eda_resources(current_metrics)
        redis = self.calculate_redis_resources(workload_tier)
        event_processing = self.calculate_event_processing_rate(current_metrics)

        # Calculate totals
        total_cpu = (gateway['total_cpu'] + controller['total_cpu'] +
                    execution['total_cpu'] + database['cpu'] +
                    hub['total_cpu'] + eda['total_cpu'] + redis['total_cpu'])

        total_memory = (gateway['total_memory_gb'] + controller['total_memory_gb'] +
                       execution['total_memory_gb'] + database['memory_gb'] +
                       hub['total_memory_gb'] + eda['total_memory_gb'] + redis['total_memory_gb'])

        return {
            'workload_tier': workload_tier,
            'topology_recommendation': self._get_topology_recommendation(workload_tier),
            'components': {
                'platform_gateway': gateway,
                'automation_controller_control_plane': controller,
                'automation_controller_execution_plane': execution,
                'database': database,
                'automation_hub': hub,
                'event_driven_ansible': eda,
                'redis': redis
            },
            'event_processing': event_processing,
            'summary': {
                'total_cpu': total_cpu,
                'total_memory_gb': total_memory,
                'total_storage_gb': database['storage_gb'],
                'estimated_pods': (gateway['gateway_pods'] + controller['control_plane_pods'] +
                                 execution['execution_pods'] + hub['hub_pods'] +
                                 eda['eda_pods'] + redis.get('total_nodes', redis.get('nodes', 1)))
            },
            'calculation_method': {
                'execution_capacity_formula': f"({current_metrics.get('concurrent_jobs_peak', 0)} jobs × {execution.get('avg_forks_per_job', 5)} forks) + ({current_metrics.get('concurrent_jobs_peak', 0)} × 1) = {execution.get('execution_capacity', 0)} units",
                'capacity_per_node': f"{self.CAPACITY_PER_NODE} units per 4vCPU/16GB node",
                'memory_per_fork': f"{self.MEMORY_PER_FORK_MB}MB per fork + {self.MEMORY_RESERVATION_GB}GB reservation",
                'event_rate_peak': f"{event_processing['events_per_second_peak']} events/second peak"
            },
            'deployment_notes': self._get_deployment_notes(workload_tier, current_metrics, execution, event_processing)
        }

    def _get_topology_recommendation(self, tier: str) -> str:
        """Get topology recommendation description."""
        if tier == 'enterprise':
            return ('Enterprise Topology - Multi-node distributed architecture for production. '
                   'Provides high availability, independent component scaling, and handles '
                   '10,000+ hosts, 80+ jobs/second, 40,000 events/second.')
        elif tier == 'enterprise_recommended':
            return ('Enterprise Topology Recommended - Your workload is approaching or exceeding '
                   'growth topology limits. Enterprise topology provides better scalability and HA.')
        else:
            return ('Growth Topology - Suitable for getting started or smaller deployments. '
                   'Handles 1,000 hosts, 20 jobs/second, 10,000 events/second. '
                   'Can be deployed on fewer resources.')

    def _get_deployment_notes(self, tier: str, metrics: Dict[str, Any],
                             execution: Dict[str, Any], event_processing: Dict[str, Any]) -> list:
        """Generate deployment notes and recommendations."""
        notes = []

        # Calculation method note
        notes.append(f'✓ Calculations use official Red Hat capacity formulas')
        notes.append(f'✓ Execution capacity: {execution.get("execution_capacity", 0)} units (137 units per 4vCPU/16GB node)')
        notes.append(f'✓ Memory sizing: {self.MEMORY_PER_FORK_MB}MB per fork + {self.MEMORY_RESERVATION_GB}GB reservation')

        # General notes
        notes.append('All values include appropriate headroom for peaks and growth')
        notes.append('Minimum 2 replicas per service recommended for high availability')

        # Topology specific notes
        if tier in ['enterprise', 'enterprise_recommended']:
            notes.append('Consider separate PostgreSQL instances per component for better isolation')
            notes.append('Use clustered Redis (3 primary + 3 replica) for HA')
            notes.append('Implement load balancing for API endpoints')

        # Event processing notes
        events_per_sec = event_processing.get('events_per_second_peak', 0)
        if events_per_sec > 20000:
            notes.append(f'High event processing rate ({events_per_sec}/sec peak) - ensure adequate control plane capacity')
        elif events_per_sec > 10000:
            notes.append(f'Event processing: {events_per_sec} events/sec peak (within enterprise capacity)')
        else:
            notes.append(f'Event processing: {events_per_sec} events/sec peak (within growth capacity)')

        # Database notes
        db_growth = metrics.get('db_growth_per_day_gb', 0)
        if db_growth > 100:
            notes.append(f'High database growth rate ({db_growth}GB/day) - consider shorter retention periods')

        # Concurrent jobs note
        concurrent_jobs = metrics.get('concurrent_jobs_peak', 0)
        if concurrent_jobs > 400:
            notes.append(f'High concurrency ({concurrent_jobs} jobs) - execution plane appropriately sized')

        # Migration notes
        notes.append('Test in non-production environment before migration')
        notes.append('Container deployments typically 20-30% more efficient than VMs')
        notes.append('Monitor and adjust resources post-migration based on actual usage')
        notes.append('Validate sizing with Red Hat support for production deployments')

        return notes


def main():
    """Example usage"""
    calculator = AAP26SizingCalculator()

    # Example: User's current AAP 2.4 environment
    current_aap24_metrics = {
        # Controllers
        'num_controllers': 12,
        'controller_cpu_percent_avg': 35,
        'controller_cpu_percent_peak': 50,
        'controller_memory_percent': 20,

        # Automation Hub
        'num_hub_nodes': 2,
        'hub_cpu_percent': 25,
        'hub_memory_percent': 30,

        # Execution Nodes
        'num_execution_nodes': 30,
        'execution_cpu_percent': 90,
        'execution_memory_percent': 50,
        'forks_observed': 165,  # Total concurrent forks observed

        # Database
        'database_vcpu': 16,
        'database_memory_gb': 128,
        'database_cpu_percent': 90,
        'database_memory_percent': 35,
        'concurrent_db_requests_peak': 600,
        'db_growth_per_day_gb': 200,

        # Workload
        'playbooks_per_day_peak': 70000,
        'concurrent_jobs_peak': 500,
        'concurrent_jobs_pending': 30,
        'job_retention_hours': 48,
        'managed_hosts': 40000,
    }

    recommendation = calculator.generate_sizing_recommendation(current_aap24_metrics)

    import json
    print(json.dumps(recommendation, indent=2))


if __name__ == '__main__':
    main()
