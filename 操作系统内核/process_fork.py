# -*- coding: utf-8 -*-
"""
算法实现：操作系统内核 / process_fork

本文件实现 process_fork 相关的算法功能。
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import time
import hashlib


@dataclass
class ProcessSignal:
    """信号"""
    signum: int
    pid: int  # 发送者


class ProcessExitStatus:
    """进程退出状态"""
    def __init__(self):
        self.exit_code: int = 0
        self.termsig: int = 0  # 导致终止的信号
        self.core_dumped: bool = False


class Process:
    """
    进程

    包含进程的所有信息。
    """

    # 进程状态
    STATE_ZOMBIE = "ZOMBIE"
    STATE_RUNNING = "RUNNING"
    STATE_SLEEPING = "SLEEPING"
    STATE_STOPPED = "STOPPED"

    def __init__(self, pid: int, name: str):
        self.pid = pid
        self.name = name

        # 标识
        self.ppid: int = 0  # 父进程PID
        self.tgid: int = pid  # 线程组ID
        self.uid: int = 0

        # 状态
        self.state = self.STATE_RUNNING
        self.exit_state = ProcessExitStatus()

        # 资源
        self.files: Dict[int, any] = {0: None, 1: None, 2: None}
        self.memory: Dict[int, bytes] = {}
        self.vm_size: int = 0

        # 调度
        self.priority: int = 0
        self.nice: int = 0
        self.utime: int = 0
        self.stime: int = 0
        self.start_time: int = int(time.time())

        # 父子关系
        self.children: List[Process] = []
        self.parent: Optional[Process] = None

        # 退出相关
        self.exit_code: int = 0
        self.pending_signals: Set[ProcessSignal] = set()

        # 程序
        self.program: Optional[str] = None
        self.argv: List[str] = []
        self.envp: Dict[str, str] = {}

    def copy_process(self) -> 'Process':
        """
        复制进程（fork的核心）
        返回新的子进程
        """
        # 创建新进程
        new_pid = self.pid + 1000  # 简化
        child = Process(new_pid, f"{self.name}_copy")

        # 复制属性
        child.ppid = self.pid
        child.uid = self.uid
        child.priority = self.priority
        child.nice = self.nice

        # 复制文件描述符
        child.files = self.files.copy()

        # 复制内存（COW，会在写时复制）
        child.memory = self.memory.copy()
        child.vm_size = self.vm_size

        # 父子关系
        child.parent = self
        self.children.append(child)

        return child

    def execve(self, program: str, argv: List[str], envp: Dict[str, str]):
        """
        替换进程映像
        """
        self.program = program
        self.argv = argv
        self.envp = envp
        # 清空内存，替换为新程序
        self.memory.clear()
        self.vm_size = 0
        print(f"  [PID={self.pid}] execve: {program}")

    def do_exit(self, code: int):
        """
        进程主动终止
        """
        self.exit_code = code
        self.state = self.STATE_ZOMBIE
        print(f"  [PID={self.pid}] exit({code})")
        print(f"  [PID={self.pid}] 进入ZOMBIE状态，等待父进程回收")

    def signal(self, signum: int):
        """发送信号"""
        signal = ProcessSignal(signum, self.pid)
        self.pending_signals.add(signal)
        print(f"  [PID={self.pid}] 收到信号 {signum}")


class ProcessManager:
    """
    进程管理器

    管理所有进程。
    """

    def __init__(self):
        self.processes: Dict[int, Process] = {}
        self.next_pid = 1
        self.zombies: List[Process] = []

    def create_init_process(self) -> Process:
        """创建init进程"""
        init = Process(1, "init")
        self.processes[1] = init
        self.next_pid = 2
        return init

    def fork(self, parent: Process) -> Process:
        """
        fork系统调用
        返回子进程PID
        """
        child = parent.copy_process()
        self.processes[child.pid] = child
        return child

    def do_execve(self, pid: int, program: str, argv: List[str], envp: Dict[str, str]):
        """execve系统调用"""
        if pid in self.processes:
            self.processes[pid].execve(program, argv, envp)

    def do_exit(self, pid: int, code: int):
        """exit系统调用"""
        if pid in self.processes:
            self.processes[pid].do_exit(code)
            self.zombies.append(self.processes[pid])

    def wait(self, pid: int) -> Optional[int]:
        """
        wait系统调用
        父进程等待子进程终止
        """
        if pid > 0:
            # 等待指定PID
            if pid in self.processes:
                proc = self.processes[pid]
                if proc.state == Process.STATE_ZOMBIE:
                    # 回收
                    if proc in self.zombies:
                        self.zombies.remove(proc)
                    exit_code = proc.exit_code
                    del self.processes[pid]
                    return exit_code
        elif pid == -1:
            # 等待任意子进程
            for child in list(self.zombies):
                exit_code = child.exit_code
                self.zombies.remove(child)
                del self.processes[child.pid]
                return exit_code

        return None

    def kill(self, pid: int, sig: int) -> bool:
        """发送信号"""
        if pid in self.processes:
            self.processes[pid].signal(sig)
            return True
        return False


def simulate_fork_exec():
    """
    模拟fork/exec
    """
    print("=" * 60)
    print("进程创建与终止：fork/exec")
    print("=" * 60)

    # 创建进程管理器
    manager = ProcessManager()

    # 创建init进程
    init = manager.create_init_process()
    print(f"\n创建init进程: PID={init.pid}, name={init.name}")

    # fork演示
    print("\n" + "-" * 50)
    print("fork() 演示")
    print("-" * 50)

    print("\n父进程调用fork():")
    child = manager.fork(init)
    print(f"  fork返回: 子进程PID={child.pid}")

    print("\n子进程状态:")
    print(f"  PID={child.pid}, PPID={child.ppid}, name={child.name}")
    print(f"  文件描述符: {len(child.files)} 个")
    print(f"  内存大小: {child.vm_size} bytes")

    # exec演示
    print("\n" + "-" * 50)
    print("execve() 演示")
    print("-" * 50)

    print("\n子进程调用execve('/bin/bash'):")
    child.execve("/bin/bash", ["/bin/bash", "-c", "echo hello"], {"HOME": "/root"})
    print(f"  程序: {child.program}")
    print(f"  参数: {child.argv}")
    print(f"  环境: HOME={child.envp.get('HOME')}")

    # 进程树
    print("\n" + "-" * 50)
    print("进程树")
    print("-" * 50)

    def print_process_tree(proc: Process, indent: int = 0):
        prefix = "  " * indent
        print(f"{prefix}PID={proc.pid}: {proc.name} (state={proc.state})")
        for child in proc.children:
            print_process_tree(child, indent + 1)

    print("\n当前进程树:")
    print_process_tree(init)

    # exit和wait演示
    print("\n" + "-" * 50)
    print("exit() 和 wait() 演示")
    print("-" * 50)

    print("\n子进程调用exit(42):")
    manager.do_exit(child.pid, 42)

    print("\n父进程调用wait():")
    exit_code = manager.wait(child.pid)
    print(f"  wait返回: exit_code={exit_code}")

    # kill演示
    print("\n" + "-" * 50)
    print("信号 (kill) 演示")
    print("-" * 50)

    # 创建新进程用于测试信号
    test_proc = Process(100, "test_signal")
    manager.processes[100] = test_proc

    print(f"\n发送信号 SIGTERM(15) 到 PID={test_proc.pid}:")
    manager.kill(test_proc.pid, 15)

    print(f"\n发送信号 SIGKILL(9) 到 PID={test_proc.pid}:")
    manager.kill(test_proc.pid, 9)


if __name__ == "__main__":
    simulate_fork_exec()
