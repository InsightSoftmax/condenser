"""
Temporary script to explore IBM Quantum account.
Run with: uvx --from qiskit-ibm-runtime python scripts/check_ibm.py
Requires: export IBM_QUANTUM_TOKEN="your-token-here"
"""

import os

from qiskit_ibm_runtime import QiskitRuntimeService

token = os.environ.get("IBM_QUANTUM_TOKEN")
if not token:
    raise SystemExit("Set IBM_QUANTUM_TOKEN environment variable first.")

service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)

print("=== Instances ===")
for instance in service.instances():
    print(" ", instance)

for instance_info in service.instances():
    crn = instance_info["crn"]
    name = instance_info["name"]
    print(f"\n=== Jobs in: {name} ===")
    try:
        instance_service = QiskitRuntimeService(
            channel="ibm_quantum_platform",
            token=token,
            instance=crn,
        )
        jobs = instance_service.jobs(limit=100)
        if not jobs:
            print("  (no jobs found)")
        for j in jobs:
            created = str(j.creation_date)[:19]
            print(f"  {j.job_id():<40} {str(j.backend()):<20} {created}  {j.status()}")
    except Exception as e:
        print(f"  Error querying instance: {e}")
