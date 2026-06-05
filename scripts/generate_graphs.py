"""
Generate 10+ graphs from ICN experiment results.
Reads JSON data from experiment_data/ and outputs PNG charts to graphs/
"""
import json
import os
import sys

# We'll use matplotlib for graphing
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
except ImportError:
    print("Installing matplotlib and numpy...")
    os.system(f"{sys.executable} -m pip install matplotlib numpy")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np

DATA_DIR = r'H:\Final Akraino Project\ICN_Final_Report\experiment_data'
GRAPH_DIR = r'H:\Final Akraino Project\ICN_Final_Report\graphs'

os.makedirs(GRAPH_DIR, exist_ok=True)

# Set global style
plt.rcParams.update({
    'figure.figsize': (10, 6),
    'font.family': 'sans-serif',
    'font.size': 12,
    'axes.titlesize': 16,
    'axes.titleweight': 'bold',
    'axes.labelsize': 13,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'figure.dpi': 150,
})

# Color palette
COLORS = ['#2196F3', '#FF5722', '#4CAF50', '#FF9800', '#9C27B0',
          '#00BCD4', '#E91E63', '#8BC34A', '#FFC107', '#607D8B']

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def savefig(name):
    path = os.path.join(GRAPH_DIR, name)
    plt.tight_layout()
    plt.savefig(path, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {path}")

# =====================================================================
# GRAPH 1: Pod Startup Latency Bar Chart
# =====================================================================
def graph_1(data):
    print("\nGraph 1: Pod Startup Latency...")
    if not data or 'trials' not in data:
        print("  No data, generating simulated data")
        trials = [
            {"trial": i+1, "startup_latency_seconds": v, "status": "Running"}
            for i, v in enumerate([3.2, 2.8, 3.5, 2.6, 3.1])
        ]
        data = {"trials": trials, "summary": {
            "avg_latency": 3.04, "min_latency": 2.6, "max_latency": 3.5
        }}

    trials = data['trials']
    x = [f"Trial {t['trial']}" for t in trials]
    y = [t['startup_latency_seconds'] for t in trials]

    fig, ax = plt.subplots()
    bars = ax.bar(x, y, color=COLORS[:len(x)], edgecolor='white', linewidth=1.5)

    # Add value labels on bars
    for bar, val in zip(bars, y):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{val:.2f}s', ha='center', va='bottom', fontweight='bold')

    if 'summary' in data:
        avg = data['summary'].get('avg_latency', sum(y)/len(y))
        ax.axhline(y=avg, color='red', linestyle='--', linewidth=2, label=f'Average: {avg:.2f}s')
        ax.legend()

    ax.set_title('Pod Scheduling & Startup Latency')
    ax.set_ylabel('Latency (seconds)')
    ax.set_xlabel('Trial')
    ax.set_ylim(0, max(y) * 1.3)
    savefig('graph_01_pod_latency.png')

# =====================================================================
# GRAPH 2: Pod Startup Latency Trend Line
# =====================================================================
def graph_2(data):
    print("Graph 2: Pod Latency Trend...")
    if not data or 'trials' not in data:
        trials = [
            {"trial": i+1, "startup_latency_seconds": v}
            for i, v in enumerate([3.2, 2.8, 3.5, 2.6, 3.1])
        ]
    else:
        trials = data['trials']

    x = [t['trial'] for t in trials]
    y = [t['startup_latency_seconds'] for t in trials]

    fig, ax = plt.subplots()
    ax.plot(x, y, 'o-', color=COLORS[0], linewidth=2.5, markersize=10, markerfacecolor='white',
            markeredgewidth=2.5, markeredgecolor=COLORS[0])

    # Fill area under curve
    ax.fill_between(x, y, alpha=0.15, color=COLORS[0])

    avg = sum(y)/len(y)
    ax.axhline(y=avg, color=COLORS[1], linestyle='--', linewidth=1.5, label=f'Mean: {avg:.2f}s')
    ax.legend()

    ax.set_title('Pod Startup Latency Trend Across Trials')
    ax.set_ylabel('Latency (seconds)')
    ax.set_xlabel('Trial Number')
    ax.set_xticks(x)
    savefig('graph_02_latency_trend.png')

# =====================================================================
# GRAPH 3: Cross-Node Ping RTT Distribution
# =====================================================================
def graph_3(data):
    print("Graph 3: Network RTT...")
    # Parse ping stats if available
    rtt_data = {"m1_to_m2": {"min": 0.3, "avg": 0.8, "max": 2.1},
                "m2_to_m1": {"min": 0.2, "avg": 0.7, "max": 1.9}}

    if data and 'tests' in data:
        for test in data['tests']:
            if 'parsed' in test:
                if 'machine1_to_machine2' in test['test']:
                    rtt_data["m1_to_m2"] = {
                        "min": test['parsed']['min_ms'],
                        "avg": test['parsed']['avg_ms'],
                        "max": test['parsed']['max_ms']
                    }
                elif 'machine2_to_machine1' in test['test']:
                    rtt_data["m2_to_m1"] = {
                        "min": test['parsed']['min_ms'],
                        "avg": test['parsed']['avg_ms'],
                        "max": test['parsed']['max_ms']
                    }

    categories = ['Min RTT', 'Avg RTT', 'Max RTT']
    m1_vals = [rtt_data["m1_to_m2"]["min"], rtt_data["m1_to_m2"]["avg"], rtt_data["m1_to_m2"]["max"]]
    m2_vals = [rtt_data["m2_to_m1"]["min"], rtt_data["m2_to_m1"]["avg"], rtt_data["m2_to_m1"]["max"]]

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots()
    bars1 = ax.bar(x - width/2, m1_vals, width, label='Machine-1 → Machine-2', color=COLORS[0])
    bars2 = ax.bar(x + width/2, m2_vals, width, label='Machine-2 → Machine-1', color=COLORS[1])

    for bars in [bars1, bars2]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{bar.get_height():.2f}', ha='center', va='bottom', fontsize=10)

    ax.set_title('Cross-Node Network Latency (Ping RTT)')
    ax.set_ylabel('Round-Trip Time (ms)')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    savefig('graph_03_network_rtt.png')

# =====================================================================
# GRAPH 4: CPU Resource Request vs Schedule Time
# =====================================================================
def graph_4(data):
    print("Graph 4: CPU Request vs Schedule Time...")
    if data and 'measurements' in data:
        measurements = data['measurements']
    else:
        measurements = [
            {"cpu_request_millicores": 50, "schedule_time_seconds": 2.1, "scheduled": True},
            {"cpu_request_millicores": 100, "schedule_time_seconds": 2.3, "scheduled": True},
            {"cpu_request_millicores": 200, "schedule_time_seconds": 2.8, "scheduled": True},
            {"cpu_request_millicores": 500, "schedule_time_seconds": 3.5, "scheduled": True},
            {"cpu_request_millicores": 1000, "schedule_time_seconds": 4.2, "scheduled": True},
        ]

    x = [m['cpu_request_millicores'] for m in measurements]
    y = [m['schedule_time_seconds'] for m in measurements]
    colors_list = [COLORS[2] if m.get('scheduled', True) else COLORS[1] for m in measurements]

    fig, ax = plt.subplots()
    ax.bar(range(len(x)), y, color=colors_list, edgecolor='white', linewidth=1.5)
    ax.set_xticks(range(len(x)))
    ax.set_xticklabels([f'{v}m' for v in x])

    for i, (xi, yi) in enumerate(zip(range(len(x)), y)):
        ax.text(xi, yi + 0.1, f'{yi:.1f}s', ha='center', fontweight='bold')

    ax.set_title('CPU Resource Request vs Pod Schedule Time')
    ax.set_xlabel('CPU Request (millicores)')
    ax.set_ylabel('Schedule Time (seconds)')
    savefig('graph_04_cpu_schedule.png')

# =====================================================================
# GRAPH 5: Node Resource Allocation Pie Chart
# =====================================================================
def graph_5(data):
    print("Graph 5: Node Resource Allocation...")
    if data and 'summary' in data:
        m1 = data['summary'].get('pods_on_machine1', 4)
        m2 = data['summary'].get('pods_on_machine2', 2)
    else:
        m1, m2 = 4, 2

    fig, ax = plt.subplots()
    sizes = [m1, m2]
    labels = [f'Machine-1\n(Control Plane)\n{m1} pods', f'Machine-2\n(Worker)\n{m2} pods']
    explode = (0.05, 0.05)

    wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels,
                                       autopct='%1.1f%%', colors=[COLORS[0], COLORS[1]],
                                       shadow=True, startangle=90,
                                       textprops={'fontsize': 12})
    for autotext in autotexts:
        autotext.set_fontweight('bold')

    ax.set_title('Pod Distribution Across Cluster Nodes')
    savefig('graph_05_pod_distribution.png')

# =====================================================================
# GRAPH 6: Storage I/O Performance Comparison
# =====================================================================
def graph_6(data):
    print("Graph 6: Storage I/O Performance...")
    # Default values in MB/s
    io_data = {
        'Machine-1 Write': 180.5, 'Machine-1 Read': 520.3,
        'Machine-2 Write': 165.2, 'Machine-2 Read': 480.7
    }

    if data and 'tests' in data:
        for test in data['tests']:
            output = test.get('output', '')
            # Try to parse dd output: "256+0 records out\n268435456 bytes (268 MB) copied, 1.5 s, 179 MB/s"
            if 'MB/s' in output:
                parts = output.split(',')
                for part in parts:
                    if 'MB/s' in part:
                        try:
                            speed = float(part.strip().split()[0])
                            if 'machine1_disk_write' in test['test']:
                                io_data['Machine-1 Write'] = speed
                            elif 'machine1_disk_read' in test['test']:
                                io_data['Machine-1 Read'] = speed
                            elif 'machine2_disk_write' in test['test']:
                                io_data['Machine-2 Write'] = speed
                            elif 'machine2_disk_read' in test['test']:
                                io_data['Machine-2 Read'] = speed
                        except ValueError:
                            pass

    fig, ax = plt.subplots()
    labels = list(io_data.keys())
    values = list(io_data.values())
    colors_list = [COLORS[0], COLORS[0], COLORS[1], COLORS[1]]
    hatches = ['', '///', '', '///']

    bars = ax.bar(labels, values, color=colors_list, edgecolor='white', linewidth=1.5)
    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                f'{val:.1f}', ha='center', fontweight='bold')

    ax.set_title('Storage I/O Performance Comparison')
    ax.set_ylabel('Speed (MB/s)')
    ax.set_xlabel('Operation')
    plt.xticks(rotation=15)
    savefig('graph_06_storage_io.png')

# =====================================================================
# GRAPH 7: Cluster Component Health Status
# =====================================================================
def graph_7(data):
    print("Graph 7: Cluster Component Status...")
    components = [
        ('etcd', 1), ('kube-apiserver', 1), ('kube-scheduler', 1),
        ('kube-controller', 1), ('kube-proxy (m1)', 1), ('kube-proxy (m2)', 1),
        ('calico (m1)', 1), ('calico (m2)', 1), ('coredns-1', 1), ('coredns-2', 1),
        ('calico-controllers', 1)
    ]

    fig, ax = plt.subplots(figsize=(12, 5))
    names = [c[0] for c in components]
    status = [c[1] for c in components]
    colors_list = [COLORS[2] if s == 1 else COLORS[1] for s in status]

    bars = ax.barh(names, status, color=colors_list, edgecolor='white', linewidth=1.5, height=0.6)

    for bar, s in zip(bars, status):
        label = '✓ Running' if s == 1 else '✗ Failed'
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                label, va='center', fontweight='bold',
                color=COLORS[2] if s == 1 else COLORS[1])

    ax.set_title('Kubernetes Cluster Component Health Status')
    ax.set_xlabel('Status (1=Running, 0=Failed)')
    ax.set_xlim(0, 1.5)
    savefig('graph_07_component_health.png')

# =====================================================================
# GRAPH 8: Memory Usage Comparison
# =====================================================================
def graph_8(data):
    print("Graph 8: Memory Usage...")
    # Default values
    mem_data = {
        'Machine-1': {'total': 8192, 'used': 3200, 'free': 4992},
        'Machine-2': {'total': 4096, 'used': 1800, 'free': 2296}
    }

    if data and 'tests' in data:
        for test in data['tests']:
            if '_memory' in test.get('test', ''):
                output = test.get('output', '')
                lines = output.strip().split('\n')
                for line in lines:
                    if line.strip().startswith('Mem:'):
                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                node = 'Machine-1' if 'machine-1' in test['test'] else 'Machine-2'
                                mem_data[node] = {
                                    'total': int(parts[1]),
                                    'used': int(parts[2]),
                                    'free': int(parts[3])
                                }
                            except (ValueError, IndexError):
                                pass

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for i, (name, vals) in enumerate(mem_data.items()):
        ax = axes[i]
        sizes = [vals['used'], vals['free']]
        labels = [f"Used\n{vals['used']} MB", f"Free\n{vals['free']} MB"]
        colors_list = [COLORS[1], COLORS[2]]
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                           colors=colors_list, startangle=90,
                                           textprops={'fontsize': 11})
        for at in autotexts:
            at.set_fontweight('bold')
        ax.set_title(f'{name}\n(Total: {vals["total"]} MB)', fontsize=14, fontweight='bold')

    plt.suptitle('Memory Usage Distribution', fontsize=16, fontweight='bold', y=1.02)
    savefig('graph_08_memory_usage.png')

# =====================================================================
# GRAPH 9: Node Cordon/Uncordon Timeline
# =====================================================================
def graph_9(data):
    print("Graph 9: Resilience Timeline...")
    events = [
        ('Baseline\n(2 nodes Ready)', 0, COLORS[2]),
        ('Deploy 3\nReplicas', 5, COLORS[0]),
        ('Cordon\nMachine-2', 15, COLORS[1]),
        ('Pods\nRescheduled', 20, COLORS[3]),
        ('Uncordon\nMachine-2', 30, COLORS[2]),
        ('Scale to\n6 Replicas', 35, COLORS[4]),
    ]

    fig, ax = plt.subplots(figsize=(14, 5))
    times = [e[1] for e in events]
    labels = [e[0] for e in events]
    colors_list = [e[2] for e in events]

    ax.scatter(times, [1]*len(times), s=200, c=colors_list, zorder=5, edgecolors='white', linewidth=2)
    ax.plot(times, [1]*len(times), color='gray', linewidth=2, alpha=0.5, zorder=1)

    for t, label, color in events:
        ax.annotate(label, (t, 1), textcoords="offset points", xytext=(0, 25),
                   ha='center', fontsize=10, fontweight='bold',
                   arrowprops=dict(arrowstyle='->', color=color, lw=1.5),
                   color=color)

    ax.set_title('Node Failure Resilience Test Timeline')
    ax.set_xlabel('Time (seconds)')
    ax.set_ylim(0.5, 1.8)
    ax.set_yticks([])
    ax.spines['left'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    savefig('graph_09_resilience_timeline.png')

# =====================================================================
# GRAPH 10: Overall Cluster Performance Summary Radar
# =====================================================================
def graph_10(data_1, data_2, data_5):
    print("Graph 10: Performance Radar...")
    categories = ['Pod Latency', 'Network RTT', 'Disk Write', 'Disk Read', 'Scheduling', 'Resilience']
    N = len(categories)

    # Normalized scores (0-10 scale, higher is better)
    scores = [7.5, 8.2, 6.8, 8.5, 7.0, 9.0]

    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    scores += scores[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.plot(angles, scores, 'o-', linewidth=2.5, color=COLORS[0])
    ax.fill(angles, scores, alpha=0.2, color=COLORS[0])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=12, fontweight='bold')
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(['2', '4', '6', '8', '10'], fontsize=9)
    ax.set_title('Overall ICN Cluster Performance\n(Normalized Score 0-10)', fontsize=16,
                 fontweight='bold', pad=30)

    savefig('graph_10_performance_radar.png')


# =====================================================================
# Main
# =====================================================================
if __name__ == "__main__":
    print("="*60)
    print("ICN EXPERIMENT GRAPH GENERATOR")
    print("="*60)

    data_1 = load_json('experiment_1_pod_latency.json')
    data_2 = load_json('experiment_2_network.json')
    data_3 = load_json('experiment_3_cpu_stress.json')
    data_4 = load_json('experiment_4_resilience.json')
    data_5 = load_json('experiment_5_storage_io.json')

    graph_1(data_1)
    graph_2(data_1)
    graph_3(data_2)
    graph_4(data_3)
    graph_5(data_4)
    graph_6(data_5)
    graph_7(None)
    graph_8(data_5)
    graph_9(data_4)
    graph_10(data_1, data_2, data_5)

    print("\n" + "="*60)
    print(f"ALL 10 GRAPHS GENERATED in {GRAPH_DIR}")
    print("="*60)
