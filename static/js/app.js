// AAP Sizing Calculator - Client-side JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('sizingForm');
    const loadExampleBtn = document.getElementById('loadExample');
    const resultsDiv = document.getElementById('results');
    const resultsContent = document.getElementById('resultsContent');

    // Load example data
    loadExampleBtn.addEventListener('click', async function(e) {
        e.preventDefault();
        try {
            const response = await fetch('/api/example');
            const data = await response.json();

            // Populate form with example data
            Object.keys(data).forEach(key => {
                const input = document.getElementById(key);
                if (input) {
                    input.value = data[key];
                }
            });

            showAlert('Example data loaded successfully!', 'success');
        } catch (error) {
            showAlert('Failed to load example data', 'error');
        }
    });

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Collect form data
        const formData = new FormData(form);
        const data = {};

        for (let [key, value] of formData.entries()) {
            data[key] = parseFloat(value) || 0;
        }

        // Show loading state
        resultsContent.innerHTML = '<div class="loading">Calculating sizing recommendations</div>';
        resultsDiv.style.display = 'block';

        try {
            // Send data to API
            const response = await fetch('/api/calculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error('Calculation failed');
            }

            const result = await response.json();
            displayResults(result);

        } catch (error) {
            resultsContent.innerHTML = `
                <div class="alert alert-error">
                    <strong>Error:</strong> ${error.message}
                </div>
            `;
        }
    });

    function displayResults(result) {
        const { topology, components, summary, deployment_notes } = result;

        let html = `
            <div class="topology-info">
                <h3>Recommended Topology</h3>
                <span class="topology-badge ${topology}">${formatTier(topology)}</span>
            </div>

            <div class="summary-grid">
                <div class="summary-item">
                    <h4>Total CPU</h4>
                    <div class="value">${summary.total_cpu}</div>
                    <small>vCPU cores</small>
                </div>
                <div class="summary-item">
                    <h4>Total Memory</h4>
                    <div class="value">${summary.total_memory_gb}</div>
                    <small>GB RAM</small>
                </div>
                <div class="summary-item">
                    <h4>Storage</h4>
                    <div class="value">${summary.total_storage_gb}</div>
                    <small>GB</small>
                </div>
                <div class="summary-item">
                    <h4>Total Pods</h4>
                    <div class="value">${summary.estimated_pods}</div>
                    <small>containers</small>
                </div>
            </div>

            <h3 style="margin-top: 30px; margin-bottom: 20px;">Component Breakdown</h3>
        `;

        // Platform Gateway
        html += createComponentSection(
            'Platform Gateway',
            '🔒',
            components.platform_gateway,
            ['gateway_pods', 'cpu_per_pod', 'memory_per_pod_gb', 'total_cpu', 'total_memory_gb']
        );

        // Automation Controller - Control Plane
        html += createComponentSection(
            'Automation Controller - Control Plane',
            '🎛️',
            components.automation_controller_control_plane,
            ['control_plane_pods', 'cpu_per_pod', 'memory_per_pod_gb', 'total_cpu', 'total_memory_gb']
        );

        // Automation Controller - Execution Plane
        html += createComponentSection(
            'Automation Controller - Execution Plane',
            '⚙️',
            components.automation_controller_execution_plane,
            ['execution_pods', 'cpu_per_pod', 'memory_per_pod_gb', 'total_cpu', 'total_memory_gb']
        );

        // Database
        html += createComponentSection(
            'Database (PostgreSQL)',
            '💾',
            components.database,
            ['cpu', 'memory_gb', 'storage_gb', 'iops']
        );

        // Automation Hub
        html += createComponentSection(
            'Automation Hub',
            '📦',
            components.automation_hub,
            ['hub_pods', 'cpu_per_pod', 'memory_per_pod_gb', 'total_cpu', 'total_memory_gb']
        );

        // Event-Driven Ansible
        html += createComponentSection(
            'Event-Driven Ansible',
            '⚡',
            components.event_driven_ansible,
            ['eda_pods', 'cpu_per_pod', 'memory_per_pod_gb', 'total_cpu', 'total_memory_gb']
        );

        // Redis
        const redisFields = components.redis.type === 'clustered'
            ? ['type', 'primary_nodes', 'replica_nodes', 'cpu_per_node', 'memory_per_node_gb', 'total_cpu', 'total_memory_gb']
            : ['type', 'nodes', 'cpu', 'memory_gb'];

        html += createComponentSection(
            'Redis Cache',
            '🔴',
            components.redis,
            redisFields
        );

        // Deployment Notes
        html += `
            <div class="notes-section">
                <h4>📋 Deployment Notes</h4>
                <ul>
                    ${deployment_notes.map(note => `<li>${note}</li>`).join('')}
                </ul>
            </div>
        `;

        resultsContent.innerHTML = html;
    }

    function createComponentSection(title, icon, data, fields) {
        let html = `
            <div class="component-section">
                <h4>${icon} ${title}</h4>
                <div class="resource-grid">
        `;

        fields.forEach(field => {
            if (data[field] !== undefined) {
                html += `
                    <div class="resource-item">
                        <div class="label">${formatFieldName(field)}</div>
                        <div class="value">${formatValue(field, data[field])}</div>
                    </div>
                `;
            }
        });

        if (data.note) {
            html += `
                <div class="resource-item" style="grid-column: 1 / -1;">
                    <div class="label">Note</div>
                    <div style="font-size: 0.9rem; margin-top: 5px;">${data.note}</div>
                </div>
            `;
        }

        html += `
                </div>
            </div>
        `;

        return html;
    }

    function formatFieldName(field) {
        return field
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase())
            .replace('Cpu', 'CPU')
            .replace('Gb', 'GB')
            .replace('Iops', 'IOPS')
            .replace('Eda', 'EDA');
    }

    function formatValue(field, value) {
        if (field.includes('cpu') && !field.includes('vcpu')) {
            return `${value} vCPU`;
        } else if (field.includes('memory') || field.includes('gb')) {
            return `${value} GB`;
        } else if (field.includes('storage')) {
            return `${value} GB`;
        } else if (field.includes('iops')) {
            return `${value}`;
        } else if (field.includes('pods') || field.includes('nodes')) {
            return `${value}`;
        } else if (field === 'type') {
            return value.charAt(0).toUpperCase() + value.slice(1);
        } else {
            return value;
        }
    }

    function formatTier(tier) {
        if (!tier) return 'Unknown';
        return tier
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    function showAlert(message, type) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;

        form.insertBefore(alert, form.firstChild);

        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
});
