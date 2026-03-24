# Phase 1 Testing Guide

**Branch:** `enhance-calculator-accuracy`
**Features to Test:** Verbosity levels, Peak patterns, Input validation, Results validation

---

## Quick Test: Run the Enhanced Calculator

### Option 1: Command Line Testing

```bash
source venv/bin/activate
python3 -c "
from sizing_calculator import AAP26SizingCalculator
import json

calc = AAP26SizingCalculator()

# Your metrics here
metrics = {
    'managed_hosts': 40000,
    'playbooks_per_day_peak': 70000,
    'tasks_per_job': 100,
    'job_duration_hours': 0.25,
    'allowed_hours_per_day': 24,
    'job_retention_hours': 48,
    'forks_observed': 5,

    # NEW PARAMETERS (Phase 1):
    'verbosity_level': 1,              # 0-4 (0=minimal, 1=normal, 2=verbose, 3=debug, 4=connection)
    'peak_pattern': 'distributed_24x7', # Options: distributed_24x7, business_hours, batch_window, mixed

    # Existing required parameters:
    'database_vcpu': 16,
    'database_memory_gb': 128,
    'database_cpu_percent': 90,
    'database_memory_percent': 35,
    'num_hub_nodes': 2,
    'hub_cpu_percent': 25,
    'hub_memory_percent': 30,
    'num_controllers': 12,
    'controller_cpu_percent_avg': 35,
    'controller_cpu_percent_peak': 50,
    'controller_memory_percent': 20,
    'num_execution_nodes': 30,
    'execution_cpu_percent': 90,
    'execution_memory_percent': 50
}

result = calc.generate_sizing_recommendation(metrics)

# Show key results
print('EXECUTION PLANE:')
exec_p = result['components']['automation_controller_execution_plane']
print(f\"  Pattern: {exec_p.get('peak_pattern')} ({exec_p.get('peak_multiplier')}x)\")
print(f\"  Forks: {exec_p.get('forks_needed')}\")
print(f\"  Pods: {exec_p.get('execution_pods')}\")
print(f\"  CPU: {exec_p.get('total_cpu')} vCPU\")
print(f\"  Memory: {exec_p.get('total_memory_gb')} GB\")

print('\nCONTROL PLANE:')
ctrl = result['components']['automation_controller_control_plane']
print(f\"  Verbosity: Level {ctrl.get('verbosity_level')} ({ctrl.get('events_per_task')} events/task)\")
print(f\"  Event Forks: {ctrl.get('event_forks'):,.0f}\")
print(f\"  Pods: {ctrl.get('control_plane_pods')}\")
print(f\"  CPU: {ctrl.get('total_cpu')} vCPU\")
print(f\"  Memory: {ctrl.get('total_memory_gb')} GB\")

print('\nWARNINGS:')
for warning in result.get('warnings', []):
    print(f\"  {warning}\")

print(f\"\nTotal Warnings: {len(result.get('warnings', []))}\")
"
```

### Option 2: Use Test Script

Create a test file:

```bash
cat > test_phase1.py << 'EOF'
#!/usr/bin/env python3
from sizing_calculator import AAP26SizingCalculator
import json

def test_scenario(name, metrics, show_full=False):
    calc = AAP26SizingCalculator()
    result = calc.generate_sizing_recommendation(metrics)

    exec_p = result['components']['automation_controller_execution_plane']
    ctrl = result['components']['automation_controller_control_plane']

    print(f"\n{'='*70}")
    print(f"SCENARIO: {name}")
    print(f"{'='*70}")
    print(f"Peak Pattern: {exec_p.get('peak_pattern')} ({exec_p.get('peak_multiplier')}x)")
    print(f"Verbosity: Level {ctrl.get('verbosity_level')} ({ctrl.get('events_per_task')} events/task)")
    print()
    print(f"EXECUTION - Pods: {exec_p.get('execution_pods'):3}, CPU: {exec_p.get('total_cpu'):4} vCPU, Memory: {exec_p.get('total_memory_gb'):4} GB")
    print(f"CONTROL   - Pods: {ctrl.get('control_plane_pods'):3}, CPU: {ctrl.get('total_cpu'):4} vCPU, Memory: {ctrl.get('total_memory_gb'):4} GB")

    warnings = result.get('warnings', [])
    if warnings:
        print(f"\n⚠️ WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  • {w}")

    if show_full:
        print(f"\nFULL RESULT:")
        print(json.dumps(result, indent=2))

# Base metrics
base = {
    'managed_hosts': 40000,
    'playbooks_per_day_peak': 70000,
    'tasks_per_job': 100,
    'job_duration_hours': 0.25,
    'allowed_hours_per_day': 24,
    'job_retention_hours': 48,
    'forks_observed': 5,
    'database_vcpu': 16,
    'database_memory_gb': 128,
    'database_cpu_percent': 90,
    'database_memory_percent': 35,
    'num_hub_nodes': 2,
    'hub_cpu_percent': 25,
    'hub_memory_percent': 30,
    'num_controllers': 12
}

# Test 1: Baseline (distributed, normal verbosity)
test1 = base.copy()
test1.update({
    'verbosity_level': 1,
    'peak_pattern': 'distributed_24x7'
})
test_scenario("Baseline - Distributed 24/7, Normal Verbosity", test1)

# Test 2: Business hours (2.5x impact!)
test2 = base.copy()
test2.update({
    'verbosity_level': 1,
    'peak_pattern': 'business_hours'
})
test_scenario("Business Hours Pattern (2.5x multiplier)", test2)

# Test 3: Debug verbosity
test3 = base.copy()
test3.update({
    'verbosity_level': 3,
    'peak_pattern': 'distributed_24x7'
})
test_scenario("Debug Verbosity (Level 3)", test3)

# Test 4: Worst case - batch window + debug
test4 = base.copy()
test4.update({
    'verbosity_level': 3,
    'peak_pattern': 'batch_window'
})
test_scenario("Worst Case - Batch Window + Debug", test4)

# Test 5: Best case - distributed + minimal verbosity
test5 = base.copy()
test5.update({
    'verbosity_level': 0,
    'peak_pattern': 'distributed_24x7'
})
test_scenario("Best Case - Distributed + Minimal Verbosity", test5)

print(f"\n{'='*70}")
print("Testing complete!")
print(f"{'='*70}")
EOF

chmod +x test_phase1.py
python3 test_phase1.py
```

---

## Test Scenarios

### Scenario 1: Baseline (What most users should have)

**Parameters:**
- 40,000 hosts
- 70,000 jobs/day
- Distributed 24/7
- Normal verbosity (level 1)

**Expected Results:**
- Execution: ~15 pods, ~49 vCPU, ~102 GB
- Control: ~2 pods, ~52 vCPU, ~185 GB
- No warnings

### Scenario 2: Business Hours (Very common in enterprises)

**Parameters:**
- Same as baseline
- Peak pattern: `business_hours` (2.5x multiplier)

**Expected Results:**
- Execution: ~37 pods, ~120 vCPU, ~253 GB (2.5x increase!)
- Control: Same as baseline
- No warnings

### Scenario 3: Debug Mode (Troubleshooting)

**Parameters:**
- Same as baseline
- Verbosity: Level 3 (debug)

**Expected Results:**
- Execution: Same as baseline
- Control: ~63 vCPU, ~198 GB (20% increase!)
- Possible warning if control > 2x execution

### Scenario 4: Batch Jobs (Common for patching)

**Parameters:**
- Same as baseline
- Peak pattern: `batch_window` (10x multiplier!)

**Expected Results:**
- Execution: ~146 pods, ~450 vCPU, ~986 GB (10x increase!)
- Control: Same as baseline
- Warning: "50+ execution pods is very large"

### Scenario 5: Invalid Inputs (Test validation)

**Parameters:**
- tasks_per_job: 500 (way too high)
- job_duration_hours: 5.0 (very unusual)
- forks_observed: 100 (too many)

**Expected Results:**
- Warnings about unusual values
- Calculation still completes
- Suggests typical ranges

---

## Comparison Test: Old vs New Calculator

Run this to see the difference:

```python
from sizing_calculator import AAP26SizingCalculator

calc = AAP26SizingCalculator()

# Same workload, different patterns
base_metrics = {
    'managed_hosts': 40000,
    'playbooks_per_day_peak': 70000,
    'tasks_per_job': 100,
    'job_duration_hours': 0.25,
    'allowed_hours_per_day': 24,
    'job_retention_hours': 48,
    'forks_observed': 5,
    'database_vcpu': 16,
    'database_memory_gb': 128,
    'database_cpu_percent': 90,
    'database_memory_percent': 35,
}

print("OLD BEHAVIOR (assumed distributed, verbosity 1):")
old = base_metrics.copy()
old.update({'verbosity_level': 1, 'peak_pattern': 'distributed_24x7'})
result_old = calc.generate_sizing_recommendation(old)
exec_old = result_old['components']['automation_controller_execution_plane']
ctrl_old = result_old['components']['automation_controller_control_plane']
print(f"  Execution: {exec_old['execution_pods']} pods, {exec_old['total_cpu']} vCPU, {exec_old['total_memory_gb']} GB")
print(f"  Control:   {ctrl_old['control_plane_pods']} pods, {ctrl_old['total_cpu']} vCPU, {ctrl_old['total_memory_gb']} GB")

print("\nREALITY (business hours, debug verbosity):")
real = base_metrics.copy()
real.update({'verbosity_level': 3, 'peak_pattern': 'business_hours'})
result_real = calc.generate_sizing_recommendation(real)
exec_real = result_real['components']['automation_controller_execution_plane']
ctrl_real = result_real['components']['automation_controller_control_plane']
print(f"  Execution: {exec_real['execution_pods']} pods, {exec_real['total_cpu']} vCPU, {exec_real['total_memory_gb']} GB")
print(f"  Control:   {ctrl_real['control_plane_pods']} pods, {ctrl_real['total_cpu']} vCPU, {ctrl_real['total_memory_gb']} GB")

print("\nDIFFERENCE:")
exec_diff = (exec_real['total_cpu'] / exec_old['total_cpu'] - 1) * 100
ctrl_diff = (ctrl_real['total_cpu'] / ctrl_old['total_cpu'] - 1) * 100
print(f"  Execution CPU: +{exec_diff:.0f}%")
print(f"  Control CPU:   +{ctrl_diff:.0f}%")
print(f"\n⚠️ Old calculator would have UNDER-SIZED by {max(exec_diff, ctrl_diff):.0f}%!")
```

---

## Validation Testing

### Test 1: Input Warnings

```python
from sizing_calculator import AAP26SizingCalculator

calc = AAP26SizingCalculator()

# Bad inputs
bad_metrics = {
    'managed_hosts': 40000,
    'playbooks_per_day_peak': 70000,
    'tasks_per_job': 500,         # WAY TOO HIGH (typical: 10-100)
    'job_duration_hours': 5.0,    # VERY LONG (typical: 0.02-2.0)
    'forks_observed': 100,        # TOO MANY (typical: 5-25)
    'allowed_hours_per_day': 24,
    'job_retention_hours': 48,
    'verbosity_level': 1,
    'peak_pattern': 'distributed_24x7',
    'database_vcpu': 16,
    'database_memory_gb': 128,
    'database_cpu_percent': 90,
    'database_memory_percent': 35,
}

result = calc.generate_sizing_recommendation(bad_metrics)

print("WARNINGS FOR BAD INPUTS:")
for warning in result.get('warnings', []):
    print(f"  {warning}")
```

**Expected Output:**
```
WARNINGS FOR BAD INPUTS:
  ℹ️ tasks_per_job value (500) is outside typical range (5-200).
     This may indicate unusual workload. Typical playbooks: 10-100 tasks
  ℹ️ job_duration_hours value (5.0) is outside typical range (0.02-2.0).
     This may indicate unusual workload. Typical jobs: 5-60 minutes
  ℹ️ forks_observed value (100) is outside typical range (1-50).
     This may indicate unusual workload. Typical forks: 5-25
```

### Test 2: Results Warnings

```python
# Metrics that will cause unusual results
unusual = {
    'managed_hosts': 1000,        # Small environment
    'playbooks_per_day_peak': 100,
    'tasks_per_job': 500,         # But VERY complex playbooks
    'job_duration_hours': 0.25,
    'allowed_hours_per_day': 24,
    'job_retention_hours': 24,
    'forks_observed': 2,
    'verbosity_level': 4,         # Connection debug!
    'peak_pattern': 'distributed_24x7',
    'database_vcpu': 4,
    'database_memory_gb': 16,
    'database_cpu_percent': 50,
    'database_memory_percent': 30,
}

result = calc.generate_sizing_recommendation(unusual)

print("WARNINGS FOR UNUSUAL RESULTS:")
for warning in result.get('warnings', []):
    print(f"  {warning}")
```

**Expected Output:**
```
WARNINGS FOR UNUSUAL RESULTS:
  ℹ️ tasks_per_job value (500) is outside typical range...
  ⚠️ HIGH SEVERITY: Control plane memory (XX GB) > 2× execution plane (XX GB).
     This is unusual. Verify 'tasks per job' and 'verbosity level' inputs.
  ℹ️ Database storage (XX GB) < 100 GB seems low for production...
```

---

## Verbosity Impact Matrix

Run this to see the full impact:

```python
from sizing_calculator import AAP26SizingCalculator

calc = AAP26SizingCalculator()

base = {
    'managed_hosts': 40000,
    'playbooks_per_day_peak': 70000,
    'tasks_per_job': 100,
    'job_duration_hours': 0.25,
    'allowed_hours_per_day': 24,
    'job_retention_hours': 48,
    'forks_observed': 5,
    'peak_pattern': 'distributed_24x7',
    'database_vcpu': 16,
    'database_memory_gb': 128,
    'database_cpu_percent': 90,
    'database_memory_percent': 35,
}

print("VERBOSITY LEVEL IMPACT ON CONTROL PLANE:")
print("-" * 80)
print(f"{'Level':<8} {'Events/Task':<13} {'Event Forks':<14} {'CPU':<8} {'Memory':<10}")
print("-" * 80)

for level in [0, 1, 2, 3, 4]:
    metrics = base.copy()
    metrics['verbosity_level'] = level
    result = calc.generate_sizing_recommendation(metrics)
    ctrl = result['components']['automation_controller_control_plane']

    print(f"{level:<8} {ctrl['events_per_task']:<13} {ctrl['event_forks']:>13,.0f} {ctrl['total_cpu']:>7} {ctrl['total_memory_gb']:>9} GB")

print("\n💡 Recommendation: Production should use level 0 or 1")
print("⚠️  Debug levels (3-4) increase control plane by 20-35%!")
```

---

## Peak Pattern Impact Matrix

```python
from sizing_calculator import AAP26SizingCalculator

calc = AAP26SizingCalculator()

base = {
    'managed_hosts': 40000,
    'playbooks_per_day_peak': 70000,
    'tasks_per_job': 100,
    'job_duration_hours': 0.25,
    'allowed_hours_per_day': 24,
    'job_retention_hours': 48,
    'forks_observed': 5,
    'verbosity_level': 1,
    'database_vcpu': 16,
    'database_memory_gb': 128,
    'database_cpu_percent': 90,
    'database_memory_percent': 35,
}

print("PEAK PATTERN IMPACT ON EXECUTION PLANE:")
print("-" * 90)
print(f"{'Pattern':<20} {'Multiplier':<12} {'Forks':<10} {'Pods':<6} {'CPU':<8} {'Memory':<10}")
print("-" * 90)

for pattern in ['distributed_24x7', 'mixed', 'business_hours', 'batch_window']:
    metrics = base.copy()
    metrics['peak_pattern'] = pattern
    result = calc.generate_sizing_recommendation(metrics)
    exec_p = result['components']['automation_controller_execution_plane']

    print(f"{pattern:<20} {exec_p['peak_multiplier']:<12} {exec_p['forks_needed']:>9.0f} {exec_p['execution_pods']:>5} {exec_p['total_cpu']:>7} {exec_p['total_memory_gb']:>9} GB")

print("\n💡 Recommendation: Choose pattern based on actual job schedule")
print("⚠️  Business hours requires 2.5x resources!")
print("⚠️  Batch windows require 10x resources!")
```

---

## API Testing (if Flask is running)

If you have the Flask app running, test via API:

```bash
# Test new parameters via API
curl -X POST http://localhost:5001/api/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "managed_hosts": 40000,
    "playbooks_per_day_peak": 70000,
    "concurrent_jobs_peak": 500,
    "tasks_per_job": 100,
    "job_duration_hours": 0.25,
    "allowed_hours_per_day": 24,
    "job_retention_hours": 48,
    "forks_observed": 5,
    "verbosity_level": 2,
    "peak_pattern": "business_hours",
    "database_vcpu": 16,
    "database_memory_gb": 128,
    "database_cpu_percent": 90,
    "database_memory_percent": 35,
    "num_hub_nodes": 2,
    "hub_cpu_percent": 25,
    "hub_memory_percent": 30,
    "num_controllers": 12,
    "controller_cpu_percent_avg": 35,
    "controller_cpu_percent_peak": 50,
    "controller_memory_percent": 20,
    "num_execution_nodes": 30,
    "execution_cpu_percent": 90,
    "execution_memory_percent": 50
  }' | python3 -m json.tool
```

---

## Expected Test Results Summary

| Test | What to Check | Expected Result |
|------|---------------|-----------------|
| **Baseline** | distributed + verbosity 1 | 15 exec pods, 52 control CPU, no warnings |
| **Business Hours** | 2.5x pattern | 37 exec pods (~2.5x increase) |
| **Debug Mode** | verbosity 3 | 63 control CPU (~20% increase) |
| **Batch Window** | 10x pattern | 146 exec pods (~10x increase) |
| **Worst Case** | batch + debug | Huge numbers, possible warnings |
| **Invalid Inputs** | tasks=500, duration=5 | Multiple warnings shown |
| **Unusual Results** | Small env, complex jobs | Control > execution warning |

---

## What to Look For

### ✅ Good Signs:
- Warnings appear for unusual values
- Verbosity changes control plane sizing
- Peak pattern changes execution plane sizing
- Results are consistent and reasonable
- Warnings make sense and are helpful

### ⚠️ Red Flags:
- No warnings when inputs are clearly wrong
- Verbosity has no effect on results
- Peak pattern has no effect on results
- Results are identical regardless of inputs
- Errors or crashes

---

## Common Issues & Solutions

### Issue: "AttributeError: EVENTS_PER_TASK"
**Solution:** Fixed in Phase 1. Database now uses baseline 6 events/task.

### Issue: API returns error "Missing required field"
**Solution:** New parameters are optional. Old API calls still work.

### Issue: Warnings not showing
**Solution:** Check `result.get('warnings', [])` in response

### Issue: Peak pattern has no effect
**Solution:** Verify `peak_pattern` parameter is passed correctly

---

## Next Steps After Testing

Once you've tested and verified Phase 1:

1. ✅ **Approve** - Merge to main, start Phase 2 (UI updates)
2. 🔄 **Iterate** - Found issues? I'll fix them before proceeding
3. 📝 **Document** - Need more documentation or examples?
4. 🚀 **Deploy** - Ready to use as-is, even without UI?

Let me know what you find!
