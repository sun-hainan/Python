# -*- coding: utf-8 -*-

"""

算法实现：15_操作系统与调度 / hypervisor



本文件实现 hypervisor 相关的算法功能。

"""



from enum import Enum

from dataclasses import dataclass, field

from typing import Optional





class HypervisorType(Enum):

    """Hypervisor类型"""

    TYPE1_BAREMETAL = 1  # 直接运行在硬件上（KVM/Xen/ESXi）

    TYPE2_HOSTED = 2      # 运行在宿主机操作系统上（VirtualBox/VMware Workstation）





@dataclass

class VMConfiguration:

    """虚拟机配置"""

    vmid: int

    name: str

    vcpus: int = 1

    memory_mb: int = 512

    disk_gb: int = 10

    guest_os: str = "Linux"

    boot_device: str = "hd"





@dataclass

class VirtualCPU:

    """虚拟CPU"""

    vcpu_id: int

    host_thread_id: int  # 宿主机的线程ID

    is_running: bool = False

    current_guest_gprs: dict = field(default_factory=dict)  # 通用寄存器





class VMState(Enum):

    """虚拟机状态"""

    STOPPED = 0

    RUNNING = 1

    PAUSED = 2

    SUSPENDED = 3





class Hypervisor:

    """Hypervisor基类"""



    def __init__(self, hv_type: HypervisorType, name: str):

        self.hv_type = hv_type

        self.name = name

        self.vms: dict[int, "VirtualMachine"] = {}



    def create_vm(self, config: VMConfiguration) -> "VirtualMachine":

        """创建虚拟机"""

        vm = VirtualMachine(config, self)

        self.vms[config.vmid] = vm

        return vm



    def start_vm(self, vmid: int) -> bool:

        """启动虚拟机"""

        vm = self.vms.get(vmid)

        if vm:

            vm.start()

            return True

        return False



    def stop_vm(self, vmid: int) -> bool:

        """停止虚拟机"""

        vm = self.vms.get(vmid)

        if vm:

            vm.stop()

            return True

        return False





class VirtualMachine:

    """虚拟机"""



    def __init__(self, config: VMConfiguration, hypervisor: Hypervisor):

        self.config = config

        self.hypervisor = hypervisor

        self.state = VMState.STOPPED

        self.vcpus: list[VirtualCPU] = []

        self.vmm_memory = bytearray(config.memory_mb * 1024 * 1024)

        self.guest_physical_memory: dict[int, bytearray] = {}



        # 初始化虚拟CPU

        for i in range(config.vcpus):

            self.vcpus.append(VirtualCPU(vcpu_id=i, host_thread_id=0))



        # 初始化guest物理内存（简化）

        self._init_guest_memory()



    def _init_guest_memory(self):

        """初始化guest物理内存"""

        for addr in range(0, self.config.memory_mb * 1024 * 1024, 4096):

            self.guest_physical_memory[addr] = bytearray(4096)



    def start(self):

        """启动虚拟机"""

        self.state = VMState.RUNNING

        for vcpu in self.vcpus:

            vcpu.is_running = True



    def stop(self):

        """停止虚拟机"""

        self.state = VMState.STOPPED

        for vcpu in self.vcpus:

            vcpu.is_running = False



    def pause(self):

        """暂停虚拟机"""

        self.state = VMState.PAUSED

        for vcpu in self.vcpus:

            vcpu.is_running = False



    def snapshot(self):

        """快照（保存虚拟机状态）"""

        self.state = VMState.SUSPENDED



    def restore(self):

        """恢复快照"""

        self.state = VMState.RUNNING





class Type1Hypervisor(Hypervisor):

    """

    Type 1 Hypervisor（裸金属虚拟化）

    直接运行在硬件上，无宿主机操作系统

    代表：KVM（Linux内核模块）、Xen、VMware ESXi、Hyper-V

    """



    def __init__(self):

        super().__init__(HypervisorType.TYPE1_BAREMETAL, "KVM-like Hypervisor")

        self.hardware_intercepts: list[str] = []  # 硬件拦截点

        self.vmm_memory_base = 0xFFFF000000000000  # VMM内存映射区域

        self.host_memory_base = 0x100000  # 宿主物理内存起始



    def setup_hardware_intercepts(self):

        """设置硬件级拦截（VMX Root模式）"""

        self.hardware_intercepts = [

            "CR3 writes (页表切换)",

            "MSR reads/writes",

            "I/O port accesses",

            "Interrupt injection",

            "CPUID execution",

        ]



    def setup_ept(self):

        """设置Extended Page Tables（硬件级内存虚拟化）"""

        print("启用EPT（Extended Page Tables）实现内存虚拟化")

        print("  - 客户虚拟地址 → 客户物理地址 → 宿主机物理地址")

        print("  - 硬件自动转换，无需软件模拟")



    def setup_vmx(self):

        """设置VMX（硬件虚拟化扩展）"""

        print("启用VMX (Virtual Machine Extensions)")

        print("  - VMX root mode: VMM运行在这里")

        print("  - VMX non-root mode: Guest运行在这里")

        print("  - VM Exit: Guest到VMM的控制转移")

        print("  - VM Enter: VMM到Guest的控制转移")





class Type2Hypervisor(Hypervisor):

    """

    Type 2 Hypervisor（宿主型虚拟化）

    运行在宿主机操作系统之上

    代表：VirtualBox、VMware Workstation、QEMU (用户态)

    """



    def __init__(self):

        super().__init__(HypervisorType.TYPE2_HOSTED, "VirtualBox-like Hypervisor")

        self.host_os_info = "Linux/Windows"

        self.vmm_process_id = None



    def setup_kvm_module(self):

        """加载KVM内核模块（Type2模式下使用用户空间QEMU）"""

        print("模拟：在宿主操作系统上运行")

        print("  - VMM作为普通进程运行")

        print("  - 使用宿主操作系统的调度器")

        print("  - 通过系统调用访问硬件")



    def setup_emulation_layer(self):

        """设置二进制翻译/模拟层"""

        print("模拟硬件环境：")

        print("  - 模拟BIOS/UEFI")

        print("  - 模拟IDE/SATA控制器")

        print("  - 模拟网络适配器")

        print("  - 模拟显卡（VGA/PCI）")





if __name__ == "__main__":

    print("=== Hypervisor虚拟化演示 ===")



    # Type 1 Hypervisor

    print("\n--- Type 1 (裸金属) Hypervisor ---")

    type1 = Type1Hypervisor()

    type1.setup_hardware_intercepts()

    type1.setup_vmx()

    type1.setup_ept()



    # 创建VM

    config = VMConfiguration(vmid=1, name="Ubuntu-VM", vcpus=2, memory_mb=2048)

    vm = type1.create_vm(config)

    type1.start_vm(1)



    print(f"\n启动VM: {vm.config.name}")

    print(f"  vCPUs: {vm.config.vcpus}")

    print(f"  内存: {vm.config.memory_mb} MB")

    print(f"  状态: {vm.state.name}")



    # Type 2 Hypervisor

    print("\n--- Type 2 (宿主型) Hypervisor ---")

    type2 = Type2Hypervisor()

    type2.setup_kvm_module()

    type2.setup_emulation_layer()



    config2 = VMConfiguration(vmid=2, name="Windows-VM", vcpus=4, memory_mb=4096)

    vm2 = type2.create_vm(config2)

    type2.start_vm(2)



    print(f"\n启动VM: {vm2.config.name}")

    print(f"  vCPUs: {vm2.config.vcpus}")

    print(f"  状态: {vm2.state.name}")



    # 对比

    print("\n=== Type1 vs Type2 对比 ===")

    print(f"{'特性':<20} {'Type1':<20} {'Type2':<20}")

    print("-" * 60)

    print(f"{'运行层级':<20} {'直接硬件之上':<20} {'宿主机操作系统之上':<20}")

    print(f"{'性能':<20} {'高（硬件辅助）':<20} {'中（模拟开销）':<20}")

    print(f"{'隔离性':<20} {'强':<20} {'中':<20}")

    print(f"{'示例':<20} {'KVM,Xen,ESXi':<20} {'VirtualBox,QEMU':<20}")

