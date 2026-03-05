"""
AAP 2.4 to 2.6 Sizing Calculator
Calculates recommended container resources for AAP 2.6 based on AAP 2.4 VM metrics
Using Official Red Hat Excel Reference Formulas
"""

import math
from typing import Dict, Any


class AAP26SizingCalculator:
    """
    Calculates sizing recommendations for AAP 2.6 container deployment
    based on AAP 2.4 VM metrics and workload characteristics.

    Uses official Red Hat formulas from Excel reference:
    - Time-based concurrency: forks = hosts × jobs_per_hostday × job_duration / allowed_hours
    - Memory: (forks × 100MB) / 1024 + 2GB × nodes
    - CPU (AVG): 2 × nodes + forks / 4 / 10
    - Control plane: AVERAGE of event processing AND job management
    """

    # Red Hat official benchmarked constants (from Excel reference)
    MEMORY_PER_FORK_MB = 100  # Memory consumed per parallel fork
    FORKS_PER_CPU = 4  # Number of forks one CPU core can handle
    EVENTS_PER_TASK = 10  # Average events generated per task (with loops)
    EVENT_SIZE_KB = 2  # Event size in database (debug mode)
    FACTS_SIZE_PER_HOST_KB = 50  # Inventory facts per host
    EE_AVERAGE_SIZE_MB = 1600  # Execution Environment image size
    CONTROLLER_EVENTS_PER_SEC = 400  # Events processed per second
    MEMORY_PER_EVENT_FORK_MB = 0.0124  # Memory for event processing
    CPU_PER_EVENT_FORK = 0.00011  # CPU for event processing
    API_CALLS_PER_CONTROLLER = 100  # Concurrent API calls supported

    # Standard node base reservations
    BASE_MEMORY_GB_PER_NODE = 2  # Base memory reservation per node
    BASE_CPU_PER_EXECUTION_NODE = 2  # Base CPU per execution node
    BASE_CPU_PER_CONTROL_NODE = 1.6  # Base CPU per control node

    # Standard node specifications
    STANDARD_NODE_SPEC = {
        'cpu': 4,
        'memory_gb': 16,
        'disk_gb': 128,
        'iops': 3000
    }

    def __init__(self):
        pass

    def calculate_execution_forks(self, number_of_hosts: int, jobs_per_host_per_day: float,
                                  job_duration_hours: float, allowed_hours_per_day: int = 24) -> float:
        """
        Calculate needed forks for parallel execution using time-based formula.

        Formula: forks = (hosts × jobs_per_host_per_day × job_duration_hours) / allowed_hours_per_day

        This accounts for how many jobs need to run concurrently based on:
        - Total daily job volume
        - How long each job takes
        - Time window available for execution
        """
        forks_needed = (
            number_of_hosts *
            jobs_per_host_per_day *
            job_duration_hours /
            allowed_hours_per_day
        )
        return forks_needed

    def calculate_execution_memory(self, forks_needed: float, number_of_nodes: int) -> float:
        """
        Calculate execution node memory using Red Hat's fork-based formula.

        Formula: memory_gb = (forks_needed × 100MB) / 1024 + (2GB × number_of_nodes)
        """
        memory_gb = (forks_needed * self.MEMORY_PER_FORK_MB) / 1024
        memory_total_gb = memory_gb + (self.BASE_MEMORY_GB_PER_NODE * number_of_nodes)
        return memory_total_gb

    def calculate_execution_cpu_avg(self, forks_needed: float, number_of_nodes: int) -> float:
        """
        Calculate execution node CPU using AVERAGED formula (realistic).

        Formula: cpu_avg = 2 × number_of_nodes + forks_needed / 4 / 10

        The /10 divisor accounts for average vs peak load.
        Do NOT use the MAX formula (forks / 4) as it's typically too high.
        """
        cpu_avg = (
            self.BASE_CPU_PER_EXECUTION_NODE * number_of_nodes +
            forks_needed / self.FORKS_PER_CPU / 10
        )
        return cpu_avg

    def calculate_event_forks(self, number_of_hosts: int, jobs_per_host_per_day: float,
                             tasks_per_job: int, job_duration_hours: float,
                             allowed_hours_per_day: int = 24) -> float:
        """
        Calculate event forks that need to be processed in parallel.

        Formula: event_forks = hosts × jobs_per_host_per_day × tasks_per_job ×
                              events_per_task × job_duration_hours / allowed_hours_per_day
        """
        event_forks = (
            number_of_hosts *
            jobs_per_host_per_day *
            tasks_per_job *
            self.EVENTS_PER_TASK *
            job_duration_hours /
            allowed_hours_per_day
        )
        return event_forks

    def calculate_control_memory_for_events(self, event_forks: float, number_of_nodes: int) -> float:
        """
        Calculate control node memory for event processing.

        Formula: memory_gb = (event_forks × 0.0124MB) / 1024 + (2GB × number_of_nodes)
        """
        memory_for_events_mb = event_forks * self.MEMORY_PER_EVENT_FORK_MB
        memory_gb = memory_for_events_mb / 1024 + (self.BASE_MEMORY_GB_PER_NODE * number_of_nodes)
        return memory_gb

    def calculate_control_cpu_for_events_avg(self, event_forks: float, number_of_nodes: int) -> float:
        """
        Calculate control node CPU for event processing (AVERAGED).

        Formula: cpu_avg = event_forks × 0.00011 / 10 + (1.6 × number_of_nodes)
        """
        cpu_avg = (
            event_forks * self.CPU_PER_EVENT_FORK / 10 +
            self.BASE_CPU_PER_CONTROL_NODE * number_of_nodes
        )
        return cpu_avg

    def calculate_control_memory_for_jobs(self, forks_for_jobs: float, number_of_nodes: int) -> float:
        """
        Calculate control node memory for job management.

        Formula: memory_gb = (forks_for_jobs × 100MB) / 1024 + (2GB × number_of_nodes)
        """
        memory_gb = (forks_for_jobs * self.MEMORY_PER_FORK_MB) / 1024
        memory_total_gb = memory_gb + (self.BASE_MEMORY_GB_PER_NODE * number_of_nodes)
        return memory_total_gb

    def calculate_control_cpu_for_jobs_avg(self, forks_for_jobs: float, number_of_nodes: int) -> float:
        """
        Calculate control node CPU for job management (AVERAGED).

        Formula: cpu_avg = 2 × number_of_nodes + forks_for_jobs / 4 / 10
        """
        cpu_avg = (
            self.BASE_CPU_PER_EXECUTION_NODE * number_of_nodes +
            forks_for_jobs / self.FORKS_PER_CPU / 10
        )
        return cpu_avg

    def calculate_database_storage(self, number_of_hosts: int, jobs_per_host_per_day: float,
                                  tasks_per_job: int, days_to_keep_jobs: int) -> Dict[str, Any]:
        """
        Calculate database storage requirements.

        Formula:
        - Facts: hosts × 50KB / 1024 (MB)
        - Inventory: hosts × 50KB / 1024 (MB)
        - Jobs: hosts × jobs_per_host_per_day × tasks_per_job × events_per_task ×
                days_to_keep_jobs × 2KB / 1024 (MB)
        - Total: (Facts + Inventory + Jobs) / 1024 (GB)
        """
        # Facts storage
        db_facts_mb = (number_of_hosts * self.FACTS_SIZE_PER_HOST_KB) / 1024

        # Inventory storage (similar to facts)
        db_inventory_mb = (number_of_hosts * self.FACTS_SIZE_PER_HOST_KB) / 1024

        # Jobs storage (MAIN COMPONENT)
        db_jobs_mb = (
            number_of_hosts *
            jobs_per_host_per_day *
            tasks_per_job *
            self.EVENTS_PER_TASK *
            days_to_keep_jobs *
            self.EVENT_SIZE_KB
        ) / 1024

        # Total database size
        db_total_gb = (db_facts_mb + db_inventory_mb + db_jobs_mb) / 1024

        return {
            'facts_mb': db_facts_mb,
            'inventory_mb': db_inventory_mb,
            'jobs_mb': db_jobs_mb,
            'total_gb': db_total_gb
        }

    def calculate_execution_node_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate execution node resources using time-based concurrency formula.

        Uses Excel formulas:
        - Forks = hosts × jobs_per_hostday × job_duration / allowed_hours
        - Memory = forks × 100 / 1024 + 2 × nodes
        - CPU (AVG) = 2 × nodes + forks / 4 / 10
        """
        # Extract parameters
        managed_hosts = current_metrics.get('managed_hosts', 0)
        playbooks_per_day = current_metrics.get('playbooks_per_day_peak', 0)

        # Calculate jobs per host per day
        if managed_hosts > 0:
            jobs_per_host_per_day = playbooks_per_day / managed_hosts
        else:
            jobs_per_host_per_day = 0

        # Get job characteristics
        tasks_per_job = current_metrics.get('tasks_per_job', 100)
        job_duration_hours = current_metrics.get('job_duration_hours', 0.25)  # 15 minutes default
        allowed_hours_per_day = current_metrics.get('allowed_hours_per_day', 24)  # 24/7 default

        # Calculate forks needed
        forks_needed = self.calculate_execution_forks(
            managed_hosts,
            jobs_per_host_per_day,
            job_duration_hours,
            allowed_hours_per_day
        )

        # Start with minimum 2 nodes for HA
        execution_nodes = max(2, math.ceil(forks_needed / 50))  # ~50 forks per node as baseline

        # Calculate memory needed
        memory_total_gb = self.calculate_execution_memory(forks_needed, execution_nodes)

        # Calculate CPU needed (averaged)
        cpu_total = self.calculate_execution_cpu_avg(forks_needed, execution_nodes)

        # Adjust nodes if memory or CPU per node exceeds reasonable limits
        memory_per_pod = memory_total_gb / execution_nodes
        cpu_per_pod = cpu_total / execution_nodes

        # If memory per pod > 32GB or CPU > 8, add more nodes
        if memory_per_pod > 32:
            execution_nodes = math.ceil(memory_total_gb / 32)
            memory_per_pod = math.ceil(memory_total_gb / execution_nodes)
            cpu_per_pod = cpu_total / execution_nodes

        if cpu_per_pod > 8:
            execution_nodes = math.ceil(cpu_total / 8)
            cpu_per_pod = math.ceil(cpu_total / execution_nodes)
            memory_per_pod = math.ceil(memory_total_gb / execution_nodes)

        return {
            'execution_pods': execution_nodes,
            'cpu_per_pod': math.ceil(cpu_per_pod),
            'memory_per_pod_gb': math.ceil(memory_per_pod),
            'total_cpu': math.ceil(cpu_total),
            'total_memory_gb': math.ceil(memory_total_gb),
            'forks_needed': round(forks_needed, 2),
            'jobs_per_host_per_day': round(jobs_per_host_per_day, 2),
            'note': f'Time-based calculation: {managed_hosts} hosts × {round(jobs_per_host_per_day, 2)} jobs/host/day × {job_duration_hours}h job / {allowed_hours_per_day}h day = {round(forks_needed, 2)} forks'
        }

    def calculate_controller_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate automation controller control plane resources.

        Control plane needs BOTH event processing AND job management capacity,
        then uses the AVERAGE of both (as per Excel row 54).
        """
        # Extract parameters
        managed_hosts = current_metrics.get('managed_hosts', 0)
        playbooks_per_day = current_metrics.get('playbooks_per_day_peak', 0)
        tasks_per_job = current_metrics.get('tasks_per_job', 100)
        job_duration_hours = current_metrics.get('job_duration_hours', 0.25)
        allowed_hours_per_day = current_metrics.get('allowed_hours_per_day', 24)
        average_forks_per_job = current_metrics.get('forks_observed', 5)

        # Calculate jobs per host per day
        if managed_hosts > 0:
            jobs_per_host_per_day = playbooks_per_day / managed_hosts
        else:
            jobs_per_host_per_day = 0

        # Start with 2 control nodes for HA
        control_nodes = 2

        # Step 1: Calculate event processing capacity
        event_forks = self.calculate_event_forks(
            managed_hosts,
            jobs_per_host_per_day,
            tasks_per_job,
            job_duration_hours,
            allowed_hours_per_day
        )

        memory_for_events = self.calculate_control_memory_for_events(event_forks, control_nodes)
        cpu_for_events = self.calculate_control_cpu_for_events_avg(event_forks, control_nodes)

        # Step 2: Calculate job management capacity
        concurrent_jobs = (playbooks_per_day * job_duration_hours) / allowed_hours_per_day
        forks_for_jobs = concurrent_jobs * average_forks_per_job

        memory_for_jobs = self.calculate_control_memory_for_jobs(forks_for_jobs, control_nodes)
        cpu_for_jobs = self.calculate_control_cpu_for_jobs_avg(forks_for_jobs, control_nodes)

        # Step 3: AVERAGE both (as per Excel formula)
        memory_control_gb = (memory_for_events + memory_for_jobs) / 2
        cpu_control = (cpu_for_events + cpu_for_jobs) / 2

        # Adjust if per-node resources exceed limits
        memory_per_pod = memory_control_gb / control_nodes
        cpu_per_pod = cpu_control / control_nodes

        if memory_per_pod > 128:
            control_nodes = math.ceil(memory_control_gb / 128)
            memory_per_pod = math.ceil(memory_control_gb / control_nodes)
            cpu_per_pod = cpu_control / control_nodes

        if cpu_per_pod > 32:
            control_nodes = math.ceil(cpu_control / 32)
            cpu_per_pod = math.ceil(cpu_control / control_nodes)
            memory_per_pod = math.ceil(memory_control_gb / control_nodes)

        return {
            'control_plane_pods': control_nodes,
            'cpu_per_pod': math.ceil(cpu_per_pod),
            'memory_per_pod_gb': math.ceil(memory_per_pod),
            'total_cpu': math.ceil(cpu_control),
            'total_memory_gb': math.ceil(memory_control_gb),
            'event_forks': round(event_forks, 2),
            'forks_for_jobs': round(forks_for_jobs, 2),
            'calculation_breakdown': {
                'event_processing': {
                    'memory_gb': round(memory_for_events, 2),
                    'cpu': round(cpu_for_events, 2)
                },
                'job_management': {
                    'memory_gb': round(memory_for_jobs, 2),
                    'cpu': round(cpu_for_jobs, 2)
                },
                'averaged_result': {
                    'memory_gb': round(memory_control_gb, 2),
                    'cpu': round(cpu_control, 2)
                }
            },
            'note': 'Control plane uses AVERAGED result of event processing AND job management capacity'
        }

    def calculate_database_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate database resources based on workload.
        """
        # Extract parameters
        managed_hosts = current_metrics.get('managed_hosts', 0)
        playbooks_per_day = current_metrics.get('playbooks_per_day_peak', 0)
        tasks_per_job = current_metrics.get('tasks_per_job', 100)
        days_to_keep_jobs = current_metrics.get('job_retention_hours', 48) / 24

        # Calculate jobs per host per day
        if managed_hosts > 0:
            jobs_per_host_per_day = playbooks_per_day / managed_hosts
        else:
            jobs_per_host_per_day = 0

        # Calculate storage using Excel formula
        storage_breakdown = self.calculate_database_storage(
            managed_hosts,
            jobs_per_host_per_day,
            tasks_per_job,
            math.ceil(days_to_keep_jobs)
        )

        # Get current utilization if available
        cpu_percent = current_metrics.get('database_cpu_percent', 50)
        memory_percent = current_metrics.get('database_memory_percent', 35)
        current_db_vcpu = current_metrics.get('database_vcpu', 16)
        current_db_memory = current_metrics.get('database_memory_gb', 128)

        # Calculate actual used resources
        actual_cpu_used = current_db_vcpu * (cpu_percent / 100)
        actual_memory_used = current_db_memory * (memory_percent / 100)

        # Add headroom for growth and peaks
        recommended_cpu = max(8, math.ceil(actual_cpu_used * 1.3))  # 30% headroom
        recommended_memory = max(32, math.ceil(actual_memory_used * 1.5))  # 50% headroom

        # Storage with 20% buffer
        storage_with_buffer = math.ceil(storage_breakdown['total_gb'] * 1.2)

        return {
            'cpu': recommended_cpu,
            'memory_gb': recommended_memory,
            'storage_gb': max(60, storage_with_buffer),  # Minimum 60GB
            'iops': 3000,
            'storage_breakdown': {
                'facts_mb': round(storage_breakdown['facts_mb'], 2),
                'inventory_mb': round(storage_breakdown['inventory_mb'], 2),
                'jobs_mb': round(storage_breakdown['jobs_mb'], 2),
                'total_gb': round(storage_breakdown['total_gb'], 2)
            },
            'note': 'Storage based on jobs history; CPU/Memory based on current utilization with headroom'
        }

    def calculate_automation_hub_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate automation hub resources.
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
            'note': 'Minimum 2 pods for HA; scale based on collection sync and content serving needs'
        }

    def calculate_gateway_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate platform gateway resources.
        """
        managed_hosts = current_metrics.get('managed_hosts', 0)

        if managed_hosts > 20000:
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
            'total_memory_gb': gateway_pods * memory_per_pod,
            'note': 'Gateway handles authentication and routing; 2-3 pods for HA'
        }

    def calculate_eda_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Event-Driven Ansible resources.
        """
        # Basic EDA setup, can be scaled based on activations
        eda_pods = 2
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

    def calculate_redis_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Redis resources.
        """
        managed_hosts = current_metrics.get('managed_hosts', 0)

        if managed_hosts > 10000:
            # Clustered Redis for enterprise
            return {
                'type': 'clustered',
                'primary_nodes': 3,
                'replica_nodes': 3,
                'cpu_per_node': 1,
                'memory_per_node_gb': 4,
                'total_nodes': 6,
                'total_cpu': 6,
                'total_memory_gb': 24,
                'note': 'Clustered Redis (3 primary + 3 replica) for high availability'
            }
        else:
            # Standalone Redis
            return {
                'type': 'standalone',
                'nodes': 1,
                'cpu': 1,
                'memory_gb': 2,
                'total_cpu': 1,
                'total_memory_gb': 2,
                'note': 'Standalone Redis for smaller deployments'
            }

    def generate_sizing_recommendation(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate complete sizing recommendation for AAP 2.6 based on AAP 2.4 metrics.
        Uses official Red Hat Excel reference formulas.
        """
        # Calculate resources for each component
        gateway = self.calculate_gateway_resources(current_metrics)
        controller = self.calculate_controller_resources(current_metrics)
        execution = self.calculate_execution_node_resources(current_metrics)
        database = self.calculate_database_resources(current_metrics)
        hub = self.calculate_automation_hub_resources(current_metrics)
        eda = self.calculate_eda_resources(current_metrics)
        redis = self.calculate_redis_resources(current_metrics)

        # Calculate totals
        total_cpu = (
            gateway['total_cpu'] +
            controller['total_cpu'] +
            execution['total_cpu'] +
            database['cpu'] +
            hub['total_cpu'] +
            eda['total_cpu'] +
            redis['total_cpu']
        )

        total_memory = (
            gateway['total_memory_gb'] +
            controller['total_memory_gb'] +
            execution['total_memory_gb'] +
            database['memory_gb'] +
            hub['total_memory_gb'] +
            eda['total_memory_gb'] +
            redis['total_memory_gb']
        )

        # Determine topology
        managed_hosts = current_metrics.get('managed_hosts', 0)
        if managed_hosts > 10000:
            topology = 'enterprise'
        elif managed_hosts > 5000:
            topology = 'enterprise_recommended'
        else:
            topology = 'growth'

        return {
            'topology': topology,
            'components': {
                'platform_gateway': gateway,
                'automation_controller_control_plane': controller,
                'automation_controller_execution_plane': execution,
                'database': database,
                'automation_hub': hub,
                'event_driven_ansible': eda,
                'redis': redis
            },
            'summary': {
                'total_cpu': total_cpu,
                'total_memory_gb': total_memory,
                'total_storage_gb': database['storage_gb'],
                'estimated_pods': (
                    gateway['gateway_pods'] +
                    controller['control_plane_pods'] +
                    execution['execution_pods'] +
                    hub['hub_pods'] +
                    eda['eda_pods'] +
                    redis.get('total_nodes', redis.get('nodes', 1))
                )
            },
            'formulas_used': {
                'source': 'Red Hat AAP Excel Reference Sheet (AAp-sizing-sheet-reference.xlsx)',
                'execution_forks': 'hosts × jobs_per_host_per_day × job_duration_hours / allowed_hours_per_day',
                'execution_memory': 'forks × 100MB / 1024 + 2GB × nodes',
                'execution_cpu': '2 × nodes + forks / 4 / 10 (averaged)',
                'control_plane': 'AVERAGE of (event_processing + job_management) / 2',
                'event_forks': 'hosts × jobs_per_host_per_day × tasks_per_job × 10 events/task × duration / allowed_hours',
                'database_storage': 'hosts × jobs_per_host_per_day × tasks_per_job × 10 events × retention_days × 2KB / 1024'
            },
            'deployment_notes': self._get_deployment_notes(current_metrics, execution, controller)
        }

    def _get_deployment_notes(self, metrics: Dict[str, Any], execution: Dict[str, Any],
                             controller: Dict[str, Any]) -> list:
        """Generate deployment notes and recommendations."""
        notes = []

        # Calculation method note
        notes.append('✓ Calculations based on official Red Hat Excel reference formulas')
        notes.append('✓ Uses time-based concurrency: forks = hosts × jobs/host/day × duration / allowed_hours')
        notes.append('✓ Control plane uses AVERAGED result of event processing AND job management')
        notes.append(f'✓ Execution plane: {execution.get("forks_needed", 0)} forks needed')
        notes.append(f'✓ Control plane: {controller.get("event_forks", 0)} event forks, {controller.get("forks_for_jobs", 0)} job forks')

        # General recommendations
        notes.append('All values include appropriate headroom for peaks and growth')
        notes.append('Minimum 2 replicas per service recommended for high availability')
        notes.append('Container deployments typically 20-30% more efficient than VMs')

        # Specific recommendations
        managed_hosts = metrics.get('managed_hosts', 0)
        if managed_hosts > 20000:
            notes.append('Consider separate PostgreSQL instances per component for better isolation')
            notes.append('Use clustered Redis (3 primary + 3 replica) for HA')
            notes.append('Implement load balancing for API endpoints')

        # Migration notes
        notes.append('Test in non-production environment before migration')
        notes.append('Monitor and adjust resources post-migration based on actual usage')
        notes.append('Validate sizing with Red Hat support for production deployments')

        return notes


def main():
    """Example usage"""
    calculator = AAP26SizingCalculator()

    # Example: User's current AAP 2.4 environment
    current_aap24_metrics = {
        # Managed environment
        'managed_hosts': 40000,

        # Workload characteristics
        'playbooks_per_day_peak': 70000,
        'tasks_per_job': 100,  # Average tasks per playbook
        'job_duration_hours': 0.25,  # 15 minutes average
        'allowed_hours_per_day': 24,  # 24/7 operation
        'job_retention_hours': 48,  # Keep jobs for 2 days
        'forks_observed': 5,  # Average forks per job

        # Current controllers
        'num_controllers': 12,

        # Automation Hub
        'num_hub_nodes': 2,
        'hub_cpu_percent': 25,
        'hub_memory_percent': 30,

        # Database
        'database_vcpu': 16,
        'database_memory_gb': 128,
        'database_cpu_percent': 90,
        'database_memory_percent': 35,
    }

    recommendation = calculator.generate_sizing_recommendation(current_aap24_metrics)

    import json
    print(json.dumps(recommendation, indent=2))


if __name__ == '__main__':
    main()
