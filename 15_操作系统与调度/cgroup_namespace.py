# -*- coding: utf-8 -*-

"""

算法实现：15_操作系统与调度 / cgroup_namespace



本文件实现 cgroup_namespace 相关的算法功能。

"""



from dataclasses import dataclass, field

from typing import Optional

from enum import Enum





class NamespaceType(Enum):

    """命名空间类型"""

    PID = "pid"      # 进程ID隔离

    NETWORK = "net"  # 网络设备/端口隔离

    UTS = "uts"      # 主机名/域名隔离

    IPC = "ipc"      # System V IPC隔离

    MOUNT = "mount"  # 文件系统挂载点隔离

    USER = "user"    # 用户/组ID映射

    CGROUP = "cgroup"  # cgroup命名空间





@dataclass

class Namespace:

    """命名空间"""

    ns_type: NamespaceType

    id: int  # 内核分配的namespace ID

    child_ns_ids: list[int] = field(default_factory=list)





@dataclass

class CgroupLimit:

    """cgroup资源限制"""

    cpu_shares: int = 1024       # CPU权重

    cpu_quota_us: int = 0        # CPU时间上限（微秒）

    cpu_period_us: int = 100000  # CPU周期

    memory_limit: int = 0       # 内存限制（字节）

    memory_soft_limit: int = 0  # 软限制

    blkio_weight: int = 0       # 块设备权重





@dataclass

class ContainerSpec:

    """容器规格"""

    container_id: str

    hostname: str = "container"

    pid_namespace: bool = True

    network_mode: str = "bridge"  # bridge/host/none

    memory_limit: int = 256 * 1024 * 1024  # 256MB

    cpu_quota: int = 50000  # 50% CPU

    readonly_rootfs: bool = True





class LinuxNamespace:

    """Linux命名空间模拟"""



    def __init__(self, ns_type: NamespaceType):

        self.type = ns_type

        self.id = id(self)  # 模拟namespace ID

        self.processes: list[int] = []  # 此namespace中的进程



    def attach_process(self, pid: int):

        """将进程加入此namespace"""

        if pid not in self.processes:

            self.processes.append(pid)





class CgroupController:

    """cgroup控制器"""



    def __init__(self, name: str):

        self.name = name

        self.limits = CgroupLimit()

        self.tasks: list[int] = []  # 属于此cgroup的进程

        self.children: list["CgroupController"] = []





class ContainerProcess:

    """容器内的进程"""



    def __init__(self, pid: int, hostname: str):

        self.real_pid = pid

        self.virtual_pid = pid  # 在容器内看自己的PID

        self.hostname = hostname

        self.namespaces: dict[NamespaceType, LinuxNamespace] = {}

        self.cgroup_path: str = ""





class ContainerManager:

    """

    容器管理器

    创建/管理容器进程及其隔离环境

    """



    def __init__(self):

        self.namespaces: dict[NamespaceType, LinuxNamespace] = {}

        self.cgroups: dict[str, CgroupController] = {}

        self.containers: dict[str, list[ContainerProcess]] = {}



    def create_namespace(self, ns_type: NamespaceType) -> LinuxNamespace:

        """创建新的命名空间"""

        ns = LinuxNamespace(ns_type)

        self.namespaces[ns_type] = ns

        return ns



    def create_cgroup(self, name: str, parent: Optional[str] = None) -> CgroupController:

        """创建cgroup"""

        cg = CgroupController(name)

        if parent and parent in self.cgroups:

            self.cgroups[parent].children.append(cg)

        self.cgroups[name] = cg

        return cg



    def create_container(self, spec: ContainerSpec) -> list[ContainerProcess]:

        """创建容器"""

        procs = []



        # 创建namespace

        if spec.pid_namespace:

            pid_ns = self.create_namespace(NamespaceType.PID)

        net_ns = self.create_namespace(NamespaceType.NETWORK)

        uts_ns = self.create_namespace(NamespaceType.UTS)



        # 创建cgroup

        cg = self.create_cgroup(spec.container_id)

        cg.limits.memory_limit = spec.memory_limit

        cg.limits.cpu_quota_us = spec.cpu_quota



        # 创建初始进程

        for i in range(spec.pid_namespace and 3 or 1):

            pid = 1000 + i  # 模拟PID

            proc = ContainerProcess(pid=pid, hostname=spec.hostname)



            if spec.pid_namespace:

                proc.namespaces[NamespaceType.PID] = pid_ns

            proc.namespaces[NamespaceType.NETWORK] = net_ns

            proc.namespaces[NamespaceType.UTS] = uts_ns



            proc.cgroup_path = f"/sys/fs/cgroup/{spec.container_id}"



            procs.append(proc)



            # 关联到namespace和cgroup

            for ns in proc.namespaces.values():

                ns.attach_process(proc.real_pid)

            cg.tasks.append(proc.real_pid)



        self.containers[spec.container_id] = procs

        return procs



    def list_namespaces(self) -> list[str]:

        """列出活跃的namespace"""

        result = []

        for ns_type, ns in self.namespaces.items():

            result.append(f"{ns_type.value}:{ns.id} (procs={len(ns.processes)})")

        return result



    def get_cgroup_stats(self, container_id: str) -> dict:

        """获取容器的cgroup统计"""

        if container_id not in self.cgroups:

            return {}

        cg = self.cgroups[container_id]

        return {

            "name": cg.name,

            "memory_limit": cg.limits.memory_limit,

            "cpu_quota": cg.limits.cpu_quota_us,

            "tasks": len(cg.tasks),

        }





if __name__ == "__main__":

    mgr = ContainerManager()



    print("=== Linux容器隔离演示 ===")



    # 创建容器

    spec = ContainerSpec(

        container_id="web-server",

        hostname="web-01",

        pid_namespace=True,

        network_mode="bridge",

        memory_limit=512 * 1024 * 1024,

        cpu_quota=80000  # 80% CPU

    )



    procs = mgr.create_container(spec)

    print(f"\n创建容器 '{spec.container_id}':")

    print(f"  主机名: {spec.hostname}")

    print(f"  进程数: {len(procs)}")

    print(f"  内存限制: {spec.memory_limit // (1024*1024)} MB")

    print(f"  CPU配额: {spec.cpu_quota / 1000}%")



    # 查看namespace

    print(f"\n活跃命名空间:")

    for ns in mgr.list_namespaces():

        print(f"  {ns}")



    # 查看cgroup

    print(f"\ncgroup统计:")

    stats = mgr.get_cgroup_stats("web-server")

    for k, v in stats.items():

        print(f"  {k}: {v}")



    # 网络隔离演示

    print("\n=== 网络命名空间隔离 ===")

    net_ns = mgr.namespaces[NamespaceType.NETWORK]

    print(f"容器内网络: 独立的eth0/veth对")

    print(f"隔离: 不同容器间不会看到对方端口")



    # UTS隔离演示

    print("\n=== UTS命名空间隔离 ===")

    print(f"容器hostname: {spec.hostname}")

    print(f"容器有独立的域名/DNS")

