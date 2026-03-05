"""
AAP 2.4 to 2.6 Sizing Calculator
Calculates recommended container resources for AAP 2.6 based on AAP 2.4 VM metrics
"""

import math
from typing import Dict, Any


class AAP26SizingCalculator:
    """
    Calculates sizing recommendations for AAP 2.6 container deployment
    based on AAP 2.4 VM metrics and workload characteristics.
    """

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

    # Base resource recommendations (minimum viable)
    BASE_RESOURCES = {
        'gateway': {'cpu': 2, 'memory': 4},  # GB
        'controller_control': {'cpu': 4, 'memory': 16},
        'controller_execution': {'cpu': 4, 'memory': 16},
        'automation_hub': {'cpu': 4, 'memory': 16},
        'eda': {'cpu': 4, 'memory': 16},
        'database': {'cpu': 4, 'memory': 16},
        'redis': {'cpu': 1, 'memory': 2}
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

    def calculate_controller_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate automation controller resources based on current utilization.
        """
        # Extract metrics
        cpu_percent_avg = current_metrics.get('controller_cpu_percent_avg', 35)
        cpu_percent_peak = current_metrics.get('controller_cpu_percent_peak', 50)
        memory_percent = current_metrics.get('controller_memory_percent', 20)
        num_controllers = current_metrics.get('num_controllers', 1)

        # Calculate total current capacity being used
        # If 35% avg on 12 controllers means: 12 * 4 vCPU * 0.35 = 16.8 vCPU avg workload
        # Need headroom for peaks and growth

        total_cpu_needed = math.ceil(num_controllers * 4 * (cpu_percent_peak / 100) * 1.3)  # 30% headroom
        total_memory_needed = math.ceil(num_controllers * 16 * (memory_percent / 100) * 1.5)  # 50% headroom

        # Calculate number of pods needed (each with 4 CPU, 16GB base)
        control_pods = max(2, math.ceil(total_cpu_needed / 4))  # Minimum 2 for HA
        cpu_per_pod = max(4, math.ceil(total_cpu_needed / control_pods))
        memory_per_pod = max(16, math.ceil(total_memory_needed / control_pods))

        return {
            'control_plane_pods': control_pods,
            'cpu_per_pod': cpu_per_pod,
            'memory_per_pod_gb': memory_per_pod,
            'total_cpu': control_pods * cpu_per_pod,
            'total_memory_gb': control_pods * memory_per_pod
        }

    def calculate_execution_node_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate execution node resources based on current utilization.
        """
        cpu_percent = current_metrics.get('execution_cpu_percent', 90)
        memory_percent = current_metrics.get('execution_memory_percent', 50)
        num_execution_nodes = current_metrics.get('num_execution_nodes', 1)
        concurrent_jobs = current_metrics.get('concurrent_jobs_peak', 100)
        forks_observed = current_metrics.get('forks_observed', 150)

        # Each execution node needs capacity for concurrent job execution
        # Assume 4 vCPU, 16GB per execution node baseline
        # High CPU usage indicates we need similar or slightly reduced count (containers are more efficient)

        # Calculate based on concurrent job capacity
        # Rule of thumb: Each execution pod can handle ~15-20 concurrent forks efficiently
        execution_pods = max(2, math.ceil(forks_observed / 15))

        # Resource per pod
        cpu_per_pod = 4
        memory_per_pod = 16

        # Adjust if current utilization is extreme
        if cpu_percent > 95:
            execution_pods = math.ceil(execution_pods * 1.2)  # 20% more capacity

        return {
            'execution_pods': execution_pods,
            'cpu_per_pod': cpu_per_pod,
            'memory_per_pod_gb': memory_per_pod,
            'total_cpu': execution_pods * cpu_per_pod,
            'total_memory_gb': execution_pods * memory_per_pod
        }

    def calculate_database_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate database resources based on workload and current utilization.
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
            jobs_per_day=math.ceil(jobs_per_day / 30),  # Convert to daily if needed
            retention_days=math.ceil(retention_days)
        )

        # Add observed daily growth
        storage_with_buffer = math.ceil(storage_gb + (db_growth_per_day_gb * retention_days * 1.2))

        return {
            'cpu': recommended_cpu,
            'memory_gb': recommended_memory,
            'storage_gb': storage_with_buffer,
            'iops': 3000,  # Minimum required
            'note': 'Consider separate PostgreSQL instances for each component at scale'
        }

    def calculate_automation_hub_resources(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate automation hub resources.
        """
        cpu_percent = current_metrics.get('hub_cpu_percent', 25)
        memory_percent = current_metrics.get('hub_memory_percent', 30)
        num_hub_nodes = current_metrics.get('num_hub_nodes', 2)

        # Hub is less resource intensive, but needs capacity for content sync
        # Minimum 2 pods for HA
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
        Assuming basic EDA usage if not heavily used in 2.4
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

    def generate_sizing_recommendation(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate complete sizing recommendation for AAP 2.6 based on AAP 2.4 metrics.
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
            'summary': {
                'total_cpu': total_cpu,
                'total_memory_gb': total_memory,
                'total_storage_gb': database['storage_gb'],
                'estimated_pods': (gateway['gateway_pods'] + controller['control_plane_pods'] +
                                 execution['execution_pods'] + hub['hub_pods'] +
                                 eda['eda_pods'] + redis.get('total_nodes', redis.get('nodes', 1)))
            },
            'deployment_notes': self._get_deployment_notes(workload_tier, current_metrics)
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

    def _get_deployment_notes(self, tier: str, metrics: Dict[str, Any]) -> list:
        """Generate deployment notes and recommendations."""
        notes = []

        # General notes
        notes.append('All values include headroom for peaks and growth (30-50%)')
        notes.append('Minimum 2 replicas per service recommended for high availability')

        # Topology specific notes
        if tier in ['enterprise', 'enterprise_recommended']:
            notes.append('Consider separate PostgreSQL instances per component for better isolation')
            notes.append('Use clustered Redis (3 primary + 3 replica) for HA')
            notes.append('Implement load balancing for API endpoints')

        # Database notes
        db_growth = metrics.get('db_growth_per_day_gb', 0)
        if db_growth > 100:
            notes.append(f'High database growth rate ({db_growth}GB/day) - consider shorter retention periods')

        # CPU/Memory notes
        controller_cpu = metrics.get('controller_cpu_percent_peak', 0)
        if controller_cpu > 80:
            notes.append('High controller CPU utilization detected - recommend aggressive horizontal scaling')

        execution_cpu = metrics.get('execution_cpu_percent', 0)
        if execution_cpu > 90:
            notes.append('Execution nodes at capacity - additional execution pods recommended')

        # Migration notes
        notes.append('Test in non-production environment before migration')
        notes.append('Container deployments typically 20-30% more efficient than VMs')
        notes.append('Monitor and adjust resources post-migration based on actual usage')

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
        'forks_observed': 165,

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
