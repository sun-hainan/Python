# -*- coding: utf-8 -*-

"""

算法实现：12_密码学与安全 / elf



本文件实现 elf 相关的算法功能。

"""



import struct

from typing import List, Tuple





# ELF 类型

ELF_TYPES = {

    0: "ET_NONE",

    1: "ET_REL",   # 可重定位文件

    2: "ET_EXEC",  # 可执行文件

    3: "ET_DYN",   # 共享对象

    4: "ET_CORE",  # Core dump

}



# ELF 机器类型

ELF_MACHINES = {

    0: "EM_NONE",

    3: "EM_386",

    62: "EM_X86_64",

    183: "EM_AARCH64",

}





class ELFHeader:

    """ELF文件头"""



    def __init__(self):

        self.e_type = 0        # 文件类型

        self.e_machine = 0     # 目标架构

        self.e_version = 0     # 版本

        self.e_entry = 0       # 入口点虚拟地址

        self.e_phoff = 0       # 程序头偏移

        self.e_shoff = 0       # 节头偏移

        self.e_flags = 0       # 处理器特定标志

        self.e_ehsize = 0      # ELF头大小

        self.e_phentsize = 0  # 程序头大小

        self.e_phnum = 0       # 程序头数量

        self.e_shentsize = 0   # 节头大小

        self.e_shnum = 0       # 节头数量

        self.e_shstrndx = 0   # 节名字符串表索引





class ProgramHeader:

    """程序段头"""



    def __init__(self):

        self.p_type = 0       # 段类型

        self.p_offset = 0     # 段在文件中的偏移

        self.p_vaddr = 0      # 虚拟地址

        self.p_paddr = 0      # 物理地址

        self.p_filesz = 0     # 段在文件中的大小

        self.p_memsz = 0      # 段在内存中的大小

        self.p_flags = 0      # 段标志

        self.p_align = 0      # 对齐





class SectionHeader:

    """节头"""



    def __init__(self):

        self.sh_name = 0      # 名字（字符串表索引）

        self.sh_type = 0      # 类型

        self.sh_flags = 0     # 标志

        self.sh_addr = 0      # 地址

        self.sh_offset = 0    # 文件偏移

        self.sh_size = 0      # 大小

        self.sh_link = 0      # 链接

        self.sh_info = 0       # 信息

        self.sh_addralign = 0 # 对齐

        self.sh_entsize = 0   # 条目大小





def parse_elf_header(data: bytes) -> ELFHeader:

    """

    解析ELF头



    参数：

        data: ELF文件的前512字节



    返回：ELFHeader对象

    """

    header = ELFHeader()



    # 检查ELF魔数

    if data[:4] != b'\x7fELF':

        raise ValueError("不是有效的ELF文件")



    # 解析ELF32头

    # e_type (2), e_machine (2), e_version (4), ...

    header.e_type, header.e_machine = struct.unpack('<HH', data[16:20])

    header.e_version = struct.unpack('<I', data[20:24])[0]

    header.e_entry, header.e_phoff, header.e_shoff = struct.unpack('<III', data[24:36])

    header.e_flags = struct.unpack('<I', data[36:40])[0]

    header.e_ehsize = struct.unpack('<H', data[40:42])[0]

    header.e_phentsize = struct.unpack('<H', data[42:44])[0]

    header.e_phnum = struct.unpack('<H', data[44:46])[0]

    header.e_shentsize = struct.unpack('<H', data[46:48])[0]

    header.e_shnum = struct.unpack('<H', data[48:50])[0]

    header.e_shstrndx = struct.unpack('<H', data[50:52])[0]



    return header





def parse_program_headers(data: bytes, offset: int, count: int, entsize: int) -> List[ProgramHeader]:

    """

    解析程序段头



    参数：

        data: 文件内容

        offset: 偏移量

        count: 段数量

        entsize: 每段大小



    返回：ProgramHeader列表

    """

    headers = []



    for i in range(count):

        ph = ProgramHeader()

        off = offset + i * entsize



        (ph.p_type, ph.p_offset, ph.p_vaddr, ph.p_paddr,

         ph.p_filesz, ph.p_memsz, ph.p_flags,

         ph.p_align) = struct.unpack('<IIIIIIII', data[off:off+entsize])



        headers.append(ph)



    return headers





def parse_section_headers(data: bytes, offset: int, count: int, entsize: int) -> List[SectionHeader]:

    """

    解析节头



    参数：

        data: 文件内容

        offset: 偏移量

        count: 节数量

        entsize: 每节大小



    返回：SectionHeader列表

    """

    headers = []



    for i in range(count):

        sh = SectionHeader()

        off = offset + i * entsize



        (sh.sh_name, sh.sh_type, sh.sh_flags, sh.sh_addr,

         sh.sh_offset, sh.sh_size, sh.sh_link, sh.sh_info,

         sh.sh_addralign, sh.sh_entsize) = struct.unpack('<IIQQQQIIqq', data[off:off+entsize])



        headers.append(sh)



    return headers





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== ELF文件格式解析 ===\n")



    print("ELF文件结构：")

    print("  1. ELF Header：文件基本信息")

    print("     - 入口点地址")

    print("     - 程序头表偏移")

    print("     - 节头表偏移")

    print()

    print("  2. Program Headers：运行时视图")

    print("     - PT_LOAD：可加载段")

    print("     - PT_DYNAMIC：动态链接信息")

    print()

    print("  3. Section Headers：链接视图")

    print("     - .text：代码")

    print("     - .data：已初始化数据")

    print("     - .bss：未初始化数据")

    print("     - .symtab：符号表")

    print("     - .strtab：字符串表")

    print()



    print("常见ELF类型：")

    for num, name in ELF_TYPES.items():

        print(f"  {num}: {name}")



    print()

    print("常用架构：")

    for num, name in list(ELF_MACHINES.items())[:4]:

        print(f"  {num}: {name}")



    print()

    print("说明：")

    print("  - Linux可执行文件都是ELF格式")

    print("  - readelf -h 查看ELF头")

    print("  - objdump -d 反汇编")

    print("  - ldd 查看动态链接库")

