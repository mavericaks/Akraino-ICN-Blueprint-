# Akraino ICN Blueprint Evaluation Project

This repository contains the comprehensive evaluation, architectural diagrams, performance experiments, and deployment guides for the Akraino Integrated Cloud Native (ICN) Blueprint.

The Akraino ICN Blueprint provides Zero Touch Provisioning (ZTP) of bare-metal Kubernetes clusters for edge computing environments using Metal3 and OpenStack Ironic.

## 📁 Repository Structure

- `ICN_Blueprint_Report.md`: The main 5,900+ word comprehensive technical report detailing the architecture, implementation, challenges, and results.
- `ICN_Demo_Guide.md`: A step-by-step demonstration guide to showcase ICN's Zero Touch Provisioning and bare-metal node lifecycle management.
- `diagrams/`: High-resolution architectural diagrams illustrating the nested virtualization setup and OpenStack Ironic integration.
- `graphs/`: 15 performance and architectural visualization graphs (including pod latency, network RTT, storage I/O, resilience timelines, and ICN component stacks).
- `experiment_data/`: Raw and enriched JSON data collected from the 5 live experiments run on the deployed cluster.
- `scripts/`: Python automation scripts used to conduct experiments, orchestrate SSH commands across the nested VMs, and generate the matplotlib graphs.

## 🚀 Key Highlights

1. **Zero Touch Provisioning (ZTP)**: Demonstrates how ICN uses `BareMetalHost` CRDs to automatically PXE boot, inspect, and provision physical servers without human intervention.
2. **OpenStack Ironic Integration**: Shows how ICN elegantly extracts only the bare-metal provisioning service (Ironic) from OpenStack, avoiding the overhead of a full cloud deployment.
3. **Nested Virtualization Proof-of-Concept**: Proves the feasibility of evaluating complex bare-metal blueprints using a 4-layer nested virtualization stack (Windows Host → VMware → KVM/libvirt → Nested KVM).
4. **Performance Validation**: Contains empirical data proving sub-millisecond network latency, fast pod scheduling (~3s), and rapid node failure recovery (cordon reaction in ~9s).

## 🛠️ Experiments Included
1. Pod Scheduling and Startup Latency
2. Cross-Node Network Performance (Ping RTT)
3. CPU Stress Test and Resource Scheduling
4. Node Failure Resilience (Cordon/Uncordon/Drain)
5. Storage I/O and System Performance Benchmarks

## 📝 Usage
Read the main [ICN_Blueprint_Report.md](ICN_Blueprint_Report.md) for the complete project narrative. To replicate the demo, follow the instructions in [ICN_Demo_Guide.md](ICN_Demo_Guide.md).

*This project was completed as an intensive proof-of-concept evaluation of the LF Edge Akraino ICN Blueprint.*
