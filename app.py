"""
Flask web application for AAP 2.4 to 2.6 Sizing Calculator
"""

from flask import Flask, render_template, request, jsonify
from sizing_calculator import AAP26SizingCalculator
import json

app = Flask(__name__)
calculator = AAP26SizingCalculator()


@app.route('/')
def index():
    """Render the main calculator interface"""
    return render_template('index.html')


@app.route('/api/calculate', methods=['POST'])
def calculate_sizing():
    """
    API endpoint to calculate AAP 2.6 sizing based on AAP 2.4 metrics
    """
    try:
        metrics = request.get_json()

        # Validate required fields
        required_fields = [
            'num_controllers', 'controller_cpu_percent_avg', 'controller_cpu_percent_peak',
            'controller_memory_percent', 'num_execution_nodes', 'execution_cpu_percent',
            'execution_memory_percent', 'database_vcpu', 'database_memory_gb',
            'database_cpu_percent', 'database_memory_percent', 'playbooks_per_day_peak',
            'concurrent_jobs_peak'
        ]

        for field in required_fields:
            if field not in metrics:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Calculate sizing recommendation
        recommendation = calculator.generate_sizing_recommendation(metrics)

        return jsonify(recommendation)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/example', methods=['GET'])
def get_example_data():
    """
    Return example AAP 2.4 metrics for testing
    """
    example_data = {
        'num_controllers': 12,
        'controller_cpu_percent_avg': 35,
        'controller_cpu_percent_peak': 50,
        'controller_memory_percent': 20,
        'num_hub_nodes': 2,
        'hub_cpu_percent': 25,
        'hub_memory_percent': 30,
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
        'managed_hosts': 40000
    }
    return jsonify(example_data)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
