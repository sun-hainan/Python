# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构 / register_renaming



本文件实现 register_renaming 相关的算法功能。

"""



from typing import Dict, List, Optional, Set

from dataclasses import dataclass, field

from enum import Enum





class PhysicalRegister:

    """物理寄存器"""

    def __init__(self, reg_id: int, name: str = ""):

        self.reg_id = reg_id

        self.name = name

        self.value: Optional[float] = None

        self.state: str = "FREE"  # FREE, ALLOCATED, WRITING

        self.renamed_from: Optional[int] = None  # 重命名自哪个架构寄存器





class ArchitectureRegister:

    """架构寄存器（软件可见的寄存器）"""

    def __init__(self, reg_id: int, name: str = ""):

        self.reg_id = reg_id

        self.name = name

        self.pending_reg: Optional[int] = None  # 指向pending的物理寄存器





class RegisterRenamer:

    """

    寄存器重命名器



    管理物理寄存器到架构寄存器的映射。

    """



    def __init__(self, num_physical: int = 32, num_architectural: int = 16):

        self.num_physical = num_physical

        self.num_architectural = num_architectural



        # 物理寄存器池

        self.physical_registers: Dict[int, PhysicalRegister] = {

            i: PhysicalRegister(i, f"R{i}") for i in range(num_physical)

        }



        # 架构寄存器映射

        self.arch_registers: Dict[int, ArchitectureRegister] = {

            i: ArchitectureRegister(i, f"AR{i}") for i in range(num_architectural)

        }



        # 空闲物理寄存器列表

        self.free_list: List[int] = list(range(num_architectural, num_physical))



        # 重命名表：架构寄存器ID -> 物理寄存器ID

        self.rename_table: Dict[int, int] = {}



        # 初始化：前num_architectural个物理寄存器对应架构寄存器

        for i in range(num_architectural):

            self.rename_table[i] = i

            self.physical_registers[i].state = "ALLOCATED"



        # 统计

        self.rename_count = 0

        self.freelist_count = 0



    def allocate_physical_register(self) -> Optional[int]:

        """

        分配一个物理寄存器

        return: 物理寄存器ID，或None（无空闲寄存器）

        """

        if not self.free_list:

            return None



        phys_reg = self.free_list.pop(0)

        self.physical_registers[phys_reg].state = "ALLOCATED"

        self.freelist_count += 1



        return phys_reg



    def free_physical_register(self, phys_reg: int):

        """释放物理寄存器"""

        if 0 <= phys_reg < self.num_physical:

            self.physical_registers[phys_reg].state = "FREE"

            self.physical_registers[phys_reg].renamed_from = None

            self.free_list.append(phys_reg)



    def rename(self, arch_reg: int) -> int:

        """

        重命名架构寄存器

        为arch_reg分配一个新的物理寄存器

        return: 新的物理寄存器ID

        """

        if arch_reg not in self.rename_table:

            return -1



        # 获取旧的物理寄存器

        old_phys = self.rename_table[arch_reg]



        # 分配新的物理寄存器

        new_phys = self.allocate_physical_register()

        if new_phys is None:

            # 没有空闲寄存器，使用原有的

            return old_phys



        # 记录重命名关系（用于后续释放）

        self.physical_registers[new_phys].renamed_from = old_phys



        # 更新重命名表

        self.rename_table[arch_reg] = new_phys



        # 标记旧物理寄存器状态

        # （在所有依赖完成后才能释放）

        if old_phys >= self.num_architectural:

            self.free_physical_register(old_phys)



        self.rename_count += 1

        return new_phys



    def get_physical_register(self, arch_reg: int) -> int:

        """获取架构寄存器当前对应的物理寄存器"""

        return self.rename_table.get(arch_reg, -1)



    def is_pending(self, arch_reg: int) -> bool:

        """检查架构寄存器是否有pending的写"""

        phys = self.get_physical_register(arch_reg)

        if phys >= 0:

            return self.physical_registers[phys].state == "WRITING"

        return False



    def write_value(self, phys_reg: int, value: float):

        """写入物理寄存器值"""

        if 0 <= phys_reg < self.num_physical:

            self.physical_registers[phys_reg].value = value

            self.physical_registers[phys_reg].state = "ALLOCATED"



    def read_value(self, phys_reg: int) -> Optional[float]:

        """读取物理寄存器值"""

        if 0 <= phys_reg < self.num_physical:

            return self.physical_registers[phys_reg].value

        return None



    def get_status(self) -> Dict:

        """获取重命名器状态"""

        allocated = sum(1 for r in self.physical_registers.values() if r.state == "ALLOCATED")

        return {

            'total_physical': self.num_physical,

            'allocated': allocated,

            'free': len(self.free_list),

            'renames': self.rename_count,

        }





def simulate_register_renaming():

    """

    模拟寄存器重命名

    """

    print("=" * 60)

    print("Tomasulo算法：寄存器重命名")

    print("=" * 60)



    # 创建重命名器：16个物理寄存器，8个架构寄存器

    renamer = RegisterRenamer(num_physical=16, num_architectural=8)



    print("\n初始状态:")

    print("-" * 50)

    status = renamer.get_status()

    print(f"  物理寄存器: {status['allocated']}/{status['total_physical']} 已分配")

    print(f"  空闲: {status['free']}")

    print(f"  重命名次数: {status['renames']}")



    # 模拟指令序列

    # I1: R1 = R2 + R3 (WAW hazard with I2, WAR hazard with I3)

    # I2: R1 = R4 * R5 (WAW hazard with I1)

    # I3: R6 = R1 + R7 (RAW hazard with I1, WAR hazard with I2)

    # I4: R7 = R8 + R9



    print("\n指令序列:")

    print("-" * 50)

    instructions = [

        ("I1", "R1 = R2 + R3"),

        ("I2", "R1 = R4 * R5"),

        ("I3", "R6 = R1 + R7"),

        ("I4", "R7 = R8 + R9"),

    ]



    for instr_id, instr in instructions:

        print(f"  {instr_id}: {instr}")



    print("\n重命名过程:")

    print("-" * 50)



    rename_map = {}



    for instr_id, instr in instructions:

        # 解析指令

        parts = instr.replace("=", " ").replace("+", " ").replace("*", " ").split()

        dest = parts[1]

        src1 = parts[2]

        src2 = parts[3] if len(parts) > 3 else None



        # 解析寄存器号

        dest_reg = int(dest[1])

        src1_reg = int(src1[1])

        src2_reg = int(src2[1]) if src2 else None



        # 重命名目标寄存器

        new_phys = renamer.rename(dest_reg)

        rename_map[instr_id] = {'dest': new_phys, 'dest_arch': dest_reg}

        print(f"\n{instr_id}:")

        print(f"  目标 {dest} -> 物理寄存器 P{new_phys}")



        # 重命名源寄存器

        src1_phys = renamer.get_physical_register(src1_reg)

        print(f"  源 {src1} -> 物理寄存器 P{src1_phys}")



        if src2_reg is not None:

            src2_phys = renamer.get_physical_register(src2_reg)

            print(f"  源 {src2} -> 物理寄存器 P{src2_phys}")



    print("\n重命名后状态:")

    print("-" * 50)

    print("  物理寄存器分配:")

    for reg_id, phys_reg in renamer.rename_table.items():

        print(f"    架构 AR{reg_id} -> P{phys_reg}")



    status = renamer.get_status()

    print(f"\n  统计:")

    print(f"    已分配: {status['allocated']}/{status['total_physical']}")

    print(f"    空闲: {status['free']}")

    print(f"    重命名次数: {status['renames']}")



    # 演示WAR和WAW hazard的解决

    print("\n" + "=" * 60)

    print("WAR/WAW Hazard通过重命名解决")

    print("=" * 60)



    print("\n场景:")

    print("  I1: R1 = R2 + R3  (使用 P{rename_map['I1']['dest']})")

    print("  I2: R1 = R4 * R5  (使用 P{rename_map['I2']['dest']}) <- WAW解决！")

    print("  I3: R6 = R1 + R7  (读取I1的结果) <- WAR可能解决")



    print("\n结果:")

    print(f"  I1写入P{rename_map['I1']['dest']}")

    print(f"  I2写入P{rename_map['I2']['dest']}（不同物理寄存器，无WAW）")

    print(f"  I3读取P{rename_map['I1']['dest']}（正确数据）")





if __name__ == "__main__":

    simulate_register_renaming()

