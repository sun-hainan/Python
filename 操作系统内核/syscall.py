# -*- coding: utf-8 -*-
"""
算法实现：操作系统内核 / syscall

本文件实现 syscall 相关的算法功能。
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum


class SystemCallNumber(Enum):
    """x86-64系统调用号（部分）"""
    READ = 0
    WRITE = 1
    OPEN = 2
    CLOSE = 3
    EXIT = 60
    BRK = 12
    MMAP = 9
    MPROTECT = 10
    RT_SIGACTION = 13
    GETPID = 39
    GETTID = 186
    CLONE = 56
    FUTEX = 202


@dataclass
class TrapFrame:
    """陷阱帧（系统调用时的CPU状态）"""
    # 通用寄存器
    rax: int = 0  # 系统调用号/返回值
    rbx: int = 0
    rcx: int = 0
    rdx: int = 0
    rsi: int = 0
    rdi: int = 0
    rbp: int = 0
    r8: int = 0
    r9: int = 0
    r10: int = 0
    r11: int = 0
    r12: int = 0
    r13: int = 0
    r14: int = 0
    r15: int = 0

    # 程序计数器
    rip: int = 0
    cs: int = 0x33  # 代码段
    rflags: int = 0

    # 栈
    rsp: int = 0
    ss: int = 0x2B  # 栈段


class Process:
    """进程（简化）"""
    def __init__(self, pid: int):
        self.pid = pid
        self.regs = TrapFrame()
        self.memory: Dict[int, bytes] = {}
        self.fd_table: Dict[int, Any] = {0: None, 1: None, 2: None}  # stdin, stdout, stderr
        self.next_fd = 3


class SystemCallTable:
    """
    系统调用表

    存储每个系统调用的处理函数。
    """

    def __init__(self):
        self.table: Dict[int, Callable] = {}
        self._init_table()

    def _init_table(self):
        """初始化系统调用表"""
        self.table[SystemCallNumber.READ.value] = self.sys_read
        self.table[SystemCallNumber.WRITE.value] = self.sys_write
        self.table[SystemCallNumber.OPEN.value] = self.sys_open
        self.table[SystemCallNumber.CLOSE.value] = self.sys_close
        self.table[SystemCallNumber.EXIT.value] = self.sys_exit
        self.table[SystemCallNumber.GETPID.value] = self.sys_getpid
        self.table[SystemCallNumber.BRK.value] = self.sys_brk
        self.table[SystemCallNumber.MMAP.value] = self.sys_mmap
        self.table[SystemCallNumber.CLONE.value] = self.sys_clone

    def get_handler(self, syscall_number: int) -> Optional[Callable]:
        """获取系统调用处理函数"""
        return self.table.get(syscall_number)

    # 系统调用实现
    def sys_read(self, process: Process, args: List[int]) -> int:
        """read(int fd, void *buf, size_t count)"""
        fd = args[0]
        buf_addr = args[1]
        count = args[2]

        if fd not in process.fd_table:
            return -1

        # 简化：模拟读取
        data = b"Hello from read!"
        process.memory[buf_addr] = data[:count]
        return len(data)

    def sys_write(self, process: Process, args: List[int]) -> int:
        """write(int fd, const void *buf, size_t count)"""
        fd = args[0]
        buf_addr = args[1]
        count = args[2]

        if fd not in process.fd_table:
            return -1

        # 模拟写入
        data = process.memory.get(buf_addr, b'')
        written = len(data[:count])

        # 标准输出
        if fd == 1:
            print(f"  [write] {data[:count]}", end='')

        return written

    def sys_open(self, process: Process, args: List[int]) -> int:
        """open(const char *pathname, int flags, mode_t mode)"""
        pathname_addr = args[0]
        flags = args[1]
        mode = args[2]

        # 简化：创建新fd
        fd = process.next_fd
        process.next_fd += 1
        process.fd_table[fd] = {"pathname": "unknown", "flags": flags}

        return fd

    def sys_close(self, process: Process, args: List[int]) -> int:
        """close(int fd)"""
        fd = args[0]

        if fd in process.fd_table:
            del process.fd_table[fd]
            return 0
        return -1

    def sys_exit(self, process: Process, args: List[int]) -> int:
        """exit(int status)"""
        status = args[0]
        print(f"  [exit] 进程退出, status={status}")
        return 0

    def sys_getpid(self, process: Process, args: List[int]) -> int:
        """getpid()"""
        return process.pid

    def sys_brk(self, process: Process, args: List[int]) -> int:
        """brk(void *addr)"""
        new_addr = args[0]
        # 简化：更新进程brk
        return new_addr

    def sys_mmap(self, process: Process, args: List[int]) -> int:
        """mmap(void *addr, size_t length, int prot, int flags, int fd, off_t offset)"""
        addr = args[0]
        length = args[1]
        prot = args[2]
        flags = args[3]
        fd = args[4]
        offset = args[5]

        # 简化：分配内存
        alloc_addr = 0x10000000
        process.memory[alloc_addr] = b'\x00' * length
        return alloc_addr

    def sys_clone(self, process: Process, args: List[int]) -> int:
        """clone(int (*fn)(void *), void *child_stack, int flags, void *arg)"""
        fn = args[0]
        child_stack = args[1]
        flags = args[2]
        arg = args[3]

        # 简化：创建新进程
        new_pid = process.pid + 1000
        print(f"  [clone] 创建新进程 PID={new_pid}")
        return new_pid


class InterruptDescriptorTable:
    """
    中断描述符表 (IDT)

    存储中断/异常处理程序的入口地址。
    """

    def __init__(self):
        self.entries: Dict[int, int] = {}  # vector -> handler_address

        # 初始化常见中断
        self._init_idt()

    def _init_idt(self):
        """初始化IDT"""
        # 0x80 是系统调用向量
        self.entries[0x80] = 0xFFFF0000  # 模拟地址

        # 页面故障
        self.entries[0x0E] = 0xFFFF1000

    def set_entry(self, vector: int, handler: int):
        """设置中断处理程序"""
        self.entries[vector] = handler


class SystemCallDispatcher:
    """
    系统调用分发器

    负责从用户态切换到内核态，执行系统调用，然后返回。
    """

    def __init__(self):
        self.sct = SystemCallTable()
        self.idt = InterruptDescriptorTable()

        # 统计
        self.syscall_count = 0

    def handle_syscall(self, process: Process) -> int:
        """
        处理系统调用
        从trap frame中获取系统调用号和参数
        """
        syscall_number = process.regs.rax
        args = [
            process.regs.rdi,
            process.regs.rsi,
            process.regs.rdx,
            process.regs.r10,
            process.regs.r8,
            process.regs.r9,
        ]

        handler = self.sct.get_handler(syscall_number)
        if handler is None:
            print(f"  未知系统调用: {syscall_number}")
            return -1

        # 调用处理函数
        result = handler(process, args)

        # 设置返回值
        process.regs.rax = result
        self.syscall_count += 1

        return result

    def simulate_int_0x80(self, process: Process, syscall_number: int, args: List[int]):
        """
        模拟 int 0x80（软中断方式）
        """
        # 保存用户态寄存器
        original_rax = process.regs.rax

        # 设置系统调用号
        process.regs.rax = syscall_number
        process.regs.rdi = args[0] if len(args) > 0 else 0
        process.regs.rsi = args[1] if len(args) > 1 else 0
        process.regs.rdx = args[2] if len(args) > 2 else 0
        process.regs.r10 = args[3] if len(args) > 3 else 0
        process.regs.r8 = args[4] if len(args) > 4 else 0
        process.regs.r9 = args[5] if len(args) > 5 else 0

        # 调用分发器
        result = self.handle_syscall(process)

        # 恢复寄存器
        process.regs.rax = original_rax

        return result

    def simulate_syscall(self, process: Process, syscall_number: int, args: List[int]):
        """
        模拟 syscall 指令
        """
        # 使用快速系统调用方式
        return self.simulate_int_0x80(process, syscall_number, args)


def simulate_syscall():
    """
    模拟系统调用
    """
    print("=" * 60)
    print("系统调用：int 0x80 / syscall")
    print("=" * 60)

    # 创建进程
    process = Process(pid=1234)
    process.memory[0x1000] = b"Hello, syscall!"

    # 创建分发器
    dispatcher = SystemCallDispatcher()

    # 模拟int 0x80系统调用
    print("\n使用 int 0x80 方式调用系统调用:")
    print("-" * 50)

    # getpid
    print("\n1. getpid()")
    result = dispatcher.simulate_int_0x80(process, SystemCallNumber.GETPID.value, [])
    print(f"   返回值: {result}")

    # write
    print("\n2. write(1, buf, 13)")
    process.memory[0x2000] = b"Hello, World!"
    result = dispatcher.simulate_int_0x80(
        process,
        SystemCallNumber.WRITE.value,
        [1, 0x2000, 13]
    )
    print(f"   返回值: {result}")

    # read
    print("\n3. read(0, buf, 100)")
    result = dispatcher.simulate_int_0x80(
        process,
        SystemCallNumber.READ.value,
        [0, 0x3000, 100]
    )
    print(f"   返回值: {result}")

    # open
    print("\n4. open('/test.txt', O_RDONLY)")
    result = dispatcher.simulate_int_0x80(
        process,
        SystemCallNumber.OPEN.value,
        [0x4000, 0, 0]  # 简化
    )
    print(f"   返回值 (fd): {result}")

    # 模拟syscall指令方式
    print("\n使用 syscall 指令方式:")
    print("-" * 50)

    print("\n5. getpid() [via syscall]")
    result = dispatcher.simulate_syscall(process, SystemCallNumber.GETPID.value, [])
    print(f"   返回值: {result}")

    # mmap
    print("\n6. mmap()")
    result = dispatcher.simulate_syscall(
        process,
        SystemCallNumber.MMAP.value,
        [0, 4096, 7, 0x22, -1, 0]  # PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS
    )
    print(f"   返回值 (映射地址): 0x{result:08X}")

    # clone
    print("\n7. clone()")
    result = dispatcher.simulate_syscall(
        process,
        SystemCallNumber.CLONE.value,
        [0, 0, 0, 0]  # 简化
    )
    print(f"   返回值 (新PID): {result}")

    # exit
    print("\n8. exit(0)")
    dispatcher.simulate_syscall(
        process,
        SystemCallNumber.EXIT.value,
        [0]
    )

    # 统计
    print("\n" + "=" * 60)
    print("系统调用统计")
    print("=" * 60)
    print(f"  总系统调用数: {dispatcher.syscall_count}")

    # 显示系统调用表
    print("\n系统调用表:")
    print("-" * 50)
    print(f"  {'编号':<8} {'名称':<15}")
    print(f"  {'-'*30}")
    for num, name in [
        (0, "read"),
        (1, "write"),
        (2, "open"),
        (3, "close"),
        (39, "getpid"),
        (56, "clone"),
        (60, "exit"),
    ]:
        print(f"  {num:<8} {name:<15}")


if __name__ == "__main__":
    simulate_syscall()
