# LeEco Le 2 (Helio X20 / MT6797) Docker Kernel Builder

Automated GitHub Actions workflow to build a custom Linux 3.18 kernel with full Docker support (Namespaces, Cgroups, OverlayFS, Veth) for LeEco Le 2 (X620 / MT6797).

## Features
- Preserves native MT6631 Wi-Fi drivers and hardware device tree (`le_x620.dtb`).
- Enables all Docker kernel requirements:
  - `CONFIG_NAMESPACES=y`, `CONFIG_PID_NS=y`, `CONFIG_NET_NS=y`, `CONFIG_IPC_NS=y`, `CONFIG_UTS_NS=y`, `CONFIG_USER_NS=y`
  - `CONFIG_CGROUP_DEVICE=y`, `CONFIG_MEMCG=y`, `CONFIG_CGROUP_PIDS=y`
  - `CONFIG_OVERLAY_FS=y`, `CONFIG_VETH=y`, `CONFIG_BRIDGE=y`
- Packages output directly as `boot_docker.img` via GitHub Actions Artifacts.
