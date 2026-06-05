# ICN Blueprint Demo: BareMetalHost Lifecycle & Zero Touch Provisioning

## Overview
This demo showcases ICN's core capability: managing bare-metal infrastructure as Kubernetes resources.
We will inspect the BareMetalHost Custom Resources, observe the provisioning state machine,
deploy a workload, and demonstrate how ICN treats physical servers as cloud-native resources.

---

## Prerequisites
- SSH access to the ICN Host VM (192.168.137.155)
- The jump host (vm-jump) running with the bootstrap cluster
- machine-1 and machine-2 already provisioned and in the workload cluster

---

## Part 1: Inspect the BareMetalHost Resources (Shows Ironic/Metal3 in action)

### Step 1: SSH into the jump host
```bash
# From the ICN Host VM:
cd /home/icn/icn
vagrant ssh jump
```

### Step 2: List BareMetalHost resources
```bash
# On the jump host, check the Metal3 BareMetalHost CRDs (must run as sudo):
sudo kubectl get baremetalhost -n metal3 -o wide
```
**Expected output:** Shows machine-1 and machine-2 with their provisioning state,
BMC addresses, and current status (should be "provisioned").

### Step 3: Inspect a BareMetalHost in detail
```bash
# See the full lifecycle of machine-1:
sudo kubectl describe baremetalhost machine-1 -n metal3
```
**What to look for:**
- `Status.Provisioning.State`: Should be "provisioned"
- `Status.HardwareDetails`: CPU count, RAM, disk size — discovered by Ironic during inspection
- `Spec.BMC.Address`: The Redfish/IPMI endpoint (redfish+http://192.168.121.1:8000/...)
- `Spec.Image`: The OS image that was deployed
- `Events`: The full provisioning timeline (registering → inspecting → available → provisioning → provisioned)

### Step 4: Check Ironic containers
```bash
# See OpenStack Ironic running as containers (it runs 6 containers in 1 pod):
sudo kubectl get pods -n capm3-system | grep ironic
```
**Expected:** You will see a pod like `capm3-ironic-...` showing `6/6 Running`. This single pod contains all the OpenStack components (ironic, ironic-inspector, dnsmasq) running inside the bootstrap cluster.

---

## Part 2: Demonstrate the Workload Cluster (Provisioned by ICN)

### Step 5: SSH into the provisioned control plane
```bash
# From jump host:
ssh -o StrictHostKeyChecking=no ubuntu@192.168.151.100
```

### Step 6: Verify the cluster ICN provisioned
```bash
# Show the cluster that ICN built from bare metal:
sudo KUBECONFIG=/etc/kubernetes/admin.conf kubectl get nodes -o wide
sudo KUBECONFIG=/etc/kubernetes/admin.conf kubectl get pods -A
```
**Key point:** This entire cluster — both nodes, all system pods, networking — was
provisioned AUTOMATICALLY by ICN from empty virtual "bare-metal" machines.

### Step 7: Deploy a real workload
```bash
# First, remove the default control-plane taint so workloads can run on machine-1:
sudo KUBECONFIG=/etc/kubernetes/admin.conf kubectl taint nodes --all node-role.kubernetes.io/master- || true

# Deploy an nginx web server:
sudo KUBECONFIG=/etc/kubernetes/admin.conf kubectl create deployment icn-demo-web \
  --image=k8s.gcr.io/pause:3.4.1 --replicas=4

# Watch pods get distributed across BOTH ICN-provisioned nodes:
sudo KUBECONFIG=/etc/kubernetes/admin.conf kubectl get pods -l app=icn-demo-web -o wide -w

```
**What this shows:** The cluster ICN provisioned from bare metal is fully functional
and can run real workloads distributed across nodes.

### Step 8: Expose the deployment as a service
```bash
sudo KUBECONFIG=/etc/kubernetes/admin.conf kubectl expose deployment icn-demo-web \
  --port=80 --type=ClusterIP

# Verify service creation:
sudo KUBECONFIG=/etc/kubernetes/admin.conf kubectl get svc icn-demo-web
```

---

## Part 3: Demonstrate Node Lifecycle Management (ICN's Power Move)

### Step 9: Show node details (hardware discovered by Ironic)
```bash
sudo KUBECONFIG=/etc/kubernetes/admin.conf kubectl describe node machine-1 | head -40
sudo KUBECONFIG=/etc/kubernetes/admin.conf kubectl describe node machine-2 | head -40
```
**Key point:** The node labels, capacity, and allocatable resources were all
automatically discovered during Ironic's hardware inspection phase.

### Step 10: Demonstrate cordon/drain (simulating node maintenance)
```bash
# In a real ICN deployment, you could decommission a node back through Metal3:
# kubectl annotate baremetalhost machine-2 -n metal3 \
#   reboot.metal3.io/poweroff=""
# This would trigger Ironic to power off the physical server via BMC!

# For our demo, simulate with cordon:
sudo KUBECONFIG=/etc/kubernetes/admin.conf kubectl cordon machine-2
sudo KUBECONFIG=/etc/kubernetes/admin.conf kubectl get nodes
# machine-2 shows "SchedulingDisabled"

# Drain workloads off machine-2:
sudo KUBECONFIG=/etc/kubernetes/admin.conf kubectl drain machine-2 \
  --ignore-daemonsets --delete-emptydir-data --force

# Watch pods migrate to machine-1:
sudo KUBECONFIG=/etc/kubernetes/admin.conf kubectl get pods -l app=icn-demo-web -o wide
```

### Step 11: Restore the node
```bash
sudo KUBECONFIG=/etc/kubernetes/admin.conf kubectl uncordon machine-2
sudo KUBECONFIG=/etc/kubernetes/admin.conf kubectl get nodes
# Both nodes Ready again
```

---

## Part 4: Show the ZTP Configuration (What makes ICN unique)

### Step 12: Examine the site configuration
```bash
# Exit machine-1 and exit the jump host to get back to the ICN Host VM:
exit
exit

# Now back on the ICN Host VM (user `icn`):
cat /home/icn/icn/deploy/site/vm/deployment/site.yaml
```
**What this shows:** The full declarative site definition (`site.yaml`). This file contains everything: the `BareMetalHost` definitions, BMC addresses, OS images, and even the embedded `KubeadmConfigTemplate` (which acts as the cloud-init script). ICN takes this YAML and turns it into running bare-metal Kubernetes nodes. THIS is Zero Touch Provisioning.

### Step 14: Check the Sushy emulator (Virtual BMC)
```bash
# This is the OpenStack component that emulates physical BMC hardware:
curl -s http://192.168.121.1:8000/redfish/v1/Systems | python3 -m json.tool
```
**What this shows:** The Redfish API — the same standard API used by real
Dell iDRAC, HP iLO, and Lenovo XClarity hardware management interfaces.
In production, Ironic talks to real BMCs instead of Sushy.

---

## Cleanup
```bash
sudo KUBECONFIG=/etc/kubernetes/admin.conf kubectl delete deployment icn-demo-web
sudo KUBECONFIG=/etc/kubernetes/admin.conf kubectl delete svc icn-demo-web
```

---

## Key Takeaways for the Demo

1. **OpenStack Ironic** runs inside the jump host as containers — it's the engine that
   does the actual bare-metal provisioning (PXE boot, OS install, hardware discovery).

2. **BareMetalHost CRDs** are the Kubernetes-native way to manage physical servers.
   Create a YAML → server gets provisioned. Delete it → server gets decommissioned.

3. **Zero Touch Provisioning** means the entire workflow (power on → inspect hardware →
   install OS → join cluster) happens automatically once you define the desired state.

4. **This is what K3s/MicroK8s CANNOT do** — they require someone to manually install
   the OS and run installation commands. ICN provisions from bare metal automatically.
