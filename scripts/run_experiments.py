"""
ICN Blueprint Experiment Runner
Runs 5 experiments on the Akraino ICN two-node K8s cluster and collects results.
"""
import paramiko
import json
import time
import os
import sys

HOST = '192.168.137.155'
USER = 'icn'
PASS = '123'
SSH_KEY_PATH = '/home/icn/icn/deploy/site/vm/id_rsa'
MACHINE1_IP = '192.168.151.100'
MACHINE2_IP = '192.168.151.101'
RESULTS_DIR = r'H:\Final Akraino Project\ICN_Final_Report\experiment_data'

def ssh_exec(cmd, timeout=120):
    """Execute a command on the ICN host VM via SSH."""
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=30)
    stdin, stdout, stderr = c.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    c.close()
    return out, err

def kubectl(cmd, timeout=120):
    """Execute kubectl command on machine-1 (control plane)."""
    full = (
        f"echo '{PASS}' | sudo -S ssh -o UserKnownHostsFile=/dev/null "
        f"-o StrictHostKeyChecking=no -i /home/icn/icn/deploy/site/vm/id_rsa "
        f"ubuntu@{MACHINE1_IP} 'sudo KUBECONFIG=/etc/kubernetes/admin.conf {cmd}'"
    )
    return ssh_exec(full, timeout)

def ssh_machine(ip, cmd, timeout=120):
    """Execute a command on a nested VM (machine-1 or machine-2)."""
    full = (
        f"echo '{PASS}' | sudo -S ssh -o UserKnownHostsFile=/dev/null "
        f"-o StrictHostKeyChecking=no -i /home/icn/icn/deploy/site/vm/id_rsa "
        f"ubuntu@{ip} '{cmd}'"
    )
    return ssh_exec(full, timeout)

def save_result(filename, data):
    """Save experiment result to a JSON file."""
    path = os.path.join(RESULTS_DIR, filename)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"  -> Saved: {path}")

# =====================================================================
# EXPERIMENT 1: Pod Scheduling and Startup Latency
# =====================================================================
def experiment_1():
    print("\n" + "="*70)
    print("EXPERIMENT 1: Pod Scheduling and Startup Latency")
    print("="*70)
    results = {"experiment": "Pod Scheduling and Startup Latency", "trials": []}

    for i in range(5):
        pod_name = f"latency-test-{i}"
        print(f"  Trial {i+1}/5: Creating pod '{pod_name}'...")

        # Delete pod if exists
        kubectl(f"kubectl delete pod {pod_name} --ignore-not-found=true")
        time.sleep(2)

        # Record start time and create pod
        start = time.time()
        kubectl(f"kubectl run {pod_name} --image=k8s.gcr.io/pause:3.4.1 --restart=Never")

        # Poll until Running
        for attempt in range(60):
            out, _ = kubectl(f"kubectl get pod {pod_name} -o jsonpath={{.status.phase}}")
            if 'Running' in out:
                elapsed = time.time() - start
                print(f"    Running in {elapsed:.2f}s")
                results["trials"].append({
                    "trial": i+1,
                    "pod_name": pod_name,
                    "startup_latency_seconds": round(elapsed, 2),
                    "status": "Running"
                })
                break
            time.sleep(1)
        else:
            elapsed = time.time() - start
            print(f"    Timeout after {elapsed:.2f}s")
            results["trials"].append({
                "trial": i+1,
                "pod_name": pod_name,
                "startup_latency_seconds": round(elapsed, 2),
                "status": "Timeout"
            })

        # Cleanup
        kubectl(f"kubectl delete pod {pod_name} --ignore-not-found=true")

    # Calculate stats
    latencies = [t["startup_latency_seconds"] for t in results["trials"] if t["status"] == "Running"]
    if latencies:
        results["summary"] = {
            "avg_latency": round(sum(latencies)/len(latencies), 2),
            "min_latency": round(min(latencies), 2),
            "max_latency": round(max(latencies), 2),
            "successful_trials": len(latencies),
            "total_trials": 5
        }
    save_result("experiment_1_pod_latency.json", results)
    return results

# =====================================================================
# EXPERIMENT 2: Cross-Node Network Performance
# =====================================================================
def experiment_2():
    print("\n" + "="*70)
    print("EXPERIMENT 2: Cross-Node Network Performance (ping RTT)")
    print("="*70)
    results = {"experiment": "Cross-Node Network Performance", "tests": []}

    # Test 1: Machine-1 -> Machine-2 ping
    print("  Test 1: machine-1 -> machine-2 ping (100 packets)...")
    out, _ = ssh_machine(MACHINE1_IP, "ping -c 100 -i 0.1 172.22.0.87 2>&1 | tail -5", timeout=60)
    results["tests"].append({"test": "machine1_to_machine2_ping", "output": out.strip()})
    print(f"    {out.strip().split(chr(10))[-1] if out.strip() else 'No output'}")

    # Test 2: Pod-to-Pod latency across nodes
    print("  Test 2: Checking pod IPs across nodes...")
    out, _ = kubectl("kubectl get pods -A -o wide")
    results["tests"].append({"test": "pod_ip_layout", "output": out.strip()})

    # Test 3: Machine-2 -> Machine-1 ping
    print("  Test 3: machine-2 -> machine-1 ping (100 packets)...")
    out, _ = ssh_machine(MACHINE2_IP, "ping -c 100 -i 0.1 192.168.151.100 2>&1 | tail -5", timeout=60)
    results["tests"].append({"test": "machine2_to_machine1_ping", "output": out.strip()})
    print(f"    {out.strip().split(chr(10))[-1] if out.strip() else 'No output'}")

    # Test 4: DNS resolution from machine-2
    print("  Test 4: DNS resolution from machine-2...")
    out, _ = ssh_machine(MACHINE2_IP, "time nslookup kubernetes.default.svc.cluster.local 10.96.0.10 2>&1", timeout=30)
    results["tests"].append({"test": "dns_resolution", "output": out.strip()})

    # Parse ping statistics for summary
    for test in results["tests"]:
        if "rtt" in test.get("output", ""):
            # Parse: rtt min/avg/max/mdev = 0.123/0.456/0.789/0.012 ms
            lines = test["output"].split("\n")
            for line in lines:
                if "rtt" in line or "round-trip" in line:
                    parts = line.split("=")
                    if len(parts) > 1:
                        values = parts[1].strip().split("/")
                        if len(values) >= 4:
                            test["parsed"] = {
                                "min_ms": float(values[0]),
                                "avg_ms": float(values[1]),
                                "max_ms": float(values[2]),
                                "mdev_ms": float(values[3].split()[0])
                            }

    save_result("experiment_2_network.json", results)
    return results

# =====================================================================
# EXPERIMENT 3: CPU Stress Test and Resource Monitoring
# =====================================================================
def experiment_3():
    print("\n" + "="*70)
    print("EXPERIMENT 3: CPU Stress Test and Resource Monitoring")
    print("="*70)
    results = {"experiment": "CPU Stress and Resource Monitoring", "measurements": []}

    # Baseline measurement
    print("  Measuring baseline resource usage...")
    out, _ = kubectl("kubectl top nodes 2>/dev/null || echo 'metrics-server not available'")
    results["baseline_nodes"] = out.strip()

    # Get node resource info
    out, _ = kubectl("kubectl describe nodes | grep -A 5 'Allocated resources'")
    results["allocated_resources"] = out.strip()

    # Deploy stress pods with varying CPU requests
    cpu_loads = [50, 100, 200, 500, 1000]  # millicores
    for i, mcpu in enumerate(cpu_loads):
        pod_name = f"stress-cpu-{mcpu}m"
        print(f"  Trial {i+1}/5: Deploying pod with {mcpu}m CPU request...")

        # Create stress pod
        kubectl(f"kubectl delete pod {pod_name} --ignore-not-found=true")
        time.sleep(2)

        yaml_cmd = (
            f"kubectl run {pod_name} --image=k8s.gcr.io/pause:3.4.1 "
            f"--requests=cpu={mcpu}m --restart=Never"
        )
        start = time.time()
        kubectl(yaml_cmd)

        # Wait for scheduling
        scheduled = False
        for attempt in range(30):
            out, _ = kubectl(f"kubectl get pod {pod_name} -o jsonpath={{.status.phase}}")
            if 'Running' in out:
                elapsed = time.time() - start
                scheduled = True
                break
            time.sleep(1)

        if not scheduled:
            elapsed = time.time() - start

        # Get node it was scheduled on
        node_out, _ = kubectl(f"kubectl get pod {pod_name} -o jsonpath={{.spec.nodeName}}")

        results["measurements"].append({
            "cpu_request_millicores": mcpu,
            "pod_name": pod_name,
            "scheduled": scheduled,
            "schedule_time_seconds": round(elapsed, 2),
            "assigned_node": node_out.strip()
        })
        print(f"    Scheduled={scheduled}, Node={node_out.strip()}, Time={elapsed:.2f}s")

    # Cleanup
    for mcpu in cpu_loads:
        kubectl(f"kubectl delete pod stress-cpu-{mcpu}m --ignore-not-found=true")

    # Get final cluster state
    out, _ = kubectl("kubectl get pods -A -o wide")
    results["final_pod_state"] = out.strip()

    save_result("experiment_3_cpu_stress.json", results)
    return results

# =====================================================================
# EXPERIMENT 4: Node Failure Resilience (Cordon/Uncordon)
# =====================================================================
def experiment_4():
    print("\n" + "="*70)
    print("EXPERIMENT 4: Node Failure Resilience (Cordon/Uncordon)")
    print("="*70)
    results = {"experiment": "Node Failure Resilience", "phases": []}

    # Phase 1: Baseline - check node and pod status
    print("  Phase 1: Recording baseline state...")
    out, _ = kubectl("kubectl get nodes -o wide")
    results["phases"].append({"phase": "baseline_nodes", "output": out.strip()})
    out, _ = kubectl("kubectl get pods -A -o wide")
    results["phases"].append({"phase": "baseline_pods", "output": out.strip()})

    # Phase 2: Deploy a test deployment with 3 replicas
    print("  Phase 2: Deploying test workload (3 replicas)...")
    kubectl("kubectl delete deployment resilience-test --ignore-not-found=true")
    time.sleep(3)
    kubectl("kubectl create deployment resilience-test --image=k8s.gcr.io/pause:3.4.1 --replicas=3")
    time.sleep(10)
    out, _ = kubectl("kubectl get pods -l app=resilience-test -o wide")
    results["phases"].append({"phase": "deployment_created", "output": out.strip()})
    print(f"    Pods: {out.strip()}")

    # Phase 3: Cordon machine-2 (simulate node failure)
    print("  Phase 3: Cordoning machine-2 (simulating node unavailability)...")
    start = time.time()
    kubectl("kubectl cordon machine-2")
    out, _ = kubectl("kubectl get nodes")
    results["phases"].append({"phase": "node_cordoned", "output": out.strip()})

    # Phase 4: Check if pods get rescheduled
    print("  Phase 4: Checking pod rescheduling...")
    time.sleep(5)
    out, _ = kubectl("kubectl get pods -l app=resilience-test -o wide")
    results["phases"].append({"phase": "after_cordon_pods", "output": out.strip()})
    cordon_time = round(time.time() - start, 2)
    print(f"    After cordon ({cordon_time}s): {out.strip()}")

    # Phase 5: Uncordon machine-2
    print("  Phase 5: Uncordoning machine-2...")
    kubectl("kubectl uncordon machine-2")
    time.sleep(3)
    out, _ = kubectl("kubectl get nodes")
    results["phases"].append({"phase": "node_uncordoned", "output": out.strip()})

    # Phase 6: Scale up and observe distribution
    print("  Phase 6: Scaling deployment to 6 replicas...")
    kubectl("kubectl scale deployment resilience-test --replicas=6")
    time.sleep(15)
    out, _ = kubectl("kubectl get pods -l app=resilience-test -o wide")
    results["phases"].append({"phase": "scaled_to_6", "output": out.strip()})
    print(f"    6 replicas: {out.strip()}")

    # Parse pod distribution
    m1_count = out.count("machine-1")
    m2_count = out.count("machine-2")
    results["summary"] = {
        "cordon_reaction_time_seconds": cordon_time,
        "pods_on_machine1": m1_count,
        "pods_on_machine2": m2_count,
        "total_pods": m1_count + m2_count
    }

    # Cleanup
    kubectl("kubectl delete deployment resilience-test --ignore-not-found=true")

    save_result("experiment_4_resilience.json", results)
    return results

# =====================================================================
# EXPERIMENT 5: Storage I/O and System Performance
# =====================================================================
def experiment_5():
    print("\n" + "="*70)
    print("EXPERIMENT 5: Storage I/O and System Performance")
    print("="*70)
    results = {"experiment": "Storage I/O and System Performance", "tests": []}

    # Test 1: Disk write speed on machine-1
    print("  Test 1: Disk write speed on machine-1...")
    out, _ = ssh_machine(MACHINE1_IP,
        "dd if=/dev/zero of=/tmp/testfile bs=1M count=256 conv=fdatasync 2>&1 | tail -1",
        timeout=60)
    results["tests"].append({"test": "machine1_disk_write", "output": out.strip()})
    print(f"    {out.strip()}")

    # Test 2: Disk write speed on machine-2
    print("  Test 2: Disk write speed on machine-2...")
    out, _ = ssh_machine(MACHINE2_IP,
        "dd if=/dev/zero of=/tmp/testfile bs=1M count=256 conv=fdatasync 2>&1 | tail -1",
        timeout=60)
    results["tests"].append({"test": "machine2_disk_write", "output": out.strip()})
    print(f"    {out.strip()}")

    # Test 3: Disk read speed on machine-1
    print("  Test 3: Disk read speed on machine-1...")
    out, _ = ssh_machine(MACHINE1_IP,
        "dd if=/tmp/testfile of=/dev/null bs=1M count=256 2>&1 | tail -1",
        timeout=60)
    results["tests"].append({"test": "machine1_disk_read", "output": out.strip()})
    print(f"    {out.strip()}")

    # Test 4: Disk read speed on machine-2
    print("  Test 4: Disk read speed on machine-2...")
    out, _ = ssh_machine(MACHINE2_IP,
        "dd if=/tmp/testfile of=/dev/null bs=1M count=256 2>&1 | tail -1",
        timeout=60)
    results["tests"].append({"test": "machine2_disk_read", "output": out.strip()})
    print(f"    {out.strip()}")

    # Test 5: Memory info
    print("  Test 5: Memory info on both nodes...")
    for name, ip in [("machine-1", MACHINE1_IP), ("machine-2", MACHINE2_IP)]:
        out, _ = ssh_machine(ip, "free -m | head -3", timeout=30)
        results["tests"].append({"test": f"{name}_memory", "output": out.strip()})
        print(f"    {name}: {out.strip()}")

    # Test 6: CPU info
    print("  Test 6: CPU info on both nodes...")
    for name, ip in [("machine-1", MACHINE1_IP), ("machine-2", MACHINE2_IP)]:
        out, _ = ssh_machine(ip, "nproc && cat /proc/cpuinfo | grep 'model name' | head -1", timeout=30)
        results["tests"].append({"test": f"{name}_cpu", "output": out.strip()})
        print(f"    {name}: {out.strip()}")

    # Test 7: Uptime and load averages
    print("  Test 7: Uptime and load averages...")
    for name, ip in [("machine-1", MACHINE1_IP), ("machine-2", MACHINE2_IP)]:
        out, _ = ssh_machine(ip, "uptime", timeout=30)
        results["tests"].append({"test": f"{name}_uptime", "output": out.strip()})
        print(f"    {name}: {out.strip()}")

    # Cleanup temp files
    ssh_machine(MACHINE1_IP, "rm -f /tmp/testfile", timeout=10)
    ssh_machine(MACHINE2_IP, "rm -f /tmp/testfile", timeout=10)

    save_result("experiment_5_storage_io.json", results)
    return results

# =====================================================================
# Main
# =====================================================================
if __name__ == "__main__":
    print("="*70)
    print("ICN BLUEPRINT EXPERIMENT SUITE")
    print("="*70)

    os.makedirs(RESULTS_DIR, exist_ok=True)

    all_results = {}

    # Verify connectivity first
    print("\nVerifying connectivity to ICN host...")
    out, err = ssh_exec("echo 'Connection OK'")
    if 'Connection OK' not in out:
        print(f"ERROR: Cannot connect to ICN host. Output: {out} {err}")
        sys.exit(1)
    print("  Connected!")

    # Verify cluster health
    print("\nVerifying cluster health...")
    out, _ = kubectl("kubectl get nodes")
    print(f"  {out.strip()}")
    if 'Ready' not in out:
        print("WARNING: Cluster may not be healthy, proceeding anyway...")

    try:
        all_results["experiment_1"] = experiment_1()
    except Exception as e:
        print(f"  ERROR in Experiment 1: {e}")
        all_results["experiment_1"] = {"error": str(e)}

    try:
        all_results["experiment_2"] = experiment_2()
    except Exception as e:
        print(f"  ERROR in Experiment 2: {e}")
        all_results["experiment_2"] = {"error": str(e)}

    try:
        all_results["experiment_3"] = experiment_3()
    except Exception as e:
        print(f"  ERROR in Experiment 3: {e}")
        all_results["experiment_3"] = {"error": str(e)}

    try:
        all_results["experiment_4"] = experiment_4()
    except Exception as e:
        print(f"  ERROR in Experiment 4: {e}")
        all_results["experiment_4"] = {"error": str(e)}

    try:
        all_results["experiment_5"] = experiment_5()
    except Exception as e:
        print(f"  ERROR in Experiment 5: {e}")
        all_results["experiment_5"] = {"error": str(e)}

    # Save combined results
    save_result("all_experiments.json", all_results)

    print("\n" + "="*70)
    print("ALL EXPERIMENTS COMPLETE")
    print("="*70)
